"""
app/agent/genie.py

Databricks Genie integration - natural language to SQL via the Genie API.
"""

from __future__ import annotations

import logging
import os
import time
from typing import Any, Optional

logger = logging.getLogger("agent.genie")

# Keywords that suggest the user is asking a data question
_DATA_KEYWORDS = [
    "how many",
    "show me",
    "show all",
    "list all",
    "list me",
    "total",
    "count",
    "query",
    "data",
    "table",
    "rows",
    "records",
    "entries",
    "find all",
    "get all",
    "average",
    "sum",
    "max",
    "min",
    "top ",
    "report",
    "breakdown",
    "distribution",
    "trend",
    "statistics",
    "stats",
    "chart",
    "graph",
]

# Max number of polls before giving up
_MAX_POLL_ATTEMPTS = 20
# Seconds between polls
_POLL_INTERVAL     = 2.0


def is_data_question(message: str) -> bool:
    """
    Heuristic: returns True if the message looks like a data/analytics question
    that Genie should answer via SQL rather than the LLM answering from memory.
    """
    msg_lower = message.lower()
    return any(kw in msg_lower for kw in _DATA_KEYWORDS)


def query_genie(space_id: str, question: str) -> str:
    """
    Send a natural language question to a Databricks Genie Space and return
    a formatted string with the results.

    Uses the Databricks SDK Genie API.
    Polls until the conversation reaches a terminal state.
    Returns a formatted string on success, or an error message.
    """
    if not space_id:
        return "(Genie is not configured - GENIE_SPACE_ID is empty)"

    try:
        from databricks.sdk import WorkspaceClient
        client = WorkspaceClient()

        logger.info("Starting Genie conversation for question: %.80s", question)

        # Start a new conversation
        start_resp = client.genie.start_conversation_and_wait(
            space_id=space_id,
            content=question,
        )

        message_id       = start_resp.message_id
        conversation_id  = start_resp.conversation_id

        # The SDK's start_conversation_and_wait handles polling, but if it
        # returns quickly we may still need to fetch the query result.
        # Get the final message to extract the SQL result.
        msg = client.genie.get_message(
            space_id=space_id,
            conversation_id=conversation_id,
            message_id=message_id,
        )

        return _format_genie_message(msg)

    except AttributeError:
        # Fallback: older SDK version - use raw HTTP approach
        return _query_genie_raw(space_id, question)
    except Exception as exc:
        logger.error("Genie query failed: %s", exc)
        return f"(Genie error: {exc})"


def _query_genie_raw(space_id: str, question: str) -> str:
    """
    Fallback Genie query using raw SDK HTTP client for older SDK versions
    that don't have the genie namespace.
    """
    try:
        from databricks.sdk import WorkspaceClient
        client = WorkspaceClient()
        api    = client.api_client

        # Start conversation
        start_body = {"content": question}
        start = api.do(
            "POST",
            f"/api/2.0/genie/spaces/{space_id}/start-conversation",
            body=start_body,
        )
        conversation_id = start["conversation_id"]
        message_id      = start["message_id"]

        # Poll for completion
        for attempt in range(_MAX_POLL_ATTEMPTS):
            msg = api.do(
                "GET",
                f"/api/2.0/genie/spaces/{space_id}/conversations/{conversation_id}/messages/{message_id}",
            )
            status = msg.get("status", "")
            logger.debug("Genie poll %d: status=%s", attempt + 1, status)

            if status in ("COMPLETED", "FAILED", "CANCELLED", "QUERY_RESULT_EXPIRED"):
                break

            time.sleep(_POLL_INTERVAL)

        return _format_genie_message_dict(msg)

    except Exception as exc:
        logger.error("Genie raw query failed: %s", exc)
        return f"(Genie error: {exc})"


def _format_genie_message(msg: Any) -> str:
    """Format a Genie API message object (SDK type) into a readable string."""
    try:
        # Try to get query result attachments
        attachments = getattr(msg, "attachments", None) or []
        for att in attachments:
            query = getattr(att, "query", None)
            if query:
                result = getattr(query, "result", None)
                if result:
                    return _format_query_result(result)
            # Text attachment
            text = getattr(att, "text", None)
            if text:
                txt_val = getattr(text, "content", str(text))
                if txt_val:
                    return txt_val

        # Fallback: use description
        content = getattr(msg, "content", None)
        if content:
            return str(content)

        return "(Genie returned no result)"
    except Exception as exc:
        logger.warning("Error formatting Genie message: %s", exc)
        return "(Error formatting Genie response)"


def _format_genie_message_dict(msg: dict) -> str:
    """Format a raw Genie API message dict into a readable string."""
    try:
        attachments = msg.get("attachments", [])
        for att in attachments:
            query = att.get("query", {})
            result = query.get("result", {})
            if result:
                return _format_query_result_dict(result)
            text = att.get("text", {})
            if text.get("content"):
                return text["content"]

        content = msg.get("content", "")
        if content:
            return str(content)

        return "(Genie returned no result)"
    except Exception as exc:
        logger.warning("Error formatting Genie dict message: %s", exc)
        return "(Error formatting Genie response)"


def _format_query_result(result: Any) -> str:
    """Format an SDK query result object as a human-readable table string."""
    try:
        columns  = [col.name for col in (result.statement_response.manifest.schema.columns or [])]
        data_arr = result.statement_response.result.data_array or []
        return _render_table(columns, data_arr)
    except Exception:
        return str(result)


def _format_query_result_dict(result: dict) -> str:
    """Format a raw query result dict as a human-readable table string."""
    try:
        manifest = result.get("statement_response", {}).get("manifest", {})
        columns  = [col["name"] for col in manifest.get("schema", {}).get("columns", [])]
        data_arr = result.get("statement_response", {}).get("result", {}).get("data_array", [])
        return _render_table(columns, data_arr)
    except Exception:
        return str(result)


def format_genie_result(result: Any) -> str:
    """
    Public helper: converts any Genie result (dict or SDK object) into
    a readable text string.
    """
    if isinstance(result, dict):
        return _format_genie_message_dict(result)
    return _format_genie_message(result)


def _render_table(columns: list[str], rows: list[list]) -> str:
    """Render column names and row data as a plain-text table."""
    if not rows:
        return "(Query returned no rows)"

    if not columns:
        return "\n".join(str(row) for row in rows[:50])

    # Build column widths
    widths = [max(len(c), max((len(str(r[i])) if i < len(r) else 0 for r in rows[:100]), default=0))
              for i, c in enumerate(columns)]

    header  = " | ".join(c.ljust(widths[i]) for i, c in enumerate(columns))
    divider = "-+-".join("-" * w for w in widths)
    lines   = [header, divider]

    for row in rows[:100]:  # Cap at 100 rows in response
        line = " | ".join(str(row[i]).ljust(widths[i]) if i < len(row) else "".ljust(widths[i])
                          for i, _ in enumerate(columns))
        lines.append(line)

    if len(rows) > 100:
        lines.append(f"... ({len(rows) - 100} more rows not shown)")

    return "\n".join(lines)
