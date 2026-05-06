# Delta Lake & Unity Catalog Standards - eToro

## Naming Convention

```
<catalog>.<schema>.<table>

Catalogs: prod, dev, test
Schemas (= layers): bronze, silver, gold, ops
```

### Table Naming
```
bronze.trading.raw_positions
bronze.trading.raw_orders
silver.trading.positions
silver.trading.trades
gold.trading.portfolio_summary
gold.reporting.daily_pnl
ops.pipeline_runs
```

### Rules
- All lowercase, snake_case
- No abbreviations unless widely known (pnl, api, etl)
- Prefix with domain: `trading_`, `payments_`, `users_`
- Avoid generic names: `data`, `table1`, `temp`

## Table Creation Standards

```sql
-- ✅ Always create with schema, partitioning, and properties
CREATE TABLE IF NOT EXISTS silver.trading.positions (
    position_id     BIGINT      NOT NULL,
    instrument_id   INT         NOT NULL,
    user_id         STRING      NOT NULL,
    amount          DOUBLE      NOT NULL,
    unrealized_pnl  DOUBLE,
    opened_at       TIMESTAMP   NOT NULL,
    closed_at       TIMESTAMP,
    status          STRING      NOT NULL,
    date            DATE        NOT NULL,  -- partition key
    processed_at    TIMESTAMP   NOT NULL   -- ingestion metadata
)
USING DELTA
PARTITIONED BY (date)
TBLPROPERTIES (
    'delta.autoOptimize.optimizeWrite' = 'true',
    'delta.autoOptimize.autoCompact' = 'true',
    'delta.enableChangeDataFeed' = 'true',
    'owner' = 'data-engineering',
    'domain' = 'trading'
);
```

## Write Patterns

```python
# ✅ Append (most common for raw/events)
df.write.format("delta").mode("append").saveAsTable("bronze.trading.raw_positions")

# ✅ Overwrite with schema evolution
(
    df.write
    .format("delta")
    .mode("overwrite")
    .option("overwriteSchema", "true")
    .saveAsTable("silver.trading.positions")
)

# ✅ MERGE (upsert) - for slowly changing dimensions and deduplication
from delta.tables import DeltaTable

def upsert_positions(spark: SparkSession, updates_df: DataFrame) -> None:
    target = DeltaTable.forName(spark, "silver.trading.positions")

    (
        target.alias("target")
        .merge(
            updates_df.alias("source"),
            "target.position_id = source.position_id"
        )
        .whenMatchedUpdateAll()
        .whenNotMatchedInsertAll()
        .execute()
    )
```

## Bronze / Silver / Gold Layer Rules

### Bronze (raw)
- **Exact copy** of source - no transformations
- Always append, never overwrite
- Add metadata columns only: `_ingested_at`, `_source_file`, `_batch_id`
- Keep bad/malformed data - don't filter

```python
def write_bronze(df: DataFrame, table: str) -> None:
    (
        df
        .withColumn("_ingested_at", F.current_timestamp())
        .withColumn("_source", F.lit("etoro_api"))
        .write
        .format("delta")
        .mode("append")
        .saveAsTable(f"bronze.{table}")
    )
```

### Silver (cleaned)
- Deduplicated, validated, typed
- Nulls handled, outliers flagged (not removed)
- Schema enforced
- Partitioned by date

```python
def write_silver(df: DataFrame, table: str) -> None:
    cleaned = (
        df
        .dropDuplicates(["position_id"])
        .withColumn("processed_at", F.current_timestamp())
        .filter(F.col("amount") > 0)
    )
    upsert_to_delta(spark, cleaned, f"silver.{table}", merge_key="position_id")
```

### Gold (aggregated/business)
- Business-ready metrics
- Denormalized for query performance
- Overwrite or merge (never append raw records)
- Named for business consumers

```python
def build_gold_portfolio_summary(silver_df: DataFrame) -> DataFrame:
    return (
        silver_df
        .filter(F.col("status") == "open")
        .groupBy("user_id", "date")
        .agg(
            F.sum("amount").alias("total_invested"),
            F.sum("unrealized_pnl").alias("total_pnl"),
            F.count("position_id").alias("open_positions"),
        )
        .withColumn("pnl_pct", F.col("total_pnl") / F.col("total_invested") * 100)
    )
```

## Table Maintenance

```python
# ✅ Run OPTIMIZE + VACUUM in maintenance jobs (not in regular pipelines)
def maintain_table(spark: SparkSession, table: str) -> None:
    spark.sql(f"OPTIMIZE {table}")
    spark.sql(f"VACUUM {table} RETAIN 168 HOURS")  # 7 days retention
```

## Never Do

```python
# ❌ Never write to Unity Catalog tables with path-based writes
df.write.format("delta").save("/mnt/data/silver/positions")  # bypasses Unity Catalog

# ❌ Never use overwrite in bronze layer
df.write.mode("overwrite").saveAsTable("bronze.trading.raw_positions")  # loses history

# ❌ Never drop and recreate production tables
spark.sql("DROP TABLE IF EXISTS silver.trading.positions")  # data loss risk
```
