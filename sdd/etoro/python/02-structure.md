# Python Project Structure - eToro

## Standard Project Layout

```
my_project/
├── src/
│   └── etoro_<domain>/          ← e.g. etoro_trading, etoro_ingestion
│       ├── __init__.py
│       ├── models/              ← Pydantic/dataclass models
│       │   ├── __init__.py
│       │   └── trade.py
│       ├── services/            ← Business logic
│       │   ├── __init__.py
│       │   └── trade_service.py
│       ├── repositories/        ← Data access layer (DB, API, Delta)
│       │   ├── __init__.py
│       │   └── trade_repository.py
│       ├── utils/               ← Shared helpers
│       │   ├── __init__.py
│       │   └── date_utils.py
│       └── config.py            ← Settings / env config
├── tests/
│   ├── unit/
│   ├── integration/
│   └── conftest.py
├── notebooks/                   ← Databricks notebooks (exploratory only)
├── pyproject.toml               ← Project config (black, isort, mypy, pytest)
├── requirements.txt             ← Pinned dependencies
├── requirements-dev.txt         ← Dev/test dependencies
└── README.md
```

## Module Responsibilities

### models/
- Pure data containers (Pydantic BaseModel or @dataclass)
- No business logic here
- Validation only via Pydantic validators

```python
# ✅ Good model
from pydantic import BaseModel, Field
from datetime import datetime

class Trade(BaseModel):
    trade_id: str
    instrument_id: int
    amount: float = Field(gt=0)
    is_buy: bool
    opened_at: datetime
```

### services/
- All business logic lives here
- Services depend on repositories (via dependency injection)
- Never access DB/API directly from services

```python
# ✅ Good service
class TradeService:
    def __init__(self, repo: TradeRepository) -> None:
        self._repo = repo

    def open_trade(self, request: OpenTradeRequest) -> Trade:
        self._validate_request(request)
        return self._repo.create(request)
```

### repositories/
- All I/O: Delta Lake, REST APIs, databases
- Returns domain models, not raw dicts/rows
- Handles retries and connection errors

```python
# ✅ Good repository
class TradeRepository:
    def __init__(self, spark: SparkSession) -> None:
        self._spark = spark

    def get_open_positions(self, account_id: str) -> list[Position]:
        df = self._spark.table("gold.trading.positions")
        rows = df.filter(f"account_id = '{account_id}'").collect()
        return [Position(**row.asDict()) for row in rows]
```

### config.py
- Uses `pydantic-settings` for env-based config
- Never hardcode secrets or URLs

```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    etoro_api_base_url: str
    etoro_api_key: str
    databricks_catalog: str = "prod"

    class Config:
        env_file = ".env"

settings = Settings()
```

## Dependency Injection Pattern

```python
# ✅ Always inject dependencies - never instantiate inside methods
# Good
class ReportService:
    def __init__(self, trade_repo: TradeRepository, spark: SparkSession) -> None:
        self._trade_repo = trade_repo
        self._spark = spark

# ❌ Never
class ReportService:
    def generate(self):
        spark = SparkSession.builder.getOrCreate()  # hidden dependency
        ...
```

## __init__.py Convention

```python
# ✅ Export public API explicitly in __init__.py
# services/__init__.py
from etoro_trading.services.trade_service import TradeService
from etoro_trading.services.portfolio_service import PortfolioService

__all__ = ["TradeService", "PortfolioService"]
```
