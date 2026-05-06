# DataFrame Best Practices - eToro

## Schema Definition

```python
from pyspark.sql.types import StructType, StructField, StringType, DoubleType, TimestampType, IntegerType, BooleanType

# ✅ Always define schema explicitly for production reads
TRADE_SCHEMA = StructType([
    StructField("trade_id", StringType(), nullable=False),
    StructField("instrument_id", IntegerType(), nullable=False),
    StructField("amount", DoubleType(), nullable=False),
    StructField("is_buy", BooleanType(), nullable=False),
    StructField("open_rate", DoubleType(), nullable=True),
    StructField("opened_at", TimestampType(), nullable=False),
    StructField("user_id", StringType(), nullable=False),
])

df = spark.read.schema(TRADE_SCHEMA).parquet("path/to/data")

# ❌ Never infer schema in production - brittle and slow
df = spark.read.parquet("path/to/data")  # schema inference
```

## Null Handling

```python
# ✅ Always handle nulls explicitly
df.filter(F.col("amount").isNotNull())

# ✅ Fill nulls with defaults
df.fillna({"unrealized_pnl": 0.0, "close_rate": 0.0})

# ✅ Use coalesce for fallback values
df.withColumn(
    "effective_rate",
    F.coalesce(F.col("close_rate"), F.col("open_rate"))
)

# ❌ Never assume columns are non-null without checking
df.withColumn("ratio", F.col("pnl") / F.col("amount"))  # division by null/zero risk
```

## Joins

```python
# ✅ Use explicit join type (never rely on default)
trades_df.join(instruments_df, on="instrument_id", how="inner")
positions_df.join(pnl_df, on="position_id", how="left")

# ✅ Rename ambiguous columns before joining
trades_renamed = trades_df.withColumnRenamed("updated_at", "trade_updated_at")
result = trades_renamed.join(instruments_df, on="instrument_id", how="left")

# ✅ For small lookup tables - broadcast join
from pyspark.sql.functions import broadcast

result = large_df.join(
    broadcast(small_lookup_df),
    on="instrument_id",
    how="left"
)

# ❌ Never join on nullable columns without handling nulls first
# This silently drops null-keyed rows
df.join(other_df, on="nullable_id", how="inner")
```

## Aggregations

```python
# ✅ Always alias aggregated columns
result = (
    df
    .groupBy("instrument_id", "date")
    .agg(
        F.sum("amount").alias("total_invested"),
        F.avg("unrealized_pnl").alias("avg_pnl"),
        F.count("trade_id").alias("trade_count"),
        F.max("opened_at").alias("latest_open"),
    )
)

# ✅ Window functions for running totals / rankings
from pyspark.sql import Window

window_spec = Window.partitionBy("user_id").orderBy(F.desc("opened_at"))

df.withColumn("trade_rank", F.row_number().over(window_spec))
df.withColumn("running_pnl", F.sum("unrealized_pnl").over(window_spec))
```

## Select Over Select *

```python
# ✅ Always select only needed columns
df.select("trade_id", "amount", "instrument_id", "opened_at")

# ❌ Never use select("*") in production pipelines
df.select("*")  # pulls all columns - schema drift risk
```

## Deduplication

```python
# ✅ Always deduplicate with specific columns, not blindly
df.dropDuplicates(["trade_id"])  # dedup by business key

# ✅ For "latest record wins" pattern
window = Window.partitionBy("trade_id").orderBy(F.desc("updated_at"))
(
    df
    .withColumn("rn", F.row_number().over(window))
    .filter(F.col("rn") == 1)
    .drop("rn")
)
```

## Data Quality Checks

```python
# ✅ Add data quality assertions in pipelines
def assert_no_nulls(df: DataFrame, columns: list[str], table_name: str) -> DataFrame:
    for col_name in columns:
        null_count = df.filter(F.col(col_name).isNull()).count()
        if null_count > 0:
            raise DataQualityError(
                f"Table {table_name}: column '{col_name}' has {null_count} null values"
            )
    return df

def assert_positive_amounts(df: DataFrame) -> DataFrame:
    negatives = df.filter(F.col("amount") <= 0).count()
    if negatives > 0:
        raise DataQualityError(f"Found {negatives} non-positive amounts")
    return df
```

## count() Usage - Be Careful

```python
# ⚠️ count() triggers a full scan - expensive!
# ✅ Cache before counting if you'll use the DataFrame again
df.cache()
total = df.count()
logger.info("Records loaded", count=total)
# ... use df for further transformations

# ❌ Don't count just for logging if DataFrame isn't cached
df.count()           # full scan
df.filter(...).count()  # another full scan
df.groupBy(...).agg(...)  # yet another full scan
```
