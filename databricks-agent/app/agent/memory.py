"""
app/agent/memory.py

Memory layer for the AI Agent Platform.
Reads and writes to Unity Catalog Delta tables using the Databricks SQL
connector (via SDK) so the FastAPI app does not need a live SparkSession
(it runs in a Databricks App container without a cluster attached).

Tables used:
  ai_agent.memory.longterm
  ai_agent.memory.daily
  ai_agent.memory.preferences
  ai_agent.sessions.history
  ai_agent.audit.agent_runs
"""

from __future__ import annotations

import datetime
import json
import logging
import os
import uuid
from typing import Any, Optional

from databricks.sdk import WorkspaceClient
from databricks.sdk.service.sql import StatementState

logger = logging.getLogger("agent.memory")

CATALOG        = os.getenv("CATALOG", "ai_agent")
WAREHOUSE_ID   = os.getenv("WAREHOUSE_ID", "")


# ---------------------------------------------------------------------------
# Internal SQL execution helper
# ---------------------------------------------------------------------------

_sdk_client: Optional[WorkspaceClient] = None


def _get_client() -> WorkspaceClient:
    global _sdk_client
    if _sdk_client is None:
        _sdk_client = WorkspaceClient()
    return _sdk_client


def _exec_sql(statement: str, params: Optional[list] = None) -> list[dict]:
    """Execute a SQL statement via the SQL Warehouse and return rows as dicts."""
    client = _get_client()
    warehouse_id = WAREHOUSE_ID
    if not warehouse_id:
        raise RuntimeError("WAREHOUSE_ID env var is not set.")

    response = client.statement_execution.execute_statement(
        warehouse_id=warehouse_id,
        statement=statement,
        wait_timeout="30s",
    )

    if response.status.state not in (StatementState.SUCCEEDED,):
        err = response.status.error
        raise RuntimeError(f"SQL error [{response.status.state}]: {err.message if err else 'unknown'}")

    if response.result is None or response.result.data_array is None:
        return []

    schema  = response.manifest.schema.columns
    columns = [col.name for col in schema]
    rows    = []
    for row_data in response.result.data_array:
        rows.append(dict(zip(columns, row_data)))
    return rows


def _exec_dml(statement: str) -> None:
    """Execute a DML statement (INSERT / MERGE / UPDATE). No rows returned."""
    _exec_sql(statement)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def get_user_context(user_id: str) -> str:
    """
    Load and format:
      - Top 50 long-term memories by importance
      - Today's daily notes
      - All user preferences
    Returns a formatted string ready for injection into a system prompt.
    """
    parts: list[str] = []

    # --- Long-term memory ---
    try:
        rows = _exec_sql(f"""
            SELECT category, key, value, importance
            FROM   {CATALOG}.memory.longterm
            WHERE  user_id = '{_esc(user_id)}'
              AND  (expires_at IS NULL OR expires_at > CURRENT_TIMESTAMP)
            ORDER BY importance DESC, updated_at DESC
            LIMIT 50
        """)
        if rows:
            mem_lines = [
                f"  [{r['category']}] {r['key']}: {r['value']} (importance={r['importance']})"
                for r in rows
            ]
            parts.append("## Long-term Memory\n" + "\n".join(mem_lines))
    except Exception as exc:
        logger.warning("Could not load longterm memory for %s: %s", user_id, exc)

    # --- Today's daily notes ---
    try:
        today = datetime.date.today().isoformat()
        rows = _exec_sql(f"""
            SELECT content, tags, session_id
            FROM   {CATALOG}.memory.daily
            WHERE  user_id    = '{_esc(user_id)}'
              AND  note_date  = '{today}'
            ORDER BY created_at
        """)
        if rows:
            note_lines = []
            for r in rows:
                tags_str = ", ".join(r["tags"]) if r.get("tags") else ""
                note_lines.append(f"  - {r['content']}" + (f" [{tags_str}]" if tags_str else ""))
            parts.append(f"## Today's Notes ({today})\n" + "\n".join(note_lines))
    except Exception as exc:
        logger.warning("Could not load daily notes for %s: %s", user_id, exc)

    # --- Preferences ---
    try:
        rows = _exec_sql(f"""
            SELECT pref_key, pref_value, pref_type
            FROM   {CATALOG}.memory.preferences
            WHERE  user_id = '{_esc(user_id)}'
            ORDER BY pref_key
        """)
        if rows:
            pref_lines = [f"  {r['pref_key']} = {r['pref_value']} ({r['pref_type']})" for r in rows]
            parts.append("## Preferences\n" + "\n".join(pref_lines))
    except Exception as exc:
        logger.warning("Could not load preferences for %s: %s", user_id, exc)

    if not parts:
        return "(No memory context available for this user)"

    return "\n\n".join(parts)


def save_memory(
    user_id: str,
    key: str,
    value: str,
    category: str = "fact",
    importance: int = 5,
    source: str = "agent",
) -> None:
    """
    MERGE a memory entry into ai_agent.memory.longterm.
    If (user_id, category, key) already exists, update value/importance/updated_at.
    """
    now = _ts_now()
    entry_id = str(uuid.uuid4())

    statement = f"""
    MERGE INTO {CATALOG}.memory.longterm AS target
    USING (
        SELECT
            '{_esc(entry_id)}'  AS id,
            '{_esc(user_id)}'   AS user_id,
            '{_esc(category)}'  AS category,
            '{_esc(key)}'       AS key,
            '{_esc(value)}'     AS value,
            {int(importance)}   AS importance,
            '{_esc(source)}'    AS source,
            TIMESTAMP '{now}'   AS created_at,
            TIMESTAMP '{now}'   AS updated_at,
            NULL                AS expires_at
    ) AS source
    ON  target.user_id  = source.user_id
    AND target.category = source.category
    AND target.key      = source.key
    WHEN MATCHED THEN UPDATE SET
        target.value      = source.value,
        target.importance = source.importance,
        target.source     = source.source,
        target.updated_at = source.updated_at
    WHEN NOT MATCHED THEN INSERT *
    """
    try:
        _exec_dml(statement)
        logger.debug("Saved memory [%s|%s|%s] for %s", category, key, value[:40], user_id)
    except Exception as exc:
        logger.error("Failed to save memory for %s: %s", user_id, exc)
        raise


def save_daily_note(
    user_id: str,
    content: str,
    tags: Optional[list[str]] = None,
    session_id: Optional[str] = None,
) -> None:
    """Insert a daily note into ai_agent.memory.daily."""
    note_id    = str(uuid.uuid4())
    now        = _ts_now()
    today      = datetime.date.today().isoformat()
    tags_str   = _format_array(tags or [])
    session_val = f"'{_esc(session_id)}'" if session_id else "NULL"

    statement = f"""
    INSERT INTO {CATALOG}.memory.daily
        (id, user_id, note_date, content, tags, session_id, created_at)
    VALUES
        (
            '{note_id}',
            '{_esc(user_id)}',
            '{today}',
            '{_esc(content)}',
            {tags_str},
            {session_val},
            TIMESTAMP '{now}'
        )
    """
    try:
        _exec_dml(statement)
        logger.debug("Saved daily note for %s", user_id)
    except Exception as exc:
        logger.error("Failed to save daily note for %s: %s", user_id, exc)
        raise


def save_preference(
    user_id: str,
    key: str,
    value: str,
    pref_type: str = "string",
) -> None:
    """MERGE a user preference into ai_agent.memory.preferences."""
    now = _ts_now()

    statement = f"""
    MERGE INTO {CATALOG}.memory.preferences AS target
    USING (
        SELECT
            '{_esc(user_id)}'  AS user_id,
            '{_esc(key)}'      AS pref_key,
            '{_esc(value)}'    AS pref_value,
            '{_esc(pref_type)}'AS pref_type,
            TIMESTAMP '{now}'  AS updated_at
    ) AS source
    ON  target.user_id  = source.user_id
    AND target.pref_key = source.pref_key
    WHEN MATCHED THEN UPDATE SET
        target.pref_value = source.pref_value,
        target.pref_type  = source.pref_type,
        target.updated_at = source.updated_at
    WHEN NOT MATCHED THEN INSERT *
    """
    try:
        _exec_dml(statement)
        logger.debug("Saved preference [%s=%s] for %s", key, value, user_id)
    except Exception as exc:
        logger.error("Failed to save preference for %s: %s", user_id, exc)
        raise


def get_session_history(session_id: str, limit: int = 20) -> list[dict]:
    """Return the most recent `limit` turns for a session, oldest-first."""
    try:
        rows = _exec_sql(f"""
            SELECT turn_index, role, content, skill_used, genie_query, tokens_used, model, created_at
            FROM   {CATALOG}.sessions.history
            WHERE  session_id = '{_esc(session_id)}'
            ORDER BY turn_index DESC
            LIMIT {int(limit)}
        """)
        # Reverse so oldest turn is first (correct message order for LLM)
        rows.reverse()
        return rows
    except Exception as exc:
        logger.warning("Could not load session history for %s: %s", session_id, exc)
        return []


def save_turn(
    session_id: str,
    user_id: str,
    role: str,
    content: str,
    skill_used: Optional[str] = None,
    genie_query: bool = False,
    tokens_used: Optional[int] = None,
    model: Optional[str] = None,
) -> None:
    """Append a conversation turn to ai_agent.sessions.history."""
    now = _ts_now()

    # Determine next turn_index
    try:
        rows = _exec_sql(f"""
            SELECT COALESCE(MAX(turn_index), -1) AS max_idx
            FROM   {CATALOG}.sessions.history
            WHERE  session_id = '{_esc(session_id)}'
        """)
        turn_index = int(rows[0]["max_idx"]) + 1 if rows else 0
    except Exception:
        turn_index = 0

    skill_val  = f"'{_esc(skill_used)}'"  if skill_used   else "NULL"
    tokens_val = str(int(tokens_used))    if tokens_used  else "NULL"
    model_val  = f"'{_esc(model)}'"       if model        else "NULL"
    genie_val  = "true" if genie_query else "false"

    statement = f"""
    INSERT INTO {CATALOG}.sessions.history
        (session_id, user_id, turn_index, role, content,
         skill_used, genie_query, tokens_used, model, created_at)
    VALUES
        (
            '{_esc(session_id)}',
            '{_esc(user_id)}',
            {turn_index},
            '{_esc(role)}',
            '{_esc(content)}',
            {skill_val},
            {genie_val},
            {tokens_val},
            {model_val},
            TIMESTAMP '{now}'
        )
    """
    try:
        _exec_dml(statement)
    except Exception as exc:
        logger.error("Failed to save turn for session %s: %s", session_id, exc)
        raise


def log_audit_run(
    user_id: str,
    session_id: str,
    channel: str,
    skill_matched: Optional[str],
    genie_used: bool,
    latency_ms: int,
    success: bool,
    error_message: Optional[str] = None,
) -> None:
    """Insert a record into ai_agent.audit.agent_runs."""
    run_id    = str(uuid.uuid4())
    now       = _ts_now()
    skill_val = f"'{_esc(skill_matched)}'" if skill_matched else "NULL"
    err_val   = f"'{_esc(error_message)}'" if error_message else "NULL"
    genie_val = "true" if genie_used else "false"
    ok_val    = "true" if success else "false"

    statement = f"""
    INSERT INTO {CATALOG}.audit.agent_runs
        (run_id, user_id, session_id, channel, skill_matched,
         genie_used, latency_ms, success, error_message, created_at)
    VALUES
        (
            '{run_id}',
            '{_esc(user_id)}',
            '{_esc(session_id)}',
            '{_esc(channel)}',
            {skill_val},
            {genie_val},
            {int(latency_ms)},
            {ok_val},
            {err_val},
            TIMESTAMP '{now}'
        )
    """
    try:
        _exec_dml(statement)
    except Exception as exc:
        logger.warning("Failed to log audit run: %s", exc)


# ---------------------------------------------------------------------------
# Private helpers
# ---------------------------------------------------------------------------

def _esc(s: Any) -> str:
    """Escape single quotes in a string value for SQL."""
    if s is None:
        return ""
    return str(s).replace("'", "\\'")


def _ts_now() -> str:
    """Return current UTC timestamp as ISO string compatible with Spark TIMESTAMP."""
    return datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")


def _format_array(items: list[str]) -> str:
    """Format a Python list as a Spark SQL ARRAY literal."""
    if not items:
        return "ARRAY()"
    escaped = ", ".join(f"'{_esc(i)}'" for i in items)
    return f"ARRAY({escaped})"
