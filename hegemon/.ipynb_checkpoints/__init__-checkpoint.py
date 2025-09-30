"""
HEGEMON - Dialectical Bootstrapping Multi-Agent System.

Main package exposing core functionality.
"""

from __future__ import annotations

__version__ = "0.1.0"

# Export core components from submodules
from hegemon.config import (
    AgentConfig,
    DebateConfig,
    HegemonSettings,
    get_agent_config,
    get_settings,
)
from hegemon.graph import create_hegemon_graph, run_debate
from hegemon.schemas import (
    AgentContribution,
    DebateState,
    ExecutionAgentSpec,
    FinalPlan,
    GovernorEvaluation,
    WorkflowStep,
)

__all__ = [
    # Version
    "__version__",
    # Main graph functions
    "create_hegemon_graph",
    "run_debate",
    # Configuration
    "HegemonSettings",
    "AgentConfig",
    "DebateConfig",
    "get_settings",
    "get_agent_config",
    # Schemas
    "DebateState",
    "AgentContribution",
    "GovernorEvaluation",
    "FinalPlan",
    "ExecutionAgentSpec",
    "WorkflowStep",
]