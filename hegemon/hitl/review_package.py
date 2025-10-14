"""
Review Package Generator - Phase 2.3.

Automatically generates contextual review summaries for HITL checkpoints,
integrating Layer 2 (confidence) and Layer 6 (semantic) data.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import HumanMessage, SystemMessage
from pydantic import BaseModel, Field

from .models import (
    CheckpointType,
    ReviewHighlight,
    ReviewPackage,
    SuggestedAction,
)

if TYPE_CHECKING:
    from hegemon.schemas import AgentContribution, DebateState


class Layer2Data(BaseModel):
    """Layer 2 explainability data snapshot.
    
    Complexity: O(1) for all operations
    """
    
    aggregate_confidence: float = Field(ge=0.0, le=1.0)
    low_confidence_claims: list[tuple[str, float]] = Field(default_factory=list)


class Layer6Data(BaseModel):
    """Layer 6 semantic concepts snapshot.
    
    Complexity: O(1) for all operations
    """
    
    key_concepts: list[str] = Field(default_factory=list, max_items=5)
    cognitive_shifts: list[str] = Field(default_factory=list)


class ReviewGenerator(Protocol):
    """Protocol for review package generation.
    
    Enables dependency injection and testing.
    """
    
    def generate(
        self,
        checkpoint: CheckpointType,
        state: DebateState,
        layer2_data: Layer2Data | None,
        layer6_data: Layer6Data | None,
    ) -> ReviewPackage:
        """Generate review package for checkpoint."""
        ...


class LLMReviewGenerator:
    """LLM-powered review package generator.
    
    Uses structured output to generate contextual summaries,
    highlights, and suggested actions.
    
    Attributes:
        llm: Language model for generation
        max_retries: Maximum retry attempts on failure
        
    Complexity:
        - generate(): O(n) where n = total tokens in state
        - _extract_highlights(): O(m) where m = number of contributions
    """
    
    def __init__(
        self,
        llm: BaseChatModel,
        max_retries: int = 2,
    ) -> None:
        """Initialize generator.
        
        Args:
            llm: Language model for generation
            max_retries: Maximum retry attempts
            
        Complexity: O(1)
        """
        self.llm = llm
        self.max_retries = max_retries
    
    def generate(
        self,
        checkpoint: CheckpointType,
        state: DebateState,
        layer2_data: Layer2Data | None = None,
        layer6_data: Layer6Data | None = None,
    ) -> ReviewPackage:
        """Generate review package for checkpoint.
        
        Args:
            checkpoint: Which checkpoint in workflow
            state: Current debate state
            layer2_data: Optional Layer 2 explainability data
            layer6_data: Optional Layer 6 semantic data
            
        Returns:
            Complete review package with summary, highlights, suggestions
            
        Raises:
            ValueError: If state invalid or required data missing
            RuntimeError: If LLM fails after retries
            
        Complexity: O(n + m) where n = tokens, m = contributions
        """
        if not state.contributions:
            raise ValueError("Cannot generate review for empty state")
        
        last_contribution = state.contributions[-1]
        
        # Extract highlights from contributions
        highlights = self._extract_highlights(
            state.contributions,
            layer2_data,
        )
        
        # Generate summary and suggestions using LLM
        summary, suggestions = self._generate_summary_and_actions(
            checkpoint,
            state,
            layer2_data,
            layer6_data,
        )
        
        # Extract key points from summary
        key_points = self._extract_key_points(summary, max_points=5)
        
        return ReviewPackage(
            checkpoint=checkpoint,
            cycle=state.cycle_count,
            agent_id=last_contribution.agent_id,
            summary=summary,
            key_points=key_points,
            highlights=highlights,
            suggested_actions=suggestions,
            layer2_confidence=(
                layer2_data.aggregate_confidence if layer2_data else None
            ),
            layer6_concepts=(
                layer6_data.key_concepts if layer6_data else []
            ),
            original_output=last_contribution.content,
            metadata={
                "total_contributions": len(state.contributions),
                "current_consensus": state.current_consensus_score,
            },
        )
    
    def _extract_highlights(
        self,
        contributions: list[AgentContribution],
        layer2_data: Layer2Data | None,
    ) -> list[ReviewHighlight]:
        """Extract important claims to highlight.
        
        Args:
            contributions: All contributions so far
            layer2_data: Optional confidence data
            
        Returns:
            List of highlighted claims
            
        Complexity: O(m) where m = len(contributions)
        """
        highlights: list[ReviewHighlight] = []
        
        if not layer2_data or not layer2_data.low_confidence_claims:
            # Fallback: highlight last agent's main points
            last = contributions[-1]
            highlights.append(
                ReviewHighlight(
                    claim_id=f"{last.agent_id}_{last.cycle}_main",
                    content=last.content[:500],
                    confidence=0.8,  # Default
                    reason="high_impact",
                )
            )
            return highlights[:10]  # Max 10
        
        # Use Layer 2 low-confidence claims
        for claim_id, confidence in layer2_data.low_confidence_claims[:10]:
            # Find claim in contributions
            for contrib in contributions:
                if claim_id in contrib.content:
                    highlights.append(
                        ReviewHighlight(
                            claim_id=claim_id,
                            content=contrib.content[:500],
                            confidence=confidence,
                            reason="low_confidence",
                        )
                    )
                    break
        
        return highlights[:10]
    
    def _generate_summary_and_actions(
        self,
        checkpoint: CheckpointType,
        state: DebateState,
        layer2_data: Layer2Data | None,
        layer6_data: Layer6Data | None,
    ) -> tuple[str, list[SuggestedAction]]:
        """Generate summary and suggested actions using LLM.
        
        Args:
            checkpoint: Current checkpoint
            state: Debate state
            layer2_data: Optional Layer 2 data
            layer6_data: Optional Layer 6 data
            
        Returns:
            Tuple of (summary, suggested_actions)
            
        Raises:
            RuntimeError: If LLM fails after retries
            
        Complexity: O(n) where n = total tokens
        """
        last_contrib = state.contributions[-1]
        
        system_prompt = f"""You are a debate review assistant. Generate a concise summary
and 3-5 suggested actions for the user at this checkpoint.

Checkpoint: {checkpoint.value}
Agent: {last_contrib.agent_id}
Cycle: {state.cycle_count}

Context:
- Mission: {state.mission[:200]}...
- Current consensus: {state.current_consensus_score:.2f}
- Total contributions: {len(state.contributions)}
"""
        
        if layer2_data:
            system_prompt += f"\n- Aggregate confidence: {layer2_data.aggregate_confidence:.2f}"
        
        if layer6_data:
            system_prompt += f"\n- Key concepts: {', '.join(layer6_data.key_concepts[:3])}"
        
        user_prompt = f"""Latest output from {last_contrib.agent_id}:

{last_contrib.content[:2000]}

Generate:
1. Executive summary (100-200 words)
2. 3-5 suggested actions for user

Format as JSON:
{{
  "summary": "...",
  "actions": [
    {{
      "action_type": "approve|revise_claim|add_constraint|reject",
      "description": "...",
      "rationale": "...",
      "priority": "low|medium|high"
    }}
  ]
}}"""
        
        for attempt in range(self.max_retries + 1):
            try:
                response = self.llm.invoke([
                    SystemMessage(content=system_prompt),
                    HumanMessage(content=user_prompt),
                ])
                
                # Parse JSON response
                import json
                result = json.loads(response.content)
                
                summary = result["summary"]
                actions = [
                    SuggestedAction(**action)
                    for action in result["actions"][:5]
                ]
                
                return summary, actions
                
            except Exception as e:
                if attempt == self.max_retries:
                    # Fallback to simple summary
                    return self._fallback_summary(last_contrib), []
                continue
        
        raise RuntimeError("LLM failed to generate review after retries")
    
    def _fallback_summary(self, contribution: AgentContribution) -> str:
        """Generate simple fallback summary.
        
        Args:
            contribution: Agent contribution
            
        Returns:
            Simple summary text
            
        Complexity: O(1)
        """
        return (
            f"{contribution.agent_id} completed analysis in cycle {contribution.cycle}. "
            f"Review the output below for key claims and concerns."
        )
    
    def _extract_key_points(
        self,
        summary: str,
        max_points: int = 5,
    ) -> list[str]:
        """Extract bullet points from summary.
        
        Args:
            summary: Summary text
            max_points: Maximum points to extract
            
        Returns:
            List of key points
            
        Complexity: O(n) where n = len(summary)
        """
        # Simple extraction: split by periods, take first N
        sentences = [s.strip() for s in summary.split(".") if s.strip()]
        return sentences[:max_points]


def create_review_generator(llm: BaseChatModel) -> ReviewGenerator:
    """Factory function for review generator.
    
    Args:
        llm: Language model
        
    Returns:
        Review generator instance
        
    Complexity: O(1)
    """
    return LLMReviewGenerator(llm=llm)
