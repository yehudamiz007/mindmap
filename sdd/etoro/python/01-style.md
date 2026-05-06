# Python Style Standards - eToro

## Formatter & Linter
- **Formatter**: `black` (line length: 100)
- **Linter**: `flake8` + `pylint`
- **Import sorter**: `isort` (profile: black)
- **Type checker**: `mypy` (strict mode)

## Naming Conventions

### Variables & Functions
```python
# ✅ snake_case for variables and functions
user_account_id = 123
total_trade_amount = 0.0

def calculate_portfolio_value(positions: list[Position]) -> float:
    ...

# ❌ Never
userAccountId = 123
TotalTradeAmount = 0.0
def CalculatePortfolioValue(): ...
```

### Classes
```python
# ✅ PascalCase for classes
class TradeExecutionService:
    ...

class PortfolioRebalancer:
    ...

# ❌ Never
class trade_execution_service: ...
class tradeExecutionService: ...
```

### Constants
```python
# ✅ UPPER_SNAKE_CASE for module-level constants
MAX_RETRY_ATTEMPTS = 3
DEFAULT_LEVERAGE = 1
ETORO_API_BASE_URL = "https://public-api.etoro.com/api/v1"

# ❌ Never
maxRetryAttempts = 3
```

### Private Members
```python
# ✅ Single underscore for internal use
class TradeService:
    def _validate_amount(self, amount: float) -> bool: ...
    _cache: dict = {}

# ✅ Double underscore only for name mangling (rare)
class Base:
    def __secret(self): ...
```

### Files & Modules
```python
# ✅ snake_case for file names
trade_execution.py
portfolio_calculator.py
delta_ingestion.py

# ❌ Never
TradeExecution.py
tradeExecution.py
```

## Line Length & Formatting

```python
# Max line length: 100 characters
# Black handles formatting automatically

# ✅ Long function calls - one arg per line
result = calculate_portfolio_value(
    positions=open_positions,
    account_currency="USD",
    include_unrealized=True,
)

# ✅ Long imports
from etoro.trading.execution import (
    TradeExecutor,
    OrderValidator,
    PositionManager,
)

# ✅ String concatenation - use f-strings
message = f"Trade {trade_id} executed for user {user_id} at {timestamp}"

# ❌ Never %-format or .format()
message = "Trade %s executed" % trade_id
message = "Trade {} executed".format(trade_id)
```

## Imports Order (isort)

```python
# 1. Standard library
import os
import sys
from datetime import datetime, timezone
from typing import Optional

# 2. Third-party
import pandas as pd
from pyspark.sql import SparkSession

# 3. Internal / eToro
from etoro.common.config import Settings
from etoro.trading.models import Trade, Position
```

## Whitespace Rules

```python
# ✅ Two blank lines between top-level definitions
def function_one():
    pass


def function_two():
    pass


class MyClass:
    # ✅ One blank line between methods
    def method_one(self):
        pass

    def method_two(self):
        pass
```

## Magic Numbers - Forbidden

```python
# ❌ Never use magic numbers inline
if retry_count > 3:
    raise MaxRetriesExceeded()

# ✅ Always name constants
MAX_RETRY_ATTEMPTS = 3
if retry_count > MAX_RETRY_ATTEMPTS:
    raise MaxRetriesExceeded()
```
