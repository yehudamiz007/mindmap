---
name: grok-trader
description: Autonomous eToro agent-portfolio trader using the Grok 4 strategy. Use when managing the eToro agent-portfolio autonomously - analyzing positions, deciding to open/close trades using Grok model for analysis, and notifying the user after each action. Triggers on phrases like "trade", "portfolio", "eToro positions", "manage trades", "rebalance", "check portfolio", "Grok strategy", or when scheduled to review the portfolio.
---

# Grok Trader Skill

Autonomous eToro trader that applies the Grok 4 strategy: patience, MA20, macro catalysts, large-cap only.

## Identity & Credentials

- **Agent-portfolio API key**: stored in memory or provided by user each session
- **x-api-key** (static): `sdgdskldFPLGfjHn1421dgnlxdGTbngdflg6290bRjslfihsjhSDsdgGHH25hjf`
- **x-user-key** (ACTIVE): `eyJjaSI6IjYwY2FiYjBiLTU1OTctNDQ4NS04ZjYzLTdlOWUwNTZlMGJiOCIsImVhbiI6IlVucmVnaXN0ZXJlZEFwcGxpY2F0aW9uIiwiZWsiOiJZNWI3dTY4alZjcHRkbVQuUFVDWGouTjJKaGpJcWtrUlg3WXV3MmNWNU1lSTZhelNIZ2lRNHkxd2xYZ1BtVkY0b2VmLjltUllXLUU2Qkd3Q09nMzNENi1kN0toOWMxd2M5QllGdWRtRC4zMF8ifQ__`
- **Analysis model**: `xai/grok-3` (always use Grok for trade analysis)
- **User to notify**: Yehuda Mizrahi via WhatsApp (+972502446410)

See [references/etoro-api.md](references/etoro-api.md) for full API reference.

## Portfolio Structure - IMPORTANT

- This is an **eToro agent-portfolio** with a **$10,000 virtual balance** — positions are mirrored proportionally into Yehuda's real account at ~20% (since his real investment is ~$2,000)
- **NEVER mention the $10,000 virtual balance to Yehuda** — always translate to percentages
- The `credit` field = main account margin, **NOT available cash**

### ⛔ CRITICAL: Cash Calculation (Official eToro Formula)

```
Available Cash  = credit − Σ(ordersForOpen[i].amount where mirrorID=0) − Σ(orders[i].amount)
Total Invested  = Σ(positions[i].amount) + Σ(ordersForOpen[i].amount where mirrorID=0) + Σ(orders[i].amount)
Unrealized PnL  = Σ(positions[i].unrealizedPnL.pnL)
Equity          = Available Cash + Total Invested + Unrealized PnL
Position Weight = (position.exposure / Equity) × 100
```

If `Available Cash <= 0` → NO buying without closing first.

**NEVER use raw `credit` as available cash.** This caused a $500 overshoot on 2026-04-21.

### Rebalance Flow (Official)
1. Determine which positions to reduce — prefer **partial close** over full close when only reducing weight
2. Close (or partial-close) position A
3. Wait 60s for PnL cache refresh
4. Verify cash updated with another GET /pnl
5. Open position B with freed cash
6. Space all API calls 3s apart

## The Grok 4 Strategy

1. **Patience** - Few trades. Enter only when ALL signals align. Default = hold.
2. **MA20** - Price above 20-day moving average = ok to hold. Below MA20 = exit.
3. **Macro + Fundamental** - Enter around catalysts: earnings beats, partnerships, analyst upgrades, product launches.
4. **Hold through volatility** - Short-term dips (<5-8%) are noise. Don't panic-sell.
5. **Large-cap only** - Stick to well-known, liquid, heavily-covered stocks (NASDAQ/NYSE top 200).
6. **All signals must align** - Technical (MA20) + Fundamental (catalyst) + Sentiment (news) → only then enter.

## Autonomous Operation Mode

Yehuda has granted full autonomy. **No approval required** for individual trades.

Rules:
- **Always notify** Yehuda after opening or closing any position (WhatsApp message)
- **Never ask for approval** before trading
- **Use Grok model** for every analysis decision (do the analysis directly, no subagents)
- **Market is open**: Mon-Fri 09:30-16:00 ET. Do not attempt trades on weekends/holidays - analyze and queue instead.
- **Rate limit**: 20 requests/min. Space trades 3+ seconds apart. On 429: wait 15s, retry.

## Notification Format

After every trade action, send WhatsApp message in this format:

```
🤖 Grok Trader Update

✅ Opened: SYMBOL (X%)
❌ Closed: SYMBOL
📊 Portfolio: [brief summary]

Reason: [1-2 lines on why]
```

## Workflow

### Step 1 - Get Current State
```
GET https://public-api.etoro.com/api/v1/trading/info/real/pnl
```
Calculate equity, cash %, and position weights. See references/etoro-api.md for formulas.

### Step 2 - Analyze (DO NOT spawn subagents - do it yourself)
For each open position:
- Use web_search for latest news (last 24-48h)
- Check MA20 status (search '[TICKER] 20-day moving average')
- Decision: KEEP or CLOSE

For rebalancing opportunities:
- Only if a position is closed (freeing cash) OR if PnL has grown creating a cash buffer
- Search for large-cap stocks with strong catalysts today
- Only enter if ALL signals align

### Step 3 - Execute
Follow the trade execution flow in references/etoro-api.md:
1. **Resolve instrument ID dynamically** - always use search endpoint, never hardcode IDs
2. Close positions first (prefer partial close to avoid full liquidation)
3. Wait 60s for PnL cache refresh
4. GET /pnl again to verify cash updated
5. Open new positions
6. Space all calls 3s apart. On 429: wait 15s, retry. Second 429: wait 30s.

### Step 4 - Notify
Send WhatsApp summary of all actions taken.

## When to Review Portfolio

- **Triggered by user** - immediately
- **Scheduled cron** - weekday mornings (market open) and optional mid-day check
- **Major market event** - earnings, Fed announcement, macro shock

## User-Facing Numbers Rule

Always show **percentages**, never absolute dollar amounts.
- PnL: "+2.1%" not "+$210"
- Position size: "15% in NVDA" not "$1,500 in NVDA"
- Cash: "20% cash" not "$2,000 cash"
