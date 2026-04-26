# Data Architecture Design Patterns - Azure

## 1. Medallion Architecture (Default)

The standard Databricks/Azure lakehouse pattern. Always start here unless there's a specific reason not to.

### Layers

| Layer | Storage | Format | Purpose | Who writes |
|---|---|---|---|---|
| Bronze | ADLS raw/ | Delta (or Parquet) | Exact copy of source, immutable | ADF / ingestion pipeline |
| Silver | ADLS processed/ | Delta | Cleaned, typed, deduped, validated | Databricks / dbt |
| Gold | ADLS curated/ | Delta | Business aggregates, star/wide schema | Databricks / dbt |

### Key Rules
- **Bronze is sacred** - never transform, never delete. It's your audit trail.
- **Silver enforces schema** - use Delta schema enforcement + Evolution
- **Gold is for consumers** - design for the query pattern, not the source
- **Each layer has its own schema** in Unity Catalog: `catalog.bronze`, `catalog.silver`, `catalog.gold`

### When to Add a Layer (Platinum)
Add a "platinum" or "serving" layer when:
- You need heavily pre-aggregated data for high-QPS APIs
- You need different physical formats (e.g., Parquet-only for a non-Databricks consumer)

---

## 2. Lambda Architecture

Use when you need **both real-time and historical batch** views, and they must serve the same query.

```
                ┌─────────────────┐
                │   Batch Layer   │
Sources ──────► │  ADF + Spark    ├──► Batch Views
    │           └─────────────────┘         │
    │                                       ▼
    │           ┌─────────────────┐    ┌─────────┐
    └──────────►│   Speed Layer   ├───►│ Serving │──► Consumers
                │  Event Hubs+DLT │    │  Layer  │
                └─────────────────┘    └─────────┘
```

### Pros
- Real-time + batch in same query
- Batch corrects streaming errors over time

### Cons
- Two codebases to maintain (batch + streaming logic)
- Complex merge at serving layer

### Azure Implementation
- Batch: ADF + Databricks (daily/hourly)
- Speed: Event Hubs + Delta Live Tables
- Serving: Delta Lake with MERGE to reconcile

---

## 3. Kappa Architecture

Use when **streaming can replace batch**. Simpler than Lambda - one codebase.

```
Sources ──► Event Hubs ──► Databricks DLT ──► Delta Lake ──► Serving
                │
                └── Retain events for N days
                    (reprocess = replay from offset 0)
```

### When to Use Kappa
- Source events are naturally ordered and complete
- You can tolerate reprocessing time for historical corrections
- Event Hubs retention covers your backfill window (max 90 days standard, unlimited with Capture)

### Reprocessing Pattern
```python
# Replay from beginning
(spark.readStream
  .format("kafka")
  .option("startingOffsets", "earliest")  # replay all
  .option("subscribe", "my_topic")
  .load()
)
```

---

## 4. Data Mesh

Use for **large organizations** with multiple domains and teams that own their data.

### Core Principles
1. **Domain ownership** - each team owns its data product end-to-end
2. **Data as a product** - SLAs, documentation, discoverability
3. **Self-serve platform** - central team provides infrastructure templates
4. **Federated governance** - Unity Catalog + Purview as the glue

### Azure Implementation

```
Platform Team:
- Provides Unity Catalog setup
- Provides IaC templates (Terraform/Bicep) for new domains
- Operates Microsoft Purview for catalog + lineage
- Sets governance policies (tagging, retention, PII)

Domain Teams (e.g., Sales, Marketing, Finance):
- Own their Databricks workspace or Lakehouse
- Publish Data Products to Unity Catalog
- Grant access via UC permissions
- Use Delta Sharing for cross-domain or external sharing
```

### Data Product Standards
Every domain data product must have:
- [ ] Schema documented in Unity Catalog (comments on tables + columns)
- [ ] SLA defined (freshness, quality score)
- [ ] Owner tag set
- [ ] PII columns masked via UC column masking
- [ ] At least one quality expectation (DLT or Great Expectations)

---

## 5. Hub-and-Spoke (Enterprise Integration)

Use when multiple systems need to exchange data via a central hub.

```
CRM ──────────────────────────────────► Consumers
                 ▲                    │  - BI team
ERP ──► ADF ──► │ ADLS Gen2 (Hub) ───┤  - Data Science
                 │ Unity Catalog      │  - External (Delta Sharing)
API ────────────►│                    │  - Operational Apps (Lakebase)
```

### When to Use
- Multiple source systems with different formats/frequencies
- Central data team managing all pipelines
- Consumers need a single source of truth

---

## 6. Event-Driven Architecture

Use when systems must react to data changes in near-real-time.

```
Source DB ──► Debezium CDC ──► Event Hubs ──► DLT ──► Delta Lake
                                    │
                                    ├──► Azure Function (alert)
                                    └──► Logic App (workflow)
```

### CDC (Change Data Capture) on Azure
- **Debezium** on Azure Kubernetes Service - full CDC for any DB
- **ADF Change Data Capture** - native CDC for Azure SQL, SQL Server
- **Cosmos DB Change Feed** - built-in CDC for Cosmos
- **SQL Server CDC + ADF** - for on-prem sources

---

## Architecture Decision Checklist

When designing a new data platform, answer these questions:

### Data Characteristics
- [ ] Batch or streaming (or both)?
- [ ] Volume: GB/day or TB/day?
- [ ] Velocity: real-time (<1s), near-real-time (<1min), or batch?
- [ ] Variety: structured SQL, semi-structured JSON, unstructured files?

### Business Requirements
- [ ] Who are the consumers? (BI, ML, APIs, operational apps)
- [ ] SLA for data freshness? (hourly, daily, real-time)
- [ ] Data retention requirements? (regulatory, cost)
- [ ] PII/GDPR requirements?

### Technical Constraints
- [ ] Existing Azure services in use?
- [ ] Team skills (SQL-heavy? Python/Spark? Low-code?)
- [ ] Budget (serverless vs dedicated compute)
- [ ] Multi-region requirements?

### Output
Based on answers → choose:
- Architecture pattern (medallion / lambda / kappa / mesh)
- Ingestion service (ADF / Event Hubs / Fabric Pipelines)
- Processing engine (Databricks / Synapse / Fabric Notebook)
- Serving layer (Power BI / Databricks SQL / API)
