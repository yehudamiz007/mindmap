# Documentation Standards - eToro

## Docstring Style: Google Style

```python
def calculate_portfolio_value(
    positions: list[Position],
    include_unrealized: bool = True,
) -> float:
    """Calculate total portfolio value across all open positions.

    Args:
        positions: List of open positions to evaluate.
        include_unrealized: Whether to include unrealized PnL in the total.
            Defaults to True.

    Returns:
        Total portfolio value in USD.

    Raises:
        ValidationError: If positions list contains invalid data.
        ValueError: If a position has negative amount.

    Example:
        >>> positions = [Position(amount=1000.0, unrealized_pnl=50.0)]
        >>> calculate_portfolio_value(positions)
        1050.0
    """
    ...
```

## Class Docstrings

```python
class TradeExecutionService:
    """Service for executing trades on the eToro platform.

    Handles trade lifecycle: open, close, partial close.
    Implements retry logic for rate-limited API calls.

    Attributes:
        max_retries: Maximum number of retry attempts on rate limits.
        backoff_seconds: Wait time between retries in seconds.

    Example:
        >>> service = TradeExecutionService(repo=trade_repo)
        >>> result = service.open_trade(request)
    """

    max_retries: int = 3
    backoff_seconds: float = 15.0
```

## Module Docstrings

```python
"""Trade execution module for eToro agent portfolios.

This module provides services for opening and closing positions
via the eToro public API. It handles authentication, rate limiting,
and error recovery.

Typical usage:
    from etoro_trading.services import TradeExecutionService
    service = TradeExecutionService(repo=TradeRepository(spark))
    result = service.open_trade(request)
"""
```

## What Needs a Docstring

| Item | Docstring Required? |
|------|-------------------|
| Public functions/methods | ✅ Always |
| Public classes | ✅ Always |
| Public modules | ✅ Always |
| Private methods (`_`) | Only if non-obvious |
| Simple properties | Only if non-obvious |
| `__init__` | Only if complex setup |

## Inline Comments - Use Sparingly

```python
# ✅ Comment WHY, not WHAT
# eToro API caches PnL for 60s - must wait before reading updated balance
time.sleep(60)

# ✅ Non-obvious business logic
# credit field includes main account margin - NOT available cash
available_cash = credit - sum(p.amount for p in positions)

# ❌ Obvious comments are noise
x = x + 1  # increment x by 1
positions = []  # create empty list
```

## README Requirements (every project)

```markdown
# Project Name

## What it does
One paragraph.

## Quick Start
pip install / databricks setup / run command.

## Architecture
Link to SDD or diagram.

## Environment Variables
Table of required env vars.

## Running Tests
pytest command.

## Deployment
How to deploy to Databricks / prod.
```
