"""
Simple Text-Based UI for HITL Checkpoints - Cloud-Friendly Version.

This version uses basic input() instead of ipywidgets, making it compatible
with all Jupyter environments including Vertex AI JupyterLab, Colab, etc.

Works everywhere: Local Jupyter, JupyterLab, Vertex AI, Google Colab, Kaggle.
"""

from __future__ import annotations

import html
from typing import Any

from IPython.display import HTML, Markdown, clear_output, display

from .models import (
    CheckpointType,
    FeedbackDecision,
    HumanFeedback,
    InterventionMode,
    ReviewPackage,
)


class SimpleCheckpointUI:
    """Text-based Jupyter UI for HITL checkpoints (cloud-friendly).

    Uses standard input() instead of ipywidgets for maximum compatibility
    with cloud-based Jupyter environments (Vertex AI, Colab, etc.).

    Attributes:
        mode: Intervention mode (observer/reviewer/collaborator)
        feedback_history: All collected feedback

    Complexity:
        - show_checkpoint(): O(n) where n = review package size
        - All operations are blocking but responsive
    """

    def __init__(
        self,
        mode: InterventionMode = InterventionMode.REVIEWER,
    ) -> None:
        """Initialize simple checkpoint UI.

        Args:
            mode: Intervention mode

        Complexity: O(1)
        """
        self.mode = mode
        self.feedback_history: list[HumanFeedback] = []

    def show_checkpoint(
        self,
        review_package: ReviewPackage,
        previous_output: str | None = None,
    ) -> HumanFeedback:
        """Display checkpoint and collect user feedback via text input.

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

        # Display full output
        if previous_output:
            self._display_comparison(previous_output, review_package.original_output)
        else:
            self._display_output(review_package.original_output)

        # Collect feedback via simple text input
        feedback = self._collect_feedback_simple(review_package)

        # Store in history
        self.feedback_history.append(feedback)

        return feedback

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
        confidence_str = f"{review.layer2_confidence:.2f}" if review.layer2_confidence else "N/A"

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

    def _collect_feedback_simple(self, review: ReviewPackage) -> HumanFeedback:
        """Collect user feedback via simple text input (no widgets needed).

        This version works in ALL Jupyter environments including:
        - Vertex AI JupyterLab
        - Google Colab
        - Kaggle Notebooks
        - Local Jupyter/JupyterLab

        Args:
            review: Review package

        Returns:
            Collected feedback

        Complexity: O(1) - simple blocking input
        """
        print("\n" + "=" * 80)
        print("👤 YOUR FEEDBACK")
        print("=" * 80)
        print()
        print("Options:")
        print("  1 - ✅ Approve (continue with this output)")
        print("  2 - ✏️ Request Revision (provide guidance for improvement)")
        print("  3 - ❌ Reject (end debate - critical issue)")
        print()

        # Get decision
        while True:
            try:
                choice = input("Enter your choice (1/2/3): ").strip()
                if choice == "1":
                    decision = FeedbackDecision.APPROVE
                    guidance = ""
                    break
                elif choice == "2":
                    decision = FeedbackDecision.REVISE
                    print()
                    print("=" * 80)
                    print("REVISION GUIDANCE")
                    print("=" * 80)
                    print("Provide specific, actionable guidance (min 10 characters).")
                    print("Example:")
                    print("  - Add quantitative data for conversion rate claim")
                    print("  - Include GDPR compliance checkpoints")
                    print("  - Extend timeline from 3 to 4-5 months")
                    print()

                    guidance = input("Your guidance: ").strip()

                    if len(guidance) < 10:
                        print()
                        print("❌ ERROR: Guidance must be at least 10 characters.")
                        print("   Please provide detailed feedback to help the agent improve.")
                        print()
                        continue

                    break
                elif choice == "3":
                    decision = FeedbackDecision.REJECT
                    guidance = input("Optional rejection reason: ").strip()
                    break
                else:
                    print("❌ Invalid choice. Please enter 1, 2, or 3.")
                    print()
            except (KeyboardInterrupt, EOFError):
                print()
                print("⚠️ Input cancelled - auto-approving...")
                decision = FeedbackDecision.APPROVE
                guidance = "[Auto-approved due to input cancellation]"
                break

        # Create feedback
        feedback = HumanFeedback(
            checkpoint=review.checkpoint,
            decision=decision,
            guidance=guidance,
        )

        # Display confirmation
        print()
        print("=" * 80)
        print("✅ FEEDBACK SUBMITTED")
        print("=" * 80)
        print(f"Decision: {decision.value.upper()}")
        if guidance:
            print(f"Guidance: {guidance[:100]}{'...' if len(guidance) > 100 else ''}")
        print()
        print("Continuing debate...")
        print("=" * 80)
        print()

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


def create_simple_checkpoint_ui(
    mode: InterventionMode = InterventionMode.REVIEWER,
) -> SimpleCheckpointUI:
    """Factory function for simple text-based checkpoint UI.

    This version works everywhere - no ipywidgets required!
    Perfect for cloud environments like Vertex AI, Colab, Kaggle.

    Args:
        mode: Intervention mode

    Returns:
        Simple checkpoint UI instance

    Complexity: O(1)
    """
    return SimpleCheckpointUI(mode=mode)
