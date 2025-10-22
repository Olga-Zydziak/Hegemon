"""
HITL (Human-in-the-Loop) Package - Phase 2.3/2.4.

Provides checkpoint management, review generation, and interactive
Jupyter UI for collaborative debate control.
"""

from __future__ import annotations

__version__ = "2.4.0"

# Export main components
from .checkpoint_handler import CheckpointHandler
from .jupyter_ui import CheckpointUI, create_checkpoint_ui
from .simple_ui import SimpleCheckpointUI, create_simple_checkpoint_ui
from .models import (
    CheckpointState,
    CheckpointType,
    FeedbackDecision,
    HumanFeedback,
    InterventionMode,
    ReviewHighlight,
    ReviewPackage,
    SuggestedAction,
)
from .review_package import (
    Layer2Data,
    Layer6Data,
    LLMReviewGenerator,
    ReviewGenerator,
    create_review_generator,
)

__all__ = [
    # Version
    "__version__",
    # Models
    "CheckpointType",
    "InterventionMode",
    "FeedbackDecision",
    "HumanFeedback",
    "ReviewHighlight",
    "SuggestedAction",
    "ReviewPackage",
    "CheckpointState",
    # Review Generation
    "ReviewGenerator",
    "LLMReviewGenerator",
    "Layer2Data",
    "Layer6Data",
    "create_review_generator",
    # UI
    "CheckpointUI",
    "create_checkpoint_ui",
    "SimpleCheckpointUI",
    "create_simple_checkpoint_ui",
    # Handler
    "CheckpointHandler",
]
