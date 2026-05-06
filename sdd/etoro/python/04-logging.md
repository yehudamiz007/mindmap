# Logging Standards - eToro

## Setup

```python
# ✅ Always use structlog or standard logging with structured output
import logging
import structlog

# Configure once at app entry point
structlog.configure(
    processors=[
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.JSONRenderer(),
    ],
    wrapper_class=structlog.BoundLogger,
    context_class=dict,
    logger_factory=structlog.PrintLoggerFactory(),
)

# In each module:
logger = structlog.get_logger(__name__)
```

## Log Levels

| Level | When to use |
|-------|------------|
| `DEBUG` | Detailed flow, values for development only |
| `INFO` | Normal business events (trade opened, job started) |
| `WARNING` | Recoverable issues (rate limit hit, retry attempt) |
| `ERROR` | Failures that need attention (API down, data quality issue) |
| `CRITICAL` | System-level failure, data corruption risk |

## Structured Logging Pattern

```python
# ✅ Always use keyword arguments for structured context
logger.info(
    "Trade opened",
    trade_id=trade.trade_id,
    instrument_id=trade.instrument_id,
    amount=trade.amount,
    user_id=user_id,
)

logger.warning(
    "Rate limit hit - retrying",
    attempt=attempt_number,
    wait_seconds=wait_time,
    endpoint="/market-open-orders",
)

logger.error(
    "External API call failed",
    service="etoro_trading_api",
    status_code=response.status_code,
    error=str(exc),
    trade_request=request.model_dump(),
)

# ❌ Never concatenate strings in log messages
logger.info(f"Trade {trade_id} opened for {amount}")  # loses structure
logger.info("Trade " + trade_id + " opened")           # even worse
```

## What to Log

### ✅ Always log:
- Job/pipeline start and end (with duration)
- Each trade open/close action
- External API calls (request + response status)
- Retry attempts
- Validation failures
- Unexpected data shapes

### ❌ Never log:
- API keys, tokens, passwords
- Full PII (mask/truncate user data)
- Entire large DataFrames (log .count() or schema only)

## Sensitive Data Masking

```python
# ✅ Mask tokens before logging
def _mask_token(token: str) -> str:
    if len(token) <= 8:
        return "***"
    return token[:4] + "***" + token[-4:]

logger.debug("API request", auth_token=_mask_token(token))

# ✅ For user data - log only IDs, not names/emails
logger.info("Processing user", user_id=user.id)  # not user.email
```

## Job/Pipeline Logging Pattern

```python
import time

def run_pipeline(job_name: str) -> None:
    start_time = time.monotonic()
    logger.info("Pipeline started", job=job_name)

    try:
        result = _execute(job_name)
        duration_ms = int((time.monotonic() - start_time) * 1000)
        logger.info(
            "Pipeline completed",
            job=job_name,
            duration_ms=duration_ms,
            records_processed=result.record_count,
        )
    except Exception as exc:
        duration_ms = int((time.monotonic() - start_time) * 1000)
        logger.error(
            "Pipeline failed",
            job=job_name,
            duration_ms=duration_ms,
            error=str(exc),
            exc_info=True,
        )
        raise
```

## Databricks / Spark Logging

```python
# In Databricks notebooks and jobs - use display() for DataFrames, not print()
# For pipeline logging, write to a Delta log table

def log_pipeline_run(
    spark: SparkSession,
    job_name: str,
    status: str,
    records: int,
    error: str | None = None,
) -> None:
    from datetime import datetime, timezone
    log_row = [{
        "job_name": job_name,
        "run_at": datetime.now(timezone.utc).isoformat(),
        "status": status,
        "records_processed": records,
        "error_message": error,
    }]
    spark.createDataFrame(log_row).write.format("delta").mode("append").saveAsTable(
        "bronze.ops.pipeline_runs"
    )
```
