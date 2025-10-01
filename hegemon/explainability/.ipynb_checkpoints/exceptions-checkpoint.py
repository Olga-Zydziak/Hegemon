"""
Explainability Custom Exceptions.

Hierarchical exception structure for clear error handling.
All exceptions inherit from base ExplainabilityError.

Complexity: O(1) for all exception operations.
"""

from typing import Any


class ExplainabilityError(Exception):
    """Base exception for all explainability-related errors."""

    def __init__(self, message: str, details: dict[str, Any] | None = None) -> None:
        """
        Initialize explainability error.

        Args:
            message: Human-readable error description
            details: Optional dict with context (e.g., agent_id, text_length)

        Complexity: O(1)
        """
        super().__init__(message)
        self.message = message
        self.details = details or {}


class ClassificationError(ExplainabilityError):
    """Error during concept classification (LLM call failure)."""

    pass


class ValidationError(ExplainabilityError):
    """Error during concept vector validation (invalid scores)."""

    pass


class ConceptDictionaryError(ExplainabilityError):
    """Error loading or parsing concept dictionary."""

    pass


class CacheError(ExplainabilityError):
    """Error in caching layer (rare, non-critical)."""

    pass