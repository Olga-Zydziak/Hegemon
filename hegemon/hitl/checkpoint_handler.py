"""
Checkpoint Handler - Coordinator for Phase 2.3/2.4.

Orchestrates review package generation, UI display, and feedback
processing at HITL checkpoints.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from .jupyter_ui import CheckpointUI
from .models import CheckpointState, CheckpointType, HumanFeedback, InterventionMode
from .review_package import Layer2Data, Layer6Data, ReviewGenerator

if TYPE_CHECKING:
    from hegemon.schemas import DebateState


class CheckpointHandler:
    """Coordinates checkpoint processing.
    
    Handles the complete checkpoint workflow:
    1. Generate review package
    2. Display in UI
    3. Collect feedback
    4. Process and inject into debate
    
    Attributes:
        review_generator: Review package generator
        ui: Checkpoint UI
        checkpoint_history: All checkpoint states
        
    Complexity:
        - handle_checkpoint(): O(n + m) where n = review generation, m = UI display
        - get_checkpoint_history(): O(1)
    """
    
    def __init__(
        self,
        review_generator: ReviewGenerator,
        mode: InterventionMode = InterventionMode.REVIEWER,
    ) -> None:
        """Initialize checkpoint handler.
        
        Args:
            review_generator: Review package generator
            mode: Intervention mode for UI
            
        Complexity: O(1)
        """
        self.review_generator = review_generator
        self.ui = CheckpointUI(mode=mode, on_feedback_callback=self._on_feedback)
        self.checkpoint_history: list[CheckpointState] = []
    
    def handle_checkpoint(
        self,
        checkpoint: CheckpointType,
        state: DebateState,
        layer2_data: Layer2Data | None = None,
        layer6_data: Layer6Data | None = None,
        previous_output: str | None = None,
    ) -> HumanFeedback:
        """Process a checkpoint and collect feedback.
        
        Args:
            checkpoint: Which checkpoint
            state: Current debate state
            layer2_data: Optional Layer 2 explainability data
            layer6_data: Optional Layer 6 semantic data
            previous_output: Optional previous version for comparison
            
        Returns:
            Human feedback collected at checkpoint
            
        Complexity: O(n + m) where n = review gen, m = UI display
        """
        # Generate review package
        review_package = self.review_generator.generate(
            checkpoint=checkpoint,
            state=state,
            layer2_data=layer2_data,
            layer6_data=layer6_data,
        )
        
        # Display and collect feedback
        feedback = self.ui.show_checkpoint(
            review_package=review_package,
            previous_output=previous_output,
        )
        
        # Store checkpoint state
        checkpoint_state = CheckpointState(
            checkpoint=checkpoint,
            review_package=review_package,
            user_feedback=feedback,
            state_snapshot=state.model_dump(mode="json"),
            is_resolved=True,
        )
        self.checkpoint_history.append(checkpoint_state)
        
        return feedback
    
    def get_checkpoint_history(self) -> list[CheckpointState]:
        """Get all checkpoint states.
        
        Returns:
            List of checkpoint states
            
        Complexity: O(1)
        """
        return self.checkpoint_history
    
    def update_progress(
        self,
        current_step: int,
        total_steps: int,
        status: str = "",
    ) -> None:
        """Update progress bar.
        
        Args:
            current_step: Current step
            total_steps: Total steps
            status: Optional status message
            
        Complexity: O(1)
        """
        self.ui.update_progress(current_step, total_steps, status)
    
    def show_history(self) -> None:
        """Display feedback history.
        
        Complexity: O(m) where m = number of checkpoints
        """
        self.ui.show_history()
    
    def _on_feedback(self, feedback: HumanFeedback) -> None:
        """Callback when feedback submitted.
        
        Args:
            feedback: Submitted feedback
            
        Complexity: O(1)
        """
        # Hook for future analytics/logging
        pass
