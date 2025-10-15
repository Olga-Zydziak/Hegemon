"""
Feedback Form Component.

Collects user feedback at checkpoints with decision and optional guidance.
"""

from __future__ import annotations

from typing import Any

import streamlit as st


def collect_feedback(checkpoint_data: dict[str, Any]) -> dict[str, Any] | None:
    """Collect user feedback for checkpoint.
    
    Args:
        checkpoint_data: Current checkpoint data
        
    Returns:
        Feedback dict if submitted, None if not yet submitted
        
    Complexity: O(1)
    """
    st.markdown("### 👤 Your Feedback")
    st.caption("Review the output above and provide your decision")
    
    # Decision selection
    decision = st.radio(
        "Decision:",
        options=["approve", "revise", "reject"],
        format_func=lambda x: {
            "approve": "✅ Approve - Continue with this output",
            "revise": "✏️ Request Revision - Agent will revise based on guidance",
            "reject": "❌ Reject - End debate (critical issue)",
        }[x],
        key="feedback_decision",
    )
    
    # Guidance (conditional on revision)
    guidance = ""
    if decision == "revise":
        st.markdown("**Revision Guidance:**")
        st.caption(
            "Provide specific, actionable guidance for the agent to improve the output"
        )
        
        guidance = st.text_area(
            "What should the agent change or add?",
            placeholder=(
                "Example:\n"
                "- Add more quantitative data for the conversion rate claim\n"
                "- Include GDPR compliance checkpoints in each phase\n"
                "- Extend training timeline from 3 to 4-5 months"
            ),
            height=150,
            max_chars=5000,
            key="feedback_guidance",
        )
        
        # Validation
        if len(guidance.strip()) < 10:
            st.warning(
                "⚠️ Please provide detailed guidance (at least 10 characters) "
                "to help the agent improve"
            )
    
    # Priority claims (optional, advanced)
    with st.expander("⭐ Advanced: Priority Claims (Optional)"):
        st.caption(
            "Mark specific claims that should receive special attention "
            "in the next round"
        )
        
        priority_claims = st.text_area(
            "Priority claims (one per line):",
            placeholder=(
                "Example:\n"
                "Conversion rate prediction needs validation\n"
                "GDPR compliance must be explicit"
            ),
            height=100,
            key="feedback_priority",
        )
    
    # Flagged concerns (for Skeptic)
    with st.expander("🚩 Advanced: Flagged Concerns (Optional)"):
        st.caption(
            "Flag specific concerns for the Skeptic agent to scrutinize "
            "in the next round"
        )
        
        flagged_concerns = st.text_area(
            "Concerns to flag (one per line):",
            placeholder=(
                "Example:\n"
                "Timeline seems too optimistic\n"
                "Budget allocation unclear for Phase 2"
            ),
            height=100,
            key="feedback_concerns",
        )
    
    # Submit button
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col2:
        submit = st.button(
            "Submit Feedback",
            type="primary",
            use_container_width=True,
        )
    
    with col3:
        if st.button(
            "Cancel",
            use_container_width=True,
        ):
            st.warning("Feedback cancelled - debate will continue with approval")
            return {
                "decision": "approve",
                "guidance": "[Auto-approved due to cancel]",
            }
    
    # Process submission
    if submit:
        # Validation for revise
        if decision == "revise" and len(guidance.strip()) < 10:
            st.error(
                "❌ Revision requires detailed guidance. "
                "Please provide at least 10 characters of guidance."
            )
            return None
        
        # Build feedback dict
        feedback = {
            "decision": decision,
            "guidance": guidance.strip(),
            "priority_claims": [
                claim.strip()
                for claim in priority_claims.split("\n")
                if claim.strip()
            ] if priority_claims else [],
            "flagged_concerns": [
                concern.strip()
                for concern in flagged_concerns.split("\n")
                if concern.strip()
            ] if flagged_concerns else [],
            "checkpoint": checkpoint_data.get("review_package", {}).get(
                "checkpoint", "unknown"
            ),
            "timestamp": None,  # Will be set by backend
        }
        
        return feedback
    
    return None


def display_feedback_confirmation(feedback: dict[str, Any]) -> None:
    """Display confirmation after feedback submission.
    
    Args:
        feedback: Submitted feedback data
        
    Complexity: O(1)
    """
    st.success("✅ Feedback Submitted Successfully!")
    
    with st.expander("📝 Your Feedback Summary"):
        st.markdown(f"**Decision:** {feedback['decision'].upper()}")
        
        if feedback.get('guidance'):
            st.markdown("**Guidance:**")
            st.info(feedback['guidance'])
        
        if feedback.get('priority_claims'):
            st.markdown("**Priority Claims:**")
            for claim in feedback['priority_claims']:
                st.markdown(f"- {claim}")
        
        if feedback.get('flagged_concerns'):
            st.markdown("**Flagged Concerns:**")
            for concern in feedback['flagged_concerns']:
                st.markdown(f"- {concern}")
