# Databricks AI Agent Platform

An OpenClaw-style AI agent platform running natively on Databricks using:
- **Databricks Apps** (FastAPI) for the runtime
- **Unity Catalog** for persistent memory and session history
- **Databricks Genie** for natural language data queries
- **Anthropic Claude** as the LLM backbone
- **Databricks Asset Bundles (DAB)** for deployment

---

## Architecture

```
User (Slack / Webhook / Direct)
         |
         v
  FastAPI App (Databricks Apps)
         |
    AgentRuntime
   /      |       \
Memory  Skills   Genie
(UC)   (Volume) (NL->SQL)
         |
      Claude API
         |
   [REMEMBER tags] -> Unity Catalog memory tables
```

---

## Prerequisites

- Databricks workspace (Premium or above, Unity Catalog enabled)
- Databricks CLI v0.220+ installed and configured
- Python 3.11+
- Anthropic API key (`sk-ant-...`)
- (Optional) Slack Bot Token for Slack integration

### Install Databricks CLI

```bash
curl -fsSL https://raw.githubusercontent.com/databricks/setup-cli/main/install.sh | sh
databricks configure
```

---

## Setup Guide

### Step 1: Clone the Project

```bash
git clone <your-repo-url>
cd databricks-agent
```

### Step 2: Configure Workspace Host

Edit `databricks.yml` if your workspace host is not auto-detected:

```yaml
targets:
  dev:
    workspace:
      host: https://your-workspace.azuredatabricks.net  # or .cloud.databricks.com
```

Or set the environment variable:

```bash
export DATABRICKS_HOST=https://your-workspace.azuredatabricks.net
export DATABRICKS_TOKEN=dapiXXXXXXXXXXXXXXXX
```

### Step 3: Create Secret Scope

```bash
databricks secrets create-scope ai-agent-secrets --initial-manage-principal users
```

### Step 4: Store Secrets

```bash
# Anthropic API key (required)
databricks secrets put-secret ai-agent-secrets anthropic-api-key \
  --string-value "sk-ant-api03-XXXXXXXXXXXXXXXXXXXX"

# Slack Bot Token (optional - only needed for Slack integration)
databricks secrets put-secret ai-agent-secrets slack-bot-token \
  --string-value "xoxb-XXXXXXXXXX-XXXXXXXXXXXX-XXXXXXXXXXXXXXXXXXXXXXXX"
```

### Step 5: Run Setup SQL Files

In a Databricks notebook (attach to any cluster), run the setup files in order:

```sql
-- In a Databricks SQL notebook or editor:
-- Paste contents of setup/01_init_catalog.sql and run
-- Paste contents of setup/02_init_volumes.sql and run
```

Or use the CLI:

```bash
databricks sql submit --warehouse-id <your-warehouse-id> \
  --file setup/01_init_catalog.sql

databricks sql submit --warehouse-id <your-warehouse-id> \
  --file setup/02_init_volumes.sql
```

### Step 6: Seed Skills to Volume

In a Databricks notebook, run:

```python
# Upload skills to Unity Catalog Volume
# Paste and run contents of setup/03_seed_skills.py
```

Or copy files directly via the CLI:

```bash
databricks fs cp -r skills/ dbfs:/Volumes/ai_agent/skills/library/ --overwrite
```

### Step 7: Configure the App

Edit `app/app.yaml` and fill in:

```yaml
env:
  - name: WAREHOUSE_ID
    value: "abc123def456"   # Your SQL Warehouse ID
  - name: GENIE_SPACE_ID
    value: "01234567-..."   # Your Genie Space UUID (from step 9)
```

### Step 8: Deploy (Dev)

```bash
databricks bundle deploy -t dev
```

This deploys:
- The FastAPI app to Databricks Apps
- The nightly memory maintenance job

### Step 9: Setup Genie Space

See the full guide: [`setup/04_init_genie_space.md`](setup/04_init_genie_space.md)

Quick summary:
1. Go to Databricks UI -> Genie -> Create Space
2. Add tables: `ai_agent.memory.longterm`, `ai_agent.sessions.history`, etc.
3. Copy the Space ID from the URL
4. Update `app/app.yaml` with `GENIE_SPACE_ID`
5. Redeploy: `databricks bundle deploy -t dev`

### Step 10: Test the API

Find your app URL in the Databricks Apps section of the UI, then:

```bash
# Health check
curl https://your-app.databricksapps.net/health

# Chat
curl -X POST https://your-app.databricksapps.net/chat \
  -H "Content-Type: application/json" \
  -d '{"user_id": "yehuda", "message": "Hello! What can you help me with?"}'

# Data question (triggers Genie)
curl -X POST https://your-app.databricksapps.net/chat \
  -H "Content-Type: application/json" \
  -d '{"user_id": "yehuda", "message": "How many messages have I sent this week?"}'

# Save a memory
curl -X POST https://your-app.databricksapps.net/memory/yehuda \
  -H "Content-Type: application/json" \
  -d '{"key": "favorite_language", "value": "Hebrew", "category": "preference", "importance": 9}'

# Get memory context
curl https://your-app.databricksapps.net/memory/yehuda

# List skills
curl https://your-app.databricksapps.net/skills
```

### Step 11: Deploy to Production

```bash
databricks bundle deploy -t prod
```

---

## Project Structure

```
databricks-agent/
├── databricks.yml              # Bundle definition (apps + jobs)
├── README.md
│
├── setup/
│   ├── 01_init_catalog.sql    # Create catalog, schemas, tables
│   ├── 02_init_volumes.sql    # Create skill Volumes
│   ├── 03_seed_skills.py      # Upload skills to Volume
│   └── 04_init_genie_space.md # Genie Space setup guide
│
├── app/                        # Databricks App (FastAPI)
│   ├── app.yaml               # App configuration
│   ├── app.py                 # FastAPI routes
│   ├── requirements.txt
│   ├── agent/
│   │   ├── __init__.py
│   │   ├── memory.py          # Unity Catalog memory CRUD
│   │   ├── skills.py          # Skill index + matching
│   │   ├── genie.py           # Genie NL->SQL integration
│   │   ├── context.py         # System prompt assembly
│   │   └── runtime.py         # Main agent orchestrator
│   └── channels/
│       ├── __init__.py
│       ├── slack.py           # Slack Events API handler
│       └── webhook.py         # Generic webhook handler
│
├── jobs/
│   └── memory_maintenance.py  # Nightly memory summarisation job
│
├── skills/
│   ├── _index.json            # Skill registry
│   ├── general/
│   │   └── SKILL.md
│   └── databricks/
│       └── SKILL.md
│
└── .github/
    └── workflows/
        └── deploy.yml          # GitHub Actions CI/CD
```

---

## Adding New Skills

1. Create a directory: `skills/your-skill-name/`
2. Create `skills/your-skill-name/SKILL.md` with YAML front-matter:

```markdown
---
name: your-skill-name
description: When to use this skill (used for matching)
keywords: keyword1, keyword2, keyword3
---

# Skill Title

Your instructions here...
```

3. Re-run `setup/03_seed_skills.py` (or call `POST /admin/sync-skills`)

---

## Slack Integration

1. Create a Slack App at [api.slack.com/apps](https://api.slack.com/apps)
2. Add `chat:write` and `channels:history` Bot Token Scopes
3. Install the app to your workspace
4. Copy the Bot OAuth Token and store as secret (step 4)
5. Enable Event Subscriptions, set Request URL to:
   `https://your-app.databricksapps.net/webhook/slack`
6. Subscribe to `message.channels` and `message.im` events
7. Set `SLACK_BOT_USER_ID` in app.yaml (your bot's user ID)

---

## Memory System

The agent automatically extracts and stores memories using `[REMEMBER: ...]` tags:

| Table | Purpose |
|---|---|
| `ai_agent.memory.longterm` | Persistent facts, preferences, people, projects |
| `ai_agent.memory.daily` | Daily session notes |
| `ai_agent.memory.preferences` | User preference key-value store |

The nightly job (`memory_maintenance`) summarises daily notes into long-term memory using Claude.

---

## Environment Variables

| Variable | Required | Description |
|---|---|---|
| `ANTHROPIC_API_KEY` | Yes | From secret scope |
| `CATALOG` | Yes | Unity Catalog name (`ai_agent`) |
| `WAREHOUSE_ID` | Yes | SQL Warehouse ID |
| `GENIE_SPACE_ID` | No | Genie Space UUID (enables data queries) |
| `LLM_MODEL` | No | Defaults to `claude-sonnet-4-6` |
| `SLACK_BOT_TOKEN` | No | Required for Slack channel |
| `SLACK_BOT_USER_ID` | No | Prevents Slack self-reply loops |
| `MAX_TOKENS` | No | Max LLM response tokens (default: 2048) |

---

## Troubleshooting

| Problem | Fix |
|---|---|
| `WAREHOUSE_ID is not set` | Set `WAREHOUSE_ID` in `app/app.yaml` |
| Genie not working | Check `GENIE_SPACE_ID` and that warehouse has access to `ai_agent` catalog |
| Skills not loading | Run `POST /admin/sync-skills` or re-run `03_seed_skills.py` |
| Memory not persisting | Check SQL Warehouse is running and tables exist (run `01_init_catalog.sql`) |
| Slack infinite loop | Set `SLACK_BOT_USER_ID` to your bot's user ID |
| Claude rate limit | Tenacity retry handles this automatically (3 attempts, exponential backoff) |
