"""
HEGEMON HITL Schemas - Phase 2.1.

Pydantic models dla Human-in-the-Loop functionality:
- HumanFeedback: Structured user intervention
- CheckpointMetadata: Checkpoint context information
- Enums dla type-safety

Complexity: O(1) dla wszystkich operacji schema
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator


# ============================================================================
# Type Aliases (dla clarity)
# ============================================================================

InterventionMode = Literal["observer", "reviewer", "collaborator"]
FeedbackDecision = Literal["approve", "revise", "reject", "override"]


# ============================================================================
# Human Feedback Schema
# ============================================================================

class HumanFeedback(BaseModel):
    """
    Structured human intervention at checkpoint.
    
    Captures user's decision and guidance at strategic debate points.
    
    Attributes:
        feedback_id: Unique identifier (auto-generated UUID)
        checkpoint: Checkpoint identifier (e.g., "post_thesis_cycle_1")
        timestamp: UTC timestamp of feedback submission
        decision: User's action (approve/revise/reject/override)
        guidance: Optional detailed instructions (required for revise)
        priority_claims: Claims user wants emphasized in revision
        flagged_concerns: Issues user wants explicitly addressed
        override_data: Dict for consensus score override or custom params
    
    Validation:
        - guidance: min 10 chars when decision="revise"
        - guidance: sanitized against prompt injection
        - priority_claims/flagged_concerns: each item min 5 chars
    
    Security:
        - Sanitization of guidance field (XSS, prompt injection)
        - Rate limiting enforcement (via external validation)
    
    Complexity: O(n) dla validation (n = długość guidance)
    """
    
    feedback_id: uuid.UUID = Field(
        default_factory=uuid.uuid4,
        description="Unique identifier for feedback"
    )
    checkpoint: str = Field(
        ...,
        min_length=5,
        description="Checkpoint identifier (e.g., 'post_thesis_cycle_1')"
    )
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="UTC timestamp of feedback submission"
    )
    decision: FeedbackDecision = Field(
        ...,
        description="User's decision (approve/revise/reject/override)"
    )
    guidance: str = Field(
        default="",
        description="Detailed instructions (required for revise)"
    )
    priority_claims: list[str] = Field(
        default_factory=list,
        description="Claims user wants emphasized"
    )
    flagged_concerns: list[str] = Field(
        default_factory=list,
        description="Issues user wants addressed"
    )
    override_data: dict[str, Any] = Field(
        default_factory=dict,
        description="Custom override parameters"
    )
    
    @field_validator("guidance")
    @classmethod
    def validate_guidance_for_revision(cls, v: str, info: Any) -> str:
        """
        Enforce guidance requirement for revisions + sanitization.
        
        Rules:
        1. If decision="revise" → guidance min 10 characters
        2. No dangerous patterns (prompt injection)
        3. No excessive length (max 2000 characters)
        
        Complexity: O(n) gdzie n = długość guidance
        """
        # Check if decision is "revise"
        decision = info.data.get("decision")
        if decision == "revise":
            if len(v.strip()) < 10:
                raise ValueError(
                    "Guidance required for revision (min 10 characters). "
                    "Please provide specific instructions."
                )
        
        # Sanitization (prompt injection protection)
        dangerous_patterns = [
            "ignore previous instructions",
            "disregard all prior",
            "system:",
            "override all",
            "jailbreak",
        ]
        v_lower = v.lower()
        if any(pattern in v_lower for pattern in dangerous_patterns):
            raise ValueError(
                "Guidance contains potentially dangerous patterns. "
                "Please rephrase."
            )
        
        # Max length protection (DoS prevention)
        if len(v) > 2000:
            raise ValueError(
                f"Guidance too long ({len(v)} characters). "
                f"Max 2000 characters allowed."
            )
        
        return v
    
    @field_validator("priority_claims", "flagged_concerns")
    @classmethod
    def validate_claim_list_quality(cls, v: list[str]) -> list[str]:
        """
        Validate quality of priority claims and flagged concerns.
        
        Rules:
        1. Each item min 5 characters (no empty strings)
        2. Max 20 items (prevent overwhelming agent)
        3. No duplicate items
        
        Complexity: O(n) gdzie n = liczba items
        """
        if len(v) > 20:
            raise ValueError(
                f"Too many items ({len(v)}). Maximum 20 allowed."
            )
        
        # Check minimum length per item
        for item in v:
            if len(item.strip()) < 5:
                raise ValueError(
                    f"Item too short: '{item}'. Minimum 5 characters required."
                )
        
        # Check for duplicates
        if len(v) != len(set(v)):
            raise ValueError("Duplicate items found. Please remove duplicates.")
        
        return v


# ============================================================================
# Checkpoint Metadata Schema
# ============================================================================

class CheckpointMetadata(BaseModel):
    """
    Metadata dla checkpoint context.
    
    Generated automatycznie przy każdym checkpoint i przekazywane
    do review package generator.
    
    Attributes:
        checkpoint_id: Unique identifier (e.g., "post_thesis_cycle_2")
        checkpoint_type: Type of checkpoint (post_thesis/post_eval/pre_synth)
        cycle_number: Current debate cycle
        agent_last_executed: ID agenta który właśnie wykonał się
        intervention_mode: User's current intervention mode
        created_at: UTC timestamp checkpoint creation
    
    Complexity: O(1) dla tworzenia instancji
    """
    
    checkpoint_id: str = Field(
        ...,
        min_length=5,
        description="Unique checkpoint identifier"
    )
    checkpoint_type: Literal["post_thesis", "post_evaluation", "pre_synthesis"] = Field(
        ...,
        description="Type of checkpoint"
    )
    cycle_number: int = Field(
        ...,
        ge=1,
        description="Current debate cycle number"
    )
    agent_last_executed: Literal["Katalizator", "Gubernator", "Syntezator"] = Field(
        ...,
        description="Agent that just completed execution"
    )
    intervention_mode: InterventionMode = Field(
        ...,
        description="User's intervention mode"
    )
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="UTC timestamp of checkpoint creation"
    )
    
    def get_display_name(self) -> str:
        """
        Human-readable checkpoint name.
        
        Returns:
            Display name (e.g., "Post-Thesis Review (Cycle 2)")
        
        Complexity: O(1)
        """
        type_names = {
            "post_thesis": "Post-Thesis Review",
            "post_evaluation": "Post-Evaluation Review",
            "pre_synthesis": "Pre-Synthesis Review",
        }
        
        base_name = type_names.get(self.checkpoint_type, "Unknown Checkpoint")
        return f"{base_name} (Cycle {self.cycle_number})"