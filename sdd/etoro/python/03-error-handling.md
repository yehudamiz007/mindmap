# Error Handling Standards - eToro

## Core Rules

1. **Never swallow exceptions silently**
2. **Never use bare `except:`**
3. **Always log before re-raising or handling**
4. **Use custom exceptions for domain errors**
5. **Fail fast - validate inputs early**

## Custom Exception Hierarchy

```python
# etoro/common/exceptions.py

class EToroBaseError(Exception):
    """Base exception for all eToro errors."""
    pass

class ValidationError(EToroBaseError):
    """Invalid input data."""
    pass

class NotFoundError(EToroBaseError):
    """Resource not found."""
    pass

class ExternalServiceError(EToroBaseError):
    """External API / service failure."""
    def __init__(self, service: str, message: str) -> None:
        self.service = service
        super().__init__(f"[{service}] {message}")

class RateLimitError(ExternalServiceError):
    """API rate limit exceeded."""
    pass

class InsufficientFundsError(EToroBaseError):
    """Not enough funds for operation."""
    pass
```

## Catching Exceptions

```python
# ✅ Always catch specific exceptions
try:
    result = api_client.open_trade(request)
except RateLimitError as exc:
    logger.warning("Rate limit hit, retrying after 15s", extra={"error": str(exc)})
    time.sleep(15)
    result = api_client.open_trade(request)
except ExternalServiceError as exc:
    logger.error("Trade API failed", extra={"error": str(exc), "service": exc.service})
    raise

# ❌ Never
try:
    result = api_client.open_trade(request)
except:
    pass  # Silent failure - FORBIDDEN

# ❌ Never
try:
    result = api_client.open_trade(request)
except Exception:
    print("something went wrong")  # print instead of logger - FORBIDDEN
```

## Retry Pattern

```python
from functools import wraps
import time
from typing import Callable, TypeVar

T = TypeVar("T")

def with_retry(max_attempts: int = 3, backoff_seconds: float = 15.0):
    """Decorator for retrying on transient failures."""
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(*args, **kwargs) -> T:
            last_exc: Exception | None = None
            for attempt in range(1, max_attempts + 1):
                try:
                    return func(*args, **kwargs)
                except RateLimitError as exc:
                    last_exc = exc
                    wait = backoff_seconds * attempt
                    logger.warning(
                        "Rate limit hit",
                        extra={"attempt": attempt, "wait_seconds": wait},
                    )
                    time.sleep(wait)
            raise last_exc  # type: ignore[misc]
        return wrapper
    return decorator

# Usage
@with_retry(max_attempts=3, backoff_seconds=15.0)
def execute_trade(request: TradeRequest) -> TradeResult:
    return api_client.post_trade(request)
```

## Validation - Fail Fast

```python
# ✅ Validate at boundaries (function entry), not deep inside logic
def open_position(self, amount: float, instrument_id: int) -> Position:
    if amount <= 0:
        raise ValidationError(f"Amount must be positive, got {amount}")
    if instrument_id <= 0:
        raise ValidationError(f"Invalid instrument_id: {instrument_id}")
    if amount > self._max_position_size:
        raise ValidationError(
            f"Amount {amount} exceeds max position size {self._max_position_size}"
        )
    # Now safe to proceed
    return self._repo.create_position(amount, instrument_id)
```

## Context Managers for Resources

```python
# ✅ Always use context managers for connections/files
with open(file_path, "r", encoding="utf-8") as f:
    data = json.load(f)

# ✅ Custom context managers when needed
from contextlib import contextmanager

@contextmanager
def spark_session(app_name: str):
    spark = SparkSession.builder.appName(app_name).getOrCreate()
    try:
        yield spark
    finally:
        spark.stop()
```

## What NOT to Do

```python
# ❌ Returning None to signal error
def get_trade(trade_id: str) -> Trade | None:
    ...  # Caller might forget to check None

# ✅ Raise a specific exception instead
def get_trade(trade_id: str) -> Trade:
    trade = self._repo.find(trade_id)
    if trade is None:
        raise NotFoundError(f"Trade {trade_id} not found")
    return trade

# ❌ Using assert for runtime validation
assert amount > 0, "Amount must be positive"  # Disabled with -O flag

# ✅ Use explicit if + raise
if amount <= 0:
    raise ValidationError(f"Amount must be positive, got {amount}")
```
