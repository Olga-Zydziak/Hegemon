"""
State Manager for Streamlit Session State.

Manages debate state, checkpoints, and feedback across page reruns.
"""

from __future__ import annotations

from typing import Any

import streamlit as st

from streamlit_app.config import DEFAULT_SESSION_STATE
from streamlit_app.utils.debate_runner import DebateRunner


class StateManager:
    """Manages Streamlit session state for debate workflow.
    
    Complexity: O(1) for all operations
    """
    
    def __init__(self) -> None:
        """Initialize state manager."""
        pass
    
    def initialize(self) -> None:
        """Initialize session state with defaults.
        
        Call this once at app start to ensure all keys exist.
        """
        for key, value in DEFAULT_SESSION_STATE.items():
            if key not in st.session_state:
                st.session_state[key] = value
    
    def start_debate(self, mission: str, mode: str) -> None:
        """Start a new debate.
        
        Args:
            mission: Mission description
            mode: Intervention mode
        """
        # Reset state
        self.reset()
        
        # Set configuration
        st.session_state.mission_input = mission
        st.session_state.intervention_mode = mode
        
        # Initialize debate runner
        runner = DebateRunner(mission, mode)
        st.session_state.debate_runner = runner
        
        # Start debate in background
        runner.start()
        
        # Update flags
        st.session_state.debate_started = True
        st.session_state.debate_running = True
        st.session_state.status_message = "Starting debate..."
    
    def stop_debate(self) -> None:
        """Stop running debate."""
        if st.session_state.debate_runner:
            st.session_state.debate_runner.stop()
        
        st.session_state.debate_running = False
        st.session_state.status_message = "Debate stopped by user"
    
    def submit_feedback(self, feedback: dict[str, Any]) -> None:
        """Submit user feedback and continue debate.
        
        Args:
            feedback: User feedback data
        """
        # Add timestamp
        from datetime import datetime
        feedback["timestamp"] = datetime.utcnow().isoformat()
        
        # Store in history
        st.session_state.feedback_history.append(feedback)
        
        # Pass to debate runner
        if st.session_state.debate_runner:
            st.session_state.debate_runner.submit_feedback(feedback)
        
        # Clear awaiting flag
        st.session_state.awaiting_feedback = False
        st.session_state.current_checkpoint = None
        st.session_state.debate_running = True
    
    def handle_checkpoint(self, checkpoint_data: dict[str, Any]) -> None:
        """Handle incoming checkpoint from debate.
        
        Args:
            checkpoint_data: Checkpoint data from backend
        """
        st.session_state.current_checkpoint = checkpoint_data
        st.session_state.checkpoint_count += 1
        st.session_state.awaiting_feedback = True
        st.session_state.debate_running = False
    
    def update_progress(
        self,
        current_step: int,
        total_steps: int,
        status: str = "",
    ) -> None:
        """Update progress indicators.
        
        Args:
            current_step: Current step
            total_steps: Total steps
            status: Status message
        """
        st.session_state.current_step = current_step
        st.session_state.total_steps = total_steps
        if status:
            st.session_state.status_message = status
    
    def update_agent_output(self, agent_id: str, output: str) -> None:
        """Update latest agent output.
        
        Args:
            agent_id: Agent identifier
            output: Agent output content
        """
        st.session_state.latest_agent = agent_id
        st.session_state.latest_output = output
        st.session_state.contribution_count += 1
    
    def complete_debate(self, final_state: dict[str, Any]) -> None:
        """Mark debate as complete and store results.
        
        Args:
            final_state: Final debate state
        """
        st.session_state.debate_complete = True
        st.session_state.debate_running = False
        st.session_state.awaiting_feedback = False
        
        # Store final results
        st.session_state.final_state = final_state
        st.session_state.final_plan = final_state.get("final_plan")
        st.session_state.final_consensus_score = final_state.get(
            "current_consensus_score", 0.0
        )
        st.session_state.current_cycle = final_state.get("cycle_count", 0)
        st.session_state.contribution_count = len(
            final_state.get("contributions", [])
        )
        
        st.session_state.status_message = "Debate completed successfully!"
    
    def reset(self) -> None:
        """Reset debate state for new debate."""
        for key, value in DEFAULT_SESSION_STATE.items():
            if key not in ["mission_input", "intervention_mode"]:
                st.session_state[key] = value
        
        # Clean up runner
        if st.session_state.get("debate_runner"):
            st.session_state.debate_runner.cleanup()
            st.session_state.debate_runner = None
