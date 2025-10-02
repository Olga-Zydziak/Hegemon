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
    
# ============================================================================
# Layer 2: Epistemic Uncertainty Visualization
# ============================================================================

def export_epistemic_profile_json(
    profile: EpistemicProfile,
    agent_id: str,
    cycle: int,
    output_dir: str = ".",
) -> str:
    """
    Export epistemic profile to JSON file.
    
    Args:
        profile: EpistemicProfile to export
        agent_id: Agent identifier
        cycle: Debate cycle
        output_dir: Output directory path
    
    Returns:
        Path to exported file
    
    Complexity: O(n) where n = len(profile.claims)
    """
    import json
    from pathlib import Path
    
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    filename = f"epistemic_{agent_id}_cycle{cycle}.json"
    filepath = output_path / filename
    
    # Prepare data
    data = {
        "agent_id": agent_id,
        "cycle": cycle,
        "timestamp": profile.timestamp.isoformat(),
        "model_used": profile.model_used,
        "processing_time_ms": profile.processing_time_ms,
        "aggregate_confidence": profile.aggregate_confidence,
        "summary_stats": profile.get_summary_stats(),
        "claims": [
            {
                "claim_text": claim.claim_text,
                "confidence": claim.confidence,
                "evidence_basis": claim.evidence_basis.value,
                "sentence_indices": claim.sentence_indices,
            }
            for claim in profile.claims
        ],
    }
    
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    logger.info(f"Epistemic profile exported to {filepath}")
    return str(filepath)


def export_epistemic_profile_text(
    profile: EpistemicProfile,
    agent_id: str,
    cycle: int,
    output_dir: str = ".",
) -> str:
    """
    Export epistemic profile to human-readable text file.
    
    Args:
        profile: EpistemicProfile to export
        agent_id: Agent identifier
        cycle: Debate cycle
        output_dir: Output directory path
    
    Returns:
        Path to exported file
    
    Complexity: O(n) where n = len(profile.claims)
    """
    from pathlib import Path
    
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    filename = f"epistemic_{agent_id}_cycle{cycle}.txt"
    filepath = output_path / filename
    
    stats = profile.get_summary_stats()
    
    # Build text content
    lines = [
        "=" * 70,
        "EPISTEMIC UNCERTAINTY PROFILE",
        "=" * 70,
        "",
        f"Agent: {agent_id}",
        f"Cycle: {cycle}",
        f"Model: {profile.model_used}",
        f"Processing time: {profile.processing_time_ms}ms",
        "",
        "-" * 70,
        "SUMMARY STATISTICS",
        "-" * 70,
        "",
        f"Total claims: {stats['total_claims']}",
        f"Aggregate confidence: {stats['aggregate_confidence']:.2f}",
        "",
        f"Confidence distribution:",
        f"  High (≥0.7):   {stats['high_confidence_count']} claims",
        f"  Medium (0.5-0.7): {stats['medium_confidence_count']} claims",
        f"  Low (<0.5):    {stats['low_confidence_count']} claims",
        "",
        f"Evidence basis distribution:",
    ]
    
    for basis, count in stats['basis_distribution'].items():
        pct = (count / stats['total_claims'] * 100) if stats['total_claims'] > 0 else 0
        lines.append(f"  {basis}: {count} ({pct:.1f}%)")
    
    lines.extend([
        "",
        "-" * 70,
        "CLAIMS (sorted by confidence, descending)",
        "-" * 70,
        "",
    ])
    
    # Sort claims by confidence
    sorted_claims = sorted(profile.claims, key=lambda c: c.confidence, reverse=True)
    
    for i, claim in enumerate(sorted_claims, 1):
        # Confidence emoji
        if claim.confidence >= 0.7:
            conf_emoji = "[HIGH]"
        elif claim.confidence >= 0.5:
            conf_emoji = "[MED] "
        else:
            conf_emoji = "[LOW] "
        
        lines.extend([
            f"{i}. {conf_emoji} Confidence: {claim.confidence:.2f} | Basis: {claim.evidence_basis.value}",
            f"   {claim.claim_text}",
            "",
        ])
    
    lines.extend([
        "=" * 70,
        f"Generated: {profile.timestamp.isoformat()}",
        "=" * 70,
    ])
    
    with open(filepath, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    
    logger.info(f"Epistemic profile exported to {filepath}")
    return str(filepath)


def export_all_epistemic_profiles(
    contributions: list[AgentContribution],
    output_dir: str = "epistemic_exports",
    format: str = "both",  # "json", "text", or "both"
) -> dict[str, list[str]]:
    """
    Export all epistemic profiles from debate contributions.
    
    Args:
        contributions: List of agent contributions
        output_dir: Output directory
        format: Export format ("json", "text", or "both")
    
    Returns:
        Dict with exported file paths by format
    
    Complexity: O(n*m) where n = len(contributions), m = avg claims per profile
    """
    from pathlib import Path
    
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    exported = {
        "json": [],
        "text": [],
    }
    
    for contrib in contributions:
        if not contrib.explainability or not contrib.explainability.epistemic_profile:
            logger.debug(
                f"Skipping {contrib.agent_id} Cycle {contrib.cycle} (no epistemic data)"
            )
            continue
        
        profile = contrib.explainability.epistemic_profile
        
        if format in ("json", "both"):
            json_path = export_epistemic_profile_json(
                profile=profile,
                agent_id=contrib.agent_id,
                cycle=contrib.cycle,
                output_dir=output_dir,
            )
            exported["json"].append(json_path)
        
        if format in ("text", "both"):
            text_path = export_epistemic_profile_text(
                profile=profile,
                agent_id=contrib.agent_id,
                cycle=contrib.cycle,
                output_dir=output_dir,
            )
            exported["text"].append(text_path)
    
    logger.info(
        f"Exported {len(exported['json'])} JSON, {len(exported['text'])} text files"
    )
    
    return exported


def create_epistemic_comparison_report(
    contributions: list[AgentContribution],
    output_path: str = "epistemic_comparison.md",
) -> str:
    """
    Create markdown report comparing epistemic profiles across agents/cycles.
    
    Args:
        contributions: List of agent contributions
        output_path: Output file path
    
    Returns:
        Path to generated report
    
    Complexity: O(n*m) where n = len(contributions), m = avg claims
    """
    from pathlib import Path
    
    lines = [
        "# Epistemic Uncertainty Analysis",
        "",
        "Comparison of claim confidence across agents and debate cycles.",
        "",
        "## Summary by Agent",
        "",
    ]
    
    # Group by agent
    from collections import defaultdict
    by_agent = defaultdict(list)
    
    for contrib in contributions:
        if contrib.explainability and contrib.explainability.epistemic_profile:
            by_agent[contrib.agent_id].append(
                (contrib.cycle, contrib.explainability.epistemic_profile)
            )
    
    # Agent-level summary
    for agent_id in sorted(by_agent.keys()):
        profiles = by_agent[agent_id]
        
        lines.append(f"### {agent_id}")
        lines.append("")
        lines.append("| Cycle | Claims | Avg Conf | High | Med | Low |")
        lines.append("|-------|--------|----------|------|-----|-----|")
        
        for cycle, profile in sorted(profiles):
            stats = profile.get_summary_stats()
            lines.append(
                f"| {cycle} | {stats['total_claims']} | "
                f"{stats['aggregate_confidence']:.2f} | "
                f"{stats['high_confidence_count']} | "
                f"{stats['medium_confidence_count']} | "
                f"{stats['low_confidence_count']} |"
            )
        
        lines.append("")
    
    # Cycle-level comparison
    lines.extend([
        "## Summary by Cycle",
        "",
    ])
    
    # Group by cycle
    by_cycle = defaultdict(list)
    for contrib in contributions:
        if contrib.explainability and contrib.explainability.epistemic_profile:
            by_cycle[contrib.cycle].append(
                (contrib.agent_id, contrib.explainability.epistemic_profile)
            )
    
    for cycle in sorted(by_cycle.keys()):
        agents = by_cycle[cycle]
        
        lines.append(f"### Cycle {cycle}")
        lines.append("")
        lines.append("| Agent | Claims | Avg Conf | Evidence Basis |")
        lines.append("|-------|--------|----------|----------------|")
        
        for agent_id, profile in sorted(agents):
            stats = profile.get_summary_stats()
            basis_summary = ", ".join(
                f"{k}({v})" for k, v in sorted(stats['basis_distribution'].items())
            )
            lines.append(
                f"| {agent_id} | {stats['total_claims']} | "
                f"{stats['aggregate_confidence']:.2f} | {basis_summary} |"
            )
        
        lines.append("")
    
    # Low confidence warnings
    lines.extend([
        "## Low Confidence Claims (Risk Flags)",
        "",
        "Claims with confidence < 0.5 requiring verification:",
        "",
    ])
    
    low_conf_found = False
    for contrib in contributions:
        if not contrib.explainability or not contrib.explainability.epistemic_profile:
            continue
        
        profile = contrib.explainability.epistemic_profile
        low_claims = profile.get_low_confidence_claims(threshold=0.5)
        
        if low_claims:
            low_conf_found = True
            lines.append(f"### {contrib.agent_id} (Cycle {contrib.cycle})")
            lines.append("")
            
            for claim in low_claims:
                lines.append(
                    f"- **[{claim.confidence:.2f}]** {claim.evidence_basis.value}: "
                    f"{claim.claim_text[:150]}{'...' if len(claim.claim_text) > 150 else ''}"
                )
            
            lines.append("")
    
    if not low_conf_found:
        lines.append("*No low confidence claims found.*")
        lines.append("")
    
    # Write file
    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    
    logger.info(f"Epistemic comparison report created: {output_path}")
    return output_path