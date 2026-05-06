# PySpark Performance Standards - eToro

## Partitioning

```python
# ✅ Always partition Delta tables by date for time-series data
(
    df.write
    .format("delta")
    .mode("overwrite")
    .partitionBy("date")
    .saveAsTable("silver.trading.trades")
)

# ✅ Repartition before wide operations
# Default shuffle partitions = 200, tune based on data size
spark.conf.set("spark.sql.shuffle.partitions", "50")  # small datasets
spark.conf.set("spark.sql.shuffle.partitions", "400")  # large datasets

# ✅ Coalesce to reduce small files before writing
result_df.coalesce(8).write.format("delta").mode("overwrite").save(path)

# ❌ Never repartition without reason - it triggers a full shuffle
df.repartition(200)  # no clear reason
```

## Caching Strategy

```python
# ✅ Cache DataFrames used multiple times
from pyspark import StorageLevel

# For DataFrames that fit in memory
positions_df.cache()  # MEMORY_AND_DISK

# For large DataFrames - disk spill allowed
large_df.persist(StorageLevel.MEMORY_AND_DISK_SER)

# ✅ Always unpersist when done
positions_df.unpersist()

# ✅ Cache only if DataFrame is reused 2+ times
# Don't cache DataFrames used once - caching has overhead
df = spark.table("bronze.trades").filter(...)
result1 = df.groupBy(...).agg(...)  # if df used only here, don't cache
```

## Reading Data Efficiently

```python
# ✅ Push filters down to source (partition pruning)
df = (
    spark.table("silver.trading.trades")
    .filter(F.col("date") >= "2026-01-01")  # partition filter - fast
    .filter(F.col("instrument_id").isin([1003, 1004, 1137]))  # pushed to scan
)

# ✅ Select before join - reduce data early
df = (
    spark.table("silver.trading.trades")
    .select("trade_id", "instrument_id", "amount", "opened_at")
    .filter(F.col("status") == "open")
)

# ✅ Use Delta table features - Z-ORDER for frequently filtered columns
# (run once as part of table maintenance, not in every job)
# OPTIMIZE silver.trading.trades ZORDER BY (instrument_id, opened_at)
```

## Skew Handling

```python
# ✅ Salting for skewed joins
SALT_BUCKETS = 10

skewed_df = df.withColumn(
    "salted_key",
    F.concat(F.col("instrument_id").cast("string"), F.lit("_"), (F.rand() * SALT_BUCKETS).cast("int"))
)

lookup_df_salted = (
    lookup_df
    .withColumn("salt", F.explode(F.array([F.lit(i) for i in range(SALT_BUCKETS)])))
    .withColumn("salted_key", F.concat(F.col("instrument_id").cast("string"), F.lit("_"), F.col("salt")))
)

result = skewed_df.join(lookup_df_salted, on="salted_key", how="inner")
```

## Spark Configuration Best Practices

```python
# ✅ Set in SparkSession builder or cluster config, not scattered in code
spark = (
    SparkSession.builder
    .appName("etoro-trade-ingestion")
    .config("spark.sql.shuffle.partitions", "100")
    .config("spark.sql.adaptive.enabled", "true")         # AQE - always on
    .config("spark.sql.adaptive.coalescePartitions.enabled", "true")
    .config("spark.databricks.delta.optimizeWrite.enabled", "true")
    .config("spark.databricks.delta.autoCompact.enabled", "true")
    .getOrCreate()
)
```

## Avoid These Anti-Patterns

```python
# ❌ Collecting large DataFrames to driver
all_trades = df.collect()  # OOM risk if > driver memory

# ❌ Iterating rows in Python
for row in df.collect():
    process(row)  # Not distributed - defeats purpose of Spark

# ❌ Creating DataFrames inside loops
results = []
for date in date_list:
    daily = spark.table("trades").filter(f"date = '{date}'")
    results.append(daily)
final = results[0]
for r in results[1:]:
    final = final.union(r)  # creates huge lineage graph

# ✅ Instead - filter once with a list
final = spark.table("trades").filter(F.col("date").isin(date_list))

# ❌ Using toPandas() in production pipelines
pdf = df.toPandas()  # collects all to driver, no distributed processing

# ✅ Use Pandas on Spark (koalas-style) when pandas API needed
import pyspark.pandas as ps
psdf = ps.from_pandas(pdf)  # distributed pandas
```
