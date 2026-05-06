# PySpark Style Standards - eToro

## Core Rules

1. **Always use DataFrames** - never RDDs for new code
2. **Transformations are pure functions** - take DataFrame, return DataFrame
3. **Never collect() large datasets** - use `.limit()` for samples
4. **No pandas in production pipelines** - use PySpark native operations
5. **All schemas defined explicitly** - never infer in production

## Function Design

```python
from pyspark.sql import DataFrame, SparkSession
from pyspark.sql import functions as F
from pyspark.sql.types import StructType, StructField, StringType, DoubleType, TimestampType

# ✅ Transformation functions: DataFrame in, DataFrame out
def add_processing_timestamp(df: DataFrame) -> DataFrame:
    """Add ingestion timestamp to every row."""
    return df.withColumn("processed_at", F.current_timestamp())

def filter_active_trades(df: DataFrame) -> DataFrame:
    """Keep only open, non-mirror trades."""
    return df.filter(
        (F.col("status") == "open") &
        (F.col("mirror_id") == 0)
    )

def enrich_with_pnl(df: DataFrame, pnl_df: DataFrame) -> DataFrame:
    """Join trades with PnL data."""
    return df.join(pnl_df, on="trade_id", how="left")
```

## Chaining Transformations

```python
# ✅ Chain via variables for readability (not one mega-chain)
def build_positions_report(raw_df: DataFrame, pnl_df: DataFrame) -> DataFrame:
    active = filter_active_trades(raw_df)
    enriched = enrich_with_pnl(active, pnl_df)
    aggregated = aggregate_by_instrument(enriched)
    return add_processing_timestamp(aggregated)

# ✅ For complex transformations, use method chaining with clear line breaks
result = (
    raw_df
    .filter(F.col("status") == "open")
    .withColumn("trade_value", F.col("amount") * F.col("close_rate"))
    .groupBy("instrument_id")
    .agg(
        F.sum("trade_value").alias("total_exposure"),
        F.count("trade_id").alias("position_count"),
        F.avg("unrealized_pnl").alias("avg_pnl"),
    )
    .orderBy(F.desc("total_exposure"))
)
```

## Imports Convention

```python
# ✅ Always import functions as F, types from types module
from pyspark.sql import DataFrame, SparkSession, Window
from pyspark.sql import functions as F
from pyspark.sql.types import (
    StructType, StructField,
    StringType, IntegerType, DoubleType, BooleanType, TimestampType, LongType,
)

# ❌ Never import individual functions polluting namespace
from pyspark.sql.functions import col, sum, count  # shadows Python builtins!
```

## Column References

```python
# ✅ Always use F.col() for column references in expressions
df.filter(F.col("amount") > 0)
df.withColumn("ratio", F.col("pnl") / F.col("amount"))

# ✅ String column names only for simple selects
df.select("trade_id", "amount", "instrument_id")

# ❌ Never use df["col"] style - breaks chaining
df.filter(df["amount"] > 0)
```

## SparkSession Usage

```python
# ✅ Always inject SparkSession - never getOrCreate() inside functions
class PositionRepository:
    def __init__(self, spark: SparkSession) -> None:
        self._spark = spark

    def read_positions(self) -> DataFrame:
        return self._spark.table("gold.trading.positions")

# ❌ Never
def read_positions() -> DataFrame:
    spark = SparkSession.builder.getOrCreate()  # hidden side effect
    return spark.table("gold.trading.positions")
```

## Avoid UDFs When Possible

```python
# ❌ Avoid Python UDFs - they're slow (serialize/deserialize per row)
from pyspark.sql.functions import udf
@udf(returnType=StringType())
def classify_trade(amount: float) -> str:
    return "large" if amount > 10000 else "small"

# ✅ Use native Spark functions instead
df.withColumn(
    "trade_size",
    F.when(F.col("amount") > 10000, "large").otherwise("small")
)

# ✅ If UDF is unavoidable - use Pandas UDF (Arrow-optimized)
from pyspark.sql.functions import pandas_udf
import pandas as pd

@pandas_udf(returnType=DoubleType())
def custom_calculation(series: pd.Series) -> pd.Series:
    return series * 1.05
```
