"""
HEGEMON Graph HITL v2 - Phase 2.2.

Enhanced graph using feedback-aware agents.

CRITICAL:
- Uses HITL-enhanced agent nodes (agents_hitl.py)
- Tracks effectiveness scores automatically
- 100% backward compatible with Phase 2.1
- Same checkpoint structure, enhanced agent execution

Complexity: O(1) for graph construction
"""

from __future__ import annotations

import logging
from typing import Any, Literal

from langgraph.graph import END, StateGraph

from hegemon.agents_hitl import (
    gubernator_node_hitl,
    katalizator_node_hitl,
    sceptyk_node_hitl,
    syntezator_node_hitl,
)
from hegemon.config import get_settings
from hegemon.hitl import (
    checkpoint_post_evaluation_node,
    checkpoint_post_thesis_node,
    checkpoint_pre_synthesis_node,
)
from hegemon.schemas import DebateState

logger = logging.getLogger(__name__)


# ============================================================================
# Routing Logic (UNCHANGED from Phase 2.1)
# ============================================================================

def should_continue(state: DebateState) -> Literal["checkpoint_pre_synthesis", "katalizator"]:
    """
    Routing function after Gubernator evaluation.
    
    Decides whether to continue debate or move to synthesis.
    
    Args:
        state: Current DebateState
    
    Returns:
        Next node name: "checkpoint_pre_synthesis" or "katalizator"
    
    Complexity: O(1)
    """
    settings = get_settings()
    consensus = state["current_consensus_score"]
    cycle = state["cycle_count"]
    
    # Check max cycles limit
    if cycle >= settings.debate.max_cycles:
        logger.info(
            f"🛑 Max cycles reached ({cycle} >= {settings.debate.max_cycles}). "
            f"Moving to pre-synthesis checkpoint."
        )
        return "checkpoint_pre_synthesis"
    
    # Check consensus threshold
    if consensus >= settings.debate.consensus_threshold:
        # Check minimum cycles
        if cycle >= settings.debate.min_cycles:
            logger.info(
                f"✅ Consensus threshold met ({consensus:.2f} >= "
                f"{settings.debate.consensus_threshold}) after {cycle} cycles. "
                f"Moving to pre-synthesis checkpoint."
            )
            return "checkpoint_pre_synthesis"
        else:
            logger.info(
                f"⏳ Consensus threshold met ({consensus:.2f}), but min_cycles "
                f"({settings.debate.min_cycles}) not reached. Continuing debate."
            )
            return "katalizator"
    else:
        logger.info(
            f"🔄 Consensus too low ({consensus:.2f} < "
            f"{settings.debate.consensus_threshold}). Continuing debate (cycle {cycle + 1})."
        )
        return "katalizator"


def increment_cycle(state: DebateState) -> dict[str, Any]:
    """
    Increment cycle counter before starting new debate round.
    
    Args:
        state: Current DebateState
    
    Returns:
        Dict with updated cycle_count
    
    Complexity: O(1)
    """
    new_cycle = state["cycle_count"] + 1
    logger.info(f"📈 Starting debate cycle {new_cycle}")
    
    return {"cycle_count": new_cycle}


# ============================================================================
# Graph Builder (Phase 2.2 - Uses HITL Agents)
# ============================================================================

def create_hegemon_graph_hitl_v2() -> StateGraph:
    """
    Create HEGEMON graph with Phase 2.2 feedback-aware agents.
    
    Changes from Phase 2.1:
    - Uses feedback-aware agent nodes (katalizator_node_hitl, etc.)
    - Automatically tracks effectiveness scores
    - Enhanced prompt building with feedback context
    - Rest of structure identical to Phase 2.1
    
    Graph structure:
        START → katalizator_hitl → checkpoint_post_thesis → sceptyk_hitl → 
        gubernator_hitl → checkpoint_post_evaluation → [conditional] → ...
                     ↑                                           ↓
                     └──── increment_cycle ←────────[if continue]
                                                                ↓
                                   checkpoint_pre_synthesis → syntezator_hitl → END
    
    Returns:
        Compiled LangGraph StateGraph with Phase 2.2 agents
    
    Complexity: O(1)
    
    Example:
        >>> graph = create_hegemon_graph_hitl_v2()
        >>> initial_state = {
        ...     "mission": "Design AI system",
        ...     "intervention_mode": "reviewer",
        ...     "contributions": [],
        ...     "cycle_count": 1,
        ...     "current_consensus_score": 0.0,
        ...     "final_plan": None,
        ...     "current_checkpoint": None,
        ...     "human_feedback_history": [],
        ...     "paused_at": None,
        ...     "revision_count_per_checkpoint": {},
        ...     "checkpoint_snapshots": {},
        ... }
        >>> result = graph.invoke(initial_state, config={"recursion_limit": 100})
    """
    logger.info("🏗️ Building HEGEMON graph with Phase 2.2 feedback-aware agents...")
    
    workflow = StateGraph(DebateState)
    
    # ========================================================================
    # Add nodes - Phase 2.2 HITL agents (CHANGED from Phase 2.1)
    # ========================================================================
    
    workflow.add_node("katalizator", katalizator_node_hitl)
    workflow.add_node("sceptyk", sceptyk_node_hitl)
    workflow.add_node("gubernator", gubernator_node_hitl)
    workflow.add_node("syntezator", syntezator_node_hitl)
    workflow.add_node("increment_cycle", increment_cycle)
    
    # Checkpoints (unchanged from Phase 2.1)
    workflow.add_node("checkpoint_post_thesis", checkpoint_post_thesis_node)
    workflow.add_node("checkpoint_post_evaluation", checkpoint_post_evaluation_node)
    workflow.add_node("checkpoint_pre_synthesis", checkpoint_pre_synthesis_node)
    
    # ========================================================================
    # Set entry point
    # ========================================================================
    
    workflow.set_entry_point("katalizator")
    
    # ========================================================================
    # Add edges (IDENTICAL to Phase 2.1)
    # ========================================================================
    
    # Flow: katalizator → checkpoint → sceptyk
    workflow.add_edge("katalizator", "checkpoint_post_thesis")
    workflow.add_edge("checkpoint_post_thesis", "sceptyk")
    
    # Flow: sceptyk → gubernator → checkpoint
    workflow.add_edge("sceptyk", "gubernator")
    workflow.add_edge("gubernator", "checkpoint_post_evaluation")
    
    # Conditional routing after post_evaluation checkpoint
    workflow.add_conditional_edges(
        "checkpoint_post_evaluation",
        should_continue,
        {
            "checkpoint_pre_synthesis": "checkpoint_pre_synthesis",
            "katalizator": "increment_cycle",
        }
    )
    
    # Loop back to katalizator after incrementing cycle
    workflow.add_edge("increment_cycle", "katalizator")
    
    # Flow: checkpoint → syntezator → END
    workflow.add_edge("checkpoint_pre_synthesis", "syntezator")
    workflow.add_edge("syntezator", END)
    
    # ========================================================================
    # Compile
    # ========================================================================
    
    graph = workflow.compile()
    
    logger.info("✅ HEGEMON graph Phase 2.2 compiled successfully!")
    logger.info("   Enhanced: Feedback-aware agents with effectiveness tracking")
    logger.info("   Checkpoints: post_thesis, post_evaluation, pre_synthesis")
    
    return graph