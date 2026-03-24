# Databricks notebook source
# ============================================================
# FILE: jobs/memory_maintenance.py
# Nightly maintenance job:
#   1. Find active users (sessions in last 7 days)
#   2. Read unprocessed daily notes per user
#   3. Use Claude to extract key facts
#   4. MERGE extracted facts into longterm memory
#   5. Mark notes as processed
#
# Runs daily at 02:00 Asia/Jerusalem (see databricks.yml)
# ============================================================

# COMMAND ----------
import anthropic
import datetime
import json
import os
import uuid

# ------------------------------------------------------------------
# Config
# ------------------------------------------------------------------
CATALOG      = spark.conf.get("spark.agent.catalog", "ai_agent")
LLM_MODEL    = "claude-sonnet-4-5"
ANTHROPIC_KEY = dbutils.secrets.get(scope="ai-agent-secrets", key="anthropic-api-key")

today         = datetime.date.today()
seven_days_ago = today - datetime.timedelta(days=7)

print(f"Memory maintenance started: {datetime.datetime.now().isoformat()}")
print(f"Processing notes from {seven_days_ago} to {today}")

# COMMAND ----------
# ------------------------------------------------------------------
# Step 1: Find users active in the last 7 days
# ------------------------------------------------------------------
active_users_df = spark.sql(f"""
    SELECT DISTINCT user_id
    FROM   {CATALOG}.sessions.history
    WHERE  created_at >= '{seven_days_ago}'
""")

user_ids = [row.user_id for row in active_users_df.collect()]
print(f"Active users: {len(user_ids)}")
for u in user_ids:
    print(f"  - {u}")

# COMMAND ----------
# ------------------------------------------------------------------
# Step 2 & 3: For each user, fetch unprocessed notes and summarise
# ------------------------------------------------------------------

client = anthropic.Anthropic(api_key=ANTHROPIC_KEY)


def extract_facts_from_notes(user_id: str, notes: list[dict]) -> list[dict]:
    """
    Call Claude to extract memorable facts from the user's daily notes.
    Returns a list of dicts: [{category, key, value, importance}]
    """
    if not notes:
        return []

    notes_text = "\n".join([
        f"- [{n['note_date']}] {n['content']}"
        + (f" (tags: {n['tags']})" if n.get("tags") else "")
        for n in notes
    ])

    prompt = f"""You are an AI assistant that extracts key facts worth remembering about a user.

Review these conversation notes for user '{user_id}':

{notes_text}

Extract 3-8 key facts, preferences, or important details about this user that would be valuable to remember in future conversations.

For each fact, respond with a JSON array item:
{{
  "category": "fact|preference|person|lesson|project",
  "key": "short_descriptive_key",
  "value": "the actual information",
  "importance": 1-10
}}

ONLY output a valid JSON array, no other text. Example:
[
  {{"category": "preference", "key": "response_language", "value": "Hebrew", "importance": 9}},
  {{"category": "fact", "key": "job_title", "value": "Senior Data Engineer", "importance": 7}}
]

If there are no meaningful facts to extract, return an empty array: []
"""

    try:
        response = client.messages.create(
            model     = LLM_MODEL,
            max_tokens= 1024,
            messages  = [{"role": "user", "content": prompt}],
        )
        raw = response.content[0].text.strip()
        # Strip markdown code blocks if present
        if raw.startswith("```"):
            lines = raw.split("\n")
            raw = "\n".join(lines[1:-1] if lines[-1].strip() == "```" else lines[1:])
        facts = json.loads(raw)
        print(f"  Extracted {len(facts)} facts for {user_id}")
        return facts
    except json.JSONDecodeError as e:
        print(f"  [WARN] JSON parse error for {user_id}: {e}")
        return []
    except Exception as e:
        print(f"  [ERR] Claude error for {user_id}: {e}")
        return []


def merge_facts_to_longterm(user_id: str, facts: list[dict]) -> int:
    """
    MERGE each extracted fact into ai_agent.memory.longterm.
    Returns the number of facts merged.
    """
    merged = 0
    now    = datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")

    for fact in facts:
        category   = str(fact.get("category", "fact")).replace("'", "\\'")
        key        = str(fact.get("key",      "unknown")).replace("'", "\\'")
        value      = str(fact.get("value",    "")).replace("'", "\\'")
        importance = max(1, min(10, int(fact.get("importance", 5))))
        entry_id   = str(uuid.uuid4())

        try:
            spark.sql(f"""
                MERGE INTO {CATALOG}.memory.longterm AS target
                USING (
                    SELECT
                        '{entry_id}'   AS id,
                        '{user_id}'    AS user_id,
                        '{category}'   AS category,
                        '{key}'        AS key,
                        '{value}'      AS value,
                        {importance}   AS importance,
                        'agent'        AS source,
                        TIMESTAMP '{now}' AS created_at,
                        TIMESTAMP '{now}' AS updated_at,
                        NULL           AS expires_at
                ) AS source
                ON  target.user_id  = source.user_id
                AND target.category = source.category
                AND target.key      = source.key
                WHEN MATCHED AND source.importance >= target.importance THEN UPDATE SET
                    target.value      = source.value,
                    target.importance = source.importance,
                    target.updated_at = source.updated_at
                WHEN NOT MATCHED THEN INSERT *
            """)
            merged += 1
        except Exception as e:
            print(f"    [ERR] Failed to merge fact [{category}|{key}]: {e}")

    return merged


def mark_notes_processed(user_id: str, note_ids: list[str]) -> None:
    """
    Append 'processed' to the tags array of processed daily notes
    to avoid reprocessing them on the next run.
    """
    if not note_ids:
        return

    ids_literal = ", ".join(f"'{nid}'" for nid in note_ids)
    try:
        spark.sql(f"""
            UPDATE {CATALOG}.memory.daily
            SET    tags = array_union(COALESCE(tags, ARRAY()), ARRAY('processed'))
            WHERE  user_id = '{user_id}'
              AND  id IN ({ids_literal})
        """)
    except Exception as e:
        print(f"  [WARN] Failed to mark notes processed for {user_id}: {e}")


# COMMAND ----------
# ------------------------------------------------------------------
# Main loop
# ------------------------------------------------------------------
total_users_processed = 0
total_facts_merged    = 0

for user_id in user_ids:
    print(f"\nProcessing user: {user_id}")

    # Fetch unprocessed notes from the last 7 days
    notes_df = spark.sql(f"""
        SELECT id, note_date, content, tags, session_id
        FROM   {CATALOG}.memory.daily
        WHERE  user_id   = '{user_id}'
          AND  note_date >= '{seven_days_ago}'
          AND  NOT array_contains(COALESCE(tags, ARRAY()), 'processed')
        ORDER BY note_date, created_at
    """)

    notes = [
        {
            "id":         row.id,
            "note_date":  str(row.note_date),
            "content":    row.content,
            "tags":       row.tags or [],
        }
        for row in notes_df.collect()
    ]

    print(f"  Unprocessed notes: {len(notes)}")

    if not notes:
        print("  Nothing to process.")
        continue

    # Extract facts via Claude
    facts = extract_facts_from_notes(user_id, notes)

    # Merge into longterm
    merged = merge_facts_to_longterm(user_id, facts)
    total_facts_merged += merged

    # Mark notes as processed
    note_ids = [n["id"] for n in notes]
    mark_notes_processed(user_id, note_ids)

    total_users_processed += 1
    print(f"  Done: {merged} facts merged, {len(notes)} notes marked processed.")

# COMMAND ----------
print(f"""
========================================
Memory Maintenance Complete
========================================
Users processed : {total_users_processed}
Total facts merged: {total_facts_merged}
Finished at     : {datetime.datetime.now().isoformat()}
""")

dbutils.notebook.exit("SUCCESS")
