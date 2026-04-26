# dbt Reference Guide

## Project Structure

```
dbt_project/
├── dbt_project.yml
├── profiles.yml
├── models/
│   ├── staging/          # 1:1 with source tables
│   │   ├── _sources.yml  # source definitions
│   │   ├── _staging.yml  # staging model docs + tests
│   │   └── stg_*.sql
│   ├── intermediate/     # joins and business logic
│   │   └── int_*.sql
│   └── marts/            # final business-ready tables
│       ├── core/
│       └── finance/
├── tests/                # custom singular tests
├── macros/               # reusable SQL macros
├── seeds/                # static CSV data
└── snapshots/            # SCD Type 2
```

## Model Naming Conventions
- Staging: `stg_<source>__<entity>.sql` (e.g., `stg_salesforce__accounts.sql`)
- Intermediate: `int_<entity>_<verb>.sql` (e.g., `int_orders_joined.sql`)
- Marts: `<entity>.sql` or `fct_<entity>.sql` / `dim_<entity>.sql`

## dbt_project.yml Example
```yaml
name: my_project
version: '1.0.0'
config-version: 2

profile: 'my_project'

model-paths: ["models"]
test-paths: ["tests"]
seed-paths: ["seeds"]
macro-paths: ["macros"]
snapshot-paths: ["snapshots"]

models:
  my_project:
    staging:
      +materialized: view
      +schema: staging
    intermediate:
      +materialized: ephemeral
    marts:
      +materialized: table
      core:
        +schema: core
      finance:
        +schema: finance
```

## Materializations

| Type | When to use |
|------|------------|
| `view` | Staging, rarely queried directly |
| `table` | Small-medium marts, full refresh OK |
| `incremental` | Large tables, expensive to rebuild |
| `ephemeral` | Intermediate CTEs, never stored |
| `snapshot` | SCD Type 2 history tracking |

### Incremental Model Pattern
```sql
{{ config(
    materialized='incremental',
    unique_key='order_id',
    on_schema_change='merge',
    incremental_strategy='merge'
) }}

SELECT
    order_id,
    customer_id,
    order_date,
    total_amount,
    status,
    updated_at
FROM {{ ref('stg_orders') }}

{% if is_incremental() %}
WHERE updated_at > (SELECT MAX(updated_at) FROM {{ this }})
{% endif %}
```

## Sources Definition
```yaml
# models/staging/_sources.yml
version: 2

sources:
  - name: salesforce
    database: bronze_catalog
    schema: salesforce_raw
    freshness:
      warn_after: {count: 12, period: hour}
      error_after: {count: 24, period: hour}
    loaded_at_field: _ingested_at
    tables:
      - name: accounts
        description: "Raw Salesforce accounts"
      - name: opportunities
        description: "Raw Salesforce opportunities"
```

## Schema Tests (schema.yml)
```yaml
version: 2

models:
  - name: fct_orders
    description: "One row per order"
    columns:
      - name: order_id
        description: "Primary key"
        tests:
          - unique
          - not_null
      - name: customer_id
        tests:
          - not_null
          - relationships:
              to: ref('dim_customers')
              field: customer_id
      - name: status
        tests:
          - accepted_values:
              values: ['pending', 'processing', 'shipped', 'delivered', 'cancelled']
      - name: amount
        tests:
          - not_null
          - dbt_utils.expression_is_true:
              expression: ">= 0"
```

## Useful Macros

### generate_schema_name (override default)
```sql
-- macros/generate_schema_name.sql
{% macro generate_schema_name(custom_schema_name, node) -%}
    {%- set default_schema = target.schema -%}
    {%- if custom_schema_name is none -%}
        {{ default_schema }}
    {%- else -%}
        {{ custom_schema_name | trim }}
    {%- endif -%}
{%- endmacro %}
```

### Audit columns macro
```sql
-- macros/audit_columns.sql
{% macro audit_columns() %}
    CURRENT_TIMESTAMP() AS _dbt_updated_at,
    '{{ invocation_id }}' AS _dbt_invocation_id
{% endmacro %}
```

## Snapshots (SCD Type 2)
```sql
-- snapshots/customers_snapshot.sql
{% snapshot customers_snapshot %}

{{ config(
    target_schema='snapshots',
    unique_key='customer_id',
    strategy='timestamp',
    updated_at='updated_at',
) }}

SELECT * FROM {{ source('crm', 'customers') }}

{% endsnapshot %}
```

## dbt Commands Reference

```bash
# Run all models
dbt run

# Run specific model + dependencies
dbt run --select +fct_orders

# Run all models in a folder
dbt run --select staging.*

# Run tests
dbt test
dbt test --select fct_orders

# Check sources freshness
dbt source freshness

# Generate + serve docs
dbt docs generate
dbt docs serve

# Full refresh (ignore incremental logic)
dbt run --full-refresh --select fct_orders

# Debug connection
dbt debug
```

## Databricks + dbt Setup (profiles.yml)
```yaml
my_project:
  target: dev
  outputs:
    dev:
      type: databricks
      host: "<workspace>.azuredatabricks.net"
      http_path: "/sql/1.0/warehouses/<warehouse-id>"
      token: "{{ env_var('DBT_DATABRICKS_TOKEN') }}"
      catalog: dev_catalog
      schema: dbt_dev
      threads: 4
    prod:
      type: databricks
      host: "<workspace>.azuredatabricks.net"
      http_path: "/sql/1.0/warehouses/<warehouse-id>"
      token: "{{ env_var('DBT_DATABRICKS_TOKEN') }}"
      catalog: prod_catalog
      schema: gold
      threads: 8
```
