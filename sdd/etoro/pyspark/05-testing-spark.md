# PySpark Testing Standards - eToro

## Setup

```python
# tests/conftest.py
import pytest
from pyspark.sql import SparkSession

@pytest.fixture(scope="session")
def spark() -> SparkSession:
    """Local Spark session for unit tests."""
    return (
        SparkSession.builder
        .master("local[2]")
        .appName("etoro-unit-tests")
        .config("spark.sql.shuffle.partitions", "2")
        .config("spark.sql.extensions", "io.delta.sql.DeltaSparkSessionExtension")
        .config(
            "spark.sql.catalog.spark_catalog",
            "org.apache.spark.sql.delta.catalog.DeltaCatalog",
        )
        .config("spark.databricks.delta.preview.enabled", "true")
        .getOrCreate()
    )
```

## DataFrame Assertion Helpers

```python
# tests/helpers/spark_assertions.py
from pyspark.sql import DataFrame
from pyspark.sql import functions as F

def assert_dataframe_equals(
    actual: DataFrame,
    expected: DataFrame,
    order_by: list[str] | None = None,
) -> None:
    """Assert two DataFrames are equal (schema + data)."""
    # Schema check
    assert actual.schema == expected.schema, (
        f"Schema mismatch:\nActual: {actual.schema}\nExpected: {expected.schema}"
    )

    # Data check
    if order_by:
        actual = actual.orderBy(order_by)
        expected = expected.orderBy(order_by)

    actual_rows = actual.collect()
    expected_rows = expected.collect()
    assert actual_rows == expected_rows, (
        f"Data mismatch:\nActual: {actual_rows}\nExpected: {expected_rows}"
    )

def assert_row_count(df: DataFrame, expected_count: int) -> None:
    actual = df.count()
    assert actual == expected_count, f"Expected {expected_count} rows, got {actual}"

def assert_no_nulls(df: DataFrame, column: str) -> None:
    null_count = df.filter(F.col(column).isNull()).count()
    assert null_count == 0, f"Column '{column}' has {null_count} null values"
```

## Unit Test Pattern for Transformations

```python
# tests/unit/test_trade_transformations.py
import pytest
from pyspark.sql import SparkSession
from pyspark.sql.types import StructType, StructField, StringType, DoubleType, BooleanType
from tests.helpers.spark_assertions import assert_dataframe_equals, assert_no_nulls

def test_filter_active_trades_removes_closed(spark: SparkSession):
    # Arrange
    schema = StructType([
        StructField("trade_id", StringType()),
        StructField("status", StringType()),
        StructField("mirror_id", DoubleType()),
    ])
    input_df = spark.createDataFrame(
        [
            ("t1", "open", 0.0),
            ("t2", "closed", 0.0),
            ("t3", "open", 1.0),   # mirror - should be filtered
        ],
        schema=schema,
    )

    # Act
    result = filter_active_trades(input_df)

    # Assert
    assert result.count() == 1
    assert result.first()["trade_id"] == "t1"


def test_add_processing_timestamp_adds_column(spark: SparkSession):
    # Arrange
    df = spark.createDataFrame([("t1", 100.0)], ["trade_id", "amount"])

    # Act
    result = add_processing_timestamp(df)

    # Assert
    assert "processed_at" in result.columns
    assert_no_nulls(result, "processed_at")
```

## Testing Aggregations

```python
def test_aggregate_pnl_by_instrument_sums_correctly(spark: SparkSession):
    input_df = spark.createDataFrame(
        [
            (1003, 100.0, 10.0),
            (1003, 200.0, -5.0),
            (1004, 500.0, 50.0),
        ],
        ["instrument_id", "amount", "unrealized_pnl"],
    )

    result = aggregate_pnl_by_instrument(input_df)

    rows = {row["instrument_id"]: row for row in result.collect()}
    assert rows[1003]["total_pnl"] == pytest.approx(5.0)
    assert rows[1003]["total_invested"] == pytest.approx(300.0)
    assert rows[1004]["total_pnl"] == pytest.approx(50.0)
```

## Testing Delta Lake Operations (Integration)

```python
# tests/integration/test_delta_write.py
import pytest
import tempfile
from pyspark.sql import SparkSession

@pytest.fixture
def temp_delta_path(tmp_path):
    return str(tmp_path / "test_table")

def test_upsert_positions_inserts_new_records(spark: SparkSession, temp_delta_path: str):
    # Create initial table
    initial_df = spark.createDataFrame(
        [("p1", 1003, 1000.0)],
        ["position_id", "instrument_id", "amount"]
    )
    initial_df.write.format("delta").save(temp_delta_path)

    # Upsert new record
    updates_df = spark.createDataFrame(
        [("p2", 1004, 500.0)],
        ["position_id", "instrument_id", "amount"]
    )
    upsert_to_delta(spark, updates_df, temp_delta_path, merge_key="position_id")

    # Assert
    result = spark.read.format("delta").load(temp_delta_path)
    assert result.count() == 2
```

## Coverage for PySpark

- Minimum **75%** coverage for Spark transformation functions
- Integration tests for all Delta write patterns
- Always test: schema enforcement, null handling, deduplication logic
- Skip coverage for notebook cells (exploratory only)
