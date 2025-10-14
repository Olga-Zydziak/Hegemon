"""
Jupyter UI for HITL Checkpoints - Phase 2.4 (FIXED).

Interactive ipywidgets-based interface for human-in-the-loop control
during debates with real-time progress tracking and feedback collection.
"""

from __future__ import annotations

import html
from typing import Any, Callable

try:
    import ipywidgets as widgets
    from IPython.display import HTML, clear_output, display
    
    WIDGETS_AVAILABLE = True
except ImportError:
    WIDGETS_AVAILABLE = False

from .models import (
    CheckpointType,
    FeedbackDecision,
    HumanFeedback,
    InterventionMode,
    ReviewPackage,
)


class CheckpointUI:
    """Interactive Jupyter UI for HITL checkpoints.
    
    Provides clean notebook interface with:
    - Interactive review dashboard
    - Real-time progress tracking
    - Feedback collection widgets
    - History viewer
    - Side-by-side comparison
    
    Attributes:
        mode: Intervention mode (observer/reviewer/collaborator)
        feedback_history: All collected feedback
        on_feedback_callback: Optional callback when feedback submitted
        
    Complexity:
        - show_checkpoint(): O(n) where n = review package size
        - update_progress(): O(1)
        - show_history(): O(m) where m = number of feedbacks
    """
    
    def __init__(
        self,
        mode: InterventionMode = InterventionMode.REVIEWER,
        on_feedback_callback: Callable[[HumanFeedback], None] | None = None,
    ) -> None:
        """Initialize checkpoint UI.
        
        Args:
            mode: Intervention mode
            on_feedback_callback: Optional callback for feedback events
            
        Raises:
            ImportError: If ipywidgets not available
            
        Complexity: O(1)
        """
        if not WIDGETS_AVAILABLE:
            raise ImportError(
                "ipywidgets required for Jupyter UI. "
                "Install with: pip install ipywidgets"
            )
        
        self.mode = mode
        self.feedback_history: list[HumanFeedback] = []
        self.on_feedback_callback = on_feedback_callback
        
        # Progress tracking
        self._progress_widget = widgets.IntProgress(
            value=0,
            min=0,
            max=100,
            description="Progress:",
            bar_style="info",
            style={"bar_color": "#4CAF50"},
            layout=widgets.Layout(width="100%"),
        )
        
        self._status_label = widgets.Label(value="Initializing...")
    
    def show_checkpoint(
        self,
        review_package: ReviewPackage,
        previous_output: str | None = None,
    ) -> HumanFeedback:
        """Display checkpoint and collect user feedback.
        
        Args:
            review_package: Generated review package
            previous_output: Optional previous version for comparison
            
        Returns:
            User feedback collected at checkpoint
            
        Complexity: O(n) where n = size of review package content
        """
        clear_output(wait=True)
        
        # Display header
        self._display_header(review_package)
        
        # Display summary
        self._display_summary(review_package)
        
        # Display highlights
        if review_package.highlights:
            self._display_highlights(review_package.highlights)
        
        # Display suggested actions
        if review_package.suggested_actions:
            self._display_suggestions(review_package.suggested_actions)
        
        # Display full output with optional comparison
        if previous_output:
            self._display_comparison(previous_output, review_package.original_output)
        else:
            self._display_output(review_package.original_output)
        
        # Collect feedback
        feedback = self._collect_feedback(review_package)
        
        # Store in history
        self.feedback_history.append(feedback)
        
        # Trigger callback
        if self.on_feedback_callback:
            self.on_feedback_callback(feedback)
        
        return feedback
    
    def update_progress(
        self,
        current_step: int,
        total_steps: int,
        status: str = "",
    ) -> None:
        """Update progress bar.
        
        Args:
            current_step: Current step number
            total_steps: Total number of steps
            status: Optional status message
            
        Complexity: O(1)
        """
        percentage = int((current_step / total_steps) * 100)
        self._progress_widget.value = percentage
        
        if status:
            self._status_label.value = status
        else:
            self._status_label.value = f"Step {current_step}/{total_steps}"
        
        display(self._progress_widget)
        display(self._status_label)
    
    def show_history(self) -> None:
        """Display feedback history.
        
        Complexity: O(m) where m = len(feedback_history)
        """
        clear_output(wait=True)
        
        if not self.feedback_history:
            display(HTML("<h3>No feedback history yet</h3>"))
            return
        
        html_content = "<h3>📜 Feedback History</h3>"
        
        for i, feedback in enumerate(self.feedback_history, 1):
            guidance_preview = ""
            if feedback.guidance:
                guidance_preview = f"<strong>Guidance:</strong> {html.escape(feedback.guidance[:200])}..."
            
            html_content += f"""
            <div style='border: 1px solid #ddd; padding: 15px; margin: 10px 0; border-radius: 5px;'>
                <strong>Feedback {i}</strong> - {feedback.checkpoint.value}<br>
                <strong>Decision:</strong> {feedback.decision.value}<br>
                <strong>Timestamp:</strong> {feedback.timestamp.strftime('%Y-%m-%d %H:%M:%S')}<br>
                {guidance_preview}
            </div>
            """
        
        display(HTML(html_content))
    
    def _display_header(self, review: ReviewPackage) -> None:
        """Display checkpoint header.
        
        Complexity: O(1)
        """
        # Format confidence properly (fix for f-string ternary issue)
        if review.layer2_confidence is not None:
            confidence_str = f"{review.layer2_confidence:.2f}"
        else:
            confidence_str = "N/A"
        
        header_html = f"""
        <div style='background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                    color: white; padding: 20px; border-radius: 10px; margin-bottom: 20px;'>
            <h2 style='margin: 0;'>🔍 Checkpoint: {review.checkpoint.value.replace('_', ' ').title()}</h2>
            <p style='margin: 10px 0 0 0;'>
                <strong>Agent:</strong> {review.agent_id} | 
                <strong>Cycle:</strong> {review.cycle} | 
                <strong>Confidence:</strong> {confidence_str}
            </p>
        </div>
        """
        display(HTML(header_html))
    
    def _display_summary(self, review: ReviewPackage) -> None:
        """Display executive summary.
        
        Complexity: O(n) where n = len(summary)
        """
        key_points_html = ''.join(f'<li>{html.escape(point)}</li>' for point in review.key_points)
        
        summary_html = f"""
        <div style='background: #f8f9fa; padding: 15px; border-left: 4px solid #667eea; margin-bottom: 20px;'>
            <h3 style='margin-top: 0;'>📋 Executive Summary</h3>
            <p>{html.escape(review.summary)}</p>
            <h4>Key Points:</h4>
            <ul>
                {key_points_html}
            </ul>
        </div>
        """
        display(HTML(summary_html))
    
    def _display_highlights(self, highlights: list) -> None:
        """Display highlighted claims.
        
        Complexity: O(h) where h = len(highlights)
        """
        highlights_html = "<h3>⚠️ Important Claims</h3>"
        
        for highlight in highlights:
            color = self._get_confidence_color(highlight.confidence)
            highlights_html += f"""
            <div style='border-left: 4px solid {color}; padding: 10px; margin: 10px 0; background: #f9f9f9;'>
                <strong>Confidence: {highlight.confidence:.2f}</strong> - {highlight.reason}<br>
                <p style='margin: 5px 0;'>{html.escape(highlight.content[:300])}...</p>
            </div>
            """
        
        display(HTML(highlights_html))
    
    def _display_suggestions(self, suggestions: list) -> None:
        """Display suggested actions.
        
        Complexity: O(s) where s = len(suggestions)
        """
        suggestions_html = "<h3>💡 Suggested Actions</h3>"
        
        for suggestion in suggestions:
            priority_icon = {"high": "🔴", "medium": "🟡", "low": "🟢"}[suggestion.priority]
            suggestions_html += f"""
            <div style='border: 1px solid #ddd; padding: 10px; margin: 10px 0; border-radius: 5px;'>
                {priority_icon} <strong>{suggestion.action_type.replace('_', ' ').title()}</strong><br>
                <p style='margin: 5px 0;'>{html.escape(suggestion.description)}</p>
                <small style='color: #666;'>{html.escape(suggestion.rationale)}</small>
            </div>
            """
        
        display(HTML(suggestions_html))
    
    def _display_output(self, output: str) -> None:
        """Display full agent output.
        
        Complexity: O(n) where n = len(output)
        """
        # Truncate if too long
        display_output = output[:5000]
        truncated = len(output) > 5000
        
        truncated_msg = ""
        if truncated:
            truncated_msg = '<p style="color: #ff9800;"><em>Output truncated (showing first 5000 chars)</em></p>'
        
        output_html = f"""
        <div style='border: 1px solid #ddd; padding: 15px; margin: 20px 0; border-radius: 5px;'>
            <h3>📄 Full Output</h3>
            <pre style='white-space: pre-wrap; background: #f5f5f5; padding: 10px; border-radius: 5px;'>{html.escape(display_output)}</pre>
            {truncated_msg}
        </div>
        """
        display(HTML(output_html))
    
    def _display_comparison(self, previous: str, current: str) -> None:
        """Display side-by-side comparison.
        
        Complexity: O(n + m) where n = len(previous), m = len(current)
        """
        # Truncate both
        prev_display = previous[:2500]
        curr_display = current[:2500]
        
        comparison_html = f"""
        <div style='margin: 20px 0;'>
            <h3>🔄 Comparison</h3>
            <div style='display: grid; grid-template-columns: 1fr 1fr; gap: 20px;'>
                <div style='border: 1px solid #ddd; padding: 15px; border-radius: 5px;'>
                    <h4 style='margin-top: 0;'>Previous Version</h4>
                    <pre style='white-space: pre-wrap; background: #fff3cd; padding: 10px; border-radius: 5px; font-size: 12px;'>{html.escape(prev_display)}</pre>
                </div>
                <div style='border: 1px solid #ddd; padding: 15px; border-radius: 5px;'>
                    <h4 style='margin-top: 0;'>Current Version</h4>
                    <pre style='white-space: pre-wrap; background: #d4edda; padding: 10px; border-radius: 5px; font-size: 12px;'>{html.escape(curr_display)}</pre>
                </div>
            </div>
        </div>
        """
        display(HTML(comparison_html))
    
    def _collect_feedback(self, review: ReviewPackage) -> HumanFeedback:
        """Collect user feedback via widgets.
        
        Args:
            review: Review package
            
        Returns:
            Collected feedback
            
        Complexity: O(1) - blocking wait for user input
        """
        import threading
        
        # Decision buttons
        decision_widget = widgets.RadioButtons(
            options=[
                ("✅ Approve", FeedbackDecision.APPROVE.value),
                ("✏️ Request Revision", FeedbackDecision.REVISE.value),
                ("❌ Reject", FeedbackDecision.REJECT.value),
            ],
            description="Decision:",
            disabled=False,
        )
        
        # Guidance text area
        guidance_widget = widgets.Textarea(
            value="",
            placeholder="Optional: Provide specific guidance for revision...",
            description="Guidance:",
            disabled=False,
            layout=widgets.Layout(width="100%", height="100px"),
        )
        
        # Submit button
        submit_button = widgets.Button(
            description="Submit Feedback",
            button_style="success",
            icon="check",
        )
        
        # Container
        output_area = widgets.Output()
        
        # Threading event to avoid deadlock
        submit_event = threading.Event()
        
        def on_submit(_: Any) -> None:
            """Handle submit button click."""
            with output_area:
                clear_output(wait=True)
                display(HTML("<p>✅ Feedback submitted! Continuing debate...</p>"))
            # Disable button after submit
            submit_button.disabled = True
            submit_button.button_style = "info"
            submit_button.description = "Submitted ✓"
            # Signal that submission is complete
            submit_event.set()
        
        submit_button.on_click(on_submit)
        
        # Display widgets
        display(widgets.VBox([
            widgets.HTML("<h3>👤 Your Feedback</h3>"),
            decision_widget,
            guidance_widget,
            submit_button,
            output_area,
        ]))
        
        # Wait for submission using threading.Event (releases GIL, allows callbacks)
        # Timeout after 10 minutes
        if not submit_event.wait(timeout=600):
            # Timeout - use default approve
            display(HTML("<p style='color: orange;'>⚠️ Timeout - Auto-approving...</p>"))
            feedback = HumanFeedback(
                checkpoint=review.checkpoint,
                decision=FeedbackDecision.APPROVE,
                guidance="[Auto-approved due to timeout]",
            )
        else:
            # Normal submission
            feedback = HumanFeedback(
                checkpoint=review.checkpoint,
                decision=FeedbackDecision(decision_widget.value),
                guidance=guidance_widget.value,
            )
        
        return feedback
    
    @staticmethod
    def _get_confidence_color(confidence: float) -> str:
        """Get color based on confidence level.
        
        Args:
            confidence: Confidence score 0.0-1.0
            
        Returns:
            HTML color code
            
        Complexity: O(1)
        """
        if confidence >= 0.8:
            return "#4CAF50"  # Green
        elif confidence >= 0.6:
            return "#FF9800"  # Orange
        else:
            return "#F44336"  # Red


def create_checkpoint_ui(
    mode: InterventionMode = InterventionMode.REVIEWER,
) -> CheckpointUI:
    """Factory function for checkpoint UI.
    
    Args:
        mode: Intervention mode
        
    Returns:
        Checkpoint UI instance
        
    Complexity: O(1)
    """
    return CheckpointUI(mode=mode)
