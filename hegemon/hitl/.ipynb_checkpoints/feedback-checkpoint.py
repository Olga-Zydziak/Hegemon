"""
HEGEMON HITL Feedback Processing Utilities - Phase 2.1.

Utilities dla przetwarzania human feedback:
- Feedback context builder (dla agent prompts)
- Revision tracking
- Feedback validation
- Effectiveness scoring (future Phase 2.2)

Complexity: Większość operacji O(n) gdzie n = liczba feedbacku
"""

from __future__ import annotations

import logging
from typing import Any

from hegemon.hitl.exceptions import (
    FeedbackValidationError,
    MaxRevisionsExceededError,
)
from hegemon.hitl.schemas import HumanFeedback
from hegemon.schemas import DebateState

logger = logging.getLogger(__name__)


# ============================================================================
# Constants
# ============================================================================

MAX_REVISIONS_PER_CHECKPOINT = 3
MIN_FEEDBACK_LENGTH_FOR_ACTIONABILITY = 10


# ============================================================================
# Feedback Context Builder
# ============================================================================

def build_feedback_context_for_agent(
    state: DebateState,
    agent_id: str,
) -> str:
    """
    Build feedback context string dla agent prompt.
    
    Extracts relevant feedback dla danego agenta z history i formatuje
    jako human-readable context do injection w system prompt.
    
    Args:
        state: Current DebateState
        agent_id: ID agenta ("Katalizator" | "Sceptyk" | "Gubernator" | "Syntezator")
    
    Returns:
        Formatted feedback context string (empty if no relevant feedback)
    
    Complexity: O(n) gdzie n = liczba feedbacku w history
    
    Example:
        >>> context = build_feedback_context_for_agent(state, "Katalizator")
        >>> print(context)
        '''
        === HUMAN FEEDBACK ===
        Decision: revise
        Guidance: Focus more on implementation risks
        Priority Claims: [Cost estimation, Timeline feasibility]
        Flagged Concerns: [Technical debt risk, Resource availability]
        '''
    """
    # Extract all feedback from history (convert from Any to HumanFeedback)
    all_feedback: list[HumanFeedback] = []
    for fb_dict in state.get("human_feedback_history", []):
        if isinstance(fb_dict, dict):
            all_feedback.append(HumanFeedback(**fb_dict))
        else:
            all_feedback.append(fb_dict)
    
    # Filter relevant feedback dla tego agenta
    # Logic: Feedback z checkpoint post_{agent_name} jest relevant
    agent_checkpoint_prefix = {
        "Katalizator": "post_thesis",
        "Sceptyk": "post_thesis",  # Sceptyk uses feedback from post_thesis
        "Gubernator": "post_evaluation",
        "Syntezator": "pre_synthesis",
    }.get(agent_id, "")
    
    relevant_feedback = [
        fb for fb in all_feedback
        if fb.checkpoint.startswith(agent_checkpoint_prefix)
    ]
    
    if not relevant_feedback:
        return ""
    
    # Get latest feedback (most recent)
    latest = relevant_feedback[-1]
    
    # Format context
    context_parts = [
        "=== HUMAN FEEDBACK ===",
        f"Decision: {latest.decision}",
    ]
    
    if latest.guidance:
        context_parts.append(f"Guidance: {latest.guidance}")
    
    if latest.priority_claims:
        claims_str = ", ".join(latest.priority_claims)
        context_parts.append(f"Priority Claims: [{claims_str}]")
    
    if latest.flagged_concerns:
        concerns_str = ", ".join(latest.flagged_concerns)
        context_parts.append(f"Flagged Concerns: [{concerns_str}]")
    
    if latest.override_data:
        context_parts.append(f"Override Data: {latest.override_data}")
    
    context_parts.append("=== END FEEDBACK ===")
    
    formatted_context = "\n".join(context_parts)
    
    logger.debug(
        f"Built feedback context for {agent_id}: "
        f"{len(relevant_feedback)} relevant feedback(s)"
    )
    
    return formatted_context


# ============================================================================
# Revision Tracking
# ============================================================================

def track_revision(
    state: DebateState,
    checkpoint: str,
) -> dict[str, Any]:
    """
    Increment revision counter dla checkpoint.
    
    Enforces hard limit na liczbę rewizji (default: 3 per checkpoint)
    aby zapobiec infinite revision loops.
    
    Args:
        state: Current DebateState
        checkpoint: Checkpoint identifier (e.g., "post_thesis_cycle_1")
    
    Returns:
        Dict z updated revision_count_per_checkpoint
    
    Raises:
        MaxRevisionsExceededError: If revision limit exceeded
    
    Complexity: O(1) dla dict lookup i update
    
    Example:
        >>> updates = track_revision(state, "post_thesis_cycle_1")
        >>> # Returns: {"revision_count_per_checkpoint": {"post_thesis_cycle_1": 1}}
    """
    current_counts = state.get("revision_count_per_checkpoint", {})
    current_count = current_counts.get(checkpoint, 0)
    
    # Check limit
    if current_count >= MAX_REVISIONS_PER_CHECKPOINT:
        logger.error(
            f"Max revisions ({MAX_REVISIONS_PER_CHECKPOINT}) exceeded "
            f"for checkpoint {checkpoint}"
        )
        raise MaxRevisionsExceededError(
            checkpoint=checkpoint,
            current_count=current_count,
            max_allowed=MAX_REVISIONS_PER_CHECKPOINT,
        )
    
    # Increment counter
    new_count = current_count + 1
    
    logger.info(
        f"📝 Revision tracked for {checkpoint}: "
        f"{new_count}/{MAX_REVISIONS_PER_CHECKPOINT}"
    )
    
    return {
        "revision_count_per_checkpoint": {
            checkpoint: new_count
        }
    }


# ============================================================================
# Feedback Validation
# ============================================================================

def validate_feedback_actionability(feedback: HumanFeedback) -> bool:
    """
    Validate whether feedback is actionable dla agent.
    
    Checks:
    1. If decision="revise" → guidance must be substantive (>= 10 chars)
    2. If priority_claims provided → each must be >= 5 chars
    3. If flagged_concerns provided → each must be >= 5 chars
    
    Args:
        feedback: HumanFeedback instance
    
    Returns:
        True if actionable, False otherwise
    
    Raises:
        FeedbackValidationError: If feedback is not actionable
    
    Complexity: O(n) gdzie n = max(len(priority_claims), len(flagged_concerns))
    
    Example:
        >>> feedback = HumanFeedback(decision="revise", guidance="too short")
        >>> validate_feedback_actionability(feedback)  # Raises error
    """
    # Check 1: Revision requires substantive guidance
    if feedback.decision == "revise":
        if len(feedback.guidance.strip()) < MIN_FEEDBACK_LENGTH_FOR_ACTIONABILITY:
            raise FeedbackValidationError(
                f"Revision requires substantive guidance "
                f"(min {MIN_FEEDBACK_LENGTH_FOR_ACTIONABILITY} characters). "
                f"Current guidance: '{feedback.guidance}'"
            )
    
    # Check 2: Priority claims quality
    for claim in feedback.priority_claims:
        if len(claim.strip()) < 5:
            raise FeedbackValidationError(
                f"Priority claim too short: '{claim}'. "
                f"Minimum 5 characters required."
            )
    
    # Check 3: Flagged concerns quality
    for concern in feedback.flagged_concerns:
        if len(concern.strip()) < 5:
            raise FeedbackValidationError(
                f"Flagged concern too short: '{concern}'. "
                f"Minimum 5 characters required."
            )
    
    logger.debug(f"✅ Feedback validation passed for {feedback.checkpoint}")
    return True


# ============================================================================
# Feedback Effectiveness Scoring (Placeholder - Phase 2.2)
# ============================================================================

def compute_feedback_effectiveness(
    original_output: str,
    revised_output: str,
    feedback: HumanFeedback,
) -> float:
    """
    Compute effectiveness score dla feedback (did agent follow guidance?).
    
    PLACEHOLDER for Phase 2.2 implementation.
    
    Will use semantic similarity metrics:
    - Compare original vs revised output
    - Check if guidance keywords appear in revision
    - Compute similarity score (0.0 = no change, 1.0 = complete rewrite)
    
    Args:
        original_output: Agent output przed feedbackiem
        revised_output: Agent output po feedbacku
        feedback: HumanFeedback używany dla revision
    
    Returns:
        Effectiveness score [0.0, 1.0]
    
    Complexity: TBD (will depend on similarity metric chosen)
    """
    # TODO: Implement w Phase 2.2 using semantic similarity
    logger.warning(
        "compute_feedback_effectiveness() not implemented in Phase 2.1. "
        "Placeholder returning 1.0."
    )
    return 1.0