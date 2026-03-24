-- ============================================================
-- FILE: setup/02_init_volumes.sql
-- Creates Unity Catalog Volumes for skill storage.
-- Run this AFTER 01_init_catalog.sql.
-- ============================================================

-- The `skills` schema was already created in step 01, but we
-- ensure it exists here for idempotency.
CREATE SCHEMA IF NOT EXISTS ai_agent.skills
  COMMENT 'Skill library metadata and volumes';

-- Shared skill library (agent-managed, read-only at runtime)
CREATE VOLUME IF NOT EXISTS ai_agent.skills.library
  COMMENT 'Shared skill library. Contains SKILL.md files and _index.json for all built-in skills.';

-- Per-user custom skills (users can upload their own skill packs)
CREATE VOLUME IF NOT EXISTS ai_agent.skills.user_skills
  COMMENT 'User-uploaded custom skills. Organised as user_skills/<user_id>/<skill_name>/SKILL.md.';

-- Verify
SELECT
  volume_catalog,
  volume_schema,
  volume_name,
  volume_type,
  comment
FROM information_schema.volumes
WHERE volume_catalog = 'ai_agent'
  AND volume_schema  = 'skills'
ORDER BY volume_name;
