"""<JOB_NAME> - <one-line description>.

Entry point for the <JOB_NAME> Databricks job.
Reads from <source>, transforms, and writes to <target>.

Usage:
    databricks bundle run <job_name>
    python -m etoro_<domain>.jobs.<job_name>
"""
from __future__ import annotations

import time
import logging
from pyspark.sql import SparkSession

import structlog

from etoro_<domain>.config import Settings, validate_settings
from etoro_<domain>.repositories.<repo> import <RepositoryName>
from etoro_<domain>.transformations.<layer> import <transform_function>

logger = structlog.get_logger(__name__)


def run(spark: SparkSession, settings: Settings) -> dict:
    """Main job logic. Returns run summary.

    Args:
        spark: Active SparkSession.
        settings: Validated application settings.

    Returns:
        Dict with job summary: records_read, records_written, duration_ms.
    """
    start_time = time.monotonic()
    logger.info("Job started", job="<job_name>", catalog=settings.databricks_catalog)

    # ── Read ─────────────────────────────────────────────────────────────────
    repo = <RepositoryName>(spark, settings)
    source_df = repo.read_<source>()
    source_count = source_df.cache().count()
    logger.info("Source data loaded", records=source_count)

    # ── Transform ────────────────────────────────────────────────────────────
    result_df = <transform_function>(source_df)

    # ── Data Quality Check ───────────────────────────────────────────────────
    result_count = result_df.count()
    if result_count == 0:
        logger.warning("Transform produced zero records - skipping write")
        return {"records_read": source_count, "records_written": 0}

    # ── Write ────────────────────────────────────────────────────────────────
    repo.write_<target>(result_df)
    source_df.unpersist()

    # ── Summary ──────────────────────────────────────────────────────────────
    duration_ms = int((time.monotonic() - start_time) * 1000)
    summary = {
        "records_read": source_count,
        "records_written": result_count,
        "duration_ms": duration_ms,
    }
    logger.info("Job completed", job="<job_name>", **summary)
    return summary


if __name__ == "__main__":
    from etoro_<domain>.utils.spark_utils import get_spark

    spark = get_spark("<job_name>")
    settings = Settings()
    validate_settings(settings)

    try:
        summary = run(spark, settings)
    except Exception as exc:
        logger.error("Job failed", job="<job_name>", error=str(exc), exc_info=True)
        raise
    finally:
        spark.stop()
