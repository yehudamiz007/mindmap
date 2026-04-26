# Azure Data Engineering Reference

## Azure Data Lake Storage Gen2 (ADLS)

### Container Structure
```
storage-account/
├── raw/                    # Bronze zone - raw ingestion
│   ├── salesforce/
│   │   └── accounts/
│   │       └── 2024/01/15/
│   │           └── accounts_20240115.json
│   └── events/
├── processed/              # Silver zone - cleaned data
│   └── orders/
│       └── delta/          # Delta Lake files
└── curated/                # Gold zone - business-ready
    └── sales_summary/
```

### Authentication Methods

#### Service Principal (recommended for production)
```python
storage_account = "mystorageaccount"
client_id = dbutils.secrets.get("kv-scope", "sp-client-id")
client_secret = dbutils.secrets.get("kv-scope", "sp-client-secret")
tenant_id = dbutils.secrets.get("kv-scope", "tenant-id")

spark.conf.set(f"fs.azure.account.auth.type.{storage_account}.dfs.core.windows.net", "OAuth")
spark.conf.set(f"fs.azure.account.oauth.provider.type.{storage_account}.dfs.core.windows.net",
               "org.apache.hadoop.fs.azurebfs.oauth2.ClientCredsTokenProvider")
spark.conf.set(f"fs.azure.account.oauth2.client.id.{storage_account}.dfs.core.windows.net", client_id)
spark.conf.set(f"fs.azure.account.oauth2.client.secret.{storage_account}.dfs.core.windows.net", client_secret)
spark.conf.set(f"fs.azure.account.oauth2.client.endpoint.{storage_account}.dfs.core.windows.net",
               f"https://login.microsoftonline.com/{tenant_id}/oauth2/token")
```

#### Managed Identity (recommended for Databricks on Azure)
```python
# In cluster config or via Unity Catalog external location - no code needed
# Just use abfss:// paths directly
df = spark.read.format("delta").load("abfss://processed@mystorageaccount.dfs.core.windows.net/orders/")
```

#### SAS Token (dev/testing only)
```python
spark.conf.set(
    f"fs.azure.sas.raw.{storage_account}.dfs.core.windows.net",
    dbutils.secrets.get("kv-scope", "sas-token")
)
```

### ABFSS Path Format
```
abfss://<container>@<storage-account>.dfs.core.windows.net/<path>

# Examples:
abfss://raw@mystorageaccount.dfs.core.windows.net/salesforce/accounts/
abfss://processed@mystorageaccount.dfs.core.windows.net/orders/delta/
```

---

## Azure Data Factory (ADF)

### Common Pipeline Patterns

#### Copy Activity: REST API → ADLS
- Source: REST connector with pagination
- Sink: ADLS Gen2, format: JSON or Parquet
- Use: Initial ingestion, daily snapshots

#### Copy Activity: SQL Server → Delta Lake
- Source: Azure SQL / SQL Server
- Sink: Azure Databricks Delta (via Databricks linked service)
- Use: On-prem to cloud migration, CDC

#### Databricks Notebook Activity
```json
{
    "name": "RunTransformation",
    "type": "DatabricksNotebook",
    "linkedServiceName": { "referenceName": "AzureDatabricks" },
    "typeProperties": {
        "notebookPath": "/Shared/pipelines/silver_transform",
        "baseParameters": {
            "run_date": "@pipeline().parameters.run_date",
            "env": "@pipeline().globalParameters.environment"
        }
    }
}
```

#### Trigger Types
- **Schedule trigger:** Cron-based, use for daily/hourly batches
- **Tumbling window:** For backfill-friendly pipelines with window context
- **Event trigger:** ADLS file arrival, use for streaming-like ingestion
- **Manual/on-demand:** Testing and ad-hoc runs

### ADF vs Databricks Workflows
| Use ADF when | Use Databricks Workflows when |
|---|---|
| Orchestrating non-Databricks services (AAS, SQL DW) | Pure Databricks/Spark workloads |
| Copying data between Azure services | Complex Spark DAGs |
| Simple transformations with GUI | dbt orchestration |
| Enterprise integration with on-prem | Delta Live Tables |

---

## Unity Catalog

### 3-Level Namespace
```sql
-- catalog.schema.table
SELECT * FROM prod_catalog.gold.fct_orders;

-- Set default catalog in session
USE CATALOG prod_catalog;
USE SCHEMA gold;
SELECT * FROM fct_orders;
```

### External Locations
```sql
-- Register external location (done once by admin)
CREATE EXTERNAL LOCATION raw_adls
URL 'abfss://raw@mystorageaccount.dfs.core.windows.net/'
WITH (STORAGE CREDENTIAL my_credential);

-- Create external table on ADLS
CREATE TABLE bronze.salesforce_accounts
USING DELTA
LOCATION 'abfss://raw@mystorageaccount.dfs.core.windows.net/salesforce/accounts/';
```

### Access Control
```sql
-- Grant table access
GRANT SELECT ON TABLE prod_catalog.gold.fct_orders TO `data-analysts@company.com`;

-- Grant schema access
GRANT USE SCHEMA, SELECT ON SCHEMA prod_catalog.gold TO `bi-team`;

-- Column-level masking (PII)
CREATE FUNCTION mask_email(email STRING)
  RETURN IF(IS_MEMBER('data-engineers'), email, REGEXP_REPLACE(email, '(.)(.*)(@.*)', '$1***$3'));

ALTER TABLE silver.customers ALTER COLUMN email
  SET MASK mask_email;
```

### Delta Sharing
```sql
-- Create share for external consumers
CREATE SHARE orders_share;
ADD TABLE prod_catalog.gold.fct_orders TO SHARE orders_share;

-- Create recipient
CREATE RECIPIENT partner_company;

-- Grant share
GRANT SELECT ON SHARE orders_share TO RECIPIENT partner_company;
```

---

## Databricks on Azure - Key Settings

### Cluster Configuration (Spark Config)
```
spark.sql.adaptive.enabled true
spark.sql.adaptive.coalescePartitions.enabled true
spark.databricks.delta.preview.enabled true
spark.sql.shuffle.partitions 400
spark.databricks.io.cache.enabled true
```

### Delta Lake Optimizations on Azure
```sql
-- Auto-optimize on write
ALTER TABLE bronze.events
SET TBLPROPERTIES (
  'delta.autoOptimize.optimizeWrite' = 'true',
  'delta.autoOptimize.autoCompact' = 'true'
);

-- Set retention (default 7 days)
ALTER TABLE silver.orders
SET TBLPROPERTIES ('delta.logRetentionDuration' = 'interval 30 days');
```

### Databricks Secrets (Key Vault-backed)
```python
# CLI: databricks secrets create-scope --scope kv-scope --initial-manage-principal users
# Then link to Azure Key Vault

# Usage in notebooks:
token = dbutils.secrets.get(scope="kv-scope", key="api-token")
```
