"""
HEGEMON Human-in-the-Loop (HITL) Module - Phase 2.1.

Provides infrastructure for human intervention in debates:
- Checkpoint system (pause/resume)
- Feedback schemas and validation
- Feedback processing utilities
- Custom exceptions

Complexity: O(1) for module imports
"""

from __future__ import annotations

__version__ = "2.1.0"

from hegemon.hitl.checkpoints import (
    checkpoint_post_evaluation_node,
    checkpoint_post_thesis_node,
    checkpoint_pre_synthesis_node,
)
from hegemon.hitl.exceptions import (
    CheckpointError,
    FeedbackValidationError,
    MaxRevisionsExceededError,
    StateCorruptionError,
)
from hegemon.hitl.feedback import (
    build_feedback_context_for_agent,
    track_revision,
    validate_feedback_actionability,
)
from hegemon.hitl.schemas import (
    CheckpointMetadata,
    FeedbackDecision,
    HumanFeedback,
    InterventionMode,
)

__all__ = [
    # Version
    "__version__",
    # Schemas
    "HumanFeedback",
    "CheckpointMetadata",
    "InterventionMode",
    "FeedbackDecision",
    # Checkpoint nodes
    "checkpoint_post_thesis_node",
    "checkpoint_post_evaluation_node",
    "checkpoint_pre_synthesis_node",
    # Feedback utilities
    "build_feedback_context_for_agent",
    "validate_feedback_actionability",
    "track_revision",
    # Exceptions
    "CheckpointError",
    "FeedbackValidationError",
    "MaxRevisionsExceededError",
    "StateCorruptionError",
]