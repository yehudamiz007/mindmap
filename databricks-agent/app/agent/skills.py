"""
app/agent/skills.py

Skill discovery, matching, and loading from the Unity Catalog Volume.
"""

from __future__ import annotations

import json
import logging
import os
import re
from typing import Optional

logger = logging.getLogger("agent.skills")

VOLUME_LIBRARY = "/Volumes/ai_agent/skills/library"
INDEX_PATH     = f"{VOLUME_LIBRARY}/_index.json"

# Simple singleton cache
_index_cache: Optional["SkillIndex"] = None


class SkillIndex:
    """
    Loads and caches the skill index from the Volume.
    Call SkillIndex(force_reload=True) to bust the cache.
    """

    def __init__(self, force_reload: bool = False):
        global _index_cache

        if not force_reload and _index_cache is not None:
            self._skills: list[dict] = _index_cache._skills
            return

        self._skills = self._load_index()
        _index_cache = self
        logger.info("SkillIndex loaded: %d skills", len(self._skills))

    # ------------------------------------------------------------------

    def _load_index(self) -> list[dict]:
        try:
            with open(INDEX_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
            # Support both {"skills": [...]} wrapper and bare list
            if isinstance(data, list):
                return data
            return data.get("skills", [])
        except FileNotFoundError:
            logger.warning("_index.json not found at %s; returning empty list.", INDEX_PATH)
            return []
        except json.JSONDecodeError as exc:
            logger.error("Malformed _index.json: %s", exc)
            return []

    # ------------------------------------------------------------------

    def match_skill(self, message: str) -> Optional[str]:
        """
        Keyword-match a message against skill descriptions and keyword lists.
        Returns the skill name with the highest match score, or None if no
        skill scores above zero.
        """
        msg_lower = message.lower()
        scores: dict[str, int] = {}

        for skill in self._skills:
            name     = skill.get("name", "")
            desc     = skill.get("description", "").lower()
            keywords = [k.lower() for k in skill.get("keywords", [])]

            score = 0

            # Check description words
            for word in re.findall(r"\w+", desc):
                if len(word) > 3 and word in msg_lower:
                    score += 1

            # Check explicit keywords (higher weight)
            for kw in keywords:
                if kw in msg_lower:
                    score += 3

            # Never match the "general" fallback via keywords
            if name == "general":
                continue

            if score > 0:
                scores[name] = score

        if not scores:
            return None

        best = max(scores, key=lambda k: scores[k])
        logger.debug("Skill matched: %s (score=%d)", best, scores[best])
        return best

    # ------------------------------------------------------------------

    def load_skill(self, skill_name: str) -> str:
        """Read and return the SKILL.md content for the given skill."""
        path = f"{VOLUME_LIBRARY}/{skill_name}/SKILL.md"
        try:
            with open(path, "r", encoding="utf-8") as f:
                return f.read()
        except FileNotFoundError:
            logger.warning("SKILL.md not found for skill: %s", skill_name)
            return f"# {skill_name}\n(Skill file not found)"
        except Exception as exc:
            logger.error("Error loading skill %s: %s", skill_name, exc)
            return f"# {skill_name}\n(Error loading skill)"

    # ------------------------------------------------------------------

    def load_reference(self, skill_name: str, ref_file: str) -> str:
        """Read a reference file from the skill's references/ subdirectory."""
        path = f"{VOLUME_LIBRARY}/{skill_name}/references/{ref_file}"
        try:
            with open(path, "r", encoding="utf-8") as f:
                return f.read()
        except FileNotFoundError:
            logger.warning("Reference file not found: %s/%s", skill_name, ref_file)
            return ""
        except Exception as exc:
            logger.error("Error loading reference %s/%s: %s", skill_name, ref_file, exc)
            return ""

    # ------------------------------------------------------------------

    def list_skills(self) -> list[dict]:
        """Return all skills as a list of metadata dicts."""
        return list(self._skills)

    # ------------------------------------------------------------------

    def get_skill_meta(self, skill_name: str) -> Optional[dict]:
        """Return metadata for a single skill by name."""
        for s in self._skills:
            if s.get("name") == skill_name:
                return s
        return None
