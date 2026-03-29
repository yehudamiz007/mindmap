# eToro API Reference - Grok Trader

## Auth Headers (every request)
```
x-api-key: sdgdskldFPLGfjHn1421dgnlxdGTbngdflg6290bRjslfihsjhSDsdgGHH25hjf
x-user-key: <agent-portfolio token>
x-request-id: <new UUID per request>
```

## Endpoints

### Get Portfolio & PnL
```
GET https://public-api.etoro.com/api/v1/trading/info/real/pnl
```
Returns `clientPortfolio` with `credit`, `positions[]`, `ordersForOpen[]`, `orders[]`.

### Search Instrument ID
```
GET https://public-api.etoro.com/api/v1/market-data/search?internalSymbolFull=<SYMBOL>
```
Returns `items[].instrumentId` (lowercase d). Always resolve dynamically - never hardcode IDs.

### Get Instrument Metadata
```
GET https://public-api.etoro.com/api/v1/market-data/instruments?instrumentIds=<id1,id2,...>
```

### Open Position
```
POST https://public-api.etoro.com/api/v1/trading/execution/market-open-orders/by-amount
Body: { "InstrumentID": <id>, "IsBuy": true, "Leverage": 1, "Amount": <usd> }
```
Amount = (weight% / 100) * equity

### Close Position (full)
```
POST https://public-api.etoro.com/api/v1/trading/execution/market-close-orders/positions/{positionId}
Body: { "InstrumentId": <id>, "UnitsToDeduct": null }
```
Get positionId from PnL endpoint.

### Partial Close
Same endpoint, set `"UnitsToDeduct": <units>` instead of null.

## Portfolio Calculations

**Available Cash** = `credit` - Σ(ordersForOpen[i].amount where mirrorID=0) - Σ(orders[i].amount)

**Total Invested** = Σ(positions[i].amount) + Σ(ordersForOpen[i].amount where mirrorID=0) + Σ(orders[i].amount)

**Unrealized PnL** = Σ(positions[i].unrealizedPnL.pnL)

**Equity** = Available Cash + Total Invested + Unrealized PnL

**Position Weight %** = (position.unrealizedPnL.exposureInAccountCurrency / Equity) * 100

## Trade Execution Flow

1. GET pnl → calculate available cash
2. If insufficient cash → close/partial-close positions first
3. Wait 60 seconds (PnL cache)
4. GET pnl again → verify cash updated
5. Execute open orders (3s apart)
6. On 429: wait 15s, retry. Second 429: wait 30s. Max backoff: 60s.

## Known Instrument IDs (cache)
| Symbol | ID   |
|--------|------|
| META   | 1003 |
| MSFT   | 1004 |
| AMZN   | 1005 |
| NVDA   | 1137 |
| ARM    | 1365 |
| AMD    | 1832 |
| AVGO   | 4236 |
| CRWD   | 5506 |
| GOOGL  | 6434 |
| PLTR   | 7991 |
| AAPL   | 1001 |
| TSLA   | 1002 |

Always verify with search endpoint before trading an unknown symbol.
