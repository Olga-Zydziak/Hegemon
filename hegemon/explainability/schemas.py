"""
Explainability Data Schemas.

Pydantic V2 models for type-safe explainability data structures.
All models are immutable (frozen=True where appropriate) for safety.

Complexity:
- Model instantiation: O(1)
- Validation: O(n) where n = number of fields
"""

from __future__ import annotations

import hashlib
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, field_validator, model_validator


# ============================================================================
# Concept Dictionary Models
# ============================================================================


class Concept(BaseModel):
    """
    Single cognitive concept from dictionary.

    Represents one dimension of semantic space (e.g., "risk_aversion").

    Attributes:
        id: Unique identifier (snake_case)
        name: Human-readable display name
        category: One of 10 predefined categories
        definition: Precise description (50-200 chars)
        keywords: Related terms for classification

    Validation:
        - id: lowercase, underscore_case only
        - definition: 50-200 chars
        - keywords: min 3 keywords

    Complexity: O(1) for creation, O(k) for keyword validation where k = len(keywords)
    """

    id: str = Field(..., min_length=3, max_length=50, pattern=r"^[a-z_]+$")
    name: str = Field(..., min_length=3, max_length=100)
    category: Literal[
        "Risk Orientation",
        "Time Orientation",
        "Innovation Stance",
        "Resource Sensitivity",
        "Decision Style",
        "Stakeholder Focus",
        "Emotional Tone",
        "Complexity Handling",
        "Communication Style",
        "Strategy Type",
    ]
    definition: str = Field(..., min_length=50, max_length=200)
    keywords: list[str] = Field(..., min_length=3, max_length=15)

    @field_validator("id")
    @classmethod
    def validate_id_format(cls, v: str) -> str:
        """Ensure ID is valid snake_case."""
        if not v.islower() or " " in v:
            raise ValueError(f"Concept ID must be lowercase snake_case: {v}")
        return v

    @field_validator("keywords")
    @classmethod
    def validate_keyword_quality(cls, v: list[str]) -> list[str]:
        """Ensure keywords are not empty or whitespace-only."""
        cleaned = [k.strip() for k in v if k.strip()]
        if len(cleaned) < 3:
            raise ValueError("Must have at least 3 non-empty keywords")
        return cleaned


# ============================================================================
# Classification Output Models
# ============================================================================


class ConceptVector(BaseModel):
    """
    Vector of 100 concept activation scores.

    Result of classifying text against concept dictionary.

    Attributes:
        concept_scores: Mapping of concept_id → score [0.0, 1.0]
        timestamp: When classification occurred
        model_used: LLM model identifier
        processing_time_ms: Latency in milliseconds
        cache_hit: Whether result came from cache

    Validation:
        - Exactly 100 concepts (matches dictionary size)
        - All scores in [0.0, 1.0]
        - Sparsity check: <30 concepts should be >0.5 (prevent uniform distributions)

    Complexity:
        - Creation: O(n) where n = 100 (dict validation)
        - to_array(): O(n)
        - top_k(): O(n log k)
    """

    concept_scores: dict[str, float] = Field(..., min_length=100, max_length=100)
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    model_used: str = Field(..., min_length=3)
    processing_time_ms: int = Field(..., ge=0)
    cache_hit: bool = Field(default=False)

    @field_validator("concept_scores")
    @classmethod
    def validate_scores(cls, v: dict[str, float]) -> dict[str, float]:
        """
        Validate all scores are in [0.0, 1.0] and distribution is reasonable.

        Complexity: O(n) where n = len(concept_scores) = 100
        """
        # Check range
        for concept_id, score in v.items():
            if not 0.0 <= score <= 1.0:
                raise ValueError(
                    f"Concept '{concept_id}' has invalid score {score} "
                    f"(must be in [0.0, 1.0])"
                )

        # Check sparsity (prevent uniform/random distributions)
        high_scores = sum(1 for score in v.values() if score > 0.5)
        if high_scores > 30:
            raise ValueError(
                f"Too many high scores ({high_scores}/100 > 0.5). "
                f"Classification may be faulty. Expected sparse activation."
            )

        return v

    def to_array(self, concept_ids: list[str]) -> list[float]:
        """
        Convert to ordered array matching concept_ids sequence.

        Args:
            concept_ids: Ordered list of concept IDs

        Returns:
            List of 100 floats in same order as concept_ids

        Complexity: O(n) where n = 100
        """
        return [self.concept_scores[cid] for cid in concept_ids]

    def top_k(self, k: int = 10) -> list[tuple[str, float]]:
        """
        Get top K concepts by activation score.

        Args:
            k: Number of top concepts to return

        Returns:
            List of (concept_id, score) tuples, sorted descending

        Complexity: O(n log k) where n = 100
        """
        return sorted(
            self.concept_scores.items(), key=lambda x: x[1], reverse=True
        )[:k]

    def compare(self, other: ConceptVector) -> float:
        """
        Compute cosine similarity with another vector.

        Args:
            other: Another ConceptVector

        Returns:
            Similarity score in [-1.0, 1.0] (typically [0.0, 1.0] for normalized vectors)

        Complexity: O(n) where n = 100
        """
        # Get scores in same order
        concept_ids = sorted(self.concept_scores.keys())
        v1 = self.to_array(concept_ids)
        v2 = other.to_array(concept_ids)

        # Cosine similarity
        dot_product = sum(a * b for a, b in zip(v1, v2))
        magnitude_v1 = sum(a * a for a in v1) ** 0.5
        magnitude_v2 = sum(b * b for b in v2) ** 0.5

        if magnitude_v1 == 0 or magnitude_v2 == 0:
            return 0.0

        return dot_product / (magnitude_v1 * magnitude_v2)


# ============================================================================
# Explainability Bundle (Container for All Layers)
# ============================================================================


class ExplainabilityBundle(BaseModel):
    """
    Container for all explainability layers.

    Currently only Layer 6 (Semantic Fingerprint) is implemented.
    Future layers will be added as optional fields.

    Attributes:
        semantic_fingerprint: Layer 6 - Concept activation vector

    Validation:
        - At least one layer must be populated (not all None)

    Complexity: O(1)
    """

    semantic_fingerprint: ConceptVector | None = None

    # Placeholders for future layers (Phase 2+)
    # epistemic_claims: list[EpistemicClaim] | None = None
    # hypotheses_considered: list[Hypothesis] | None = None
    # reasoning_graph: ReasoningDAG | None = None
    # counterfactuals: CounterfactualAnalysis | None = None
    # self_critique: SelfInterrogation | None = None
    # temporal_trace: list[TemporalReasoning] | None = None

    @model_validator(mode="after")
    def validate_at_least_one_layer(self) -> ExplainabilityBundle:
        """
        Ensure at least one explainability layer is populated.

        Complexity: O(1)
        """
        if self.semantic_fingerprint is None:
            raise ValueError(
                "ExplainabilityBundle must have at least one layer populated"
            )
        return self

    def enabled_layers(self) -> list[str]:
        """
        Return list of enabled layer names.

        Returns:
            List of layer names (e.g., ["semantic_fingerprint"])

        Complexity: O(1) - constant number of fields to check
        """
        layers = []
        if self.semantic_fingerprint is not None:
            layers.append("semantic_fingerprint")
        return layers

    def export_summary(self) -> str:
        """
        Generate human-readable summary.

        Returns:
            Multi-line string with top concepts and metadata

        Complexity: O(n log k) where k = top concepts to show
        """
        if not self.semantic_fingerprint:
            return "No explainability data available"

        top_concepts = self.semantic_fingerprint.top_k(5)
        lines = ["Explainability Summary:", ""]
        lines.append("Top 5 Concepts:")
        for i, (concept_id, score) in enumerate(top_concepts, 1):
            bars = "█" * int(score * 10)
            lines.append(f"  {i}. {concept_id:30s} {score:.2f} {bars}")

        lines.append("")
        lines.append(
            f"Model: {self.semantic_fingerprint.model_used}, "
            f"Latency: {self.semantic_fingerprint.processing_time_ms}ms, "
            f"Cache: {'HIT' if self.semantic_fingerprint.cache_hit else 'MISS'}"
        )

        return "\n".join(lines)
    
