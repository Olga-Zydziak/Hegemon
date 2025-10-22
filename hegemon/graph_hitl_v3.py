"""
HITL-Enhanced Graph - Phase 2.3/2.4 Integration (FIXED).

LangGraph workflow with integrated checkpoints, review generation,
and interactive Jupyter UI for human-in-the-loop control.
"""

from __future__ import annotations

from typing import Literal

from langchain_anthropic import ChatAnthropic
from langchain_core.language_models import BaseChatModel
from langchain_google_vertexai import ChatVertexAI
from langgraph.graph import StateGraph, END

from hegemon.agents import (
    gubernator_node,
    katalizator_node,
    sceptyk_node,
    syntezator_node,
)
from hegemon.config import get_settings
from hegemon.hitl.checkpoint_handler import CheckpointHandler
from hegemon.hitl.models import CheckpointType, FeedbackDecision
from hegemon.hitl.review_package import Layer2Data, create_review_generator
from hegemon.schemas_hitl import DebateStateHITL


def create_checkpoint_node(
    checkpoint_type: CheckpointType,
    handler: CheckpointHandler,
):
    """Create a checkpoint node for the graph.
    
    Args:
        checkpoint_type: Which checkpoint this is
        handler: Checkpoint handler instance
        
    Returns:
        Node function for LangGraph
        
    Complexity: O(1)
    """
    
    def checkpoint_node(state: DebateStateHITL) -> dict:
        """Process checkpoint and collect feedback.
        
        Args:
            state: Current debate state
            
        Returns:
            State updates
            
        Complexity: O(n) where n = review generation + UI display
        """
        # Skip if observer mode and not critical checkpoint
        if (
            state.intervention_mode.value == "observer"
            and checkpoint_type != CheckpointType.PRE_SYNTHESIS
        ):
            return {}
        
        # Extract Layer 2 data (if available)
        layer2_data = None
        if state.contributions:
            last_contrib = state.contributions[-1]
            # In real implementation, extract from explainability bundle
            layer2_data = Layer2Data(
                aggregate_confidence=state.current_consensus_score,
                low_confidence_claims=[],
            )
        
        # Get previous output for comparison (if revision)
        previous_output = None
        if state.revision_count > 0 and state.contributions:
            agent_id = state.contributions[-1].agent_id
            previous_output = state.previous_outputs.get(agent_id)
        
        # Handle checkpoint
        feedback = handler.handle_checkpoint(
            checkpoint=checkpoint_type,
            state=state,
            layer2_data=layer2_data,
            layer6_data=None,  # TODO: Integrate Layer 6
            previous_output=previous_output,
        )
        
        # Process feedback
        updates: dict = {
            "human_feedback": [feedback],
            "current_checkpoint": None,
            "paused_at": None,
        }
        
        if feedback.decision == FeedbackDecision.REVISE:
            # Increment revision count
            updates["revision_count"] = state.revision_count + 1
            
            # Store current output for next comparison
            if state.contributions:
                agent_id = state.contributions[-1].agent_id
                updates["previous_outputs"] = {
                    **state.previous_outputs,
                    agent_id: state.contributions[-1].content,
                }
        
        elif feedback.decision == FeedbackDecision.REJECT:
            # End debate early
            updates["final_plan"] = None  # Signal early termination
        
        return updates
    
    return checkpoint_node


def should_continue_after_gubernator(
    state: DebateStateHITL,
) -> Literal["checkpoint_pre_synthesis", "katalizator", "syntezator"]:
    """Routing after Gubernator evaluation.
    
    Args:
        state: Current state
        
    Returns:
        Next node name
        
    Complexity: O(1)
    """
    settings = get_settings()
    
    # Check if rejected by human
    if state.human_feedback and state.human_feedback[-1].decision == FeedbackDecision.REJECT:
        return "syntezator"  # End debate
    
    # Check revision limit
    if state.revision_count >= state.max_revisions_per_cycle:
        return "checkpoint_pre_synthesis"
    
    # Standard consensus check
    if state.current_consensus_score >= settings.debate.consensus_threshold:
        return "checkpoint_pre_synthesis"
    
    if state.cycle_count >= settings.debate.max_cycles:
        return "checkpoint_pre_synthesis"
    
    return "katalizator"


def create_hegemon_graph_hitl_v3(
    llm: BaseChatModel | None = None,
    use_simple_ui: bool = False,
) -> StateGraph:
    """Create HITL-enhanced Hegemon graph.

    Integrates Phase 2.3/2.4 components:
    - Review package generation at checkpoints
    - Interactive Jupyter UI for feedback
    - Feedback processing and injection

    Args:
        llm: Optional LLM (uses settings if None)
        use_simple_ui: If True, use text-based UI (works on Vertex AI, Colab).
                      If False, use ipywidgets UI (requires jupyterlab-widgets).
                      Set to True for cloud environments like Vertex AI.

    Returns:
        Compiled LangGraph
        
    Complexity: O(1) for graph construction
    """
    settings = get_settings()
    
    # Create LLM if not provided
    if llm is None:
        syntezator_config = settings.syntezator
        
        if syntezator_config.provider == "anthropic":
            llm = ChatAnthropic(
                model=syntezator_config.model,
                temperature=syntezator_config.temperature,
            )
        elif syntezator_config.provider == "google" and syntezator_config.use_vertex_ai:
            llm = ChatVertexAI(
                model=syntezator_config.model,
                temperature=syntezator_config.temperature,
                project=settings.gcp_project_id,
                location=settings.gcp_location,
            )
        else:
            # Fallback to Anthropic
            llm = ChatAnthropic(
                model="claude-sonnet-4-5-20250929",
                temperature=0.7,
            )
    
    # Create checkpoint handler
    review_generator = create_review_generator(llm)
    checkpoint_handler = CheckpointHandler(
        review_generator=review_generator,
        mode=None,  # Will be set from state
        use_simple_ui=use_simple_ui,  # Use text-based UI for cloud environments
    )
    
    # Create graph
    graph = StateGraph(DebateStateHITL)
    
    # Add agent nodes
    graph.add_node("katalizator", katalizator_node)
    graph.add_node("checkpoint_post_thesis", create_checkpoint_node(
        CheckpointType.POST_THESIS, checkpoint_handler
    ))
    graph.add_node("sceptyk", sceptyk_node)
    graph.add_node("gubernator", gubernator_node)
    graph.add_node("checkpoint_post_evaluation", create_checkpoint_node(
        CheckpointType.POST_EVALUATION, checkpoint_handler
    ))
    graph.add_node("checkpoint_pre_synthesis", create_checkpoint_node(
        CheckpointType.PRE_SYNTHESIS, checkpoint_handler
    ))
    graph.add_node("syntezator", syntezator_node)
    
    # Define edges
    graph.set_entry_point("katalizator")
    graph.add_edge("katalizator", "checkpoint_post_thesis")
    graph.add_edge("checkpoint_post_thesis", "sceptyk")
    graph.add_edge("sceptyk", "gubernator")
    graph.add_edge("gubernator", "checkpoint_post_evaluation")
    
    # Conditional routing after checkpoint
    graph.add_conditional_edges(
        "checkpoint_post_evaluation",
        should_continue_after_gubernator,
        {
            "katalizator": "katalizator",
            "checkpoint_pre_synthesis": "checkpoint_pre_synthesis",
            "syntezator": "syntezator",
        },
    )
    
    graph.add_edge("checkpoint_pre_synthesis", "syntezator")
    graph.add_edge("syntezator", END)
    
    return graph.compile()


def run_debate_hitl_v3(
    mission: str,
    intervention_mode: str = "reviewer",
) -> DebateStateHITL:
    """Run HITL-enhanced debate.
    
    Args:
        mission: Mission description
        intervention_mode: observer/reviewer/collaborator
        
    Returns:
        Final debate state
        
    Complexity: O(n * m) where n = cycles, m = checkpoint processing time
    """
    from hegemon.hitl.models import InterventionMode
    
    graph = create_hegemon_graph_hitl_v3()
    
    initial_state = DebateStateHITL(
        mission=mission,
        contributions=[],
        cycle_count=1,
        current_consensus_score=0.0,
        intervention_mode=InterventionMode(intervention_mode),
        hitl_enabled=True,
    )
    
    final_state = graph.invoke(initial_state)
    
    return final_state
