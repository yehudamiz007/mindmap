# Setting Up Your Databricks Genie Space

This guide walks you through creating a Genie Space that gives the AI Agent
natural-language access to the `ai_agent` Unity Catalog tables.

---

## Prerequisites

- Databricks workspace with Genie enabled (requires Premium or above)
- Unity Catalog enabled
- `ai_agent` catalog and tables created (run `01_init_catalog.sql` first)
- SQL Warehouse running (note the warehouse ID - you'll need it)

---

## Step 1: Open Genie

1. In the Databricks UI left sidebar, click **Genie** (star icon).
2. Click **Create Space** (top-right button).

---

## Step 2: Configure the Space

| Field | Value |
|---|---|
| **Name** | `AI Agent Memory & Sessions` |
| **Description** | Natural language access to agent memory, sessions, and audit logs |
| **SQL Warehouse** | Select your running warehouse |

Click **Create**.

---

## Step 3: Add Tables

In the space configuration, click **Add tables** and add:

| Table | Purpose |
|---|---|
| `ai_agent.memory.longterm` | Long-term user memory |
| `ai_agent.memory.daily` | Daily notes |
| `ai_agent.memory.preferences` | User preferences |
| `ai_agent.sessions.history` | Conversation history |
| `ai_agent.audit.agent_runs` | Run audit log |
| `ai_agent.memory.top_memories` | (view) High-importance memories |
| `ai_agent.sessions.recent_turns` | (view) Last 7 days of turns |

---

## Step 4: Add Table Descriptions (Unity Catalog)

Good table descriptions dramatically improve Genie's accuracy.
Run these in a SQL notebook or the SQL editor:

```sql
-- longterm memory
ALTER TABLE ai_agent.memory.longterm
  SET TBLPROPERTIES ('comment' = 'Long-term user memory. Each row is a key fact or preference about a user. importance 1-10 (10=most critical). category values: fact, preference, person, lesson, project.');

-- daily notes
ALTER TABLE ai_agent.memory.daily
  SET TBLPROPERTIES ('comment' = 'Daily conversation notes captured during AI agent sessions. tags is an array of topic strings. session_id links back to sessions.history.');

-- preferences
ALTER TABLE ai_agent.memory.preferences
  SET TBLPROPERTIES ('comment' = 'User preference key-value store. pref_type is one of: string, int, bool, json.');

-- sessions history
ALTER TABLE ai_agent.sessions.history
  SET TBLPROPERTIES ('comment' = 'Full turn-by-turn conversation log. role is user or assistant. genie_query=true means a Genie data lookup was made for that turn.');

-- audit runs
ALTER TABLE ai_agent.audit.agent_runs
  SET TBLPROPERTIES ('comment' = 'One row per agent invocation. latency_ms is the total round-trip time. channel is where the message came from.');
```

---

## Step 5: Add Verified Answers (Curated Q&A)

Verified answers are example question-SQL pairs that Genie learns from.
Add them in the Genie Space under **Verified answers** > **Add**.

### Verified Answer 1
**Question:** How many messages did user `yehuda` send this week?

```sql
SELECT COUNT(*) AS message_count
FROM   ai_agent.sessions.history
WHERE  user_id    = 'yehuda'
  AND  role       = 'user'
  AND  created_at >= DATE_TRUNC('week', CURRENT_TIMESTAMP);
```

---

### Verified Answer 2
**Question:** What are the top memories for user `yehuda`?

```sql
SELECT category, key, value, importance, updated_at
FROM   ai_agent.memory.longterm
WHERE  user_id    = 'yehuda'
  AND  (expires_at IS NULL OR expires_at > CURRENT_TIMESTAMP)
ORDER BY importance DESC, updated_at DESC
LIMIT 20;
```

---

### Verified Answer 3
**Question:** How many agent runs failed in the last 24 hours?

```sql
SELECT COUNT(*) AS failed_runs
FROM   ai_agent.audit.agent_runs
WHERE  success     = false
  AND  created_at >= CURRENT_TIMESTAMP - INTERVAL 1 DAY;
```

---

### Verified Answer 4
**Question:** What skills were most used this month?

```sql
SELECT   skill_matched, COUNT(*) AS uses
FROM     ai_agent.audit.agent_runs
WHERE    skill_matched IS NOT NULL
  AND    created_at    >= DATE_TRUNC('month', CURRENT_TIMESTAMP)
GROUP BY skill_matched
ORDER BY uses DESC;
```

---

### Verified Answer 5
**Question:** Show me today's notes for user `yehuda`.

```sql
SELECT content, tags, session_id, created_at
FROM   ai_agent.memory.daily
WHERE  user_id   = 'yehuda'
  AND  note_date = CURRENT_DATE
ORDER BY created_at;
```

---

## Step 6: Add Custom Instructions

In the Genie Space, click **Instructions** > **Add instructions** and paste:

```
You are a data assistant for the AI Agent Platform. You answer questions
about user memory, conversation sessions, skill usage, and agent performance.

Key rules:
- When a user asks about "memories" or "what does the agent know", query ai_agent.memory.longterm
- When asked about "conversations" or "chat history", query ai_agent.sessions.history  
- "Today's notes" means ai_agent.memory.daily WHERE note_date = CURRENT_DATE
- importance column is 1-10; 10 = most important
- user_id values are typically short strings like 'yehuda' or email addresses
- Always filter by user_id unless explicitly asked for all users
- Format timestamps as human-readable dates when displaying results
- When returning memory values, include the category and key for context
```

---

## Step 7: Get the Space ID

After saving the Genie Space:

1. Note the URL - it will look like:
   `https://<workspace>.azuredatabricks.net/genie/spaces/<SPACE_ID>`

2. Copy the `<SPACE_ID>` (a UUID string).

3. Update your app configuration:
   - In `app/app.yaml`, set `GENIE_SPACE_ID` to this value.
   - Or set the `GENIE_SPACE_ID` environment variable in your deployment.

---

## Step 8: Test the Space

In the Genie Space chat, try these test questions:

- "How many users have memories stored?"
- "What are the most important memories?"
- "Show me failed agent runs today"
- "Which skill is used the most?"
- "List all user preferences"

If results look correct, your Genie Space is ready.

---

## Troubleshooting

| Issue | Fix |
|---|---|
| Genie returns wrong table | Add more verified answers for that question type |
| "No data access" error | Check warehouse has SELECT on `ai_agent` catalog |
| Empty results | Ensure setup SQL was run and tables have data |
| Space ID not found in URL | Check you're in the Genie UI, not Dashboards |

---

## Next Steps

- Set `GENIE_SPACE_ID` in `app/app.yaml`
- Deploy the app: `databricks bundle deploy -t dev`
- Test via the `/chat` API endpoint with a data question like "how many memories do I have?"
