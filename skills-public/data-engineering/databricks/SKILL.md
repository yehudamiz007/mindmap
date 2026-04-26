---
name: databricks
description: Databricks platform assistant. Use when the user asks about Databricks - running notebooks, querying data with SQL, managing clusters, Unity Catalog (tables, schemas, catalogs, lineage, access control), Delta Lake, Databricks Genie (AI/BI), Delta Live Tables (DLT), MLflow, Spark jobs, workflows, Databricks Apps (Streamlit/Gradio/FastAPI deployed in workspace), dashboards, Repos, secrets, AgentBricks, Lakebase, Zerobus, Databricks AI Dev Kit, or anything related to the Databricks Lakehouse Platform. Triggers on phrases like "Databricks", "notebook", "Unity Catalog", "Delta Lake", "Genie", "DLT", "MLflow", "Spark", "cluster", "lakehouse", "DBFS", "dbutils", "Databricks Apps", "AgentBricks", "Lakebase", "Zerobus", "AI Dev Kit".
---

# Databricks Skill

You are a Databricks expert. Help users work with the full Databricks Lakehouse Platform, including the latest 2025-2026 features.

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

## 🆕 New Features (2025-2026)

### AgentBricks
Databricks-native framework for building, evaluating and deploying AI agents on the Lakehouse.
- Build agents that can query data in Unity Catalog using natural language
- Combines MLflow + Mosaic AI + UC as the agent backbone
- Agent evaluation with built-in benchmarks (relevance, groundedness, safety)
- Deploy agents as REST endpoints via Model Serving
- Supports LangChain, LlamaIndex, and custom Python agents
- Key concept: **Agent-as-a-table** - agents are versioned and tracked in UC like models

```python
import mlflow
from databricks.agents import deploy

# Register and deploy an agent
mlflow.set_registry_uri("databricks-uc")
with mlflow.start_run():
    mlflow.langchain.log_model(chain, "agent")

deploy(model_name="catalog.schema.my_agent", version=1)
```

### Lakebase
Databricks' managed operational database layer built on top of Delta Lake.
- Brings OLTP-style workloads (low-latency reads/writes) into the Lakehouse
- Postgres-compatible SQL interface
- Real-time row-level updates without full file rewrites
- Unified governance via Unity Catalog (same permissions, lineage, tags)
- Use case: replace standalone operational DBs (RDS, Cosmos) while keeping data in the lake
- Supports connection via JDBC/ODBC and standard Postgres clients

```sql
-- Create a Lakebase table (Postgres-compatible)
CREATE TABLE orders (
  order_id SERIAL PRIMARY KEY,
  customer_id INT,
  status TEXT,
  updated_at TIMESTAMP DEFAULT NOW()
);

-- Low-latency upsert
INSERT INTO orders (order_id, customer_id, status)
VALUES (1, 42, 'shipped')
ON CONFLICT (order_id) DO UPDATE SET status = EXCLUDED.status;
```

### Zerobus
Databricks' real-time streaming message bus integrated into the Lakehouse.
- Kafka-compatible API - drop-in replacement for Kafka/Confluent
- Native integration with DLT (Delta Live Tables) and Spark Structured Streaming
- Governed by Unity Catalog: topics = UC assets with lineage and access control
- No separate Kafka cluster to manage - fully serverless
- Supports exactly-once delivery semantics

```python
# Read from Zerobus topic (Kafka-compatible)
df = (spark.readStream
  .format("kafka")
  .option("kafka.bootstrap.servers", "<zerobus-endpoint>")
  .option("subscribe", "catalog.schema.my_topic")
  .load())

# Write to Zerobus
(df.writeStream
  .format("kafka")
  .option("kafka.bootstrap.servers", "<zerobus-endpoint>")
  .option("topic", "catalog.schema.output_topic")
  .start())
```

### Databricks AI Dev Kit
SDK and CLI toolset for building AI/ML applications on Databricks.
- `databricks-ai-devkit` Python package
- Local development with hot-reload against live Databricks workspace
- Built-in testing framework for agents and ML pipelines
- Prompt management and versioning
- Integration with VS Code extension (Databricks extension)
- DABs (Databricks Asset Bundles) for packaging and deploying AI apps as code

```bash
# Install
pip install databricks-ai-devkit

# Initialize a new AI project
databricks-ai init my-agent-project

# Run locally with live workspace connection
databricks-ai run --profile my_profile

# Deploy to workspace
databricks bundle deploy
```

## Reference Files

- **[references/unity-catalog.md](references/unity-catalog.md)** - 3-level namespace, governance, lineage, access control, volumes
- **[references/delta-lake.md](references/delta-lake.md)** - Delta operations, time travel, optimization, streaming
- **[references/genie.md](references/genie.md)** - Genie Spaces setup, AI/BI dashboards, natural language queries
- **[references/notebooks-clusters.md](references/notebooks-clusters.md)** - Notebook magic commands, dbutils, cluster config, widgets
- **[references/workflows-dlt.md](references/workflows-dlt.md)** - Jobs, DLT pipelines, expectations, task orchestration
- **[references/mlflow.md](references/mlflow.md)** - Experiment tracking, model registry, serving endpoints
- **[references/apps.md](references/apps.md)** - Databricks Apps: Streamlit, Gradio, FastAPI, deployment, auth, Unity Catalog access
- **[references/clusters.md](references/clusters.md)** - Cluster types, config, policies, instance pools, SQL warehouses, libraries
- **[references/jobs.md](references/jobs.md)** - Jobs, task types, task values, ForEach, conditions, scheduling, repair, DAB, monitoring
- **[references/agentbricks.md](references/agentbricks.md)** - AgentBricks: building, evaluating and deploying AI agents on the Lakehouse
- **[references/lakebase.md](references/lakebase.md)** - Lakebase: operational database layer, Postgres-compatible, UC governed
- **[references/zerobus.md](references/zerobus.md)** - Zerobus: real-time streaming message bus, Kafka-compatible
- **[references/ai-dev-kit.md](references/ai-dev-kit.md)** - Databricks AI Dev Kit: SDK, CLI, DABs, local dev

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
