-- ============================================================
-- FILE: setup/01_init_catalog.sql
-- Initializes the AI Agent catalog, schemas, and tables.
-- Run this in a Databricks SQL notebook or SQL editor.
-- ============================================================

-- ------------------------------------------------------------
-- 1. Catalog
-- ------------------------------------------------------------
CREATE CATALOG IF NOT EXISTS ai_agent
  COMMENT 'AI Agent Platform - stores memory, sessions, skills and audit data';

-- ------------------------------------------------------------
-- 2. Schemas
-- ------------------------------------------------------------
CREATE SCHEMA IF NOT EXISTS ai_agent.memory
  COMMENT 'Long-term memory, daily notes and user preferences';

CREATE SCHEMA IF NOT EXISTS ai_agent.sessions
  COMMENT 'Conversation session history';

CREATE SCHEMA IF NOT EXISTS ai_agent.skills
  COMMENT 'Skill library metadata and volumes';

CREATE SCHEMA IF NOT EXISTS ai_agent.audit
  COMMENT 'Agent run audit logs';

-- ------------------------------------------------------------
-- 3. Tables
-- ------------------------------------------------------------

-- Long-term memory (CDF enabled for change tracking)
CREATE TABLE IF NOT EXISTS ai_agent.memory.longterm (
  id           STRING    NOT NULL  COMMENT 'UUID primary key',
  user_id      STRING    NOT NULL  COMMENT 'Owning user identifier',
  category     STRING    NOT NULL  COMMENT 'Memory category: fact, preference, person, lesson, project',
  key          STRING    NOT NULL  COMMENT 'Memory key within the category',
  value        STRING    NOT NULL  COMMENT 'Memory value / content',
  importance   INT       NOT NULL  COMMENT 'Importance score 1-10',
  source       STRING    NOT NULL  COMMENT 'Who created this memory: agent, user, system',
  created_at   TIMESTAMP NOT NULL  COMMENT 'Creation timestamp',
  updated_at   TIMESTAMP NOT NULL  COMMENT 'Last update timestamp',
  expires_at   TIMESTAMP           COMMENT 'Optional expiry timestamp (NULL = never)'
)
USING DELTA
TBLPROPERTIES (
  'delta.enableChangeDataFeed' = 'true',
  'delta.minReaderVersion'     = '1',
  'delta.minWriterVersion'     = '4'
)
COMMENT 'Long-term user memory, merged by (user_id, category, key)';

-- Daily notes
CREATE TABLE IF NOT EXISTS ai_agent.memory.daily (
  id         STRING            NOT NULL  COMMENT 'UUID primary key',
  user_id    STRING            NOT NULL  COMMENT 'Owning user identifier',
  note_date  DATE              NOT NULL  COMMENT 'Calendar date of the note',
  content    STRING            NOT NULL  COMMENT 'Note content',
  tags       ARRAY<STRING>               COMMENT 'Optional tags for categorisation',
  session_id STRING                      COMMENT 'Source session identifier',
  created_at TIMESTAMP         NOT NULL  COMMENT 'Creation timestamp'
)
USING DELTA
COMMENT 'Per-day notes captured during agent sessions';

-- User preferences
CREATE TABLE IF NOT EXISTS ai_agent.memory.preferences (
  user_id    STRING    NOT NULL  COMMENT 'Owning user identifier',
  pref_key   STRING    NOT NULL  COMMENT 'Preference key',
  pref_value STRING    NOT NULL  COMMENT 'Preference value',
  pref_type  STRING    NOT NULL  COMMENT 'Value type: string, int, bool, json',
  updated_at TIMESTAMP NOT NULL  COMMENT 'Last update timestamp'
)
USING DELTA
COMMENT 'User preference key-value store, merged by (user_id, pref_key)';

-- Session / conversation history
CREATE TABLE IF NOT EXISTS ai_agent.sessions.history (
  session_id   STRING    NOT NULL  COMMENT 'Session UUID',
  user_id      STRING    NOT NULL  COMMENT 'Owning user identifier',
  turn_index   INT       NOT NULL  COMMENT 'Turn order within the session (0-based)',
  role         STRING    NOT NULL  COMMENT 'Message role: user or assistant',
  content      STRING    NOT NULL  COMMENT 'Message content',
  skill_used   STRING              COMMENT 'Skill name matched for this turn, if any',
  genie_query  BOOLEAN   NOT NULL  COMMENT 'Whether a Genie data query was made',
  tokens_used  INT                 COMMENT 'LLM tokens consumed for this turn',
  model        STRING              COMMENT 'LLM model identifier used for this turn',
  created_at   TIMESTAMP NOT NULL  COMMENT 'Creation timestamp'
)
USING DELTA
COMMENT 'Full conversation turn-by-turn history';

-- Agent run audit log
CREATE TABLE IF NOT EXISTS ai_agent.audit.agent_runs (
  run_id        STRING    NOT NULL  COMMENT 'UUID for this audit record',
  user_id       STRING    NOT NULL  COMMENT 'Owning user identifier',
  session_id    STRING    NOT NULL  COMMENT 'Session identifier',
  channel       STRING    NOT NULL  COMMENT 'Inbound channel: whatsapp, slack, generic, direct',
  skill_matched STRING              COMMENT 'Skill that was matched, if any',
  genie_used    BOOLEAN   NOT NULL  COMMENT 'Whether Genie was queried',
  latency_ms    INT                 COMMENT 'End-to-end response latency in milliseconds',
  success       BOOLEAN   NOT NULL  COMMENT 'Whether the run succeeded',
  error_message STRING              COMMENT 'Error detail if success = false',
  created_at    TIMESTAMP NOT NULL  COMMENT 'Audit record creation timestamp'
)
USING DELTA
COMMENT 'Audit log for every agent invocation';

-- ------------------------------------------------------------
-- 4. Convenience views
-- ------------------------------------------------------------

-- Recent session turns (last 7 days)
CREATE OR REPLACE VIEW ai_agent.sessions.recent_turns AS
SELECT *
FROM   ai_agent.sessions.history
WHERE  created_at >= CURRENT_TIMESTAMP - INTERVAL 7 DAYS;

-- High-importance long-term memories
CREATE OR REPLACE VIEW ai_agent.memory.top_memories AS
SELECT *
FROM   ai_agent.memory.longterm
WHERE  importance >= 7
  AND  (expires_at IS NULL OR expires_at > CURRENT_TIMESTAMP)
ORDER BY importance DESC, updated_at DESC;

-- ------------------------------------------------------------
-- Done
-- ------------------------------------------------------------
SELECT 'AI Agent catalog initialised successfully' AS status;
