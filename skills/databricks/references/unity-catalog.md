# Unity Catalog Reference

## 3-Level Namespace

```
catalog.schema.table
├── catalog       - Top-level container (e.g., prod, dev, raw)
├── schema        - Logical grouping (equivalent to database)
└── table/view    - Data object
```

## Object Types

| Object | Description |
|--------|-------------|
| CATALOG | Top-level namespace container |
| SCHEMA | Grouping of tables/views (= database) |
| TABLE | Managed or external table |
| VIEW | Logical view over tables |
| VOLUME | File storage (managed or external) |
| FUNCTION | User-defined functions |
| MODEL | MLflow registered models |

## Creating Objects

```sql
-- Create catalog
CREATE CATALOG IF NOT EXISTS my_catalog;

-- Create schema
CREATE SCHEMA IF NOT EXISTS my_catalog.my_schema
COMMENT 'Production data schema';

-- Create managed table
CREATE TABLE my_catalog.my_schema.orders (
  order_id BIGINT NOT NULL,
  customer_id BIGINT,
  amount DOUBLE,
  created_at TIMESTAMP
) USING DELTA;

-- Create external table
CREATE TABLE my_catalog.my_schema.ext_orders
USING DELTA
LOCATION 'abfss://container@storage.dfs.core.windows.net/orders';

-- Create volume
CREATE VOLUME my_catalog.my_schema.raw_files;
-- Upload path: /Volumes/my_catalog/my_schema/raw_files/
```

## Access Control (GRANT / REVOKE)

```sql
-- Grant on catalog
GRANT USE CATALOG ON CATALOG my_catalog TO `data_engineers`;

-- Grant on schema
GRANT USE SCHEMA, CREATE TABLE ON SCHEMA my_catalog.my_schema TO `data_engineers`;

-- Grant on table
GRANT SELECT ON TABLE my_catalog.my_schema.orders TO `analysts`;
GRANT MODIFY ON TABLE my_catalog.my_schema.orders TO `data_engineers`;

-- Grant to service principal
GRANT SELECT ON TABLE my_catalog.my_schema.orders TO `app-service-principal`;

-- Revoke
REVOKE SELECT ON TABLE my_catalog.my_schema.orders FROM `analysts`;

-- Show grants
SHOW GRANTS ON TABLE my_catalog.my_schema.orders;
SHOW GRANTS ON SCHEMA my_catalog.my_schema;
```

## Privilege Hierarchy

- `ALL PRIVILEGES` - Everything
- `USE CATALOG` - Required to use any object in catalog
- `USE SCHEMA` - Required to use any object in schema
- `SELECT` - Read table/view
- `MODIFY` - Insert/update/delete
- `CREATE TABLE` - Create tables in schema
- `CREATE SCHEMA` - Create schemas in catalog
- `READ VOLUME` / `WRITE VOLUME` - Access volume files

## Data Lineage

```sql
-- View column lineage (system tables)
SELECT *
FROM system.access.column_lineage
WHERE target_table_full_name = 'my_catalog.my_schema.orders'
LIMIT 50;

-- View table lineage
SELECT *
FROM system.access.table_lineage
WHERE target_table_full_name = 'my_catalog.my_schema.orders';
```

## Tags

```sql
-- Set tag on table
ALTER TABLE my_catalog.my_schema.orders
SET TAGS ('pii' = 'true', 'domain' = 'sales');

-- Set tag on column
ALTER TABLE my_catalog.my_schema.orders
ALTER COLUMN customer_id SET TAGS ('pii' = 'true');

-- List tags
SHOW TAGS ON TABLE my_catalog.my_schema.orders;
```

## Information Schema

```sql
-- List all tables in catalog
SELECT table_catalog, table_schema, table_name, table_type
FROM my_catalog.information_schema.tables;

-- List columns
SELECT column_name, data_type, is_nullable
FROM my_catalog.information_schema.columns
WHERE table_name = 'orders';

-- List all catalogs (system)
SELECT * FROM system.information_schema.catalogs;
```

## Row & Column Level Security

```sql
-- Row filter (dynamic data masking at row level)
CREATE FUNCTION my_catalog.my_schema.orders_filter(customer_id BIGINT)
RETURN IF(IS_ACCOUNT_GROUP_MEMBER('admins'), true, customer_id = CURRENT_USER());

ALTER TABLE my_catalog.my_schema.orders
SET ROW FILTER my_catalog.my_schema.orders_filter ON (customer_id);

-- Column mask
CREATE FUNCTION my_catalog.my_schema.mask_email(email STRING)
RETURN IF(IS_ACCOUNT_GROUP_MEMBER('admins'), email, 'REDACTED');

ALTER TABLE my_catalog.my_schema.customers
ALTER COLUMN email SET MASK my_catalog.my_schema.mask_email;
```

## Volumes (File Storage in UC)

```python
# Read from volume
df = spark.read.csv("/Volumes/my_catalog/my_schema/raw_files/data.csv", header=True)

# Write to volume
df.write.csv("/Volumes/my_catalog/my_schema/processed/output.csv")

# dbutils with volumes
dbutils.fs.ls("/Volumes/my_catalog/my_schema/raw_files/")
dbutils.fs.cp("/Volumes/my_catalog/my_schema/raw_files/file.csv",
              "/Volumes/my_catalog/my_schema/archive/file.csv")
```
