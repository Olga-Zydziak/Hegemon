"""
Debate Runner - Integration with HITL Backend.

Runs debates in background thread and communicates with Streamlit UI.
This is the bridge between existing HITL code and Streamlit.
"""

from __future__ import annotations

import queue
import threading
from typing import Any

import streamlit as st

# Import existing HITL components
from hegemon.config import get_settings
from hegemon.graph_hitl_v3 import create_hegemon_graph_hitl_v3
from hegemon.hitl import InterventionMode
from hegemon.hitl.checkpoint_handler import CheckpointHandler
from hegemon.hitl.models import CheckpointType, FeedbackDecision, HumanFeedback
from hegemon.hitl.review_package import Layer2Data, create_review_generator
from hegemon.schemas_hitl import DebateStateHITL


class StreamlitCheckpointHandler:
    """Custom checkpoint handler that communicates with Streamlit.
    
    Replaces Jupyter UI with queue-based communication.
    """
    
    def __init__(self, feedback_queue: queue.Queue):
        """Initialize handler.
        
        Args:
            feedback_queue: Queue for receiving feedback from UI
        """
        self.feedback_queue = feedback_queue
        self.checkpoint_queue = queue.Queue()
        
        # Initialize review generator
        from langchain_anthropic import ChatAnthropic
        settings = get_settings()
        llm = ChatAnthropic(
            model=settings.syntezator.model,
            temperature=settings.syntezator.temperature,
        )
        self.review_generator = create_review_generator(llm)
    
    def handle_checkpoint(
        self,
        checkpoint: CheckpointType,
        state: DebateStateHITL,
        layer2_data: Layer2Data | None = None,
        layer6_data: Any | None = None,
        previous_output: str | None = None,
    ) -> HumanFeedback:
        """Handle checkpoint - send to UI and wait for feedback.
        
        Args:
            checkpoint: Checkpoint type
            state: Current debate state
            layer2_data: Optional Layer 2 data
            layer6_data: Optional Layer 6 data
            previous_output: Optional previous output
            
        Returns:
            Human feedback from UI
        """
        # Generate review package
        review_package = self.review_generator.generate(
            checkpoint=checkpoint,
            state=state,
            layer2_data=layer2_data,
            layer6_data=layer6_data,
        )
        
        # Send to UI via session state
        checkpoint_data = {
            "review_package": review_package.model_dump(mode="json"),
            "previous_output": previous_output,
        }
        
        # Signal UI (will be picked up on next st.rerun())
        st.session_state.current_checkpoint = checkpoint_data
        st.session_state.awaiting_feedback = True
        st.session_state.debate_running = False
        
        # Wait for feedback from UI
        # This blocks the debate thread until user submits
        feedback_data = self.feedback_queue.get()  # Blocking
        
        # Convert to HumanFeedback
        feedback = HumanFeedback(
            checkpoint=checkpoint,
            decision=FeedbackDecision(feedback_data["decision"]),
            guidance=feedback_data.get("guidance", ""),
            priority_claims=feedback_data.get("priority_claims", []),
            flagged_concerns=feedback_data.get("flagged_concerns", []),
        )
        
        return feedback


class DebateRunner:
    """Runs debate in background thread with Streamlit integration.
    
    Manages debate lifecycle and communication between backend and UI.
    """
    
    def __init__(self, mission: str, mode: str):
        """Initialize debate runner.
        
        Args:
            mission: Mission description
            mode: Intervention mode
        """
        self.mission = mission
        self.mode = mode
        
        # Communication queues
        self.feedback_queue = queue.Queue()
        
        # Thread control
        self.thread: threading.Thread | None = None
        self.running = False
        
        # State
        self.final_state: DebateStateHITL | None = None
        
        # File manager for auto-save
        from streamlit_app.utils.file_manager import create_file_manager
        self.file_manager = create_file_manager()
    
    def start(self) -> None:
        """Start debate in background thread."""
        if self.running:
            return
        
        self.running = True
        self.thread = threading.Thread(target=self._run_debate, daemon=True)
        self.thread.start()
    
    def stop(self) -> None:
        """Stop running debate."""
        self.running = False
    
    def submit_feedback(self, feedback: dict[str, Any]) -> None:
        """Submit user feedback to debate thread.
        
        Args:
            feedback: Feedback data from UI
        """
        self.feedback_queue.put(feedback)
    
    def _run_debate(self) -> None:
        """Run debate (executed in background thread).
        
        This is where the actual HITL debate runs.
        """
        try:
            # Create custom checkpoint handler
            checkpoint_handler = StreamlitCheckpointHandler(self.feedback_queue)
            
            # Create graph with custom handler
            # NOTE: We need to modify graph creation to use our handler
            # For now, we'll run a simplified version
            
            from hegemon.graph_hitl_v3 import (
                create_checkpoint_node,
                should_continue_after_gubernator,
            )
            from hegemon.agents import (
                gubernator_node,
                katalizator_node,
                sceptyk_node,
                syntezator_node,
            )
            from langgraph.graph import StateGraph, END
            
            # Build custom graph with our checkpoint handler
            graph = StateGraph(DebateStateHITL)
            
            # Add nodes
            graph.add_node("katalizator", katalizator_node)
            graph.add_node(
                "checkpoint_post_thesis",
                create_checkpoint_node(CheckpointType.POST_THESIS, checkpoint_handler),
            )
            graph.add_node("sceptyk", sceptyk_node)
            graph.add_node("gubernator", gubernator_node)
            graph.add_node(
                "checkpoint_post_evaluation",
                create_checkpoint_node(
                    CheckpointType.POST_EVALUATION, checkpoint_handler
                ),
            )
            graph.add_node(
                "checkpoint_pre_synthesis",
                create_checkpoint_node(
                    CheckpointType.PRE_SYNTHESIS, checkpoint_handler
                ),
            )
            graph.add_node("syntezator", syntezator_node)
            
            # Define edges
            graph.set_entry_point("katalizator")
            graph.add_edge("katalizator", "checkpoint_post_thesis")
            graph.add_edge("checkpoint_post_thesis", "sceptyk")
            graph.add_edge("sceptyk", "gubernator")
            graph.add_edge("gubernator", "checkpoint_post_evaluation")
            
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
            
            compiled_graph = graph.compile()
            
            # Initialize state
            initial_state = DebateStateHITL(
                mission=self.mission,
                contributions=[],
                cycle_count=1,
                current_consensus_score=0.0,
                intervention_mode=InterventionMode(self.mode),
                hitl_enabled=True,
            )
            
            # Run debate
            final_state = compiled_graph.invoke(initial_state)
            
            # Store results
            self.final_state = final_state
            
            # Auto-save to file
            final_state_dict = final_state.model_dump(mode="json")
            saved_path = self.file_manager.save_debate_result(
                final_state=final_state_dict,
                mission=self.mission,
                mode=self.mode,
            )
            
            # Notify UI of completion
            st.session_state.final_state = final_state_dict
            st.session_state.debate_complete = True
            st.session_state.debate_running = False
            st.session_state.awaiting_feedback = False
            st.session_state.saved_filepath = str(saved_path)  # Store path
            
        except Exception as e:
            # Handle errors
            st.session_state.debate_running = False
            st.session_state.status_message = f"Error: {str(e)}"
            raise
    
    def cleanup(self) -> None:
        """Clean up resources."""
        self.stop()
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=1.0)
