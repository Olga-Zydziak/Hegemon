"""
Explainability Visualizer.

Generates heatmaps and visual representations of concept vectors.

Complexity: O(n) where n = 100 concepts
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from hegemon.explainability.schemas import ConceptVector

from hegemon.explainability.concepts import get_concept_dictionary

logger = logging.getLogger(__name__)


class HeatmapGenerator:
    """
    Generator for concept heatmaps.

    Creates text-based (ASCII art) visualizations of concept vectors.

    Complexity: O(n) where n = 100 concepts
    """

    def __init__(self) -> None:
        """Initialize generator."""
        self.concept_dict = get_concept_dictionary()

    def generate_text_heatmap(
        self,
        vector: ConceptVector,
        top_k: int = 20,
    ) -> str:
        """
        Generate text-based heatmap.

        Args:
            vector: ConceptVector to visualize
            top_k: Number of top concepts to show (default 20)

        Returns:
            Multi-line ASCII art heatmap

        Complexity: O(n log k) for top_k sorting
        """
        lines = []
        lines.append("=" * 70)
        lines.append("SEMANTIC FINGERPRINT")
        lines.append("=" * 70)
        lines.append("")

        # Show top K concepts
        top_concepts = vector.top_k(top_k)

        lines.append(f"Top {top_k} Concepts:")
        lines.append("")

        for i, (concept_id, score) in enumerate(top_concepts, 1):
            concept = self.concept_dict.get_concept(concept_id)
            name = concept.name if concept else concept_id
            
            # Generate bar
            bar_length = int(score * 20)  # Max 20 chars
            bar = "█" * bar_length + "░" * (20 - bar_length)

            lines.append(f"{i:2d}. {name:30s} {score:.2f} {bar}")

        lines.append("")
        lines.append("-" * 70)
        
        # Show by category
        lines.append("By Category (Top 3 per category):")
        lines.append("")

        for category, concepts in self.concept_dict.concepts_by_category.items():
            # Get scores for this category
            category_scores = [
                (c.id, vector.concept_scores.get(c.id, 0.0))
                for c in concepts
            ]
            # Sort descending
            category_scores.sort(key=lambda x: x[1], reverse=True)

            # Show top 3
            lines.append(f"## {category}")
            for concept_id, score in category_scores[:3]:
                concept = self.concept_dict.get_concept(concept_id)
                name = concept.name if concept else concept_id
                bar_length = int(score * 10)
                bar = "█" * bar_length
                lines.append(f"   {name:30s} {score:.2f} {bar}")
            lines.append("")

        lines.append("=" * 70)
        lines.append(
            f"Model: {vector.model_used} | "
            f"Latency: {vector.processing_time_ms}ms | "
            f"Cache: {'HIT' if vector.cache_hit else 'MISS'}"
        )
        lines.append("=" * 70)

        return "\n".join(lines)

    def generate_comparison_text(
        self,
        vector1: ConceptVector,
        vector2: ConceptVector,
        label1: str = "Vector 1",
        label2: str = "Vector 2",
        top_k: int = 10,
    ) -> str:
        """
        Generate side-by-side comparison of two vectors.

        Args:
            vector1: First vector
            vector2: Second vector
            label1: Label for first vector
            label2: Label for second vector
            top_k: Number of concepts to compare

        Returns:
            Multi-line comparison text

        Complexity: O(n log k)
        """
        lines = []
        lines.append("=" * 80)
        lines.append(f"COMPARISON: {label1} vs {label2}")
        lines.append("=" * 80)
        lines.append("")

        # Similarity score
        similarity = vector1.compare(vector2)
        lines.append(f"Cosine Similarity: {similarity:.3f}")
        lines.append("")

        # Top concepts for each
        top1 = {cid: score for cid, score in vector1.top_k(top_k)}
        top2 = {cid: score for cid, score in vector2.top_k(top_k)}

        # Merge and sort by max score
        all_concepts = set(top1.keys()) | set(top2.keys())
        concept_comparison = []
        for concept_id in all_concepts:
            score1 = top1.get(concept_id, 0.0)
            score2 = top2.get(concept_id, 0.0)
            max_score = max(score1, score2)
            concept_comparison.append((concept_id, score1, score2, max_score))

        concept_comparison.sort(key=lambda x: x[3], reverse=True)

        # Display
        lines.append(f"{'Concept':<30} {label1[:15]:>15} {label2[:15]:>15} {'Δ':>8}")
        lines.append("-" * 80)

        for concept_id, score1, score2, _ in concept_comparison[:top_k]:
            concept = self.concept_dict.get_concept(concept_id)
            name = concept.name if concept else concept_id
            delta = score2 - score1

            bar1 = "█" * int(score1 * 10)
            bar2 = "█" * int(score2 * 10)

            lines.append(
                f"{name:<30} {score1:>6.2f} {bar1:<10} "
                f"{score2:>6.2f} {bar2:<10} {delta:>+7.2f}"
            )

        lines.append("=" * 80)

        return "\n".join(lines)