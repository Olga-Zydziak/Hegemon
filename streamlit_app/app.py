"""
HEGEMON Streamlit UI - Main Application.

Production-ready web interface for human-in-the-loop debate system.
Designed for Vertex AI Workbench deployment.

Usage:
    streamlit run streamlit_app/app.py --server.port 8080
"""

from __future__ import annotations

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import streamlit as st

from streamlit_app.components.checkpoint_display import display_checkpoint
from streamlit_app.components.feedback_form import collect_feedback
from streamlit_app.components.progress_tracker import display_progress
from streamlit_app.config import PAGE_CONFIG
from streamlit_app.utils.debate_runner import DebateRunner
from streamlit_app.utils.state_manager import StateManager


def main() -> None:
    """Main Streamlit application entry point.
    
    Complexity: O(1) for UI rendering
    """
    # Page configuration
    st.set_page_config(**PAGE_CONFIG)
    
    # Initialize state manager
    state_mgr = StateManager()
    state_mgr.initialize()
    
    # Header
    st.title("🤖 HEGEMON - Human-in-the-Loop Debate System")
    st.markdown("**Phase 2.6: Web Interface** | Multi-Agent Dialectical Debate")
    st.divider()
    
    # Sidebar - Mission Configuration
    with st.sidebar:
        st.header("⚙️ Configuration")
        
        # Mission input
        mission = st.text_area(
            "Mission Description:",
            value=st.session_state.mission_input,
            height=200,
            placeholder="Describe your mission or strategic question...",
            help="Provide a clear, detailed mission description",
        )
        st.session_state.mission_input = mission
        
        # Intervention mode
        mode = st.selectbox(
            "Intervention Mode:",
            options=["reviewer", "observer", "collaborator"],
            index=["reviewer", "observer", "collaborator"].index(
                st.session_state.intervention_mode
            ),
            help=(
                "**Reviewer**: Standard checkpoints (recommended)\n\n"
                "**Observer**: Minimal checkpoints (faster)\n\n"
                "**Collaborator**: Detailed guidance (comprehensive)"
            ),
        )
        st.session_state.intervention_mode = mode
        
        st.divider()
        
        # Start/Stop buttons
        col1, col2 = st.columns(2)
        
        with col1:
            start_disabled = (
                not mission.strip()
                or st.session_state.debate_running
            )
            
            if st.button(
                "🚀 Start Debate",
                disabled=start_disabled,
                use_container_width=True,
                type="primary",
            ):
                if mission.strip():
                    state_mgr.start_debate(mission, mode)
                    st.rerun()
        
        with col2:
            if st.button(
                "⏹️ Stop",
                disabled=not st.session_state.debate_running,
                use_container_width=True,
            ):
                state_mgr.stop_debate()
                st.rerun()
        
        # Status indicator
        if st.session_state.debate_running:
            st.success("🟢 Debate in progress...")
        elif st.session_state.debate_complete:
            st.info("✅ Debate completed")
        else:
            st.warning("⚪ Ready to start")
        
        # Statistics
        if st.session_state.debate_started:
            st.divider()
            st.subheader("📊 Statistics")
            st.metric("Cycle", st.session_state.current_cycle)
            st.metric("Checkpoints", st.session_state.checkpoint_count)
            st.metric("Feedbacks", len(st.session_state.feedback_history))
        
        # Storage info
        st.divider()
        st.subheader("💾 Storage")
        
        from streamlit_app.utils.file_manager import create_file_manager
        file_manager = create_file_manager()
        
        try:
            stats = file_manager.get_storage_stats()
            st.metric("Saved Debates", stats["total_debates"])
            st.metric("Storage Used", f"{stats['total_size_mb']:.1f} MB")
            
            # Show saved debates list
            if st.button("📂 View Saved Debates", use_container_width=True):
                st.session_state.show_saved_debates = True
        except Exception:
            st.caption("Storage stats unavailable")
    
    # Main content area
    if st.session_state.get("show_saved_debates"):
        # Show saved debates browser
        st.header("📂 Saved Debates")
        
        from streamlit_app.utils.file_manager import create_file_manager
        file_manager = create_file_manager()
        
        col1, col2 = st.columns([3, 1])
        with col1:
            st.caption(f"Location: `{file_manager.debates_dir.absolute()}`")
        with col2:
            if st.button("← Back"):
                st.session_state.show_saved_debates = False
                st.rerun()
        
        st.divider()
        
        # List saved debates
        saved_debates = file_manager.list_saved_debates(limit=50)
        
        if not saved_debates:
            st.info("No saved debates yet")
        else:
            for i, debate in enumerate(saved_debates, 1):
                with st.expander(f"{i}. {debate['filename']} ({debate['size_kb']:.1f} KB)"):
                    st.caption(f"**Created:** {debate['created']}")
                    st.caption(f"**Mission:** {debate['mission_preview']}...")
                    st.caption(f"**Path:** `{debate['filepath']}`")
                    
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        # Load and view
                        if st.button(f"👁️ View", key=f"view_{i}"):
                            try:
                                data = file_manager.load_debate(debate['filepath'])
                                st.json(data)
                            except Exception as e:
                                st.error(f"Error loading: {e}")
                    
                    with col2:
                        # Delete
                        if st.button(f"🗑️ Delete", key=f"delete_{i}"):
                            if file_manager.delete_debate(debate['filepath']):
                                st.success("Deleted!")
                                st.rerun()
                            else:
                                st.error("Failed to delete")
        
        st.divider()
        
        # Cleanup option
        with st.expander("🧹 Cleanup Old Files"):
            days = st.number_input("Delete files older than (days):", min_value=1, value=30)
            if st.button("Delete Old Files"):
                deleted = file_manager.cleanup_old_files(days=days)
                st.success(f"Deleted {deleted} files")
                st.rerun()
        
    elif not st.session_state.debate_started:
        # Welcome screen
        st.info("👈 Configure your mission in the sidebar and click **Start Debate**")
        
        # Example missions
        with st.expander("💡 Example Missions"):
            st.markdown("""
            **E-commerce AI Strategy:**
            > Design a comprehensive AI strategy for a mid-size e-commerce company 
            > with $500K budget, focusing on personalization and cost reduction.
            
            **CI/CD Pipeline:**
            > Create a deployment strategy for Node.js microservices with automated 
            > testing, blue-green deployment, and rollback capabilities.
            
            **Data Platform Architecture:**
            > Design a scalable data platform for real-time analytics handling 
            > 1M events/day with GDPR compliance.
            """)
    
    elif st.session_state.awaiting_feedback:
        # Checkpoint screen - collect feedback
        st.header("🛑 Checkpoint")
        
        # Display checkpoint
        display_checkpoint(st.session_state.current_checkpoint)
        
        st.divider()
        
        # Collect feedback
        feedback = collect_feedback(st.session_state.current_checkpoint)
        
        if feedback:
            # User submitted feedback
            state_mgr.submit_feedback(feedback)
            st.success("✅ Feedback submitted! Continuing debate...")
            st.rerun()
    
    elif st.session_state.debate_running:
        # Debate in progress - show progress
        st.header("⏳ Debate in Progress")
        
        display_progress(
            current_step=st.session_state.current_step,
            total_steps=st.session_state.total_steps,
            status=st.session_state.status_message,
        )
        
        # Show latest agent output
        if st.session_state.latest_output:
            with st.expander("📄 Latest Agent Output", expanded=True):
                st.markdown(f"**Agent:** {st.session_state.latest_agent}")
                st.text_area(
                    "Output:",
                    value=st.session_state.latest_output[:2000],
                    height=300,
                    disabled=True,
                )
        
        # Auto-refresh while debate running
        if not st.session_state.awaiting_feedback:
            st.rerun()
    
    elif st.session_state.debate_complete:
        # Final results
        st.header("✅ Debate Complete!")
        
        # Show where file was saved
        if st.session_state.get("saved_filepath"):
            st.success(f"💾 **Results saved to:** `{st.session_state.saved_filepath}`")
            
            # File info
            from pathlib import Path
            filepath = Path(st.session_state.saved_filepath)
            if filepath.exists():
                size_kb = filepath.stat().st_size / 1024
                st.caption(f"File size: {size_kb:.1f} KB")
        
        # Summary statistics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Cycles", st.session_state.current_cycle)
        
        with col2:
            st.metric("Checkpoints", st.session_state.checkpoint_count)
        
        with col3:
            st.metric("Contributions", st.session_state.contribution_count)
        
        with col4:
            consensus = st.session_state.final_consensus_score
            st.metric("Consensus", f"{consensus:.2f}")
        
        st.divider()
        
        # Final plan
        if st.session_state.final_plan:
            st.subheader("📋 Final Strategic Plan")
            
            plan = st.session_state.final_plan
            
            # Overview
            with st.expander("🎯 Mission Overview", expanded=True):
                st.markdown(plan.get("mission_overview", "N/A"))
            
            # Required agents
            if plan.get("required_agents"):
                with st.expander(f"👥 Required Agents ({len(plan['required_agents'])})"):
                    for agent in plan["required_agents"]:
                        st.markdown(f"**{agent.get('role', 'N/A')}**")
                        st.caption(f"Skills: {', '.join(agent.get('skills', []))}")
                        st.divider()
            
            # Workflow
            if plan.get("workflow"):
                with st.expander(f"📊 Workflow ({len(plan['workflow'])} steps)"):
                    for step in plan["workflow"]:
                        st.markdown(
                            f"**{step.get('step_number')}. {step.get('description', 'N/A')}**"
                        )
                        st.caption(
                            f"Agent: {step.get('assigned_agent', 'N/A')} | "
                            f"Duration: {step.get('estimated_duration', 'N/A')}"
                        )
                        st.divider()
            
            # Download results
            import json
            
            results_json = json.dumps(
                st.session_state.final_state,
                indent=2,
                default=str,
            )
            
            st.download_button(
                "💾 Download Full Results (JSON)",
                data=results_json,
                file_name="hegemon_debate_results.json",
                mime="application/json",
            )
        
        # Feedback history
        if st.session_state.feedback_history:
            with st.expander("📜 Feedback History"):
                for i, feedback in enumerate(st.session_state.feedback_history, 1):
                    st.markdown(f"**{i}. {feedback['checkpoint']}**")
                    st.caption(
                        f"Decision: {feedback['decision']} | "
                        f"Time: {feedback['timestamp']}"
                    )
                    if feedback.get('guidance'):
                        st.text(feedback['guidance'][:200])
                    st.divider()
        
        # Start new debate
        if st.button("🔄 Start New Debate", type="primary"):
            state_mgr.reset()
            st.rerun()
    
    # Footer
    st.divider()
    st.caption(
        "HEGEMON v2.6 | Production-Ready Web Interface | "
        "Deployed on Vertex AI Workbench"
    )


if __name__ == "__main__":
    main()
