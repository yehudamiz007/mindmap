---
name: market-news-sentiment
description: >
  Market news sentiment analysis for stocks and crypto. Use when the user asks about a specific
  ticker/coin - whether to buy, sell, or hold based on recent news, sentiment, and momentum.
  Fetches real-time news via web search (using Grok model for web-aware analysis), analyzes
  sentiment across multiple sources, and provides a clear actionable signal with reasoning.
  ⚠️ Educational analysis only - not licensed financial advice.
---

# Market News & Sentiment Analysis

⚠️ **Disclaimer:** ניתוח סנטימנט - לא ייעוץ השקעות. כל החלטה היא באחריות המשתמש בלבד.

## Model Override

**Always request Grok model** for this skill - it has superior real-time web awareness.
Use `session_status` with model override `xai/grok-4` if not already set, or note to the user that Grok is recommended.

## When User Asks About a Ticker/Coin

### Step 1: Gather News (Multiple Sources)

Run **3-4 web searches** in parallel:

1. `"[TICKER] stock news today"` - general news
2. `"[TICKER] analyst upgrade downgrade"` - analyst actions
3. `"[TICKER] earnings revenue outlook"` - fundamentals
4. `"[TICKER] reddit wsb sentiment"` - retail sentiment (for meme stocks/crypto)

For crypto, adjust:
1. `"[COIN] crypto news today"`
2. `"[COIN] whale activity on-chain"`
3. `"[COIN] price prediction 2026"`
4. `"[COIN] twitter crypto sentiment"`

### Step 2: Fetch Key Articles

Use `web_fetch` on the top 2-3 most relevant/recent articles for deeper analysis.

### Step 3: Sentiment Scoring

Rate each dimension 1-10:

| Dimension | Weight | What to Look For |
|-----------|--------|-----------------|
| **News Sentiment** | 30% | Positive/negative headlines, tone, frequency |
| **Analyst Consensus** | 25% | Upgrades vs downgrades, price target changes |
| **Momentum** | 20% | Price trend, volume, recent performance |
| **Risk Factors** | 15% | Lawsuits, regulations, macro headwinds |
| **Retail Buzz** | 10% | Social media sentiment, Reddit, CT (crypto twitter) |

### Step 4: Generate Signal

Calculate weighted score (1-10):
- **8-10:** 🟢 **Strong Buy Signal** - חזק לקנייה
- **6.5-7.9:** 🟡 **Lean Buy** - נוטה לקנייה
- **4.5-6.4:** ⚪ **Neutral/Hold** - ניטרלי
- **2.5-4.4:** 🟠 **Lean Sell** - נוטה למכירה
- **1-2.4:** 🔴 **Strong Sell Signal** - חזק למכירה

## Output Format

Reply in Hebrew. Structure:

```
📊 ניתוח סנטימנט: [TICKER/COIN]
📅 [תאריך]

🎯 סיגנל: [SIGNAL EMOJI + Hebrew text]
📈 ציון כולל: [X.X]/10

--- פירוט ---

📰 חדשות ([X]/10): [2-3 משפטים על החדשות העיקריות]
🏦 אנליסטים ([X]/10): [קונצנזוס, שינויים אחרונים]
📈 מומנטום ([X]/10): [מגמה, ביצועים אחרונים]
⚠️ סיכונים ([X]/10): [גורמי סיכון עיקריים]
💬 סנטימנט קהל ([X]/10): [מה אומרים ברדיט/טוויטר]

--- שורה תחתונה ---
[2-3 משפטים תמציתיים - מה לעשות ולמה]

⚠️ ניתוח בלבד, לא ייעוץ השקעות.
```

## Multiple Tickers

If user asks about multiple tickers, analyze each separately and add a comparison table at the end.

## Follow-up Capabilities

- "תעדכן אותי כל יום על [TICKER]" - suggest setting up a cron job
- "תשווה בין X ל-Y" - comparative analysis
- "מה הסיכון הכי גדול?" - deep dive on risk factors
