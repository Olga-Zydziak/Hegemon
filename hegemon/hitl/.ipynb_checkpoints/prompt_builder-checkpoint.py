"""
HEGEMON HITL Prompt Builder - Phase 2.2.

Constructs feedback-aware prompts for agents with intelligent context injection.

CRITICAL:
- Feedback context injected only when relevant
- Progressive disclosure (summary → details)
- Preserves original prompt structure
- Length limits prevent context overflow

Complexity: O(n) gdzie n = liczba feedbacku
"""

from __future__ import annotations

import logging
from typing import Any

from hegemon.hitl.schemas import HumanFeedback
from hegemon.schemas import DebateState

logger = logging.getLogger(__name__)


# ============================================================================
# Constants
# ============================================================================

MAX_FEEDBACK_CONTEXT_LENGTH = 2000  # Characters
MAX_FEEDBACK_ITEMS_TO_SHOW = 3  # Only show last N feedbacks


# ============================================================================
# Enhanced Feedback Context Builder
# ============================================================================

def build_feedback_context_for_agent(
    state: DebateState,
    agent_id: str,
    include_all_history: bool = False,
) -> str:
    """
    Build rich feedback context for agent prompt.
    
    Enhanced version from Phase 2.1 with:
    - Progressive disclosure (summary first, details on demand)
    - Relevance filtering (only show feedback for this agent's checkpoint)
    - Length limits (prevent context overflow)
    - Beautiful formatting with visual hierarchy
    
    Args:
        state: Current DebateState
        agent_id: ID agenta ("Katalizator" | "Sceptyk" | "Gubernator" | "Syntezator")
        include_all_history: If True, show all feedback; else only recent/relevant
    
    Returns:
        Formatted feedback context string (empty if no relevant feedback)
    
    Complexity: O(n) gdzie n = liczba feedbacku
    
    Example:
        >>> context = build_feedback_context_for_agent(state, "Katalizator")
        >>> print(context)
        '''
        ╔══════════════════════════════════════════════════════════════╗
        ║ HUMAN FEEDBACK (1 revision requested)                        ║
        ╚══════════════════════════════════════════════════════════════╝
        
        The human reviewed your previous output and requested changes:
        
        📝 Guidance:
        "Add more detail about implementation costs and timeline"
        
        🎯 Priority Items to Emphasize:
        • Cost estimation methodology
        • Resource allocation strategy
        
        ⚠️ Concerns to Address:
        • Technical debt risk
        • Vendor lock-in potential
        
        Please incorporate this feedback in your revised output.
        '''
    """
    # Extract feedback from history
    all_feedback: list[HumanFeedback] = []
    for fb_dict in state.get("human_feedback_history", []):
        if isinstance(fb_dict, dict):
            try:
                all_feedback.append(HumanFeedback(**fb_dict))
            except Exception as e:
                logger.warning(f"Failed to parse feedback dict: {e}")
                continue
        else:
            all_feedback.append(fb_dict)
    
    if not all_feedback:
        return ""
    
    # Filter relevant feedback for this agent
    agent_checkpoint_mapping = {
        "Katalizator": ["post_thesis"],
        "Sceptyk": ["post_thesis"],  # Sceptyk uses feedback from post_thesis
        "Gubernator": ["post_evaluation"],
        "Syntezator": ["pre_synthesis"],
    }
    
    relevant_prefixes = agent_checkpoint_mapping.get(agent_id, [])
    relevant_feedback = [
        fb for fb in all_feedback
        if any(fb.checkpoint.startswith(prefix) for prefix in relevant_prefixes)
    ]
    
    if not relevant_feedback:
        return ""
    
    # Limit feedback items shown (avoid overwhelming context)
    if not include_all_history and len(relevant_feedback) > MAX_FEEDBACK_ITEMS_TO_SHOW:
        relevant_feedback = relevant_feedback[-MAX_FEEDBACK_ITEMS_TO_SHOW:]
    
    # Count revisions for this agent
    revision_count = len(relevant_feedback)
    
    # Build formatted context with visual hierarchy
    lines = [
        "╔══════════════════════════════════════════════════════════════╗",
        f"║ HUMAN FEEDBACK ({revision_count} revision{'s' if revision_count > 1 else ''} requested){'':30}║",
        "╚══════════════════════════════════════════════════════════════╝",
        "",
        "The human reviewed your previous output and requested changes:",
        "",
    ]
    
    for i, fb in enumerate(relevant_feedback, 1):
        # Section header for multiple feedbacks
        if len(relevant_feedback) > 1:
            lines.append(f"─── Feedback #{i} {'─' * 45}")
            lines.append("")
        
        # Decision with emoji
        decision_emoji = {
            "revise": "🔄",
            "approve": "✅",
            "reject": "❌",
            "override": "⚡",
        }.get(fb.decision, "📋")
        
        lines.append(f"{decision_emoji} **Decision: {fb.decision.upper()}**")
        lines.append("")
        
        # Guidance (main content)
        if fb.guidance:
            lines.append("📝 **Guidance:**")
            lines.append(f'"{fb.guidance}"')
            lines.append("")
        
        # Priority claims
        if fb.priority_claims:
            lines.append("🎯 **Priority Items to Emphasize:**")
            for claim in fb.priority_claims:
                lines.append(f"• {claim}")
            lines.append("")
        
        # Flagged concerns
        if fb.flagged_concerns:
            lines.append("⚠️ **Concerns to Address:**")
            for concern in fb.flagged_concerns:
                lines.append(f"• {concern}")
            lines.append("")
        
        # Override data (advanced)
        if fb.override_data:
            lines.append("⚡ **Special Instructions:**")
            for key, value in fb.override_data.items():
                lines.append(f"• {key}: {value}")
            lines.append("")
    
    lines.append("**ACTION REQUIRED:** Please incorporate this feedback in your revised output.")
    lines.append("")
    
    context = "\n".join(lines)
    
    # Length check (truncate if too long)
    if len(context) > MAX_FEEDBACK_CONTEXT_LENGTH:
        context = context[:MAX_FEEDBACK_CONTEXT_LENGTH] + "\n\n[...feedback truncated for length...]"
        logger.warning(
            f"Feedback context truncated for {agent_id} "
            f"(exceeded {MAX_FEEDBACK_CONTEXT_LENGTH} chars)"
        )
    
    logger.debug(
        f"Built feedback context for {agent_id}: "
        f"{len(relevant_feedback)} feedback(s), {len(context)} chars"
    )
    
    return context


# ============================================================================
# Debate Context Builder
# ============================================================================

def build_debate_context_for_agent(
    state: DebateState,
    agent_id: str,
    max_contributions: int = 6,
) -> str:
    """
    Build debate history context for agent prompt.
    
    Shows recent contributions from other agents for context.
    Helps agent understand the flow of debate.
    
    Args:
        state: Current DebateState
        agent_id: ID agenta wykonującego się
        max_contributions: Max liczba contributions do pokazania
    
    Returns:
        Formatted debate context string
    
    Complexity: O(n) gdzie n = liczba contributions
    """
    contributions = state.get("contributions", [])
    
    if not contributions:
        return ""
    
    # Limit to recent contributions (avoid overwhelming context)
    recent_contributions = contributions[-max_contributions:]
    
    lines = [
        "═══════════════════════════════════════════════════════════════",
        "DEBATE CONTEXT (Recent Contributions)",
        "═══════════════════════════════════════════════════════════════",
        "",
    ]
    
    for contrib in recent_contributions:
        # Handle both Pydantic and dict formats
        if isinstance(contrib, dict):
            contrib_agent = contrib.get("agent_id", "Unknown")
            contrib_type = contrib.get("type", "Unknown")
            contrib_cycle = contrib.get("cycle", 0)
            contrib_content = contrib.get("content", "")[:150]  # Truncate
        else:
            contrib_agent = contrib.agent_id
            contrib_type = contrib.type
            contrib_cycle = contrib.cycle
            contrib_content = contrib.content[:150]  # Truncate
        
        lines.append(f"[Cycle {contrib_cycle}] {contrib_agent} ({contrib_type}):")
        lines.append(f"  {contrib_content}...")
        lines.append("")
    
    lines.append("═══════════════════════════════════════════════════════════════")
    lines.append("")
    
    return "\n".join(lines)


# ============================================================================
# Full Prompt Builder (Feedback + Debate Context)
# ============================================================================

def build_agent_prompt_with_feedback(
    state: DebateState,
    agent_id: str,
    base_system_prompt: str,
    base_user_prompt: str,
    include_debate_context: bool = False,
) -> tuple[str, str]:
    """
    Build complete agent prompt with feedback and debate context.
    
    Intelligently injects feedback into prompts without breaking
    existing structure. Feedback appears as a special section.
    
    Args:
        state: Current DebateState
        agent_id: ID agenta
        base_system_prompt: Original system prompt (from config)
        base_user_prompt: Original user prompt template
        include_debate_context: Whether to include recent contributions
    
    Returns:
        Tuple of (enhanced_system_prompt, enhanced_user_prompt)
    
    Complexity: O(n) gdzie n = max(feedback, contributions)
    
    Example:
        >>> sys_prompt, user_prompt = build_agent_prompt_with_feedback(
        ...     state, "Katalizator", base_sys, base_user
        ... )
        >>> # sys_prompt now includes feedback section if relevant
    """
    # Build feedback context
    feedback_context = build_feedback_context_for_agent(state, agent_id)
    
    # Build debate context (optional)
    debate_context = ""
    if include_debate_context:
        debate_context = build_debate_context_for_agent(state, agent_id)
    
    # Inject feedback into system prompt (append at end)
    enhanced_system_prompt = base_system_prompt
    if feedback_context:
        enhanced_system_prompt += "\n\n" + feedback_context
    
    # Inject debate context into user prompt (prepend at start)
    enhanced_user_prompt = base_user_prompt
    if debate_context:
        enhanced_user_prompt = debate_context + "\n\n" + enhanced_user_prompt
    
    logger.debug(
        f"Built enhanced prompts for {agent_id}: "
        f"feedback={bool(feedback_context)}, debate={bool(debate_context)}"
    )
    
    return enhanced_system_prompt, enhanced_user_prompt