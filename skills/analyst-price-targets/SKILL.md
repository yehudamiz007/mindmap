---
name: analyst-price-targets
description: >
  Analyst price target aggregator for stocks. Use when the user asks about price targets,
  analyst ratings, consensus estimates, or fair value for any stock ticker. Scrapes real-time
  data from financial sites, presents Wall Street consensus with individual analyst breakdowns,
  and calculates upside/downside potential. ⚠️ Educational only - not licensed financial advice.
---

# Analyst Price Targets

⚠️ **Disclaimer:** מידע על מחירי יעד - לא ייעוץ השקעות. כל החלטה היא באחריות המשתמש בלבד.

## When User Asks About Price Targets

### Step 1: Fetch Data (Parallel)

Run these searches simultaneously:

1. `"[TICKER] analyst price target consensus"` 
2. `"[TICKER] site:tipranks.com"` - TipRanks aggregation
3. `"[TICKER] site:marketbeat.com price target"` - MarketBeat data
4. `"[TICKER] stock forecast analyst rating"` - general forecasts

Then `web_fetch` the top results from:
- **TipRanks** (tipranks.com) - best for analyst consensus
- **MarketBeat** (marketbeat.com) - individual analyst history
- **CNN Money / Yahoo Finance** - broad consensus
- **WallStreetZen** - clean price target summaries

### Step 2: Extract Key Data Points

For each ticker, collect:

| Data Point | Source |
|-----------|--------|
| Current Price | Any financial site |
| Consensus Rating | Buy/Hold/Sell + count |
| Average Price Target | Aggregated from analysts |
| High Price Target | Most bullish analyst |
| Low Price Target | Most bearish analyst |
| Number of Analysts | How many covering |
| Recent Changes | Last 30-day upgrades/downgrades |

### Step 3: Calculate Metrics

- **Upside to Average:** ((Avg Target - Current) / Current) × 100
- **Upside to High:** ((High Target - Current) / Current) × 100
- **Downside to Low:** ((Low Target - Current) / Current) × 100
- **Consensus Strength:** % of Buy ratings out of total

## Output Format

Reply in Hebrew:

```
🎯 מחירי יעד אנליסטים: [TICKER]
💰 מחיר נוכחי: $[PRICE]
📅 [תאריך]

--- קונצנזוס ---
⭐ דירוג: [BUY/HOLD/SELL] ([X] אנליסטים)
   🟢 קנייה: [X] | ⚪ החזקה: [X] | 🔴 מכירה: [X]

📊 מחירי יעד:
   🔼 גבוה: $[HIGH] (+[X]%)
   ➡️ ממוצע: $[AVG] (+[X]%)
   🔽 נמוך: $[LOW] ([X]%)

--- שינויים אחרונים (30 יום) ---
[רשימת העלאות/הורדות אחרונות עם שם האנליסט והבנק]

--- ניתוח ---
[2-3 משפטים: האם הקונצנזוס חזק? יש פיזור גדול? מגמת שינויים?]

⚠️ מידע בלבד, לא ייעוץ השקעות.
```

## Special Cases

### No Coverage
If a stock has little/no analyst coverage (micro-cap, new IPO), say so clearly and suggest alternatives:
- Check insider transactions instead
- Look at comparable company valuations
- Note that low coverage = higher uncertainty

### Crypto
Crypto doesn't have traditional analyst coverage. Redirect to:
- On-chain metrics and whale tracking
- Market news sentiment skill instead
- Note that "price predictions" for crypto are highly speculative

### Comparative Requests
If user asks "compare targets for X vs Y":
- Side-by-side table
- Highlight which has more upside potential
- Note consensus strength difference

## Follow-up Capabilities

- "תעקוב אחרי שינויים ב-[TICKER]" - suggest cron job for weekly target updates
- "מה האנליסט הכי מדויק אומר?" - deep dive on top-rated analysts
- "תראה לי היסטוריית מחירי יעד" - trend of target changes over time
