"""
HEGEMON Graph - LangGraph Orchestration.

Defines the dialectical debate workflow as a state machine:
- Katalizator → Sceptyk → Gubernator → (loop or synthesize)
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
from hegemon.schemas import DebateState

logger = logging.getLogger(__name__)


# ============================================================================
# Routing Logic (Conditional Edge)
# ============================================================================

def should_continue(state: DebateState) -> Literal["syntezator", "katalizator"]:
    """
    Routing function after Gubernator evaluation.
    
    Decides whether to:
    - Continue debate (go back to Katalizator)
    - Synthesize final plan (go to Syntezator)
    
    Logic:
    1. If max_cycles reached → ALWAYS synthesize
    2. If consensus >= threshold AND min_cycles met → synthesize
    3. Otherwise → continue debate
    
    Args:
        state: Current DebateState
    
    Returns:
        "syntezator" - move to synthesis
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
            f"Forcing synthesis."
        )
        return "syntezator"
    
    # Check consensus threshold
    if consensus >= settings.debate.consensus_threshold:
        # Check minimum cycles
        if cycle >= settings.debate.min_cycles:
            logger.info(
                f"✅ Consensus threshold met ({consensus:.2f} >= "
                f"{settings.debate.consensus_threshold}) after {cycle} cycles. "
                f"Moving to synthesis."
            )
            return "syntezator"
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
# Increment Cycle Counter
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
# Graph Builder
# ============================================================================

def create_hegemon_graph() -> StateGraph:
    """
    Create HEGEMON LangGraph state machine.
    
    Graph structure:
        START → katalizator → sceptyk → gubernator → [conditional]
                     ↑                                      ↓
                     └─── increment_cycle ←────[if continue]
                                                           ↓
                                               syntezator → END
    
    Returns:
        Compiled LangGraph StateGraph
    
    Complexity: O(1) - graph construction is constant time
    
    Example:
        >>> graph = create_hegemon_graph()
        >>> result = graph.invoke(initial_state)
    """
    logger.info("🏗️ Building HEGEMON graph...")
    
    # Initialize StateGraph with DebateState schema
    workflow = StateGraph(DebateState)
    
    # Add nodes
    workflow.add_node("katalizator", katalizator_node)
    workflow.add_node("sceptyk", sceptyk_node)
    workflow.add_node("gubernator", gubernator_node)
    workflow.add_node("syntezator", syntezator_node)
    workflow.add_node("increment_cycle", increment_cycle)
    
    # Set entry point
    workflow.set_entry_point("katalizator")
    
    # Add edges (sequential flow)
    workflow.add_edge("katalizator", "sceptyk")
    workflow.add_edge("sceptyk", "gubernator")
    
    # Add conditional edge (routing decision)
    workflow.add_conditional_edges(
        "gubernator",
        should_continue,
        {
            "syntezator": "syntezator",
            "katalizator": "increment_cycle",
        }
    )
    
    # Loop back to katalizator after incrementing cycle
    workflow.add_edge("increment_cycle", "katalizator")
    
    # Terminal node
    workflow.add_edge("syntezator", END)
    
    # Compile graph
    graph = workflow.compile()
    
    logger.info("✅ HEGEMON graph compiled successfully!")
    logger.info(
        f"   Nodes: {list(graph.nodes.keys())}"
    )
    
    return graph


# ============================================================================
# High-Level Execution Helper
# ============================================================================

def run_debate(
    mission: str,
    output_path: Path | str | None = None,
    return_state: bool = True
) -> dict[str, Any] | None:
    """
    High-level function to run complete HEGEMON debate.
    
    Convenience wrapper that:
    1. Creates graph
    2. Initializes state
    3. Runs debate
    4. Optionally saves output
    5. Returns final state
    
    Args:
        mission: Strategic mission description
        output_path: Optional path to save JSON output
        return_state: If True, return final state dict
    
    Returns:
        Final DebateState as dict (if return_state=True), else None
    
    Complexity: O(n) where n = number of debate cycles
    
    Example:
        >>> result = run_debate(
        ...     mission="Design cloud migration strategy",
        ...     output_path="output/result.json"
        ... )
        >>> print(result['final_plan'].mission_overview)
    """
    logger.info("=" * 80)
    logger.info("🚀 HEGEMON DEBATE STARTED")
    logger.info("=" * 80)
    logger.info(f"\n📋 Mission:\n{mission}\n")
    
    # Create graph
    graph = create_hegemon_graph()
    
    # Initialize state
    initial_state: DebateState = {
        "mission": mission,
        "contributions": [],
        "cycle_count": 1,
        "current_consensus_score": 0.0,
        "final_plan": None,
    }
    
    # Run debate
    start_time = datetime.now()
    logger.info(f"⏱️ Start time: {start_time.isoformat()}")
    
    try:
        final_state = graph.invoke(initial_state)
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        logger.info("=" * 80)
        logger.info("✅ HEGEMON DEBATE COMPLETED")
        logger.info("=" * 80)
        logger.info(f"⏱️ Duration: {duration:.1f} seconds")
        logger.info(f"🔄 Total cycles: {final_state['cycle_count']}")
        logger.info(
            f"📊 Final consensus: {final_state['current_consensus_score']:.2f}"
        )
        logger.info(
            f"💬 Total contributions: {len(final_state['contributions'])}"
        )
        
        # Save output if path provided
        if output_path:
            save_debate_output(final_state, output_path, duration)
        
        # Return state if requested
        if return_state:
            return final_state
        
    except Exception as e:
        logger.error(f"❌ Debate failed: {e}", exc_info=True)
        raise


# ============================================================================
# Output Serialization
# ============================================================================

def save_debate_output(
    state: DebateState,
    output_path: Path | str,
    duration: float | None = None
) -> None:
    """
    Save debate results to JSON file.
    
    Args:
        state: Final DebateState
        output_path: Path to output file
        duration: Optional debate duration in seconds
    
    Complexity: O(n) where n = size of state
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Serialize state
    output = {
        "metadata": {
            "timestamp": datetime.now().isoformat(),
            "duration_seconds": duration,
        },
        "mission": state["mission"],
        "debate_summary": {
            "total_cycles": state["cycle_count"],
            "final_consensus_score": state["current_consensus_score"],
            "total_contributions": len(state["contributions"]),
        },
        "debate_history": [
            {
                "agent_id": c.agent_id,
                "type": c.type,
                "cycle": c.cycle,
                "content": c.content,
                "rationale": c.rationale,
            }
            for c in state["contributions"]
        ],
        "final_plan": None,
    }
    
    # Serialize final plan if exists
    if state["final_plan"]:
        plan = state["final_plan"]
        output["final_plan"] = {
            "mission_overview": plan.mission_overview,
            "required_agents": [
                {
                    "role": a.role,
                    "description": a.description,
                    "required_skills": a.required_skills,
                }
                for a in plan.required_agents
            ],
            "workflow": [
                {
                    "step_id": s.step_id,
                    "description": s.description,
                    "assigned_agent_role": s.assigned_agent_role,
                    "dependencies": s.dependencies,
                }
                for s in plan.workflow
            ],
            "risk_analysis": plan.risk_analysis,
        }
    
    # Write to file
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    
    logger.info(f"💾 Output saved to: {output_path}")
    logger.info(f"📊 File size: {output_path.stat().st_size / 1024:.1f} KB")