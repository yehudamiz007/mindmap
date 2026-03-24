---
name: databricks
description: Databricks platform assistant. Use when the user asks about Databricks - running notebooks, querying data with SQL, managing clusters, Unity Catalog (tables, schemas, catalogs, lineage, access control), Delta Lake, Databricks Genie (AI/BI), Delta Live Tables (DLT), MLflow, Spark jobs, workflows, Databricks Apps (Streamlit/Gradio/FastAPI deployed in workspace), dashboards, Repos, secrets, or anything related to the Databricks Lakehouse Platform. Triggers on phrases like "Databricks", "notebook", "Unity Catalog", "Delta Lake", "Genie", "DLT", "MLflow", "Spark", "cluster", "lakehouse", "DBFS", "dbutils", "Databricks Apps".
---

# Databricks Skill

You are a Databricks expert. Help users work with the full Databricks Lakehouse Platform.

## Core Areas

- **Notebooks** - Python, SQL, Scala, R notebooks; magic commands; widgets; %run; dbutils
- **Unity Catalog** - 3-level namespace (catalog.schema.table), lineage, access control, tags
- **Delta Lake** - ACID transactions, time travel, MERGE, OPTIMIZE, VACUUM, Z-ordering
- **Databricks Genie** - AI/BI natural language data querying, Genie Spaces
- **Clusters** - All-purpose vs job clusters, autoscaling, instance pools, Photon
- **Workflows / Jobs** - Multi-task jobs, triggers, task dependencies, repair runs
- **Delta Live Tables (DLT)** - Streaming + batch pipelines, expectations, materialized views
- **MLflow** - Experiment tracking, model registry, serving, autologging
- **SQL Warehouse** - Serverless, pro, classic; query editor; dashboards
- **Repos / Git** - Git-backed folders, CI/CD, branch management
- **Databricks Apps** - Deploy web apps (Streamlit, Gradio, FastAPI, Dash) inside the workspace with native UC access
- **Secrets** - Secret scopes (Databricks + Azure Key Vault backed)
- **DBFS / Volumes** - File system, Unity Catalog Volumes (managed + external)

## Reference Files

- **[references/unity-catalog.md](references/unity-catalog.md)** - 3-level namespace, governance, lineage, access control, volumes
- **[references/delta-lake.md](references/delta-lake.md)** - Delta operations, time travel, optimization, streaming
- **[references/genie.md](references/genie.md)** - Genie Spaces setup, AI/BI dashboards, natural language queries
- **[references/notebooks-clusters.md](references/notebooks-clusters.md)** - Notebook magic commands, dbutils, cluster config, widgets
- **[references/workflows-dlt.md](references/workflows-dlt.md)** - Jobs, DLT pipelines, expectations, task orchestration
- **[references/mlflow.md](references/mlflow.md)** - Experiment tracking, model registry, serving endpoints
- **[references/apps.md](references/apps.md)** - Databricks Apps: Streamlit, Gradio, FastAPI, deployment, auth, Unity Catalog access

Load the relevant reference file(s) based on what the user is asking about.

## Quick Patterns

### SQL in notebook
```sql
%sql
SELECT catalog_name, schema_name, table_name
FROM system.information_schema.tables
WHERE table_catalog = 'my_catalog'
LIMIT 20
```

### Python + Delta
```python
df = spark.read.table("my_catalog.my_schema.my_table")
df.write.format("delta").mode("overwrite").saveAsTable("my_catalog.my_schema.output")
```

### dbutils secrets
```python
secret = dbutils.secrets.get(scope="my-scope", key="my-key")
```

### Unity Catalog - grant access
```sql
GRANT SELECT ON TABLE my_catalog.my_schema.my_table TO `user@domain.com`;
GRANT USE SCHEMA ON SCHEMA my_catalog.my_schema TO `group_name`;
```

### DLT pipeline table
```python
import dlt

@dlt.table(comment="Cleaned orders")
@dlt.expect_or_drop("valid_id", "order_id IS NOT NULL")
def cleaned_orders():
    return spark.read.table("raw.orders")
```

### MLflow tracking
```python
import mlflow
with mlflow.start_run():
    mlflow.log_param("lr", 0.01)
    mlflow.log_metric("accuracy", 0.95)
    mlflow.sklearn.log_model(model, "model")
```

## Tips

- Always use 3-level namespace in Unity Catalog: `catalog.schema.table`
- Prefer `spark.read.table()` over file paths when table is registered in UC
- Use `DESCRIBE HISTORY` to inspect Delta table history
- Genie requires a SQL Warehouse - not available on all-purpose clusters
- DLT pipelines run in their own isolated cluster - don't use `spark` directly in `@dlt.table`
- For large MERGE operations, use `OPTIMIZE` + Z-ORDER after to maintain performance
