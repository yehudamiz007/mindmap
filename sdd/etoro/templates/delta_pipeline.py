"""Delta Lake pipeline template - Bronze to Silver ingestion.

Pattern: Append to Bronze → MERGE to Silver → Quarantine bad records.

Replace all <PLACEHOLDERS> before use.
"""
from __future__ import annotations

from pyspark.sql import DataFrame, SparkSession, Window
from pyspark.sql import functions as F
from pyspark.sql.types import (
    StructType, StructField,
    StringType, IntegerType, DoubleType, TimestampType, DateType, BooleanType,
)
from delta.tables import DeltaTable
import structlog

logger = structlog.get_logger(__name__)

# ── Schemas ──────────────────────────────────────────────────────────────────
SOURCE_SCHEMA = StructType([
    StructField("<id_column>", StringType(), nullable=False),
    StructField("<value_column>", DoubleType(), nullable=True),
    StructField("<timestamp_column>", TimestampType(), nullable=False),
    # Add your source columns here
])

# ── Bronze ────────────────────────────────────────────────────────────────────
def ingest_to_bronze(
    spark: SparkSession,
    source_path: str,
    target_table: str,
    batch_id: str,
) -> DataFrame:
    """Read raw source and append to Bronze with metadata."""
    raw_df = (
        spark.read
        .schema(SOURCE_SCHEMA)
        .json(source_path)  # or .parquet(), .csv(), etc.
    )

    bronze_df = (
        raw_df
        .withColumn("_ingested_at", F.current_timestamp())
        .withColumn("_source", F.lit(source_path))
        .withColumn("_batch_id", F.lit(batch_id))
        .withColumn("_ingested_date", F.current_date())
    )

    (
        bronze_df.write
        .format("delta")
        .mode("append")
        .partitionBy("_ingested_date")
        .saveAsTable(target_table)
    )

    count = bronze_df.count()
    logger.info("Bronze ingestion complete", table=target_table, records=count, batch_id=batch_id)
    return bronze_df


# ── Silver ────────────────────────────────────────────────────────────────────
def transform_to_silver(bronze_df: DataFrame) -> tuple[DataFrame, DataFrame]:
    """Clean bronze data. Returns (valid_df, quarantine_df)."""

    # Dedup by business key - keep latest
    deduped = (
        bronze_df
        .withColumn(
            "_rn",
            F.row_number().over(
                Window
                .partitionBy("<id_column>")
                .orderBy(F.desc("_ingested_at"))
            )
        )
        .filter(F.col("_rn") == 1)
        .drop("_rn", "_source", "_batch_id", "_ingested_date")
    )

    # Separate valid from bad
    valid_condition = (
        F.col("<id_column>").isNotNull() &
        F.col("<value_column>").isNotNull() &
        (F.col("<value_column>") > 0)
    )
    valid_df = (
        deduped
        .filter(valid_condition)
        .withColumn("processed_at", F.current_timestamp())
        .withColumn("date", F.to_date(F.col("<timestamp_column>")))
    )
    quarantine_df = (
        deduped
        .filter(~valid_condition)
        .withColumn(
            "quarantine_reason",
            F.when(F.col("<id_column>").isNull(), "null_id")
            .when(F.col("<value_column>").isNull(), "null_value")
            .when(F.col("<value_column>") <= 0, "non_positive_value")
            .otherwise("unknown"),
        )
        .withColumn("quarantined_at", F.current_timestamp())
    )

    return valid_df, quarantine_df


def upsert_to_silver(
    spark: SparkSession,
    valid_df: DataFrame,
    target_table: str,
    merge_key: str,
) -> None:
    """MERGE valid records into Silver table."""
    target = DeltaTable.forName(spark, target_table)
    (
        target.alias("target")
        .merge(valid_df.alias("source"), f"target.{merge_key} = source.{merge_key}")
        .whenMatchedUpdateAll()
        .whenNotMatchedInsertAll()
        .execute()
    )
    logger.info("Silver upsert complete", table=target_table, records=valid_df.count())


def write_quarantine(quarantine_df: DataFrame, quarantine_table: str) -> None:
    """Append bad records to quarantine table."""
    if quarantine_df.count() > 0:
        quarantine_df.write.format("delta").mode("append").saveAsTable(quarantine_table)
        logger.warning(
            "Quarantine records written",
            table=quarantine_table,
            count=quarantine_df.count(),
        )


# ── Orchestrator ─────────────────────────────────────────────────────────────
def run_bronze_to_silver_pipeline(
    spark: SparkSession,
    source_path: str,
    bronze_table: str,
    silver_table: str,
    quarantine_table: str,
    merge_key: str,
    batch_id: str,
) -> None:
    """Full Bronze → Silver pipeline."""
    # 1. Bronze
    bronze_df = ingest_to_bronze(spark, source_path, bronze_table, batch_id)

    # 2. Transform
    valid_df, quarantine_df = transform_to_silver(bronze_df)

    # 3. Silver merge
    upsert_to_silver(spark, valid_df, silver_table, merge_key)

    # 4. Quarantine
    write_quarantine(quarantine_df, quarantine_table)

    logger.info(
        "Pipeline complete",
        valid=valid_df.count(),
        quarantined=quarantine_df.count(),
    )
