"""
HEGEMON Graph with HITL - Phase 2.1 Extended.

Extended LangGraph workflow z Human-in-the-Loop checkpoints.

Graph Structure (Extended):
    START → katalizator → [CHECKPOINT 1] → sceptyk → gubernator → 
    [CHECKPOINT 2] → [conditional routing] → ...
    ... → [CHECKPOINT 3] → syntezator → END

KRYTYCZNE:
- 100% backward compatible z Phase 1 graph
- Checkpoints skippowane w observer mode
- Używa LangGraph interrupt mechanism (nie custom pause)

Complexity: O(1) dla graph construction
"""

from __future__ import annotations

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Literal

from langgraph.graph import END, StateGraph

from hegemon.agents import (
    gubernator_node,
    katalizator_node,
    sceptyk_node,
    syntezator_node,
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
# Routing Logic (UNCHANGED from Phase 1)
# ============================================================================

def should_continue(state: DebateState) -> Literal["checkpoint_pre_synthesis", "katalizator"]:
    """
    Routing function after Gubernator evaluation.
    
    PHASE 2.1 CHANGE:
        Routing destinations updated:
        - "syntezator" → "checkpoint_pre_synthesis" (checkpoint inserted)
        - "katalizator" → "katalizator" (unchanged)
    
    Logic:
    1. If max_cycles reached → ALWAYS go to pre-synthesis checkpoint
    2. If consensus >= threshold AND min_cycles met → pre-synthesis checkpoint
    3. Otherwise → continue debate (back to katalizator)
    
    Args:
        state: Current DebateState
    
    Returns:
        "checkpoint_pre_synthesis" - proceed to final checkpoint before synthesis
        "katalizator" - continue debate (new cycle)
    
    Complexity: O(1)
    """
    settings = get_settings()
    
    consensus = state["current_consensus_score"]
    cycle = state["cycle_count"]
    
    # Check max cycles (hard limit)
    if cycle >= settings.debate.max_cycles:
        logger.info(
            f"🛑 Max cycles ({settings.debate.max_cycles}) reached. "
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


# ============================================================================
# Increment Cycle Counter (UNCHANGED from Phase 1)
# ============================================================================

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
# Graph Builder (EXTENDED with HITL)
# ============================================================================

def create_hegemon_graph_hitl() -> StateGraph:
    """
    Create HEGEMON LangGraph state machine with HITL checkpoints.
    
    Graph structure (Phase 2.1 Extended):
        START → katalizator → checkpoint_post_thesis → sceptyk → gubernator →
        checkpoint_post_evaluation → [conditional] → ...
                     ↑                                      ↓
                     └─── increment_cycle ←────[if continue]
                                                           ↓
                                      checkpoint_pre_synthesis → syntezator → END
    
    Changes from Phase 1:
    - Added 3 checkpoint nodes (post_thesis, post_evaluation, pre_synthesis)
    - Routing destinations updated to include checkpoints
    - Observer mode automatically skips checkpoints (no graph changes needed)
    
    Returns:
        Compiled LangGraph StateGraph with HITL support
    
    Complexity: O(1) - graph construction is constant time
    
    Example:
        >>> graph = create_hegemon_graph_hitl()
        >>> initial_state = {
        ...     "mission": "...",
        ...     "intervention_mode": "reviewer",  # NEW
        ...     "contributions": [],
        ...     "cycle_count": 1,
        ...     "current_consensus_score": 0.0,
        ...     "final_plan": None,
        ...     "current_checkpoint": None,  # NEW
        ...     "human_feedback_history": [],  # NEW
        ...     "paused_at": None,  # NEW
        ...     "revision_count_per_checkpoint": {},  # NEW
        ...     "checkpoint_snapshots": {},  # NEW
        ... }
        >>> result = graph.invoke(initial_state)
    """
    logger.info("🏗️ Building HEGEMON graph with HITL checkpoints...")
    
    # Initialize StateGraph with DebateState schema
    workflow = StateGraph(DebateState)
    
    # ========================================================================
    # Add nodes - Phase 1 agents (UNCHANGED)
    # ========================================================================
    
    workflow.add_node("katalizator", katalizator_node)
    workflow.add_node("sceptyk", sceptyk_node)
    workflow.add_node("gubernator", gubernator_node)
    workflow.add_node("syntezator", syntezator_node)
    workflow.add_node("increment_cycle", increment_cycle)
    
    # ========================================================================
    # Add nodes - Phase 2.1 checkpoints (NEW)
    # ========================================================================
    
    workflow.add_node("checkpoint_post_thesis", checkpoint_post_thesis_node)
    workflow.add_node("checkpoint_post_evaluation", checkpoint_post_evaluation_node)
    workflow.add_node("checkpoint_pre_synthesis", checkpoint_pre_synthesis_node)
    
    # ========================================================================
    # Set entry point (UNCHANGED)
    # ========================================================================
    
    workflow.set_entry_point("katalizator")
    
    # ========================================================================
    # Add edges - Sequential flow with checkpoints (EXTENDED)
    # ========================================================================
    
    # Flow: katalizator → checkpoint → sceptyk
    workflow.add_edge("katalizator", "checkpoint_post_thesis")
    workflow.add_edge("checkpoint_post_thesis", "sceptyk")
    
    # Flow: sceptyk → gubernator → checkpoint
    workflow.add_edge("sceptyk", "gubernator")
    workflow.add_edge("gubernator", "checkpoint_post_evaluation")
    
    # ========================================================================
    # Add conditional edges - Routing decision (MODIFIED)
    # ========================================================================
    
    # After post_evaluation checkpoint → routing decision
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
    
    # ========================================================================
    # Add final edges - Pre-synthesis → synthesis → end (NEW)
    # ========================================================================
    
    # Flow: checkpoint → syntezator → END
    workflow.add_edge("checkpoint_pre_synthesis", "syntezator")
    workflow.add_edge("syntezator", END)
    
    # ========================================================================
    # Compile graph
    # ========================================================================
    
    graph = workflow.compile()
    
    logger.info("✅ HEGEMON graph with HITL compiled successfully!")
    logger.info(
        "   Checkpoints: post_thesis, post_evaluation, pre_synthesis"
    )
    
    return graph


# ============================================================================
# High-Level API (convenience function)
# ============================================================================

def run_debate_hitl(
    mission: str,
    intervention_mode: Literal["observer", "reviewer", "collaborator"] = "reviewer",
    max_cycles: int = 3,
    output_file: Path | None = None,
) -> dict[str, Any]:
    """
    Run HEGEMON debate with HITL support.
    
    Convenience wrapper dla graph.invoke() z HITL state initialization.
    
    Args:
        mission: User's strategic goal
        intervention_mode: Level of human control (default: "reviewer")
        max_cycles: Maximum debate cycles (default: 3)
        output_file: Optional path to save output JSON
    
    Returns:
        Final state dict (with debate history + final plan)
    
    Complexity: O(n * m) gdzie n = cycles, m = agents per cycle
    
    Example:
        >>> result = run_debate_hitl(
        ...     mission="Design microservices architecture",
        ...     intervention_mode="reviewer",
        ...     max_cycles=3
        ... )
        >>> print(result["final_plan"])
    """
    logger.info("🚀 Starting HEGEMON debate with HITL...")
    logger.info(f"   Mission: {mission[:100]}...")
    logger.info(f"   Intervention Mode: {intervention_mode}")
    logger.info(f"   Max Cycles: {max_cycles}")
    
    # Initialize state with HITL fields
    initial_state: DebateState = {
        # Phase 1 fields
        "mission": mission,
        "contributions": [],
        "current_consensus_score": 0.0,
        "cycle_count": 1,
        "final_plan": None,
        # Phase 2.1 HITL fields
        "intervention_mode": intervention_mode,
        "current_checkpoint": None,
        "human_feedback_history": [],
        "paused_at": None,
        "revision_count_per_checkpoint": {},
        "checkpoint_snapshots": {},
    }
    
    # Create graph
    graph = create_hegemon_graph_hitl()
    
    # Execute debate
    start_time = datetime.now()
    final_state = graph.invoke(initial_state)
    end_time = datetime.now()
    
    duration = (end_time - start_time).total_seconds()
    logger.info(f"✅ Debate completed in {duration:.2f} seconds")
    
    # Save output if requested
    if output_file:
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Prepare output (convert Pydantic models to dict)
        output_data = {
            "metadata": {
                "mission": mission,
                "intervention_mode": intervention_mode,
                "max_cycles": max_cycles,
                "duration_seconds": duration,
                "completed_at": end_time.isoformat(),
            },
            "debate_history": [
                contrib.model_dump() if hasattr(contrib, "model_dump") else contrib
                for contrib in final_state["contributions"]
            ],
            "final_plan": (
                final_state["final_plan"].model_dump()
                if final_state["final_plan"]
                else None
            ),
            "hitl_metadata": {
                "total_feedback": len(final_state.get("human_feedback_history", [])),
                "checkpoints_reached": len(final_state.get("checkpoint_snapshots", {})),
                "revisions_per_checkpoint": final_state.get("revision_count_per_checkpoint", {}),
            },
        }
        
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"💾 Output saved to {output_file}")
    
    return final_state