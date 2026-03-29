---
name: grok-trader
description: Autonomous eToro agent-portfolio trader using the Grok 4 strategy. Use when managing the eToro agent-portfolio autonomously - analyzing positions, deciding to open/close trades using Grok model for analysis, and notifying the user after each action. Triggers on phrases like "trade", "portfolio", "eToro positions", "manage trades", "rebalance", "check portfolio", "Grok strategy", or when scheduled to review the portfolio.
---

# Grok Trader Skill

Autonomous eToro trader that applies the Grok 4 strategy: patience, MA20, macro catalysts, large-cap only.

## Identity & Credentials

- **Agent-portfolio API key**: stored in memory or provided by user each session
- **x-api-key** (static): `sdgdskldFPLGfjHn1421dgnlxdGTbngdflg6290bRjslfihsjhSDsdgGHH25hjf`
- **Analysis model**: `xai/grok-3` (always use Grok for trade analysis)
- **User to notify**: Yehuda Mizrahi via WhatsApp (+972502446410)

See [references/etoro-api.md](references/etoro-api.md) for full API reference.

## The Grok 4 Strategy

1. **Patience** - Few trades. Enter only when ALL signals align. Default = hold cash.
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
- **Use Grok model** for every analysis decision (spawn subagent with `model: xai/grok-3`)
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

### Step 2 - Analyze with Grok
Spawn a subagent with `model: xai/grok-3` and provide:
- Current positions with weights and PnL %
- Request: news search + MA20 assessment + KEEP/CLOSE/REBALANCE decision per position
- Ask for new position suggestions if cash > 10%

### Step 3 - Execute
Follow the trade execution flow in references/etoro-api.md:
1. Close positions first (if needed to free cash)
2. Wait 60s for PnL cache refresh
3. Open new positions
4. Space all calls 3s apart

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
