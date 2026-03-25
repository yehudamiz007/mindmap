# Data Architecture Patterns

## Medallion Architecture (Lakehouse)

The standard pattern for Databricks/Delta Lake:

```
Source Systems
     │
     ▼
┌─────────┐
│ BRONZE  │  Raw ingestion - no transformations, append-only
│         │  Schema: as-is from source + audit cols (_ingested_at, _source_file)
└────┬────┘
     │
     ▼
┌─────────┐
│ SILVER  │  Cleaned, validated, deduplicated
│         │  Schema: enforced, types cast, PII masked
└────┬────┘
     │
     ▼
┌─────────┐
│  GOLD   │  Business-ready aggregations
│         │  Schema: denormalized for BI consumption
└─────────┘
```

### Bronze Layer Rules
- Ingest raw data as-is (JSON, CSV, Parquet, CDC)
- Add audit columns: `_ingested_at`, `_source_file`, `_batch_id`
- Never delete rows - append only
- Store in Delta format with schema evolution enabled
- Partition by `_ingested_date`

### Silver Layer Rules
- Deduplicate using `MERGE INTO` or `dropDuplicates()`
- Enforce schema (`enforceSchema=True`)
- Cast data types explicitly
- Handle nulls (fill, drop, or flag)
- Mask/encrypt PII
- Add `_updated_at`, `_created_at` business timestamps
- Keep grain at source entity level (1 row per order, per event, etc.)

### Gold Layer Rules
- Denormalized wide tables for BI
- Pre-aggregated metrics where needed
- Optimized for read performance (Z-ORDER, OPTIMIZE)
- Documented with column descriptions
- SLA: refreshed on business schedule

---

## Lambda Architecture

For mixed batch + streaming workloads:

```
Data Sources
  │       │
  │       ▼
  │   Speed Layer (Streaming)
  │   Spark Structured Streaming / Kafka
  │   → Low-latency, approximate results
  │
  ▼
Batch Layer
Spark batch jobs
→ Accurate, complete results

Serving Layer (merges both)
```

**When to use:** Real-time dashboards that also need historical accuracy.
**Downside:** Duplicate logic in batch and streaming.

---

## Kappa Architecture

Single streaming pipeline for everything:

```
All Data → Kafka → Spark Structured Streaming → Delta Lake
```

**When to use:** When you can replay from Kafka/event log.
**Benefit:** No dual logic, simpler ops.
**Requirement:** Event log with sufficient retention.

---

## Incremental Loading Patterns

### Full Refresh
```python
df.write.format("delta").mode("overwrite").saveAsTable("silver.dim_product")
```
Use for: Small dimensions, reference tables.

### Append Only
```python
df.write.format("delta").mode("append").saveAsTable("silver.events")
```
Use for: Immutable event logs, audit tables.

### Upsert (SCD Type 1)
```sql
MERGE INTO silver.customers AS t
USING source AS s ON t.customer_id = s.customer_id
WHEN MATCHED AND t.updated_at < s.updated_at THEN UPDATE SET *
WHEN NOT MATCHED THEN INSERT *
```
Use for: Dimension tables with updates.

### SCD Type 2 (History preserved)
```sql
-- Expire old record
MERGE INTO silver.customers_history AS t
USING source AS s ON t.customer_id = s.customer_id AND t.is_current = true
WHEN MATCHED AND t.hash_key != s.hash_key THEN
  UPDATE SET t.is_current = false, t.valid_to = current_timestamp()
WHEN NOT MATCHED THEN
  INSERT (customer_id, ..., is_current, valid_from, valid_to)
  VALUES (s.customer_id, ..., true, current_timestamp(), '9999-12-31')
```
Use for: Slowly changing dimensions needing full history.

---

## Data Quality Framework

### Validation Rules (dbt tests or Great Expectations)
```yaml
# dbt schema.yml
models:
  - name: silver_orders
    columns:
      - name: order_id
        tests:
          - unique
          - not_null
      - name: status
        tests:
          - accepted_values:
              values: ['pending', 'shipped', 'delivered', 'cancelled']
      - name: amount
        tests:
          - dbt_utils.expression_is_true:
              expression: ">= 0"
```

### Data Quality Metrics to Track
- Completeness: % non-null for critical fields
- Uniqueness: duplicate rate on primary keys
- Freshness: max(`_ingested_at`) vs. expected schedule
- Validity: % rows passing business rules
- Consistency: referential integrity between tables

---

## Partitioning Strategy

| Table Size | Partition Strategy |
|------------|-------------------|
| < 1 GB | No partitioning needed |
| 1–100 GB | Partition by date (`year`/`month`) |
| > 100 GB | Partition by date + Z-ORDER on filter cols |
| Event tables | Partition by `event_date`, Z-ORDER on `user_id`, `event_type` |
| Fact tables | Partition by `transaction_date` |
| Dimension tables | Usually no partitioning |

### Z-ORDER vs Partitioning
- **Partition:** Physical file separation. Best for high-cardinality time columns.
- **Z-ORDER:** Co-locate related data within partitions. Best for user_id, product_id, region.

```sql
OPTIMIZE catalog.silver.events
ZORDER BY (user_id, event_type);
```
