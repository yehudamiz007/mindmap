# Testing Standards - eToro

## Framework & Tools

- **Test runner**: `pytest`
- **Mocking**: `unittest.mock` / `pytest-mock`
- **Coverage**: `pytest-cov` (minimum **80%**, target **90%+**)
- **Fixtures**: `conftest.py` at project root
- **Spark testing**: `pyspark.sql.SparkSession` with local master

## Test File Structure

```
tests/
├── conftest.py              ← Shared fixtures (spark, db, clients)
├── unit/
│   ├── services/
│   │   └── test_trade_service.py
│   ├── models/
│   │   └── test_trade.py
│   └── utils/
│       └── test_date_utils.py
├── integration/
│   ├── test_trade_repository.py
│   └── test_pipeline_end_to_end.py
└── fixtures/
    ├── sample_trades.json
    └── sample_positions.parquet
```

## Naming Convention

```python
# File: test_<module_name>.py
# Function: test_<what>_<condition>_<expected_result>

def test_open_trade_valid_request_returns_position(): ...
def test_open_trade_negative_amount_raises_validation_error(): ...
def test_calculate_portfolio_value_empty_positions_returns_zero(): ...
```

## Unit Test Pattern (AAA)

```python
# Arrange - Act - Assert
def test_calculate_portfolio_value_multiple_positions_returns_sum():
    # Arrange
    positions = [
        Position(amount=1000.0, unrealized_pnl=150.0),
        Position(amount=500.0, unrealized_pnl=-50.0),
    ]
    service = PortfolioService()

    # Act
    result = service.calculate_value(positions)

    # Assert
    assert result == 1600.0
```

## Mocking External Dependencies

```python
from unittest.mock import MagicMock, patch
import pytest

@pytest.fixture
def mock_trade_repo():
    return MagicMock(spec=TradeRepository)

def test_open_trade_calls_repository_once(mock_trade_repo):
    # Arrange
    service = TradeService(repo=mock_trade_repo)
    request = OpenTradeRequest(instrument_id=1003, amount=500.0, is_buy=True)
    mock_trade_repo.create.return_value = Trade(trade_id="t123", **request.model_dump())

    # Act
    result = service.open_trade(request)

    # Assert
    mock_trade_repo.create.assert_called_once_with(request)
    assert result.trade_id == "t123"

# ✅ Use patch for module-level dependencies
@patch("etoro_trading.services.trade_service.time.sleep")
def test_retry_on_rate_limit_waits_correct_time(mock_sleep, mock_trade_repo):
    mock_trade_repo.create.side_effect = [RateLimitError("etoro", "429"), Trade(...)]
    service = TradeService(repo=mock_trade_repo)
    service.open_trade(request)
    mock_sleep.assert_called_once_with(15.0)
```

## Testing Exceptions

```python
import pytest

def test_open_trade_zero_amount_raises_validation_error():
    service = TradeService(repo=MagicMock())

    with pytest.raises(ValidationError, match="Amount must be positive"):
        service.open_trade(OpenTradeRequest(amount=0.0, instrument_id=1003, is_buy=True))

def test_open_trade_unknown_instrument_raises_not_found():
    repo = MagicMock()
    repo.find_instrument.return_value = None
    service = TradeService(repo=repo)

    with pytest.raises(NotFoundError, match="Instrument 9999 not found"):
        service.open_trade(OpenTradeRequest(amount=100.0, instrument_id=9999, is_buy=True))
```

## Fixtures (conftest.py)

```python
# tests/conftest.py
import pytest
from pyspark.sql import SparkSession

@pytest.fixture(scope="session")
def spark() -> SparkSession:
    return (
        SparkSession.builder
        .master("local[2]")
        .appName("etoro-tests")
        .config("spark.sql.shuffle.partitions", "2")
        .config("spark.sql.extensions", "io.delta.sql.DeltaSparkSessionExtension")
        .getOrCreate()
    )

@pytest.fixture
def sample_positions() -> list[dict]:
    return [
        {"position_id": 1, "instrument_id": 1003, "amount": 1000.0, "unrealized_pnl": 100.0},
        {"position_id": 2, "instrument_id": 1004, "amount": 500.0, "unrealized_pnl": -20.0},
    ]
```

## Coverage Requirements

```toml
# pyproject.toml
[tool.pytest.ini_options]
addopts = "--cov=src --cov-report=term-missing --cov-fail-under=80"

[tool.coverage.report]
exclude_lines = [
    "pragma: no cover",
    "if __name__ == .__main__.:",
    "raise NotImplementedError",
]
```

## What NOT to Test

- ❌ Third-party library internals (pyspark, pandas)
- ❌ Pydantic model auto-validation (it's tested by Pydantic)
- ❌ `__repr__` and `__str__` unless they contain logic
- ✅ Always test: service logic, error paths, edge cases, data transformations
