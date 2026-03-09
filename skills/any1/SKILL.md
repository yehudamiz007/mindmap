# Any1 - The Human Market

## What is Any1?

Any1 is a social platform where every person has a tradable valuation - like a stock market, but for humans.
The concept: **People Power People** - Investors, Founders, Surfers and Experts each have a market cap, collateral, backers, reputation, and missions.

- **Live URL:** https://any1.vercel.app
- **GitHub Repo:** https://github.com/TM-Design-Industries/any1 (user: TM-Design-Industries)
- **Stack:** React + Vite (JavaScript), deployed on Vercel
- **Vercel User ID:** 3Bg0cV40LEET7ZlVIel6xGF7

---

## Tech Architecture

- **Frontend:** React 18 + Vite, React Router DOM
- **Styling:** Inline styles with ThemeContext (dark/light theme support)
- **State:** useState/useEffect (no Redux), localStorage for user data and portfolio
- **Data:** Mock data in `src/data/mockData.js` and `src/data/mockTransactions.js`
- **Icons:** lucide-react
- **Deploy:** Vercel (auto-deploy from GitHub main branch)

### Key Files
```
src/
  App.jsx                   # Router, splash/onboarding logic
  context/ThemeContext.jsx   # Dark/light theme
  data/mockData.js           # All mock users, USER_TYPES, generateChart
  data/mockTransactions.js   # Transaction history per user
  pages/
    Splash.jsx               # Intro animation
    Onboarding.jsx           # 3-step onboarding (type, world, goal)
    Home.jsx                 # Feed, leaderboard, notifications, ticker
    Discover.jsx             # Swipe cards (Tinder-like)
    Market.jsx               # Full market view, search, tabs
    Portfolio.jsx            # User's backed people + P&L
    Profile.jsx              # Own profile
    UserPage.jsx             # Other user's profile (tabs: dashboard/posts/transactions)
    UserPortfolio.jsx        # Another user's portfolio view
    Missions.jsx             # Mission board
    Chat.jsx                 # 1:1 DM chat
  components/
    SwipeCard.jsx            # Draggable swipe card with INTERESTED/SKIP/BACK
    UserCard.jsx             # User card for feed
    BottomNav.jsx            # Navigation bar
    TypeBadge.jsx            # Investor/Founder/Surfer/Expert badge
    MiniChart.jsx            # Sparkline chart
    GlobalFloating.jsx       # Floating action button
    SettingsDrawer.jsx       # Settings panel
  theme.js                  # Color tokens
```

---

## User Types

| Type | Color | Description |
|------|-------|-------------|
| **Investor** | `#7A9E7E` | Backs people and projects with capital |
| **Founder** | `#8B85C1` | Builder with vision, domain expert, company owner |
| **Surfer** | `#5AABA2` | Joins many projects, multitasker, no founder lock-in |
| **Expert** | `#B8714F` | Master of one craft - chef, musician, mechanic, artist |

---

## Reputation & Levels

XP is called "reputation" (rep). Level system:

| Level | Range | Name |
|-------|-------|------|
| 0-20 | Newcomer | Grey |
| 21-40 | Explorer | Teal |
| 41-60 | Contributor | Purple |
| 61-80 | Builder | Gold |
| 81-100 | Amplifier | Amber |
| 101+ | Legend | Red |

**XP Actions:**
- Welcome bonus: +32
- Complete a mission: +50
- Get backed: +20
- Apply for mission: +10
- Mission accepted: +30
- 7-day streak: +25
- Refer a friend: +40

---

## Mock Users (Production-ready Characters)

### Real People
| ID | Name | Type | Market Cap | Change | Notes |
|----|------|------|-----------|--------|-------|
| 1 | **Tamir Mizrahi** | Founder | $74.2k | +4.8% | Co-founder, TMD Industrial Designer |
| 9 | **Yehuda Mizrahi** | Founder | $38.6k | +5.1% | Co-founder, CTO NUDAY.AI |
| 10 | **Yehuda Levi** | Expert | $128k | +6.2% | Israeli actor (Fauda) |
| 11 | **Eyal Shani** | Expert | $215k | +3.7% | Chef, Miznon creator |
| 12 | **Dovi Frances** | Investor | $342k | +8.4% | VC, Group 11 |
| 13 | **Assi Azar** | Surfer | $96k | +2.9% | TV host, Eurovision 2019 |
| 14 | **Omer Adam** | Expert | $187k | +9.3% | Israeli pop star |
| 15 | **Ahavat Hashem Gordon** | Expert | $52k | +11.7% | World Youth Kickboxing Champion |

### Fictional Characters
| ID | Name | Type | Notes |
|----|------|------|-------|
| 2 | Maya Levi | Investor | Angel investor, design background |
| 3 | Oren Cohen | Investor | Managing Partner @ Apex Ventures |
| 4 | Shira Katz | Surfer | Tech writer |
| 5 | Dor Shapira | Surfer | Full-stack engineer |
| 6 | Noa Ben David | Founder | Building first company, Web3 |
| 7 | Yossi Peretz | Investor | CleanTech/Hardware angel |
| 8 | Dana Shapir | Surfer | Growth marketer |

**myProfile** (the logged-in user): ID `me`, starts with 8.5k valuation, 32 rep, 5 backers.

---

## Core Flows

### Onboarding (3 steps)
1. **Who are you?** - Choose type: Investor / Founder / Surfer (+ Expert)
2. **What's your world?** - Select up to 3 tags (Fintech, Design, Engineering, Marketing, VC, Web3, CleanTech...)
3. **What are you here for?** - Find people to back / Find collaborators / Find projects + bio
- Stored in `localStorage` as `any1_user`
- Shows confetti on completion

### Discover (Swipe)
- Swipe right = Interested (follow)
- Swipe left = Skip (pass)
- Swipe up = Back (invest) - triggers invest modal
- Undo button for last action
- Filter by type (All/Investor/Founder/Surfer/Expert)
- Match tags based on thesis (from localStorage `any1_thesis`)

### Back / Invest Flow
- Modal with user info + valuation
- Choose amount: $1 / $5 / $10 / $50 or custom
- Saves to `localStorage` as `any1_portfolio` and `any1_backer_cards`
- Shows "Backed!" confirmation

### Home Feed
- Live price ticker tape at top (30s scroll)
- Market summary: Total Value, People count, Up today, 24/7
- Filter by type + filter by All/Trending/Rising/Falling
- "Windows of Opportunity" section - rising users with fewer backers
- Leaderboard - top 5 gainers this week
- Missions CTA card
- People list (UserCards) with live price updates every 1s
- Notifications bell with badge count

### Market Screen
- All users ranked by market cap (or gainers/losers/most backed)
- Search by name/handle
- Live price flash (green/red) every 1.2s
- Mini sparkline charts per row
- Stats bar: Total cap, Top Gainer, Top Loser, Most Backed

### User Profile (UserPage)
- Cover image + avatar + type badge
- Follow + Message + Back buttons
- Stats: Market Cap, Collateral, Backers, Missions
- Reputation bar with level and progress
- Value chart (sparkline)
- Tabs: Dashboard (ventures/portfolio/projects) | Posts | Transactions
- Transactions tab: public/private visibility, buy/sell history

### Portfolio
- Hero card: total value + P&L
- 1D/1W/1M chart tabs
- Per-position: mini chart, % change, unrealized P&L
- "Best performer today" card
- Data from `localStorage: any1_portfolio`

### Missions
- Mission cards with cover, description, skills needed, deadline
- Filter: All/Design/Engineering/Marketing/Writing/Strategy
- Apply flow: textarea "Why you?" + Submit
- Submit shows "Applied ✓" confirmation

### Chat (DM)
- Slide-in from user profile
- Bubble messages with timestamps
- Read receipts (mock)
- Keyboard-aware input bar

---

## localStorage Keys
| Key | Contents |
|-----|----------|
| `any1_user` | Onboarding user profile JSON |
| `any1_thesis` | Array of thesis tags (e.g. `["tech","media"]`) |
| `any1_thesis_done` | Boolean flag (hides thesis modal) |
| `any1_portfolio` | Array of `{userId, shares, buyPrice, currentPrice}` |
| `any1_backer_cards` | Array of investment cards with amounts and dates |

---

## Task Board (TASKS.md) - Current Status

### Phase 1 - Critical
| # | Task | Status |
|---|------|--------|
| TASK-01 | Onboarding Flow | Partially built |
| TASK-02 | Mission Board | Built (basic) |
| TASK-03 | Notification System | Built (mock) |
| TASK-04 | Portfolio P&L | Built (basic) |
| TASK-11 | Live Ticker | Built |

### Phase 1 - Important
| # | Task | Status |
|---|------|--------|
| TASK-05 | Leaderboard | Built |
| TASK-06 | Reputation System | Built |
| TASK-07 | Chat / DM | Built (mock) |
| TASK-08 | Weekly Digest | Not started |
| TASK-09 | Swipe UI improvements | Partial |
| TASK-10 | Edit Profile | Not started |
| TASK-12 | UserCard enhancements | Not started |
| TASK-13 | Posts / Create | Not started |

### Phase 2 - Future
- TASK-14: Market Screen (full version)
- TASK-15: Collateral UI
- TASK-16: Any1 Score (composite score 0-1000)

---

## Theme Colors (Dark Mode Default)
```
bg:       #0E0D0C    (main background)
surface:  #161513    (cards)
surface2: #1E1C1A    (inputs, secondary)
text:     #F5F0EA    (primary text)
text2:    #C8BFB5    (secondary text)
muted:    #7A6E62    (muted text)
border:   #2A2520    (dividers)
border2:  #3D3730    (stronger borders)
accent:   #C9A84C    (gold - primary CTA)
up:       #4BBFB5    (green - price up)
down:     #C0564A    (red - price down)
```

---

## Deployment

### GitHub
- Repo: `TM-Design-Industries/any1`
- Main branch auto-deploys to Vercel

### Vercel
- URL: https://any1.vercel.app
- User ID: `3Bg0cV40LEET7ZlVIel6xGF7`

### Local Dev
```bash
npm install
npm run dev     # localhost:5173
npm run build   # build for production
```

---

## How to Help with Any1

When Yehuda or Tamir ask about Any1:
1. Use the GitHub token to read/write code
2. Understand the React component structure above
3. Check TASKS.md for pending work
4. Always preserve the dark theme + gold accent color system
5. Use inline styles (no CSS modules/Tailwind) - project convention
6. Keep mobile-first (max-width: 430px viewport)
7. localStorage is the only persistence (no backend yet)

### Common requests:
- "Implement TASK-XX" - read the task from the board above, write the code, push to GitHub
- "Fix bug in [page]" - fetch the file from GitHub, fix, push back
- "Add user [name]" - add to mockData.js with proper structure
- "Update the UI" - fetch component, apply changes, push

### Git workflow:
```powershell
# Read file
$headers = @{Authorization="token <TOKEN>"}
$file = Invoke-RestMethod -Uri "https://api.github.com/repos/TM-Design-Industries/any1/contents/PATH" -Headers $headers

# Update file (need SHA from read)
$body = @{
  message = "commit message"
  content = [Convert]::ToBase64String([Text.Encoding]::UTF8.GetBytes($newContent))
  sha = $file.sha
} | ConvertTo-Json
Invoke-RestMethod -Method Put -Uri "https://api.github.com/repos/TM-Design-Industries/any1/contents/PATH" -Headers $headers -Body $body -ContentType "application/json"
```
