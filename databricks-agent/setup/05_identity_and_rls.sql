-- ============================================================
-- FILE: setup/05_identity_and_rls.sql
-- Adds Row Level Security (RLS) to all memory tables so each
-- user can only read/write their own data, enforced by Unity
-- Catalog using CURRENT_USER() = the authenticated Databricks
-- identity.
--
-- Run AFTER 01_init_catalog.sql
-- Requires: Unity Catalog + workspace admin or data steward role
-- ============================================================

USE CATALOG ai_agent;

-- ------------------------------------------------------------
-- 1. Row Filter Functions
--    Each function returns TRUE only when the row's user_id
--    matches the currently authenticated Databricks user.
-- ------------------------------------------------------------

-- Filter for longterm memory
CREATE OR REPLACE FUNCTION ai_agent.memory.rls_user_filter(row_user_id STRING)
  RETURN row_user_id = CURRENT_USER()
  COMMENT 'RLS filter: each user sees only their own rows';

-- Filter for daily notes
CREATE OR REPLACE FUNCTION ai_agent.memory.rls_daily_filter(row_user_id STRING)
  RETURN row_user_id = CURRENT_USER()
  COMMENT 'RLS filter for daily notes';

-- Filter for preferences
CREATE OR REPLACE FUNCTION ai_agent.memory.rls_prefs_filter(row_user_id STRING)
  RETURN row_user_id = CURRENT_USER()
  COMMENT 'RLS filter for preferences';

-- Filter for session history
CREATE OR REPLACE FUNCTION ai_agent.sessions.rls_history_filter(row_user_id STRING)
  RETURN row_user_id = CURRENT_USER()
  COMMENT 'RLS filter for session history';

-- Filter for audit log (admins see all; regular users see own)
CREATE OR REPLACE FUNCTION ai_agent.audit.rls_audit_filter(row_user_id STRING)
  RETURN row_user_id = CURRENT_USER()
    OR IS_ACCOUNT_GROUP_MEMBER('ai_agent_admins')
  COMMENT 'RLS filter: admins see all, users see own audit records';

-- ------------------------------------------------------------
-- 2. Apply Row Filters to Tables
-- ------------------------------------------------------------

ALTER TABLE ai_agent.memory.longterm
  SET ROW FILTER ai_agent.memory.rls_user_filter ON (user_id);

ALTER TABLE ai_agent.memory.daily
  SET ROW FILTER ai_agent.memory.rls_daily_filter ON (user_id);

ALTER TABLE ai_agent.memory.preferences
  SET ROW FILTER ai_agent.memory.rls_prefs_filter ON (user_id);

ALTER TABLE ai_agent.sessions.history
  SET ROW FILTER ai_agent.sessions.rls_history_filter ON (user_id);

ALTER TABLE ai_agent.audit.agent_runs
  SET ROW FILTER ai_agent.audit.rls_audit_filter ON (user_id);

-- ------------------------------------------------------------
-- 3. Column Mask for sensitive preference values (optional)
--    Admins see full values; users see their own full values;
--    any other principal sees REDACTED.
-- ------------------------------------------------------------

CREATE OR REPLACE FUNCTION ai_agent.memory.mask_pref_value(
  row_user_id STRING,
  value       STRING
)
  RETURN IF(
    row_user_id = CURRENT_USER()
      OR IS_ACCOUNT_GROUP_MEMBER('ai_agent_admins'),
    value,
    '*** REDACTED ***'
  )
  COMMENT 'Column mask: only owner or admins see raw preference values';

ALTER TABLE ai_agent.memory.preferences
  ALTER COLUMN pref_value
  SET MASK ai_agent.memory.mask_pref_value USING COLUMNS (user_id);

-- ------------------------------------------------------------
-- 4. Grant permissions: each Databricks user can read/write
--    only their own data (RLS enforces the row-level boundary)
-- ------------------------------------------------------------

-- All workspace users can USE the catalog and schemas
GRANT USE CATALOG ON CATALOG ai_agent TO `account users`;
GRANT USE SCHEMA  ON SCHEMA ai_agent.memory   TO `account users`;
GRANT USE SCHEMA  ON SCHEMA ai_agent.sessions TO `account users`;
GRANT USE SCHEMA  ON SCHEMA ai_agent.audit    TO `account users`;

-- Read + write on their own rows (RLS filters what they can see)
GRANT SELECT, MODIFY ON TABLE ai_agent.memory.longterm     TO `account users`;
GRANT SELECT, MODIFY ON TABLE ai_agent.memory.daily        TO `account users`;
GRANT SELECT, MODIFY ON TABLE ai_agent.memory.preferences  TO `account users`;
GRANT SELECT         ON TABLE ai_agent.sessions.history    TO `account users`;
GRANT SELECT         ON TABLE ai_agent.audit.agent_runs    TO `account users`;

-- App service principal gets full write access (bypasses RLS for inserts)
-- Replace 'ai-agent' with your actual app service principal name
GRANT ALL PRIVILEGES ON SCHEMA ai_agent.memory   TO `ai-agent`;
GRANT ALL PRIVILEGES ON SCHEMA ai_agent.sessions TO `ai-agent`;
GRANT ALL PRIVILEGES ON SCHEMA ai_agent.audit    TO `ai-agent`;

-- Admins group sees everything
GRANT ALL PRIVILEGES ON CATALOG ai_agent TO `ai_agent_admins`;

-- ------------------------------------------------------------
-- 5. Verify RLS is active
-- ------------------------------------------------------------

-- Run as a regular user - should only show THEIR rows:
-- SELECT * FROM ai_agent.memory.longterm;

-- Show applied filters
DESCRIBE TABLE EXTENDED ai_agent.memory.longterm;

SELECT 'RLS setup complete' AS status;
