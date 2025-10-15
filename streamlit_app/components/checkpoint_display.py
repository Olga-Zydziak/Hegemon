"""
Checkpoint Display Component.

Renders checkpoint review packages with summary, highlights, and suggestions.
"""

from __future__ import annotations

from typing import Any

import streamlit as st


def display_checkpoint(checkpoint_data: dict[str, Any]) -> None:
    """Display checkpoint review package.
    
    Args:
        checkpoint_data: Checkpoint data from ReviewPackage
        
    Complexity: O(n) where n = content size
    """
    if not checkpoint_data:
        st.error("No checkpoint data available")
        return
    
    review = checkpoint_data.get("review_package", {})
    
    # Header with metadata
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        checkpoint_name = review.get("checkpoint", "Unknown")
        st.subheader(f"📍 {checkpoint_name.replace('_', ' ').title()}")
    
    with col2:
        st.metric("Cycle", review.get("cycle", 0))
    
    with col3:
        confidence = review.get("layer2_confidence")
        if confidence is not None:
            st.metric("Confidence", f"{confidence:.2f}")
        else:
            st.metric("Confidence", "N/A")
    
    st.caption(f"**Agent:** {review.get('agent_id', 'Unknown')}")
    
    st.divider()
    
    # Executive summary
    st.markdown("### 📋 Executive Summary")
    
    summary = review.get("summary", "No summary available")
    st.markdown(summary)
    
    # Key points
    key_points = review.get("key_points", [])
    if key_points:
        st.markdown("**Key Points:**")
        for point in key_points:
            st.markdown(f"- {point}")
    
    st.divider()
    
    # Highlights (low confidence claims)
    highlights = review.get("highlights", [])
    if highlights:
        st.markdown("### ⚠️ Important Claims")
        st.caption("Claims flagged for review (low confidence or high impact)")
        
        for highlight in highlights:
            confidence = highlight.get("confidence", 0.0)
            content = highlight.get("content", "")
            reason = highlight.get("reason", "unknown")
            
            # Color-code by confidence
            if confidence >= 0.8:
                color = "🟢"
            elif confidence >= 0.6:
                color = "🟡"
            else:
                color = "🔴"
            
            with st.container():
                st.markdown(
                    f"{color} **Confidence: {confidence:.2f}** - _{reason}_"
                )
                st.info(content[:300] + ("..." if len(content) > 300 else ""))
        
        st.divider()
    
    # Suggested actions
    suggestions = review.get("suggested_actions", [])
    if suggestions:
        st.markdown("### 💡 Suggested Actions")
        st.caption("AI-generated recommendations based on analysis")
        
        for suggestion in suggestions:
            action_type = suggestion.get("action_type", "unknown")
            description = suggestion.get("description", "")
            rationale = suggestion.get("rationale", "")
            priority = suggestion.get("priority", "medium")
            
            # Priority icon
            priority_icons = {
                "high": "🔴",
                "medium": "🟡",
                "low": "🟢",
            }
            icon = priority_icons.get(priority, "⚪")
            
            with st.expander(
                f"{icon} {action_type.replace('_', ' ').title()} "
                f"(Priority: {priority})"
            ):
                st.markdown(f"**Action:** {description}")
                st.caption(f"**Rationale:** {rationale}")
        
        st.divider()
    
    # Full output
    st.markdown("### 📄 Full Agent Output")
    
    original_output = review.get("original_output", "No output available")
    
    # Show preview with expand option
    preview_length = 1500
    if len(original_output) > preview_length:
        st.text_area(
            "Preview (first 1500 characters):",
            value=original_output[:preview_length],
            height=300,
            disabled=True,
        )
        
        with st.expander("Show Full Output"):
            st.text_area(
                "Complete output:",
                value=original_output,
                height=500,
                disabled=True,
            )
    else:
        st.text_area(
            "Output:",
            value=original_output,
            height=300,
            disabled=True,
        )


def get_confidence_color(confidence: float) -> str:
    """Get color for confidence level.
    
    Args:
        confidence: Confidence score 0.0-1.0
        
    Returns:
        Color name for Streamlit
        
    Complexity: O(1)
    """
    if confidence >= 0.8:
        return "green"
    elif confidence >= 0.6:
        return "orange"
    else:
        return "red"
