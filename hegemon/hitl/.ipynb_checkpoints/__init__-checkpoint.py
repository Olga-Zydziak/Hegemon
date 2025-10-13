"""
HEGEMON Human-in-the-Loop (HITL) Module - Phase 2.1 + 2.2.

Provides infrastructure for human intervention in debates:
- Checkpoint system (pause/resume)
- Feedback schemas and validation
- Feedback processing utilities
- Custom exceptions
- Phase 2.2: Enhanced prompt building, effectiveness scoring, contradiction detection

Complexity: O(1) for module imports
"""

from __future__ import annotations

__version__ = "2.2.0"

# Phase 2.1 exports
from hegemon.hitl.checkpoints import (
    checkpoint_post_evaluation_node,
    checkpoint_post_thesis_node,
    checkpoint_pre_synthesis_node,
)
from hegemon.hitl.exceptions import (
    CheckpointError,
    FeedbackValidationError,
    HITLError,
    MaxRevisionsExceededError,
    StateCorruptionError,
)
from hegemon.hitl.feedback import (
    track_revision,
    validate_feedback_actionability,
)
from hegemon.hitl.schemas import (
    CheckpointMetadata,
    FeedbackDecision,
    HumanFeedback,
    InterventionMode,
)

# Phase 2.2 exports (NEW)
from hegemon.hitl.contradiction_detector import (
    detect_feedback_contradictions,
    generate_contradiction_report,
)
from hegemon.hitl.effectiveness import (
    compute_feedback_effectiveness,
    compute_keyword_match_score,
    compute_structural_change_score,
)
from hegemon.hitl.prompt_builder import (
    build_agent_prompt_with_feedback,
    build_debate_context_for_agent,
    build_feedback_context_for_agent,
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
    # Feedback utilities (Phase 2.1)
    "validate_feedback_actionability",
    "track_revision",
    # Exceptions
    "HITLError",
    "CheckpointError",
    "FeedbackValidationError",
    "MaxRevisionsExceededError",
    "StateCorruptionError",
    # Phase 2.2: Prompt building
    "build_feedback_context_for_agent",
    "build_debate_context_for_agent",
    "build_agent_prompt_with_feedback",
    # Phase 2.2: Effectiveness scoring
    "compute_feedback_effectiveness",
    "compute_structural_change_score",
    "compute_keyword_match_score",
    # Phase 2.2: Contradiction detection
    "detect_feedback_contradictions",
    "generate_contradiction_report",
]