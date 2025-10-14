"""
Extended Schemas for HITL - Phase 2.3/2.4.

Extends base DebateState with HITL-specific fields for checkpoints,
human feedback, and pause/resume functionality.
"""

from __future__ import annotations

from datetime import datetime
from typing import Annotated

import operator
from pydantic import BaseModel, Field

from hegemon.schemas import (
    AgentContribution,
    FinalPlan,
    GovernorEvaluation,
)
from hegemon.hitl.models import HumanFeedback, InterventionMode


class DebateStateHITL(BaseModel):
    """Extended debate state with HITL capabilities.
    
    Extends base DebateState with fields for:
    - Human checkpoints and feedback
    - Pause/resume functionality
    - Intervention tracking
    - Revision counting
    
    Attributes:
        mission: The mission/task description
        contributions: Accumulated agent contributions
        cycle_count: Current debate cycle
        current_consensus_score: Latest consensus score
        final_plan: Final synthesized plan (if complete)
        
        # HITL Extensions:
        current_checkpoint: Active checkpoint (if paused)
        human_feedback: All collected feedback
        paused_at: When debate was paused
        intervention_mode: User's intervention level
        revision_count: Number of revisions per cycle
        previous_outputs: For comparison tracking
        
    Complexity: O(1) for all field access, O(n) for serialization
    """
    
    # Base debate fields
    mission: str
    contributions: Annotated[
        list[AgentContribution],
        operator.add,  # Accumulator for LangGraph
    ] = Field(default_factory=list)
    cycle_count: int = Field(default=1, ge=1)
    current_consensus_score: float = Field(default=0.0, ge=0.0, le=1.0)
    final_plan: FinalPlan | None = None
    
    # HITL-specific fields
    current_checkpoint: str | None = None
    human_feedback: Annotated[
        list[HumanFeedback],
        operator.add,  # Accumulator
    ] = Field(default_factory=list)
    paused_at: datetime | None = None
    intervention_mode: InterventionMode = InterventionMode.REVIEWER
    revision_count: int = Field(default=0, ge=0)
    previous_outputs: dict[str, str] = Field(default_factory=dict)
    
    # Metadata
    hitl_enabled: bool = True
    max_revisions_per_cycle: int = 3
    
    class Config:
        """Pydantic config."""
        
        arbitrary_types_allowed = True


class CheckpointContext(BaseModel):
    """Context passed to checkpoint handler.
    
    Contains all data needed for review generation and feedback processing.
    
    Attributes:
        state: Current debate state
        last_contribution: Most recent agent contribution
        layer2_confidence: Optional aggregate confidence
        layer6_concepts: Optional key semantic concepts
        previous_output: Optional previous version for comparison
        
    Complexity: O(1) for all operations
    """
    
    state: DebateStateHITL
    last_contribution: AgentContribution
    layer2_confidence: float | None = None
    layer6_concepts: list[str] = Field(default_factory=list)
    previous_output: str | None = None
