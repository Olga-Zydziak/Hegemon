"""
HITL Data Models - Phase 2.3/2.4.

Pydantic V2 models for Human-in-the-Loop checkpoints, review packages,
and user feedback with strict typing and validation.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Literal
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, field_validator


class CheckpointType(str, Enum):
    """Checkpoint locations in debate workflow.
    
    Complexity: O(1) - enum lookup
    """
    
    POST_THESIS = "post_thesis"
    POST_EVALUATION = "post_evaluation"
    PRE_SYNTHESIS = "pre_synthesis"


class InterventionMode(str, Enum):
    """User interaction level during debate.
    
    Complexity: O(1) - enum lookup
    """
    
    OBSERVER = "observer"
    REVIEWER = "reviewer"
    COLLABORATOR = "collaborator"


class FeedbackDecision(str, Enum):
    """User decision at checkpoint.
    
    Complexity: O(1) - enum lookup
    """
    
    APPROVE = "approve"
    REVISE = "revise"
    REJECT = "reject"
    OVERRIDE = "override"


class HumanFeedback(BaseModel):
    """User feedback at a checkpoint.
    
    Attributes:
        feedback_id: Unique identifier for tracking
        checkpoint: Which checkpoint this feedback is from
        timestamp: When feedback was provided
        decision: User's decision (approve/revise/reject/override)
        guidance: Optional detailed instructions for revision
        priority_claims: Claims user wants emphasized
        flagged_concerns: Issues user wants addressed
        override_data: For consensus score override etc
        
    Complexity: O(1) for all operations
    """
    
    feedback_id: UUID = Field(default_factory=uuid4)
    checkpoint: CheckpointType
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    decision: FeedbackDecision
    guidance: str = Field(default="", max_length=10000)
    priority_claims: list[str] = Field(default_factory=list)
    flagged_concerns: list[str] = Field(default_factory=list)
    override_data: dict[str, Any] = Field(default_factory=dict)
    
    @field_validator("guidance")
    @classmethod
    def sanitize_guidance(cls, v: str) -> str:
        """Remove potentially harmful characters from guidance.
        
        Args:
            v: Raw guidance string
            
        Returns:
            Sanitized guidance string
            
        Complexity: O(n) where n = len(v)
        """
        dangerous_chars = ["<", ">", "&", ";", "`", "$"]
        result = v
        for char in dangerous_chars:
            result = result.replace(char, "")
        return result.strip()


class ReviewHighlight(BaseModel):
    """Highlighted element in review package.
    
    Attributes:
        claim_id: Reference to specific claim
        content: The highlighted content
        confidence: Confidence score from Layer 2 (0.0-1.0)
        reason: Why this is highlighted
        
    Complexity: O(1) for all operations
    """
    
    claim_id: str
    content: str = Field(max_length=5000)
    confidence: float = Field(ge=0.0, le=1.0)
    reason: Literal["low_confidence", "high_impact", "user_concern"]


class SuggestedAction(BaseModel):
    """AI-generated suggestion for user.
    
    Attributes:
        action_type: Type of action suggested
        description: What to do
        rationale: Why this action
        priority: Importance level
        
    Complexity: O(1) for all operations
    """
    
    action_type: Literal["approve", "revise_claim", "add_constraint", "reject"]
    description: str = Field(max_length=1000)
    rationale: str = Field(max_length=2000)
    priority: Literal["low", "medium", "high"]


class ReviewPackage(BaseModel):
    """Complete review package for a checkpoint.
    
    Contains all information needed for user to make informed decision.
    
    Attributes:
        package_id: Unique identifier
        checkpoint: Which checkpoint this is
        cycle: Current debate cycle
        agent_id: Which agent just completed
        summary: Executive summary of what happened
        key_points: Top 3-5 bullet points
        highlights: Important claims to review
        suggested_actions: AI-generated recommendations
        layer2_confidence: Aggregate confidence from Layer 2
        layer6_concepts: Key semantic concepts from Layer 6
        original_output: Full original output from agent
        metadata: Additional context
        
    Complexity: O(1) for creation, O(n) for serialization where n = content size
    """
    
    package_id: UUID = Field(default_factory=uuid4)
    checkpoint: CheckpointType
    cycle: int = Field(ge=1)
    agent_id: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    summary: str = Field(max_length=2000)
    key_points: list[str] = Field(max_items=5)
    highlights: list[ReviewHighlight] = Field(max_items=10)
    suggested_actions: list[SuggestedAction] = Field(max_items=5)
    
    layer2_confidence: float | None = Field(None, ge=0.0, le=1.0)
    layer6_concepts: list[str] = Field(default_factory=list, max_items=5)
    
    original_output: str = Field(max_length=50000)
    metadata: dict[str, Any] = Field(default_factory=dict)
    
    @field_validator("summary")
    @classmethod
    def validate_summary_length(cls, v: str) -> str:
        """Ensure summary is concise.
        
        Args:
            v: Summary text
            
        Returns:
            Validated summary
            
        Raises:
            ValueError: If summary too short
            
        Complexity: O(1)
        """
        if len(v.strip()) < 50:
            raise ValueError("Summary must be at least 50 characters")
        return v.strip()


class CheckpointState(BaseModel):
    """State snapshot at checkpoint.
    
    Attributes:
        checkpoint: Which checkpoint
        review_package: Generated review
        user_feedback: Collected feedback (if any)
        state_snapshot: Serialized DebateState
        is_resolved: Whether checkpoint has been addressed
        
    Complexity: O(1) for all operations except serialization
    """
    
    checkpoint: CheckpointType
    review_package: ReviewPackage
    user_feedback: HumanFeedback | None = None
    state_snapshot: dict[str, Any] = Field(default_factory=dict)
    is_resolved: bool = False
    created_at: datetime = Field(default_factory=datetime.utcnow)
    resolved_at: datetime | None = None
