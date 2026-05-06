"""<MODULE_NAME> - <one-line description>.

<Optional longer description of what this module does,
why it exists, and any important notes.>

Example:
    >>> service = <ServiceName>(repo=<RepoName>())
    >>> result = service.<method>(<args>)
"""
from __future__ import annotations

import logging
from typing import TYPE_CHECKING

import structlog

from etoro_<domain>.config import settings
from etoro_<domain>.models.<model_file> import <ModelName>

if TYPE_CHECKING:
    from etoro_<domain>.repositories.<repo_file> import <RepoName>

logger = structlog.get_logger(__name__)

# ── Constants ────────────────────────────────────────────────────────────────
MAX_RETRY_ATTEMPTS: int = 3
DEFAULT_PAGE_SIZE: int = 100


# ── Models ───────────────────────────────────────────────────────────────────
# (move to models/ if shared across modules)


# ── Service / Main Class ─────────────────────────────────────────────────────
class <ServiceName>:
    """<One-line class description>.

    <Optional longer description.>

    Args:
        repo: Repository for data access.

    Example:
        >>> service = <ServiceName>(repo=<RepoName>())
    """

    def __init__(self, repo: <RepoName>) -> None:
        self._repo = repo

    def <public_method>(self, param: str) -> <ReturnType>:
        """<One-line method description>.

        Args:
            param: <Description of param>.

        Returns:
            <Description of return value>.

        Raises:
            ValidationError: If param is invalid.
            NotFoundError: If resource doesn't exist.
        """
        self._validate(param)
        logger.info("<public_method> called", param=param)

        result = self._repo.<method>(param)

        logger.info("<public_method> completed", result_id=result.id)
        return result

    # ── Private helpers ──────────────────────────────────────────────────────
    def _validate(self, param: str) -> None:
        if not param:
            from etoro_<domain>.common.exceptions import ValidationError
            raise ValidationError(f"param cannot be empty")


# ── Module-level helpers (if needed) ────────────────────────────────────────
def <helper_function>(value: float) -> float:
    """<One-line description>."""
    return round(value, 2)
