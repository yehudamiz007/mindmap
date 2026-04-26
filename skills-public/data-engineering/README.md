# Data Engineering Skills for OpenClaw

A collection of OpenClaw AgentSkills for the modern data stack.

## Skills

### 🔧 data-engineer
Senior Data Engineer assistant for the full modern data stack.

**Covers:** Databricks, Apache Spark, PySpark, dbt, Azure Data Factory, ADLS Gen2, S3, Unity Catalog, Delta Lake, Apache Airflow, medallion architecture (Bronze/Silver/Gold), data quality, schema design, partitioning, streaming, batch processing.

**Triggers on:** "pipeline", "ETL", "ELT", "dbt", "Spark", "Databricks", "Delta Lake", "data lake", "SQL query", "data model", "data engineering", "medallion", "streaming", "batch", "Airflow", "data quality"

### 🏗️ databricks
Databricks Lakehouse Platform assistant.

**Covers:** Notebooks, Unity Catalog, Delta Lake, Genie (AI/BI), Delta Live Tables (DLT), MLflow, Clusters, Workflows, Databricks Apps, dashboards, Repos, secrets.

**Triggers on:** "Databricks", "notebook", "Unity Catalog", "Delta Lake", "Genie", "DLT", "MLflow", "Spark", "cluster", "lakehouse", "DBFS", "dbutils", "Databricks Apps"

## Installation

Copy the skill folder to your OpenClaw workspace:
```
~/.openclaw/workspace/skills/data-engineer/
~/.openclaw/workspace/skills/databricks/
```

## Structure

```
data-engineering/
├── data-engineer/
│   ├── SKILL.md
│   └── references/
│       ├── architecture.md    # Medallion, design patterns
│       ├── azure.md           # Azure-specific (ADF, ADLS, Synapse)
│       └── dbt-reference.md   # dbt models, tests, macros
└── databricks/
    ├── SKILL.md
    └── references/
        ├── apps.md
        ├── clusters.md
        ├── delta-lake.md
        ├── genie.md
        ├── jobs.md
        ├── mlflow.md
        ├── notebooks-clusters.md
        ├── unity-catalog.md
        └── workflows-dlt.md
```
