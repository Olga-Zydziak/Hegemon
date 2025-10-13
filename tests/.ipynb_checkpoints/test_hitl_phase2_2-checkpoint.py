"""
HEGEMON HITL Phase 2.2 Tests.

Comprehensive test suite for feedback processing:
- Prompt building with feedback injection
- Effectiveness scoring (all 3 tiers)
- Contradiction detection
- Agent integration

Complexity: Test execution O(n) where n = number of test cases
"""

from __future__ import annotations

import pytest

from hegemon.hitl.contradiction_detector import (
    detect_feedback_contradictions,
    generate_contradiction_report,
)
from hegemon.hitl.effectiveness import (
    compute_feedback_effectiveness,
    compute_keyword_match_score,
    compute_structural_change_score,
)
from hegemon.hitl.prompt_builder import (
    build_agent_prompt_with_feedback,
    build_feedback_context_for_agent,
)
from hegemon.hitl.schemas import HumanFeedback
from hegemon.schemas import DebateState


# ============================================================================
# Prompt Builder Tests
# ============================================================================

class TestPromptBuilder:
    """Test suite for feedback-aware prompt building."""
    
    def test_build_feedback_context_empty_history(self) -> None:
        """Empty feedback history returns empty context."""
        state: DebateState = {
            "mission": "Test mission",
            "contributions": [],
            "cycle_count": 1,
            "current_consensus_score": 0.0,
            "final_plan": None,
            "intervention_mode": "reviewer",
            "current_checkpoint": None,
            "human_feedback_history": [],
            "paused_at": None,
            "revision_count_per_checkpoint": {},
            "checkpoint_snapshots": {},
        }
        
        context = build_feedback_context_for_agent(state, "Katalizator")
        assert context == ""
    
    def test_build_feedback_context_with_guidance(self) -> None:
        """Feedback with guidance generates formatted context."""
        feedback = HumanFeedback(
            checkpoint="post_thesis_cycle_1",
            decision="revise",
            guidance="Add more details about implementation costs and timeline",
            priority_claims=["Cost analysis", "Timeline estimation"],
            flagged_concerns=["Budget risk", "Resource availability"],
        )
        
        state: DebateState = {
            "mission": "Test mission",
            "contributions": [],
            "cycle_count": 1,
            "current_consensus_score": 0.0,
            "final_plan": None,
            "intervention_mode": "reviewer",
            "current_checkpoint": None,
            "human_feedback_history": [feedback.model_dump()],
            "paused_at": None,
            "revision_count_per_checkpoint": {},
            "checkpoint_snapshots": {},
        }
        
        context = build_feedback_context_for_agent(state, "Katalizator")
        
        # Verify key elements are present
        assert "HUMAN FEEDBACK" in context
        assert "Add more details about implementation costs" in context
        assert "Cost analysis" in context
        assert "Budget risk" in context
        assert "🔄" in context  # Decision emoji for revise
        assert "📝" in context  # Guidance emoji
        assert "🎯" in context  # Priority emoji
        assert "⚠️" in context  # Concerns emoji
    
    def test_build_feedback_context_filtering(self) -> None:
        """Only relevant feedback for agent is included."""
        feedback_thesis = HumanFeedback(
            checkpoint="post_thesis_cycle_1",
            decision="revise",
            guidance="Improve thesis",
        )
        
        feedback_eval = HumanFeedback(
            checkpoint="post_evaluation_cycle_1",
            decision="approve",
            guidance="Good evaluation",
        )
        
        state: DebateState = {
            "mission": "Test",
            "contributions": [],
            "cycle_count": 1,
            "current_consensus_score": 0.0,
            "final_plan": None,
            "intervention_mode": "reviewer",
            "current_checkpoint": None,
            "human_feedback_history": [
                feedback_thesis.model_dump(),
                feedback_eval.model_dump()
            ],
            "paused_at": None,
            "revision_count_per_checkpoint": {},
            "checkpoint_snapshots": {},
        }
        
        # Katalizator should only see post_thesis feedback
        context = build_feedback_context_for_agent(state, "Katalizator")
        assert "Improve thesis" in context
        assert "Good evaluation" not in context
        
        # Gubernator should only see post_evaluation feedback
        context = build_feedback_context_for_agent(state, "Gubernator")
        assert "Good evaluation" in context
        assert "Improve thesis" not in context
    
    def test_build_agent_prompt_with_feedback(self) -> None:
        """Full prompt construction with feedback integration."""
        feedback = HumanFeedback(
            checkpoint="post_thesis_cycle_1",
            decision="revise",
            guidance="Focus on cost analysis",
        )
        
        state: DebateState = {
            "mission": "Design AI system",
            "contributions": [],
            "cycle_count": 1,
            "current_consensus_score": 0.0,
            "final_plan": None,
            "intervention_mode": "reviewer",
            "current_checkpoint": None,
            "human_feedback_history": [feedback.model_dump()],
            "paused_at": None,
            "revision_count_per_checkpoint": {},
            "checkpoint_snapshots": {},
        }
        
        base_system = "You are Katalizator agent."
        base_user = "Mission: {mission}"
        
        enhanced_sys, enhanced_user = build_agent_prompt_with_feedback(
            state=state,
            agent_id="Katalizator",
            base_system_prompt=base_system,
            base_user_prompt=base_user,
        )
        
        # System prompt should include feedback
        assert "HUMAN FEEDBACK" in enhanced_sys
        assert "Focus on cost analysis" in enhanced_sys
        
        # User prompt should include mission
        assert "Design AI system" in enhanced_user
    
    def test_feedback_context_length_limit(self) -> None:
        """Very long feedback is truncated."""
        long_guidance = "X" * 3000  # Exceeds MAX_FEEDBACK_CONTEXT_LENGTH
        
        feedback = HumanFeedback(
            checkpoint="post_thesis_cycle_1",
            decision="revise",
            guidance=long_guidance,
        )
        
        state: DebateState = {
            "mission": "Test",
            "contributions": [],
            "cycle_count": 1,
            "current_consensus_score": 0.0,
            "final_plan": None,
            "intervention_mode": "reviewer",
            "current_checkpoint": None,
            "human_feedback_history": [feedback.model_dump()],
            "paused_at": None,
            "revision_count_per_checkpoint": {},
            "checkpoint_snapshots": {},
        }
        
        context = build_feedback_context_for_agent(state, "Katalizator")
        
        # Should be truncated
        assert len(context) <= 2100  # MAX_FEEDBACK_CONTEXT_LENGTH + buffer
        assert "truncated for length" in context


# ============================================================================
# Effectiveness Scoring Tests
# ============================================================================

class TestEffectivenessScoring:
    """Test suite for feedback effectiveness metrics."""
    
    def test_structural_change_identical_outputs(self) -> None:
        """Identical outputs = 0.0 structural change."""
        original = "This is a test output with some content."
        revised = "This is a test output with some content."
        
        score = compute_structural_change_score(original, revised)
        
        assert score == 0.0
    
    def test_structural_change_completely_different(self) -> None:
        """Completely different outputs = high structural change."""
        original = "Short text."
        revised = "This is a completely different and much longer piece of text with entirely new content and structure that bears no resemblance to the original whatsoever."
        
        score = compute_structural_change_score(original, revised)
        
        assert score > 0.7  # High change
    
    def test_structural_change_moderate(self) -> None:
        """Moderate changes = moderate score."""
        original = "The system will use microservices architecture."
        revised = "The system will use microservices architecture with event-driven communication."
        
        score = compute_structural_change_score(original, revised)
        
        assert 0.1 < score < 0.6  # Moderate change
    
    def test_keyword_match_all_keywords_present(self) -> None:
        """All guidance keywords in revision = high score."""
        revised = "The analysis includes detailed cost estimates, timeline projections, and resource allocation strategies with budget breakdown."
        
        feedback = HumanFeedback(
            checkpoint="post_thesis_cycle_1",
            decision="revise",
            guidance="Add cost estimates, timeline projections, and resource allocation details",
        )
        
        score = compute_keyword_match_score(revised, feedback)
        
        assert score > 0.7  # High keyword match
    
    def test_keyword_match_no_keywords_present(self) -> None:
        """No guidance keywords in revision = low score."""
        revised = "The system architecture follows microservices patterns with API gateway."
        
        feedback = HumanFeedback(
            checkpoint="post_thesis_cycle_1",
            decision="revise",
            guidance="Add cost estimates, timeline analysis, and budget breakdown",
        )
        
        score = compute_keyword_match_score(revised, feedback)
        
        assert score < 0.3  # Low keyword match
    
    def test_keyword_match_with_priority_claims(self) -> None:
        """Priority claims are weighted more heavily."""
        revised = "The implementation will focus on cost optimization through automated resource allocation and scheduled scaling."
        
        feedback = HumanFeedback(
            checkpoint="post_thesis_cycle_1",
            decision="revise",
            guidance="Focus on costs",
            priority_claims=["Cost optimization", "Resource allocation"],
        )
        
        score = compute_keyword_match_score(revised, feedback)
        
        # Should score high because priority claims are present
        assert score > 0.6
    
    def test_keyword_match_no_guidance(self) -> None:
        """No guidance returns neutral score."""
        revised = "Any content here"
        
        feedback = HumanFeedback(
            checkpoint="post_thesis_cycle_1",
            decision="approve",
            guidance="",  # No guidance
        )
        
        score = compute_keyword_match_score(revised, feedback)
        
        assert score == 0.5  # Neutral
    
    def test_combined_effectiveness_excellent_revision(self) -> None:
        """Excellent revision = high combined score."""
        original = "We should implement AI for customer service."
        revised = (
            "We should implement AI for customer service, with estimated costs of $50K "
            "for initial setup and $10K monthly operational costs. The implementation "
            "timeline spans 3 months, with resource allocation of 2 senior engineers "
            "and 1 product manager. Key cost drivers include model training infrastructure "
            "and integration with existing CRM systems."
        )
        
        feedback = HumanFeedback(
            checkpoint="post_thesis_cycle_1",
            decision="revise",
            guidance="Add detailed costs, timeline estimates, and resource requirements",
            priority_claims=["Cost breakdown", "Timeline"],
        )
        
        result = compute_feedback_effectiveness(original, revised, feedback)
        
        assert result["overall"] > 0.65
        assert result["interpretation"] in ["Good", "Excellent"]
        assert "structural" in result
        assert "keyword_match" in result
        assert result["details"]["guidance_provided"] is True
    
    def test_combined_effectiveness_poor_revision(self) -> None:
        """Poor revision = low combined score."""
        original = "We should implement AI."
        revised = "We should implement AI solutions."  # Minimal change
        
        feedback = HumanFeedback(
            checkpoint="post_thesis_cycle_1",
            decision="revise",
            guidance="Add comprehensive cost analysis, detailed timeline, and resource allocation plan",
        )
        
        result = compute_feedback_effectiveness(original, revised, feedback)
        
        assert result["overall"] < 0.4
        assert result["interpretation"] in ["Poor", "Minimal", "Fair"]
    
    def test_combined_effectiveness_with_llm_scoring(self) -> None:
        """LLM scoring integration (mocked)."""
        original = "Short content"
        revised = "Expanded content with details"
        
        feedback = HumanFeedback(
            checkpoint="post_thesis_cycle_1",
            decision="revise",
            guidance="Add more details",
        )
        
        # Mock LLM callable
        def mock_llm(prompt: str) -> str:
            return "0.85"
        
        result = compute_feedback_effectiveness(
            original, revised, feedback,
            use_llm_scoring=True,
            llm_callable=mock_llm
        )
        
        assert "semantic" in result
        assert result["semantic"] == 0.85


# ============================================================================
# Contradiction Detection Tests
# ============================================================================

class TestContradictionDetection:
    """Test suite for feedback contradiction detection."""
    
    def test_no_contradictions_with_single_feedback(self) -> None:
        """Single feedback = no contradictions possible."""
        feedback = HumanFeedback(
            checkpoint="post_thesis_cycle_1",
            decision="revise",
            guidance="Make it more detailed",
        )
        
        contradictions = detect_feedback_contradictions([feedback])
        
        assert len(contradictions) == 0
    
    def test_detect_length_contradiction(self) -> None:
        """Detect 'shorter' vs 'longer' contradiction."""
        fb1 = HumanFeedback(
            checkpoint="post_thesis_cycle_1",
            decision="revise",
            guidance="Make it shorter and more concise",
        )
        
        fb2 = HumanFeedback(
            checkpoint="post_thesis_cycle_2",
            decision="revise",
            guidance="Add more detail and make it longer",
        )
        
        contradictions = detect_feedback_contradictions([fb1, fb2])
        
        assert len(contradictions) > 0
        assert any(
            "shorter" in c.get("contradiction_type", "").lower() or 
            "longer" in c.get("contradiction_type", "").lower()
            for c in contradictions
        )
    
    def test_detect_detail_level_contradiction(self) -> None:
        """Detect 'simple' vs 'complex' contradiction."""
        fb1 = HumanFeedback(
            checkpoint="post_thesis_cycle_1",
            decision="revise",
            guidance="Simplify the explanation for non-technical audience",
        )
        
        fb2 = HumanFeedback(
            checkpoint="post_evaluation_cycle_2",
            decision="revise",
            guidance="Make it more comprehensive and detailed with technical depth",
        )
        
        contradictions = detect_feedback_contradictions([fb1, fb2])
        
        assert len(contradictions) > 0
    
    def test_detect_add_remove_contradiction(self) -> None:
        """Detect 'add' vs 'remove' contradiction."""
        fb1 = HumanFeedback(
            checkpoint="post_thesis_cycle_1",
            decision="revise",
            guidance="Remove the section about deployment strategies",
        )
        
        fb2 = HumanFeedback(
            checkpoint="post_thesis_cycle_2",
            decision="revise",
            guidance="Add comprehensive deployment strategies section",
        )
        
        contradictions = detect_feedback_contradictions([fb1, fb2])
        
        assert len(contradictions) > 0
    
    def test_no_contradiction_consistent_feedback(self) -> None:
        """Consistent feedback = no contradictions."""
        fb1 = HumanFeedback(
            checkpoint="post_thesis_cycle_1",
            decision="revise",
            guidance="Add more cost details",
        )
        
        fb2 = HumanFeedback(
            checkpoint="post_evaluation_cycle_2",
            decision="revise",
            guidance="Include timeline estimates",
        )
        
        contradictions = detect_feedback_contradictions([fb1, fb2])
        
        # These don't contradict
        assert len(contradictions) == 0
    
    def test_detect_shifting_priorities(self) -> None:
        """Detect when priority claims shift completely."""
        fb1 = HumanFeedback(
            checkpoint="post_thesis_cycle_1",
            decision="revise",
            guidance="Focus on technical aspects",
            priority_claims=["Architecture design", "Technology stack"],
        )
        
        fb2 = HumanFeedback(
            checkpoint="post_thesis_cycle_2",
            decision="revise",
            guidance="Focus on business aspects",
            priority_claims=["ROI analysis", "Market opportunity"],
        )
        
        contradictions = detect_feedback_contradictions([fb1, fb2])
        
        # Should detect shifting priorities
        shifting = [c for c in contradictions if c.get("contradiction_type") == "shifting_priorities"]
        assert len(shifting) > 0
        assert shifting[0]["severity"] == "low"
    
    def test_contradiction_report_generation(self) -> None:
        """Generate readable contradiction report."""
        fb1 = HumanFeedback(
            checkpoint="post_thesis_cycle_1",
            decision="revise",
            guidance="Remove unnecessary technical details",
        )
        
        fb2 = HumanFeedback(
            checkpoint="post_thesis_cycle_2",
            decision="revise",
            guidance="Add more comprehensive technical analysis",
        )
        
        contradictions = detect_feedback_contradictions([fb1, fb2])
        report = generate_contradiction_report(contradictions)
        
        assert "Contradiction Report" in report
        assert len(report) > 100  # Non-trivial report
        assert "Recommendation" in report
    
    def test_contradiction_report_empty(self) -> None:
        """Empty contradictions = positive message."""
        report = generate_contradiction_report([])
        
        assert "No contradictions detected" in report
        assert "✅" in report


# ============================================================================
# Integration Tests
# ============================================================================

class TestPhase22Integration:
    """Integration tests for Phase 2.2 workflow."""
    
    def test_full_feedback_aware_prompt_construction(self) -> None:
        """Full prompt construction with feedback and debate context."""
        feedback = HumanFeedback(
            checkpoint="post_thesis_cycle_1",
            decision="revise",
            guidance="Focus on implementation costs and ROI",
            priority_claims=["Cost-benefit analysis"],
            flagged_concerns=["Budget overruns"],
        )
        
        state: DebateState = {
            "mission": "Design microservices platform",
            "contributions": [],
            "cycle_count": 2,
            "current_consensus_score": 0.5,
            "final_plan": None,
            "intervention_mode": "reviewer",
            "current_checkpoint": None,
            "human_feedback_history": [feedback.model_dump()],
            "paused_at": None,
            "revision_count_per_checkpoint": {},
            "checkpoint_snapshots": {},
        }
        
        base_system = "You are Katalizator agent."
        base_user = "Mission: {mission}"
        
        enhanced_sys, enhanced_user = build_agent_prompt_with_feedback(
            state=state,
            agent_id="Katalizator",
            base_system_prompt=base_system,
            base_user_prompt=base_user,
            include_debate_context=False,
        )
        
        # Verify feedback integration
        assert "HUMAN FEEDBACK" in enhanced_sys
        assert "implementation costs" in enhanced_sys.lower()
        assert "Cost-benefit analysis" in enhanced_sys
        
        # Verify mission preserved
        assert "Design microservices platform" in enhanced_user
    
    def test_effectiveness_scoring_realistic_scenario(self) -> None:
        """Realistic effectiveness scoring scenario."""
        original = (
            "The proposed solution uses a microservices architecture. "
            "This will improve scalability."
        )
        
        revised = (
            "The proposed solution uses a microservices architecture with estimated "
            "implementation cost of $120K over 6 months. Initial infrastructure setup "
            "requires $30K, with ongoing operational costs of $15K/month. "
            "This will improve scalability and reduce time-to-market by 40%. "
            "ROI is projected at 18 months based on reduced maintenance costs "
            "and faster feature delivery."
        )
        
        feedback = HumanFeedback(
            checkpoint="post_thesis_cycle_1",
            decision="revise",
            guidance="Add detailed cost analysis, timeline, and ROI projections",
            priority_claims=["Cost breakdown", "ROI analysis"],
        )
        
        result = compute_feedback_effectiveness(original, revised, feedback)
        
        # Should score highly
        assert result["overall"] >= 0.7
        assert result["interpretation"] in ["Good", "Excellent"]
        assert result["structural"] > 0.5  # Significant expansion
        assert result["keyword_match"] > 0.6  # Keywords present
    
    def test_contradiction_detection_across_cycles(self) -> None:
        """Detect contradictions across multiple debate cycles."""
        feedbacks = [
            HumanFeedback(
                checkpoint="post_thesis_cycle_1",
                decision="revise",
                guidance="Make the plan more aggressive with faster timelines",
            ),
            HumanFeedback(
                checkpoint="post_evaluation_cycle_1",
                decision="approve",
                guidance="Good balance",
            ),
            HumanFeedback(
                checkpoint="post_thesis_cycle_2",
                decision="revise",
                guidance="Be more conservative and careful with timelines",
            ),
        ]
        
        contradictions = detect_feedback_contradictions(feedbacks)
        
        # Should detect aggressive vs conservative
        assert len(contradictions) > 0
        
        # Generate report
        report = generate_contradiction_report(contradictions)
        assert "aggressive" in report.lower() or "conservative" in report.lower()


# ============================================================================
# Edge Cases and Error Handling
# ============================================================================

class TestEdgeCases:
    """Test edge cases and error handling."""
    
    def test_empty_strings_structural_score(self) -> None:
        """Empty strings return 0.0 score."""
        score = compute_structural_change_score("", "")
        assert score == 0.0
        
        score = compute_structural_change_score("text", "")
        assert score == 0.0
    
    def test_very_short_texts(self) -> None:
        """Very short texts handled correctly."""
        score = compute_structural_change_score("a", "b")
        assert 0.0 <= score <= 1.0
    
    def test_unicode_handling(self) -> None:
        """Unicode characters handled correctly."""
        original = "Testowanie z polskimi znakami: ąćęłńóśźż"
        revised = "Testing with special chars: äöü"
        
        score = compute_structural_change_score(original, revised)
        assert 0.0 <= score <= 1.0
    
    def test_feedback_with_empty_lists(self) -> None:
        """Feedback with empty priority_claims and flagged_concerns."""
        feedback = HumanFeedback(
            checkpoint="post_thesis_cycle_1",
            decision="approve",
            priority_claims=[],
            flagged_concerns=[],
        )
        
        state: DebateState = {
            "mission": "Test",
            "contributions": [],
            "cycle_count": 1,
            "current_consensus_score": 0.0,
            "final_plan": None,
            "intervention_mode": "reviewer",
            "current_checkpoint": None,
            "human_feedback_history": [feedback.model_dump()],
            "paused_at": None,
            "revision_count_per_checkpoint": {},
            "checkpoint_snapshots": {},
        }
        
        # Should not crash
        context = build_feedback_context_for_agent(state, "Katalizator")
        assert isinstance(context, str)