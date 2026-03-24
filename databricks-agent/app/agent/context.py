"""
app/agent/context.py

Assembles the system prompt for each agent invocation.
"""

from __future__ import annotations

from typing import Optional


BASE_PERSONA = """You are a personal AI assistant embedded in Databricks. \
You have access to the user's data via Unity Catalog and Genie. \
You are helpful, concise, and direct - you skip filler phrases like "Great question!" \
and just answer.

When you learn something important about the user that is worth remembering for \
future sessions, include this tag somewhere in your response (it will be stripped \
before sending to the user):

  [REMEMBER: category|key|value|importance]

Rules for REMEMBER tags:
- category must be one of: preference, fact, person, lesson, project
- importance is an integer 1-10 (10 = most critical to remember)
- Use REMEMBER only for genuinely useful long-term facts, not trivial details
- Remove the tag from your visible answer - it is processed automatically

Examples:
  [REMEMBER: preference|response_language|Hebrew|9]
  [REMEMBER: fact|job_title|Senior Data Engineer|7]
  [REMEMBER: project|current_project|Migrating Spark jobs to DLT|6]
"""


def build_system_prompt(
    user_context: str,
    skill_content: Optional[str],
    genie_result: Optional[str],
    session_history: list[dict],
) -> str:
    """
    Assemble the full system prompt from all available context.

    Order:
      1. Base persona
      2. Memory / user context
      3. Active skill instructions
      4. Genie data query result (if any)
      5. Recent conversation history (as a formatted block for the system prompt)

    The conversation history is also passed separately as the `messages` list
    to the Claude API, but a summarised version is included here so the model
    is aware of it when generating the system prompt response.
    """
    sections: list[str] = [BASE_PERSONA.strip()]

    # --- User memory context ---
    if user_context and user_context.strip() and user_context != "(No memory context available for this user)":
        sections.append(
            "## User Memory\n"
            "The following is what you know about this user from previous sessions:\n\n"
            + user_context.strip()
        )

    # --- Skill-specific instructions ---
    if skill_content and skill_content.strip():
        sections.append(
            "## Active Skill\n"
            "The following skill is active for this conversation. Follow its instructions:\n\n"
            + skill_content.strip()
        )

    # --- Genie data result ---
    if genie_result and genie_result.strip():
        sections.append(
            "## Data from Databricks (via Genie)\n"
            "The following data was retrieved from the Databricks data platform "
            "in response to the user's question. Use it to answer accurately:\n\n"
            "```\n"
            + genie_result.strip()
            + "\n```"
        )

    # --- Recent conversation summary (last few turns for context window awareness) ---
    if session_history:
        recent = session_history[-6:]  # Include last 6 turns as context hint
        history_lines = []
        for turn in recent:
            role    = turn.get("role", "unknown").capitalize()
            content = str(turn.get("content", ""))[:500]  # Truncate very long turns
            history_lines.append(f"{role}: {content}")
        if history_lines:
            sections.append(
                "## Recent Conversation\n"
                + "\n".join(history_lines)
            )

    return "\n\n---\n\n".join(sections)
