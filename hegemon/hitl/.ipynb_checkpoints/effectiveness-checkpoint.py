"""
HEGEMON HITL Feedback Effectiveness Scorer - Phase 2.2.

Measures how well agents incorporated human feedback into revisions.

CRITICAL:
- 3-tier scoring system (structural → keyword → semantic)
- Lightweight by default (no heavy NLP dependencies)
- Optional LLM-based scoring for precision

Complexity: O(n) dla basic scoring, O(1) network call dla LLM scoring
"""

from __future__ import annotations

import logging
import re
from typing import Any

from hegemon.hitl.schemas import HumanFeedback

logger = logging.getLogger(__name__)


# ============================================================================
# Constants
# ============================================================================

MIN_CONTENT_CHANGE_RATIO = 0.05  # 5% minimum change to count as revision
KEYWORD_MATCH_WEIGHT = 0.6  # Weight for keyword matching
STRUCTURAL_CHANGE_WEIGHT = 0.4  # Weight for structural changes


# ============================================================================
# Tier 1: Structural Change Detection
# ============================================================================

def compute_structural_change_score(
    original: str,
    revised: str,
) -> float:
    """
    Compute structural change score (basic diff metrics).
    
    Measures:
    - Length change
    - Word count change
    - Character-level diff (Jaccard similarity on bigrams)
    
    Args:
        original: Original agent output
        revised: Revised agent output after feedback
    
    Returns:
        Score [0.0, 1.0] - 0.0 = identical, 1.0 = completely different
    
    Complexity: O(n) gdzie n = max(len(original), len(revised))
    """
    if not original or not revised:
        return 0.0
    
    # Normalize whitespace
    original = " ".join(original.split())
    revised = " ".join(revised.split())
    
    # Length ratio
    len_ratio = abs(len(revised) - len(original)) / max(len(original), len(revised), 1)
    
    # Word count ratio
    words_orig = len(original.split())
    words_rev = len(revised.split())
    word_ratio = abs(words_rev - words_orig) / max(words_orig, words_rev, 1)
    
    # Simple character-level similarity (Jaccard on character bigrams)
    def get_char_bigrams(text: str) -> set[str]:
        return {text[i:i+2] for i in range(len(text) - 1)}
    
    bigrams_orig = get_char_bigrams(original.lower())
    bigrams_rev = get_char_bigrams(revised.lower())
    
    if not bigrams_orig or not bigrams_rev:
        return 0.0
    
    intersection = len(bigrams_orig & bigrams_rev)
    union = len(bigrams_orig | bigrams_rev)
    jaccard_similarity = intersection / union if union > 0 else 0.0
    jaccard_change = 1.0 - jaccard_similarity
    
    # Weighted average
    structural_score = (
        len_ratio * 0.3 +
        word_ratio * 0.3 +
        jaccard_change * 0.4
    )
    
    # Clamp to [0.0, 1.0]
    return min(1.0, max(0.0, structural_score))


# ============================================================================
# Tier 2: Keyword Matching
# ============================================================================

def compute_keyword_match_score(
    revised: str,
    feedback: HumanFeedback,
) -> float:
    """
    Compute keyword matching score.
    
    Checks if guidance keywords appear in revised output.
    Uses stopword filtering for better precision.
    
    Args:
        revised: Revised agent output
        feedback: HumanFeedback with guidance
    
    Returns:
        Score [0.0, 1.0] - ratio of guidance keywords found in revision
    
    Complexity: O(n * m) gdzie n = words in revised, m = words in guidance
    """
    if not feedback.guidance:
        # No guidance = can't measure keyword match
        return 0.5  # Neutral score
    
    # Common English stopwords
    stopwords = {
        "the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for",
        "of", "with", "by", "from", "as", "is", "was", "are", "were", "be",
        "been", "being", "have", "has", "had", "do", "does", "did", "will",
        "would", "should", "could", "may", "might", "must", "can", "about",
        "more", "add", "include", "provide", "make", "use", "this", "that",
        "these", "those", "your", "you", "please", "also", "very", "just",
    }
    
    # Extract keywords from guidance
    guidance_words = re.findall(r'\b\w+\b', feedback.guidance.lower())
    keywords = [w for w in guidance_words if w not in stopwords and len(w) > 3]
    
    if not keywords:
        return 0.5  # No meaningful keywords
    
    # Check how many keywords appear in revised output
    revised_lower = revised.lower()
    keywords_found = sum(1 for kw in keywords if kw in revised_lower)
    
    keyword_score = keywords_found / len(keywords)
    
    # Also check priority claims (weighted more heavily)
    claims_found = 0
    total_claims = len(feedback.priority_claims)
    
    if total_claims > 0:
        for claim in feedback.priority_claims:
            claim_words = re.findall(r'\b\w+\b', claim.lower())
            # Claim matches if at least 50% of its words appear in revised
            claim_keywords = [w for w in claim_words if w not in stopwords and len(w) > 2]
            if claim_keywords:
                matches = sum(1 for w in claim_keywords if w in revised_lower)
                if matches >= len(claim_keywords) * 0.5:
                    claims_found += 1
        
        claims_score = claims_found / total_claims
        
        # Average of keyword and claims scores (claims weighted more)
        return (keyword_score * 0.4 + claims_score * 0.6)
    
    return keyword_score


# ============================================================================
# Tier 3: Semantic Similarity (LLM-based, Optional)
# ============================================================================

def compute_semantic_effectiveness_llm(
    original: str,
    revised: str,
    feedback: HumanFeedback,
    llm_callable: Any | None = None,
) -> float:
    """
    Compute semantic effectiveness using LLM.
    
    EXPENSIVE: Makes LLM API call. Use sparingly.
    Only called when user explicitly enables LLM-based scoring.
    
    Args:
        original: Original agent output
        revised: Revised agent output
        feedback: HumanFeedback
        llm_callable: Optional LLM function (if None, returns 0.5)
    
    Returns:
        Score [0.0, 1.0] - LLM's assessment of feedback incorporation
    
    Complexity: O(1) network call
    """
    if llm_callable is None:
        logger.debug(
            "No LLM callable provided for semantic scoring. "
            "Returning neutral score 0.5."
        )
        return 0.5
    
    # Construct LLM prompt
    prompt = f"""Assess how well the REVISED output incorporated the HUMAN FEEDBACK.

ORIGINAL OUTPUT:
{original[:400]}...

HUMAN FEEDBACK:
Decision: {feedback.decision}
Guidance: {feedback.guidance}
Priority Claims: {feedback.priority_claims}
Flagged Concerns: {feedback.flagged_concerns}

REVISED OUTPUT:
{revised[:400]}...

QUESTION: On a scale of 0.0 to 1.0, how well did the revised output address the human's feedback?

Scoring criteria:
- 1.0 = Perfectly addressed all feedback points
- 0.7 = Addressed most feedback, minor gaps
- 0.5 = Partially addressed feedback
- 0.3 = Minimally addressed feedback
- 0.0 = Completely ignored feedback

Respond with ONLY a number between 0.0 and 1.0."""
    
    try:
        # Call LLM
        response = llm_callable(prompt)
        
        # Extract score from response
        match = re.search(r'(\d+\.?\d*)', str(response))
        if match:
            score = float(match.group(1))
            score = min(1.0, max(0.0, score))
            logger.debug(f"LLM semantic score: {score}")
            return score
        else:
            logger.warning(f"Failed to parse LLM score from: {response}")
            return 0.5
    except Exception as e:
        logger.error(f"LLM semantic scoring failed: {e}")
        return 0.5


# ============================================================================
# Combined Effectiveness Score
# ============================================================================

def compute_feedback_effectiveness(
    original: str,
    revised: str,
    feedback: HumanFeedback,
    use_llm_scoring: bool = False,
    llm_callable: Any | None = None,
) -> dict[str, Any]:
    """
    Compute comprehensive feedback effectiveness score.
    
    Combines all 3 tiers:
    - Tier 1: Structural changes (fast, O(n))
    - Tier 2: Keyword matching (fast, O(n*m))
    - Tier 3: Semantic similarity (slow, optional, requires LLM)
    
    Args:
        original: Original agent output before feedback
        revised: Revised agent output after feedback
        feedback: HumanFeedback used for revision
        use_llm_scoring: Enable Tier 3 LLM-based scoring (expensive!)
        llm_callable: LLM function for semantic scoring
    
    Returns:
        Dict with breakdown of scores:
        {
            "overall": 0.75,
            "structural": 0.80,
            "keyword_match": 0.70,
            "semantic": 0.75,  # Only if use_llm_scoring=True
            "interpretation": "Good",
            "details": {...}
        }
    
    Complexity: 
        - O(n) dla basic scoring
        - O(1) + network latency jeśli use_llm_scoring=True
    """
    # Tier 1: Structural
    structural_score = compute_structural_change_score(original, revised)
    
    # Tier 2: Keyword matching
    keyword_score = compute_keyword_match_score(revised, feedback)
    
    # Tier 3: Semantic (optional, expensive)
    semantic_score = None
    if use_llm_scoring:
        semantic_score = compute_semantic_effectiveness_llm(
            original, revised, feedback, llm_callable
        )
    
    # Compute overall score
    if semantic_score is not None:
        # Use all 3 tiers (LLM has highest weight)
        overall_score = (
            structural_score * 0.2 +
            keyword_score * 0.3 +
            semantic_score * 0.5
        )
    else:
        # Use only Tier 1 + 2
        overall_score = (
            structural_score * STRUCTURAL_CHANGE_WEIGHT +
            keyword_score * KEYWORD_MATCH_WEIGHT
        )
    
    # Interpretation
    if overall_score >= 0.8:
        interpretation = "Excellent"
    elif overall_score >= 0.6:
        interpretation = "Good"
    elif overall_score >= 0.4:
        interpretation = "Fair"
    elif overall_score >= 0.2:
        interpretation = "Poor"
    else:
        interpretation = "Minimal"
    
    result = {
        "overall": round(overall_score, 2),
        "structural": round(structural_score, 2),
        "keyword_match": round(keyword_score, 2),
        "interpretation": interpretation,
        "details": {
            "original_length": len(original),
            "revised_length": len(revised),
            "feedback_decision": feedback.decision,
            "guidance_provided": bool(feedback.guidance),
            "priority_claims_count": len(feedback.priority_claims),
            "flagged_concerns_count": len(feedback.flagged_concerns),
        }
    }
    
    if semantic_score is not None:
        result["semantic"] = round(semantic_score, 2)
    
    logger.info(
        f"Effectiveness score: {overall_score:.2f} ({interpretation}) - "
        f"Structural: {structural_score:.2f}, Keywords: {keyword_score:.2f}"
    )
    
    return result