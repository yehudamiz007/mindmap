# Medallion Architecture Standards - eToro

## Layer Responsibilities

```
Source Systems (eToro API, Kafka, Files)
         ↓
    [BRONZE]  Raw, append-only, exact copy
         ↓
    [SILVER]  Cleaned, deduplicated, validated
         ↓
    [GOLD]    Business metrics, aggregated, ready to consume
         ↓
Consumers (Dashboards, ML, Reports, APIs)
```

## Bronze Layer Rules

| Property | Rule |
|----------|------|
| Write mode | Append-only, NEVER overwrite |
| Schema | Store as-is from source |
| Transformations | Metadata only (_ingested_at, _source, _batch_id) |
| Bad data | Keep it - don't filter |
| Retention | 90 days minimum |
| Partitioning | By ingestion date (`_ingested_date`) |

```python
BRONZE_METADATA_COLUMNS = [
    F.current_timestamp().alias("_ingested_at"),
    F.lit("etoro_api").alias("_source"),
    F.lit(batch_id).alias("_batch_id"),
    F.current_date().alias("_ingested_date"),
]

def write_to_bronze(df: DataFrame, table: str, batch_id: str) -> None:
    (
        df
        .select("*", *BRONZE_METADATA_COLUMNS)
        .write
        .format("delta")
        .mode("append")
        .partitionBy("_ingested_date")
        .saveAsTable(f"bronze.{table}")
    )
```

## Silver Layer Rules

| Property | Rule |
|----------|------|
| Write mode | MERGE (upsert) by business key |
| Schema | Strongly typed, validated |
| Deduplication | By business key (position_id, trade_id) |
| Nulls | Handle explicitly (fill or flag) |
| Bad data | Quarantine to `silver.<domain>.quarantine_<table>` |
| Partitioning | By business date |
| History | Delta time travel enabled |

```python
def build_silver_positions(bronze_df: DataFrame) -> tuple[DataFrame, DataFrame]:
    """Returns (clean_df, quarantine_df)."""
    
    # Deduplicate
    deduped = (
        bronze_df
        .withColumn("rn", F.row_number().over(
            Window.partitionBy("position_id").orderBy(F.desc("_ingested_at"))
        ))
        .filter(F.col("rn") == 1)
        .drop("rn")
    )
    
    # Separate clean from bad
    valid = deduped.filter(
        F.col("position_id").isNotNull() &
        F.col("amount") > 0 &
        F.col("instrument_id").isNotNull()
    )
    quarantine = deduped.subtract(valid).withColumn("quarantine_reason", 
        F.when(F.col("position_id").isNull(), "null_position_id")
        .when(F.col("amount") <= 0, "non_positive_amount")
        .otherwise("unknown")
    )
    
    return valid, quarantine
```

## Gold Layer Rules

| Property | Rule |
|----------|------|
| Write mode | Overwrite (daily/hourly snapshots) or MERGE |
| Granularity | Business-level (daily, by user, by instrument) |
| Naming | Named for business use case |
| SLA | Must be ready by 07:00 each business day |
| Dependencies | Only read from Silver, never Bronze |

```python
def build_gold_daily_pnl(silver_positions: DataFrame) -> DataFrame:
    """Build daily PnL summary per user - feeds trading dashboard."""
    return (
        silver_positions
        .filter(F.col("status") == "open")
        .groupBy("user_id", "date")
        .agg(
            F.sum("amount").alias("total_invested_usd"),
            F.sum("unrealized_pnl").alias("total_pnl_usd"),
            F.count("position_id").alias("open_positions"),
            F.sum(F.when(F.col("unrealized_pnl") > 0, 1).otherwise(0)).alias("winning_positions"),
        )
        .withColumn(
            "pnl_percentage",
            F.round(F.col("total_pnl_usd") / F.col("total_invested_usd") * 100, 2)
        )
        .withColumn("updated_at", F.current_timestamp())
    )
```

## Pipeline Execution Order

```
1. Bronze ingestion (append raw)
2. Silver processing (clean + merge)
3. Quarantine review (alert if > threshold)
4. Gold aggregation (business metrics)
5. Log pipeline run to ops.pipeline_runs
```

## Data Contracts Between Layers

```python
# Define expected schemas between layers as constants
SILVER_POSITIONS_SCHEMA = StructType([
    StructField("position_id", LongType(), nullable=False),
    StructField("instrument_id", IntegerType(), nullable=False),
    StructField("user_id", StringType(), nullable=False),
    StructField("amount", DoubleType(), nullable=False),
    StructField("unrealized_pnl", DoubleType(), nullable=True),
    StructField("status", StringType(), nullable=False),
    StructField("date", DateType(), nullable=False),
    StructField("processed_at", TimestampType(), nullable=False),
])

def validate_schema(df: DataFrame, expected: StructType, table: str) -> None:
    """Validate DataFrame matches expected schema before writing."""
    actual_fields = {f.name: f.dataType for f in df.schema.fields}
    for field in expected.fields:
        if field.name not in actual_fields:
            raise SchemaValidationError(f"{table}: missing column '{field.name}'")
        if actual_fields[field.name] != field.dataType:
            raise SchemaValidationError(
                f"{table}: column '{field.name}' type mismatch: "
                f"expected {field.dataType}, got {actual_fields[field.name]}"
            )
```
