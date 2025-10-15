"""
Progress Tracker Component.

Displays debate progress with visual progress bar and status updates.
"""

from __future__ import annotations

import streamlit as st


def display_progress(
    current_step: int,
    total_steps: int,
    status: str = "",
) -> None:
    """Display progress bar and status.
    
    Args:
        current_step: Current step number
        total_steps: Total number of steps
        status: Status message to display
        
    Complexity: O(1)
    """
    # Calculate percentage
    if total_steps > 0:
        percentage = int((current_step / total_steps) * 100)
    else:
        percentage = 0
    
    # Progress bar
    st.progress(percentage / 100, text=f"Progress: {percentage}%")
    
    # Status message
    if status:
        st.info(f"🔄 **Status:** {status}")
    
    # Step counter
    st.caption(f"Step {current_step} of {total_steps}")


def display_agent_activity(
    agent_name: str,
    activity: str,
    duration: float | None = None,
) -> None:
    """Display current agent activity.
    
    Args:
        agent_name: Name of active agent
        activity: What the agent is doing
        duration: Optional duration in seconds
        
    Complexity: O(1)
    """
    col1, col2 = st.columns([3, 1])
    
    with col1:
        st.markdown(f"**Agent:** `{agent_name}`")
        st.caption(activity)
    
    with col2:
        if duration is not None:
            st.metric("Duration", f"{duration:.1f}s")


def display_cycle_summary(
    cycle: int,
    contributions: int,
    consensus: float,
) -> None:
    """Display summary of current cycle.
    
    Args:
        cycle: Current cycle number
        contributions: Number of contributions so far
        consensus: Current consensus score
        
    Complexity: O(1)
    """
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Cycle", cycle)
    
    with col2:
        st.metric("Contributions", contributions)
    
    with col3:
        # Color-code consensus
        if consensus >= 0.75:
            delta_color = "normal"
            delta = "✓ Target reached"
        else:
            delta_color = "off"
            delta = f"Target: 0.75"
        
        st.metric(
            "Consensus",
            f"{consensus:.2f}",
            delta=delta,
            delta_color=delta_color,
        )
