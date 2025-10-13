"""
HEGEMON HITL Contradiction Detector - Phase 2.2.

Detects conflicting feedback across debate cycles.

CRITICAL:
- Identifies when user's guidance contradicts previous guidance
- Warns agents about conflicting instructions
- Helps users understand their feedback patterns

Complexity: O(n²) worst case (n = liczba feedbacku)
"""

from __future__ import annotations

import logging
from typing import Any

from hegemon.hitl.schemas import HumanFeedback

logger = logging.getLogger(__name__)


# ============================================================================
# Contradiction Detection
# ============================================================================

def detect_feedback_contradictions(
    feedback_history: list[HumanFeedback],
    min_similarity_threshold: float = 0.3,
) -> list[dict[str, Any]]:
    """
    Detect contradictory feedback across cycles.
    
    Identifies cases where:
    - Cycle 1: "Make it shorter"
    - Cycle 3: "Add more detail"
    
    Uses keyword-based contradiction detection with predefined
    antonym pairs.
    
    Args:
        feedback_history: List of all HumanFeedback objects
        min_similarity_threshold: Minimum similarity to consider related (unused in current impl)
    
    Returns:
        List of detected contradictions with metadata:
        [
            {
                "feedback_1": {...},
                "feedback_2": {...},
                "contradiction_type": "shorter vs longer",
                "severity": "moderate"
            }
        ]
    
    Complexity: O(n²) where n = liczba feedbacku
    """
    if len(feedback_history) < 2:
        return []  # Need at least 2 feedbacks to contradict
    
    contradictions: list[dict[str, Any]] = []
    
    # Define contradiction keywords (antonym pairs)
    contradiction_pairs = [
        (["shorter", "brief", "concise", "summarize", "reduce", "minimize"], 
         ["longer", "detail", "elaborate", "expand", "more", "comprehensive"]),
        (["simple", "simplify", "basic", "elementary"], 
         ["complex", "detailed", "advanced", "comprehensive", "sophisticated"]),
        (["remove", "delete", "omit", "exclude", "eliminate"], 
         ["add", "include", "incorporate", "append", "insert"]),
        (["general", "broad", "overview", "high-level"], 
         ["specific", "precise", "detailed", "particular", "granular"]),
        (["conservative", "cautious", "careful", "moderate"], 
         ["aggressive", "bold", "ambitious", "radical"]),
        (["fast", "quick", "rapid", "immediate"], 
         ["slow", "gradual", "careful", "thorough"]),
    ]
    
    # Check each pair of feedbacks
    for i in range(len(feedback_history)):
        for j in range(i + 1, len(feedback_history)):
            fb1 = feedback_history[i]
            fb2 = feedback_history[j]
            
            # Skip if same checkpoint (not cross-cycle)
            if fb1.checkpoint == fb2.checkpoint:
                continue
            
            # Check for contradictions in guidance
            guidance1 = fb1.guidance.lower() if fb1.guidance else ""
            guidance2 = fb2.guidance.lower() if fb2.guidance else ""
            
            if not guidance1 or not guidance2:
                continue
            
            # Check each contradiction pair
            for group_a, group_b in contradiction_pairs:
                found_a = any(word in guidance1 for word in group_a)
                found_b = any(word in guidance2 for word in group_b)
                
                if found_a and found_b:
                    contradictions.append({
                        "feedback_1": {
                            "checkpoint": fb1.checkpoint,
                            "guidance": fb1.guidance,
                            "timestamp": fb1.timestamp.isoformat(),
                            "decision": fb1.decision,
                        },
                        "feedback_2": {
                            "checkpoint": fb2.checkpoint,
                            "guidance": fb2.guidance,
                            "timestamp": fb2.timestamp.isoformat(),
                            "decision": fb2.decision,
                        },
                        "contradiction_type": f"{group_a[0]} vs {group_b[0]}",
                        "severity": "moderate",
                    })
                    
                    logger.warning(
                        f"Detected contradiction: {fb1.checkpoint} ({group_a[0]}) "
                        f"vs {fb2.checkpoint} ({group_b[0]})"
                    )
                
                # Also check opposite direction
                found_b_in_1 = any(word in guidance1 for word in group_b)
                found_a_in_2 = any(word in guidance2 for word in group_a)
                
                if found_b_in_1 and found_a_in_2:
                    contradictions.append({
                        "feedback_1": {
                            "checkpoint": fb1.checkpoint,
                            "guidance": fb1.guidance,
                            "timestamp": fb1.timestamp.isoformat(),
                            "decision": fb1.decision,
                        },
                        "feedback_2": {
                            "checkpoint": fb2.checkpoint,
                            "guidance": fb2.guidance,
                            "timestamp": fb2.timestamp.isoformat(),
                            "decision": fb2.decision,
                        },
                        "contradiction_type": f"{group_b[0]} vs {group_a[0]}",
                        "severity": "moderate",
                    })
    
    # Check for contradictory priority claims (shifting focus)
    for i in range(len(feedback_history)):
        for j in range(i + 1, len(feedback_history)):
            fb1 = feedback_history[i]
            fb2 = feedback_history[j]
            
            if fb1.checkpoint == fb2.checkpoint:
                continue
            
            # Check if claims are mutually exclusive (no overlap)
            claims1_set = {c.lower() for c in fb1.priority_claims}
            claims2_set = {c.lower() for c in fb2.priority_claims}
            
            # If both have claims but no overlap, might be shifting focus
            if claims1_set and claims2_set and not (claims1_set & claims2_set):
                contradictions.append({
                    "feedback_1": {
                        "checkpoint": fb1.checkpoint,
                        "priority_claims": fb1.priority_claims,
                        "timestamp": fb1.timestamp.isoformat(),
                    },
                    "feedback_2": {
                        "checkpoint": fb2.checkpoint,
                        "priority_claims": fb2.priority_claims,
                        "timestamp": fb2.timestamp.isoformat(),
                    },
                    "contradiction_type": "shifting_priorities",
                    "severity": "low",
                })
    
    return contradictions


# ============================================================================
# Contradiction Report Generator
# ============================================================================

def generate_contradiction_report(
    contradictions: list[dict[str, Any]],
) -> str:
    """
    Generate human-readable contradiction report.
    
    Args:
        contradictions: List of detected contradictions
    
    Returns:
        Markdown-formatted report string
    
    Complexity: O(n) where n = liczba contradictions
    """
    if not contradictions:
        return "✅ **No contradictions detected** in feedback history."
    
    lines = [
        "# ⚠️ Feedback Contradiction Report",
        "",
        f"Detected **{len(contradictions)} potential contradiction(s)** in feedback history.",
        "",
        "Review these items to ensure consistent guidance across cycles.",
        "",
        "---",
        "",
    ]
    
    for i, contra in enumerate(contradictions, 1):
        severity_emoji = {
            "high": "🔴",
            "moderate": "🟡",
            "low": "🟢",
        }.get(contra.get("severity", "moderate"), "🟡")
        
        lines.extend([
            f"## {severity_emoji} Contradiction #{i}",
            "",
            f"**Type:** {contra.get('contradiction_type', 'unknown')}",
            f"**Severity:** {contra.get('severity', 'moderate')}",
            "",
        ])
        
        fb1 = contra.get("feedback_1", {})
        fb2 = contra.get("feedback_2", {})
        
        lines.extend([
            "### First Feedback:",
            f"- **Checkpoint:** `{fb1.get('checkpoint', 'N/A')}`",
        ])
        
        if "guidance" in fb1:
            lines.append(f"- **Guidance:** *\"{fb1.get('guidance', 'N/A')}\"*")
        if "priority_claims" in fb1:
            claims_str = ", ".join(fb1.get('priority_claims', []))
            lines.append(f"- **Priority Claims:** {claims_str}")
        
        lines.extend([
            "",
            "### Conflicting Feedback:",
            f"- **Checkpoint:** `{fb2.get('checkpoint', 'N/A')}`",
        ])
        
        if "guidance" in fb2:
            lines.append(f"- **Guidance:** *\"{fb2.get('guidance', 'N/A')}\"*")
        if "priority_claims" in fb2:
            claims_str = ", ".join(fb2.get('priority_claims', []))
            lines.append(f"- **Priority Claims:** {claims_str}")
        
        lines.extend([
            "",
            "### 💡 Recommendation:",
            "Review these feedback items to ensure consistent guidance. "
            "Consider which direction better aligns with your goals.",
            "",
            "---",
            "",
        ])
    
    return "\n".join(lines)