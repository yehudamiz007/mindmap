# Type Hints Standards - eToro

## Rule: ALL Python code must be fully typed.
## mypy runs in strict mode in CI. No untyped code merges.

## Basic Types

```python
from __future__ import annotations  # Always add for forward references

# ✅ Always annotate function signatures
def calculate_pnl(amount: float, open_rate: float, close_rate: float) -> float:
    return (close_rate - open_rate) / open_rate * amount

# ✅ Annotate class attributes
class Position:
    position_id: int
    instrument_id: int
    amount: float
    is_buy: bool
```

## Collections

```python
# ✅ Use built-in generics (Python 3.10+)
def get_positions(account_id: str) -> list[Position]:
    ...

def group_by_instrument(positions: list[Position]) -> dict[int, list[Position]]:
    ...

# ✅ Use tuple for fixed-length sequences
def get_price_range(symbol: str) -> tuple[float, float]:  # (min, max)
    ...
```

## Optional & Union

```python
from typing import Optional

# ✅ Use X | None syntax (Python 3.10+)
def find_trade(trade_id: str) -> Trade | None:
    ...

# ✅ For older codebases use Optional
def find_trade(trade_id: str) -> Optional[Trade]:
    ...

# ✅ Union types
def process_id(id: int | str) -> str:
    return str(id)
```

## Callable & TypeVar

```python
from typing import Callable, TypeVar

T = TypeVar("T")
ReturnType = TypeVar("ReturnType")

def retry(func: Callable[..., T], max_attempts: int) -> T:
    ...

# ✅ Protocol for duck typing
from typing import Protocol

class Closeable(Protocol):
    def close(self) -> None: ...

def cleanup(resource: Closeable) -> None:
    resource.close()
```

## Pydantic Models (preferred for data)

```python
from pydantic import BaseModel, Field, field_validator
from datetime import datetime

class OpenTradeRequest(BaseModel):
    instrument_id: int = Field(gt=0)
    amount: float = Field(gt=0, le=50_000)
    is_buy: bool
    leverage: int = Field(default=1, ge=1, le=10)

    @field_validator("amount")
    @classmethod
    def round_to_cents(cls, v: float) -> float:
        return round(v, 2)

class TradeResult(BaseModel):
    trade_id: str
    opened_at: datetime
    status: str
```

## DataClasses (for internal models)

```python
from dataclasses import dataclass, field

@dataclass
class PipelineConfig:
    source_table: str
    target_table: str
    batch_size: int = 10_000
    tags: list[str] = field(default_factory=list)
```

## mypy Config

```toml
# pyproject.toml
[tool.mypy]
python_version = "3.11"
strict = true
ignore_missing_imports = false
disallow_untyped_defs = true
disallow_any_generics = true
warn_return_any = true
warn_unused_ignores = true
```

## Type Ignore - Use Sparingly

```python
# ✅ Only when absolutely necessary, always with a comment
result = external_lib.get_data()  # type: ignore[return-value]  # third-party returns Any
```
