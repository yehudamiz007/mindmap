# Azure Data Services - Quick Reference

## Azure Data Factory (ADF)

### What it is
Managed ETL/ELT orchestration service. Think of it as the "glue" that moves data between Azure services.

### Best for
- Copying data between Azure services (SQL → ADLS, ADLS → Databricks)
- Orchestrating non-Databricks workloads
- Low-code transformations (Mapping Data Flows)
- Scheduling and monitoring pipelines

### Key Concepts
- **Linked Services** - connections to data stores (ADLS, SQL, REST, etc.)
- **Datasets** - pointer to data within a linked service
- **Activities** - Copy, Notebook, Web, ForEach, If Condition, etc.
- **Pipelines** - DAG of activities
- **Triggers** - Schedule, Tumbling Window, Event, Manual

### Pricing
- Orchestration: ~$0.001/activity run
- Copy: $0.25/DIU-hour (Data Integration Units)
- Data Flows: cluster-based ($0.20-$1.00/hour)
- **Tip**: Use Databricks for heavy transformations, ADF just for orchestration

---

## Azure Data Lake Storage Gen2 (ADLS)

### What it is
Azure Blob Storage with hierarchical namespace (HNS) enabled. The standard data lake storage for Azure.

### Key Features
- Hierarchical namespace (folder-level operations, atomic rename)
- POSIX-compatible ACLs (folder/file level permissions)
- Integration with Unity Catalog External Locations
- Lifecycle management (hot → cool → archive tiers)

### Container Design (Standard)
```
storage-account/
├── raw/          # Bronze - immutable, source-as-is
├── processed/    # Silver - Delta Lake format
├── curated/      # Gold - aggregated
└── system/       # checkpoints, logs, temp
```

### Cost
- Hot tier: $0.023/GB/month
- Cool tier: $0.010/GB/month
- Archive: $0.001/GB/month (15h retrieval time)
- **Tip**: Move raw data >90 days old to Cool automatically via lifecycle policy

---

## Azure Databricks

### What it is
Managed Apache Spark platform with Delta Lake, MLflow, Unity Catalog, and collaborative notebooks.

### Best for
- Heavy Spark processing (TB-scale)
- Machine learning and MLOps
- Delta Lake management
- Streaming with DLT

### Key Components
- All-purpose clusters (interactive, shared)
- Job clusters (single-use, auto-terminate)
- SQL Warehouses (BI queries, Power BI)
- Workflows (job orchestration)
- Delta Live Tables (streaming pipelines)

### Cost
- DBUs (Databricks Units) + underlying VM cost
- Serverless SQL: ~$0.22/DBU (no cluster management)
- Jobs: ~$0.15/DBU
- **Tip**: Use spot/preemptible VMs for job clusters (60-80% cheaper)

---

## Azure Synapse Analytics

### What it is
Unified analytics service combining data warehousing (Synapse SQL) + big data (Synapse Spark) + ADF-like pipelines.

### Best for
- SQL-centric teams migrating from SQL DW / DW on-prem
- Tight Power BI integration without Databricks
- Hybrid: some Spark + some SQL

### When to Choose Synapse over Databricks
- Team is SQL-heavy, not Python/Spark
- You're on a Synapse enterprise agreement
- Need native PolyBase for SQL Server integration

### When to Choose Databricks over Synapse
- MLOps / ML workloads
- Delta Lake as primary format
- Complex Spark tuning needed
- Larger Spark community support

---

## Microsoft Fabric

### What it is
Microsoft's unified SaaS data platform. Combines Power BI + Synapse + ADF + Databricks capabilities in one service on top of OneLake.

### Key Components
- **OneLake** - single storage lake (Delta Parquet)
- **Lakehouse** - Delta Lake + SQL endpoint
- **Dataflows Gen2** - low-code Power Query ETL
- **Data Pipelines** - ADF-like orchestration
- **Notebooks** - Spark (Python/Scala/SQL)
- **Warehouse** - T-SQL serverless warehouse
- **Semantic Model** - Power BI dataset
- **Real-Time Intelligence** - Event Streams + KQL Database

### Best for
- All-Microsoft shops (M365, Power BI, Teams integration)
- Teams that want SaaS (no cluster management)
- Power BI as primary BI tool

### Limitations vs Databricks
- Less Spark control and tuning options
- No MLflow (uses separate ML workspace)
- Younger platform, some features still in preview

---

## Azure Event Hubs

### What it is
Managed Kafka-compatible message bus. Fully serverless, partitioned event stream.

### Best for
- Real-time streaming ingestion
- Decoupling producers from consumers
- CDC event delivery

### Key Concepts
- **Namespace** - container for event hubs (topics)
- **Event Hub** = Kafka topic (partitioned log)
- **Consumer Group** - independent reader of a hub
- **Capture** - auto-dump to ADLS (bypass Spark for archive)

### Tiers
- Basic: 1 consumer group, 1 day retention
- Standard: 20 consumer groups, 7 days retention
- Premium: 100 consumer groups, 90 days, schema registry
- Dedicated: reserved capacity, unlimited retention

---

## Azure Stream Analytics

### What it is
Serverless real-time SQL query engine over streaming data.

### Best for
- Simple aggregations on streams (no Spark needed)
- Alerting and anomaly detection
- Transforming and routing events to multiple outputs

### When to Use ASA vs DLT
- ASA: simple SQL aggregations, no Python, low latency alerting
- DLT: complex transformations, Python/Spark, Delta output, stateful processing

### Example (ASA Query)
```sql
SELECT
    IoTHub.ConnectionDeviceId AS DeviceId,
    AVG(temperature) AS AvgTemp,
    System.Timestamp AS WindowEnd
FROM IoTInput
GROUP BY
    IoTHub.ConnectionDeviceId,
    TumblingWindow(minute, 5)
HAVING AVG(temperature) > 80
```

---

## Microsoft Purview

### What it is
Enterprise data catalog and governance service. Scans, classifies, and maps data across all Azure (and non-Azure) sources.

### Best for
- Automated data discovery and classification
- Enterprise data lineage (cross-platform)
- Compliance (GDPR, HIPAA classification)
- Business glossary

### Unity Catalog vs Purview
| | Unity Catalog | Microsoft Purview |
|---|---|---|
| Scope | Databricks assets only | All Azure + external |
| Access control | ✅ Native | ❌ Read-only catalog |
| Lineage | Databricks lineage | Cross-platform lineage |
| Classification | Tags | Automated (regex + ML) |
| Use together? | ✅ Yes - they complement each other |

---

## Azure Key Vault

### What it is
Managed secrets, keys, and certificates store.

### Integration with Databricks
```python
# Create Key Vault-backed secret scope (once, via CLI)
# databricks secrets create-scope --scope kv-scope --initial-manage-principal users

# Read in notebook
secret = dbutils.secrets.get(scope="kv-scope", key="my-secret")

# Use in spark config
spark.conf.set("fs.azure.account.key.mystorageaccount.dfs.core.windows.net",
               dbutils.secrets.get("kv-scope", "adls-key"))
```

### Best Practice
- Never hardcode secrets in notebooks or code
- Use Managed Identity where possible (no secret needed)
- Rotate secrets via Key Vault rotation policies
