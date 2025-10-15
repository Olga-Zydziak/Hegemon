"""
Streamlit Application Configuration.

Centralized configuration for page settings, themes, and constants.
"""

from __future__ import annotations

# Page configuration
PAGE_CONFIG = {
    "page_title": "HEGEMON - HITL Debate",
    "page_icon": "🤖",
    "layout": "wide",
    "initial_sidebar_state": "expanded",
    "menu_items": {
        "Get Help": None,
        "Report a bug": None,
        "About": "HEGEMON Phase 2.6 - Human-in-the-Loop Debate System",
    },
}

# Theme configuration (for custom CSS)
THEME = {
    "primary_color": "#667eea",
    "background_color": "#ffffff",
    "secondary_background": "#f8f9fa",
    "text_color": "#262730",
    "font": "sans-serif",
}

# Debate configuration
DEBATE_CONFIG = {
    "default_mode": "reviewer",
    "max_cycles": 10,
    "consensus_threshold": 0.75,
    "checkpoint_timeout": 600,  # 10 minutes
}

# UI constants
UI_CONSTANTS = {
    "checkpoint_refresh_interval": 2.0,  # seconds
    "progress_update_interval": 1.0,  # seconds
    "max_output_preview": 2000,  # characters
    "max_guidance_length": 5000,  # characters
}

# Session state defaults
DEFAULT_SESSION_STATE = {
    # Debate control
    "debate_started": False,
    "debate_running": False,
    "debate_complete": False,
    "awaiting_feedback": False,
    
    # Configuration
    "mission_input": "",
    "intervention_mode": "reviewer",
    
    # Progress tracking
    "current_cycle": 0,
    "current_step": 0,
    "total_steps": 10,
    "status_message": "Initializing...",
    
    # Checkpoint data
    "current_checkpoint": None,
    "checkpoint_count": 0,
    
    # Agent outputs
    "latest_agent": None,
    "latest_output": None,
    "contribution_count": 0,
    
    # Feedback
    "feedback_history": [],
    
    # Results
    "final_plan": None,
    "final_consensus_score": 0.0,
    "final_state": None,
    
    # Background runner
    "debate_runner": None,
}
