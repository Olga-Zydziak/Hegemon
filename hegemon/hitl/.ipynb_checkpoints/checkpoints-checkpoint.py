"""
HEGEMON HITL Checkpoint Nodes - Phase 2.1.

Implementacja 3 checkpoint nodes dla LangGraph:
1. checkpoint_post_thesis_node - Po Katalizatorze
2. checkpoint_post_evaluation_node - Po Gubernatorze
3. checkpoint_pre_synthesis_node - Przed Syntezatorem

KRYTYCZNE:
- Używamy LangGraph interrupt mechanism (nie custom pause logic)
- Observer mode automatycznie skipuje checkpoints
- State snapshots dla recovery

Complexity: O(1) dla checkpoint creation, O(n) dla state snapshot (n = state size)
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

from hegemon.hitl.exceptions import CheckpointError
from hegemon.hitl.schemas import CheckpointMetadata
from hegemon.schemas import DebateState

logger = logging.getLogger(__name__)


# ============================================================================
# Constants
# ============================================================================

CHECKPOINT_NAMES = {
    "post_thesis": "post_thesis_cycle_{}",
    "post_evaluation": "post_evaluation_cycle_{}",
    "pre_synthesis": "pre_synthesis_cycle_{}",
}


# ============================================================================
# Generic Checkpoint Node Factory
# ============================================================================

def _create_checkpoint_node(
    checkpoint_type: str,
    agent_last_executed: str,
) -> Any:  # Returns Callable[[DebateState], dict[str, Any]]
    """
    Factory function dla tworzenia checkpoint nodes.
    
    Args:
        checkpoint_type: Type identifier ("post_thesis" | "post_evaluation" | "pre_synthesis")
        agent_last_executed: ID agenta który właśnie wykonał się
    
    Returns:
        Checkpoint node function compatible z LangGraph
    
    Complexity: O(1) dla factory, O(n) dla node execution (n = state size)
    """
    
    def checkpoint_node(state: DebateState) -> dict[str, Any]:
        """
        Generic checkpoint node implementation.
        
        Behavior:
        1. Check intervention mode - skip if "observer"
        2. Generate checkpoint ID
        3. Create state snapshot (for recovery)
        4. Update state with checkpoint metadata
        5. Log checkpoint arrival
        
        Args:
            state: Current DebateState
        
        Returns:
            Dict with updated state fields (checkpoint metadata)
        
        Raises:
            CheckpointError: If checkpoint creation fails
        
        Complexity: O(n) gdzie n = size of state (snapshot creation)
        """
        # Check intervention mode - skip checkpoint if observer
        mode = state.get("intervention_mode", "reviewer")
        if mode == "observer":
            logger.info(
                f"🔭 Observer mode active - skipping {checkpoint_type} checkpoint"
            )
            return {}  # No state changes
        
        # Generate checkpoint ID
        cycle = state["cycle_count"]
        checkpoint_id = CHECKPOINT_NAMES[checkpoint_type].format(cycle)
        
        logger.info(
            f"⏸️  Checkpoint reached: {checkpoint_id} (mode: {mode})"
        )
        
        try:
            # Create checkpoint metadata
            metadata = CheckpointMetadata(
                checkpoint_id=checkpoint_id,
                checkpoint_type=checkpoint_type,  # type: ignore
                cycle_number=cycle,
                agent_last_executed=agent_last_executed,  # type: ignore
                intervention_mode=mode,  # type: ignore
            )
            
            # Create state snapshot (shallow copy for recovery)
            snapshot = dict(state)
            
            # Prepare state updates
            updates: dict[str, Any] = {
                "current_checkpoint": checkpoint_id,
                "paused_at": datetime.now(timezone.utc).isoformat(),
                "checkpoint_snapshots": {
                    checkpoint_id: snapshot
                },
            }
            
            logger.info(
                f"💾 State snapshot saved for {checkpoint_id}. "
                f"Display name: {metadata.get_display_name()}"
            )
            
            return updates
            
        except Exception as e:
            error_msg = f"Failed to create checkpoint {checkpoint_id}: {e}"
            logger.error(error_msg)
            raise CheckpointError(error_msg) from e
    
    return checkpoint_node


# ============================================================================
# Concrete Checkpoint Nodes (3 Tier 1 Checkpoints)
# ============================================================================

def checkpoint_post_thesis_node(state: DebateState) -> dict[str, Any]:
    """
    Checkpoint #1: Post-Thesis Review (po Katalizatorze).
    
    User może:
    - Approve thesis → Continue do Sceptyka
    - Request revision → Katalizator re-run z feedbackiem
    - Flag concerns → Przekaż listę do Sceptyka
    
    Args:
        state: Current DebateState
    
    Returns:
        Dict z checkpoint metadata
    
    Complexity: O(n) gdzie n = state size
    """
    node_func = _create_checkpoint_node(
        checkpoint_type="post_thesis",
        agent_last_executed="Katalizator",
    )
    return node_func(state)


def checkpoint_post_evaluation_node(state: DebateState) -> dict[str, Any]:
    """
    Checkpoint #2: Post-Evaluation Review (po Gubernatorze).
    
    User może:
    - Accept evaluation → Continue routing (synth vs loop)
    - Override consensus score → Manual adjustment
    - Force additional cycle → Ignore consensus threshold
    
    Args:
        state: Current DebateState
    
    Returns:
        Dict z checkpoint metadata
    
    Complexity: O(n) gdzie n = state size
    """
    node_func = _create_checkpoint_node(
        checkpoint_type="post_evaluation",
        agent_last_executed="Gubernator",
    )
    return node_func(state)


def checkpoint_pre_synthesis_node(state: DebateState) -> dict[str, Any]:
    """
    Checkpoint #3: Pre-Synthesis Review (przed Syntezatorem).
    
    User może:
    - Mark priority arguments → Syntezator emphasizes
    - Add final constraints → Include w syntezie
    - Approve all → Uruchom Syntezator
    
    Args:
        state: Current DebateState
    
    Returns:
        Dict z checkpoint metadata
    
    Complexity: O(n) gdzie n = state size
    """
    node_func = _create_checkpoint_node(
        checkpoint_type="pre_synthesis",
        agent_last_executed="Syntezator",  # Technically before, but logically related
    )
    return node_func(state)