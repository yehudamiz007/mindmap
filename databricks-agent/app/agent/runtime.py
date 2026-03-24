"""
app/agent/runtime.py

AgentRuntime - the core orchestrator for each agent invocation.

Flow per message:
  1. Load user context from memory
  2. Get session history
  3. Match skill
  4. If is_data_question -> query Genie
  5. Build system prompt
  6. Call Anthropic Claude with tenacity retry
  7. Parse [REMEMBER: ...] tags and save to memory
  8. Save turn to history (user + assistant)
  9. Log to audit table
 10. Return cleaned response
"""

from __future__ import annotations

import logging
import os
import re
import time
import uuid
from typing import Optional

import anthropic
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from agent.context import build_system_prompt
from agent.genie   import is_data_question, query_genie
from agent.memory  import (
    get_user_context,
    get_session_history,
    log_audit_run,
    save_memory,
    save_turn,
)
from agent.skills  import SkillIndex

logger = logging.getLogger("agent.runtime")

LLM_MODEL      = os.getenv("LLM_MODEL",      "claude-sonnet-4-6")
GENIE_SPACE_ID = os.getenv("GENIE_SPACE_ID", "")
MAX_TOKENS     = int(os.getenv("MAX_TOKENS", "2048"))

# Regex to extract [REMEMBER: category|key|value|importance] tags
_REMEMBER_RE = re.compile(
    r"\[REMEMBER:\s*([^|\]]+)\|([^|\]]+)\|([^|\]]+)\|(\d+)\]",
    re.IGNORECASE,
)


class AgentRuntime:
    """
    Stateless orchestrator. Safe to use as a module-level singleton because
    all per-request state is local to process_message().
    """

    def __init__(self):
        self._anthropic = anthropic.Anthropic(
            api_key=os.getenv("ANTHROPIC_API_KEY")
        )
        self._skill_index = SkillIndex()
        logger.info("AgentRuntime ready. Model=%s", LLM_MODEL)

    # ------------------------------------------------------------------

    def process_message(
        self,
        user_id:    str,
        message:    str,
        session_id: str,
        channel:    str = "direct",
    ) -> str:
        """
        Full agent pipeline. Returns the cleaned response string.
        """
        t_start       = time.time()
        skill_name    = None
        genie_used    = False
        error_message = None
        raw_response  = ""

        try:
            # 1. Load user memory context
            user_context = get_user_context(user_id)

            # 2. Session history
            history = get_session_history(session_id, limit=20)

            # 3. Skill matching
            skill_name    = self._skill_index.match_skill(message)
            skill_content = None
            if skill_name:
                skill_content = self._skill_index.load_skill(skill_name)
                logger.info("Skill matched: %s", skill_name)
            else:
                # Load general fallback
                skill_content = self._skill_index.load_skill("general")

            # 4. Genie data query (if applicable)
            genie_result = None
            if is_data_question(message) and GENIE_SPACE_ID:
                logger.info("Data question detected - querying Genie...")
                genie_result = query_genie(GENIE_SPACE_ID, message)
                genie_used   = bool(genie_result and not genie_result.startswith("(Genie"))
                logger.info("Genie result: %.80s", genie_result)

            # 5. Build system prompt
            system_prompt = build_system_prompt(
                user_context   = user_context,
                skill_content  = skill_content,
                genie_result   = genie_result,
                session_history= history,
            )

            # 6. Call Claude with retry
            messages_payload = self._build_messages(history, message)
            raw_response = self._call_claude(system_prompt, messages_payload)

            # 7. Parse REMEMBER tags and save memories
            self._process_remember_tags(user_id, session_id, raw_response)

            # 8. Clean response (remove tags before returning to user)
            clean_response = _strip_remember_tags(raw_response)

            # 9. Save turns
            save_turn(
                session_id  = session_id,
                user_id     = user_id,
                role        = "user",
                content     = message,
                skill_used  = skill_name,
                genie_query = genie_used,
                model       = LLM_MODEL,
            )
            save_turn(
                session_id  = session_id,
                user_id     = user_id,
                role        = "assistant",
                content     = clean_response,
                skill_used  = skill_name,
                genie_query = genie_used,
                model       = LLM_MODEL,
            )

            latency_ms = int((time.time() - t_start) * 1000)

            # 10. Audit log
            log_audit_run(
                user_id       = user_id,
                session_id    = session_id,
                channel       = channel,
                skill_matched = skill_name,
                genie_used    = genie_used,
                latency_ms    = latency_ms,
                success       = True,
            )

            logger.info(
                "Request completed: user=%s session=%s skill=%s genie=%s latency=%dms",
                user_id, session_id, skill_name, genie_used, latency_ms,
            )

            return clean_response

        except Exception as exc:
            error_message = str(exc)
            latency_ms    = int((time.time() - t_start) * 1000)
            logger.exception("AgentRuntime error for user=%s: %s", user_id, exc)

            log_audit_run(
                user_id       = user_id,
                session_id    = session_id,
                channel       = channel,
                skill_matched = skill_name,
                genie_used    = genie_used,
                latency_ms    = latency_ms,
                success       = False,
                error_message = error_message,
            )
            raise

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _build_messages(self, history: list[dict], current_message: str) -> list[dict]:
        """Convert session history + current message into Anthropic messages format."""
        messages = []

        for turn in history:
            role    = turn.get("role", "user")
            content = turn.get("content", "")
            if role in ("user", "assistant") and content:
                messages.append({"role": role, "content": content})

        messages.append({"role": "user", "content": current_message})
        return messages

    @retry(
        retry=retry_if_exception_type((anthropic.APIConnectionError, anthropic.RateLimitError)),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=30),
        reraise=True,
    )
    def _call_claude(self, system_prompt: str, messages: list[dict]) -> str:
        """Call the Anthropic Claude API with retry logic."""
        response = self._anthropic.messages.create(
            model      = LLM_MODEL,
            max_tokens = MAX_TOKENS,
            system     = system_prompt,
            messages   = messages,
        )
        content = response.content
        if not content:
            return "(No response from model)"
        # Extract text from content blocks
        text_parts = [block.text for block in content if hasattr(block, "text")]
        return "\n".join(text_parts).strip()

    def _process_remember_tags(self, user_id: str, session_id: str, response: str) -> None:
        """Find all [REMEMBER: ...] tags in the response and persist them."""
        for match in _REMEMBER_RE.finditer(response):
            category   = match.group(1).strip()
            key        = match.group(2).strip()
            value      = match.group(3).strip()
            importance = int(match.group(4).strip())

            logger.info(
                "REMEMBER tag: user=%s category=%s key=%s importance=%d",
                user_id, category, key, importance,
            )

            try:
                save_memory(
                    user_id    = user_id,
                    key        = key,
                    value      = value,
                    category   = category,
                    importance = importance,
                    source     = "agent",
                )
            except Exception as exc:
                logger.warning("Failed to save REMEMBER tag [%s|%s]: %s", category, key, exc)


# ---------------------------------------------------------------------------
# Module-level helpers
# ---------------------------------------------------------------------------

def _strip_remember_tags(text: str) -> str:
    """Remove all [REMEMBER: ...] tags from a string."""
    cleaned = _REMEMBER_RE.sub("", text)
    # Clean up any resulting double blank lines
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)
    return cleaned.strip()
