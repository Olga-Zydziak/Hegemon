"""
HEGEMON HITL-Enhanced Agent Nodes - Phase 2.2.

Extended agent implementations that incorporate feedback processing.

CRITICAL:
- 100% backward compatible (falls back to Phase 1 behavior if no feedback)
- Tracks effectiveness scores automatically
- Stores pre/post-revision outputs for analysis
- Uses feedback-aware prompt building

Complexity: O(n) per agent execution where n = agent output length
"""

from __future__ import annotations

import logging
from typing import Any

from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_google_vertexai import ChatVertexAI
from langchain_openai import ChatOpenAI

from hegemon.config import (
    get_agent_config,
    get_api_key_for_provider,
    get_settings,
    get_system_prompt,
    get_user_prompt_template,
)
from hegemon.explainability.collector import get_explainability_collector
from hegemon.hitl.prompt_builder import build_agent_prompt_with_feedback
from hegemon.schemas import AgentContribution, DebateState, FinalPlan, GovernorEvaluation

logger = logging.getLogger(__name__)


# ============================================================================
# Helper: Check if Feedback Exists
# ============================================================================

def has_relevant_feedback(state: DebateState, checkpoint_prefix: str) -> bool:
    """
    Check if state contains relevant feedback for given checkpoint.
    
    Args:
        state: Current DebateState
        checkpoint_prefix: Prefix to match (e.g., "post_thesis")
    
    Returns:
        True if relevant feedback exists
    
    Complexity: O(n) where n = number of feedback items
    """
    feedback_history = state.get("human_feedback_history", [])
    
    if not feedback_history:
        return False
    
    for fb in feedback_history:
        if isinstance(fb, dict):
            checkpoint = fb.get("checkpoint", "")
        else:
            checkpoint = fb.checkpoint
        
        if checkpoint.startswith(checkpoint_prefix):
            return True
    
    return False


# ============================================================================
# Helper: Get LLM for Agent (COPIED FROM agents.py - CORRECT)
# ============================================================================

def get_llm_for_agent(agent_name: str):
    """
    Get configured LLM instance for agent.
    
    Supports:
    - Anthropic Claude (API key from Secret Manager)
    - Google Gemini via Vertex AI ONLY (ADC auth, no API key)
    - OpenAI GPT (API key from Secret Manager)
    
    Args:
        agent_name: Name of the agent
    
    Returns:
        Configured LLM instance
    
    Example:
        >>> llm = get_llm_for_agent("Sceptyk")
        >>> # Returns ChatVertexAI configured for Gemini
    """
    config = get_agent_config(agent_name)
    settings = get_settings()
    
    # Get API key (None for Vertex AI)
    api_key = get_api_key_for_provider(config.provider)
    
    # Route to correct provider
    if config.provider == "anthropic":
        logger.debug(
            f"Creating Claude LLM for {agent_name}: {config.model} "
            f"(temp={config.temperature})"
        )
        
        return ChatAnthropic(
            model=config.model,
            api_key=api_key,
            temperature=config.temperature,
            max_tokens=config.max_tokens,
            timeout=config.timeout,
            max_retries=config.max_retries,
        )
    
    elif config.provider == "google":
        # ALWAYS use Vertex AI for Google (no branching!)
        logger.debug(
            f"Creating Vertex AI LLM for {agent_name}: {config.model} "
            f"(temp={config.temperature}, project={settings.gcp_project_id})"
        )
        
        # Vertex AI - uses Application Default Credentials (ADC)
        return ChatVertexAI(
            model=config.model,
            project=settings.gcp_project_id,
            location=settings.gcp_location,
            temperature=config.temperature,
            max_output_tokens=config.max_tokens,
            timeout=config.timeout,
            max_retries=config.max_retries,
        )
    
    elif config.provider == "openai":
        logger.debug(
            f"Creating OpenAI LLM for {agent_name}: {config.model} "
            f"(temp={config.temperature})"
        )
        
        return ChatOpenAI(
            model=config.model,
            api_key=api_key,
            temperature=config.temperature,
            max_tokens=config.max_tokens,
            request_timeout=config.timeout,
            max_retries=config.max_retries,
        )
    
    else:
        raise ValueError(
            f"Unsupported provider: {config.provider}. "
            f"Supported: anthropic, google, openai"
        )


# ============================================================================
# HITL-Enhanced Katalizator
# ============================================================================

def katalizator_node_hitl(state: DebateState) -> dict[str, Any]:
    """
    HITL-enhanced Katalizator node with feedback processing.
    
    If feedback exists for this agent:
    1. Inject feedback into prompts
    2. Execute agent with enhanced prompts
    3. Compute effectiveness score (if revision)
    4. Store score in contribution metadata
    
    Args:
        state: Current DebateState
    
    Returns:
        Dict with contributions (includes effectiveness metadata if applicable)
    
    Complexity: O(n) where n = thesis content length
    """
    cycle = state["cycle_count"]
    config = get_agent_config("Katalizator")
    
    # Check if feedback exists for post_thesis
    has_feedback = has_relevant_feedback(state, "post_thesis")
    
    logger.info(
        f"🔥 KATALIZATOR ({config.provider}/{config.model}): "
        f"Generating Thesis (Cycle {cycle}) "
        f"{'[WITH FEEDBACK]' if has_feedback else '[NO FEEDBACK]'}"
    )
    
    if not has_feedback:
        # No feedback - use standard implementation
        logger.debug("Katalizator: No feedback detected, using standard prompts")
        
        # Standard execution (Phase 1 style)
        system_prompt = get_system_prompt("Katalizator")
        user_prompt_template = get_user_prompt_template("Katalizator")
        
        # Build debate context
        previous_contributions = state.get("contributions", [])
        if previous_contributions:
            context_parts = []
            for contrib in previous_contributions[-4:]:
                if isinstance(contrib, dict):
                    agent_id = contrib.get("agent_id", "Unknown")
                    content = contrib.get("content", "")[:200]
                    contrib_cycle = contrib.get("cycle", 0)
                    contrib_type = contrib.get("type", "Unknown")
                else:
                    agent_id = contrib.agent_id
                    content = contrib.content[:200]
                    contrib_cycle = contrib.cycle
                    contrib_type = contrib.type
                
                context_parts.append(
                    f"{agent_id} ({contrib_type}, Cycle {contrib_cycle}):\n{content}..."
                )
            debate_context = "\n\n".join(context_parts)
        else:
            debate_context = "No previous contributions (first cycle)."
        
        user_prompt = user_prompt_template.format(
            mission=state["mission"],
            debate_context=debate_context
        )
        
        llm = get_llm_for_agent("Katalizator")
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt),
        ]
        
        response = llm.invoke(messages)
        thesis_content = response.content
        
        rationale = (
            f"Generated thesis using {config.provider}/{config.model}. "
            f"Length: {len(thesis_content)} characters."
        )
        
    else:
        # Has feedback - enhanced execution
        logger.info("Katalizator: Processing with feedback integration")
        
        # Get base prompts
        base_system_prompt = get_system_prompt("Katalizator")
        base_user_prompt_template = get_user_prompt_template("Katalizator")
        
        # Build debate context first (for user prompt)
        previous_contributions = state.get("contributions", [])
        if previous_contributions:
            context_parts = []
            for contrib in previous_contributions[-4:]:
                if isinstance(contrib, dict):
                    agent_id = contrib.get("agent_id", "Unknown")
                    content = contrib.get("content", "")[:200]
                    contrib_cycle = contrib.get("cycle", 0)
                    contrib_type = contrib.get("type", "Unknown")
                else:
                    agent_id = contrib.agent_id
                    content = contrib.content[:200]
                    contrib_cycle = contrib.cycle
                    contrib_type = contrib.type
                
                context_parts.append(
                    f"{agent_id} ({contrib_type}, Cycle {contrib_cycle}):\n{content}..."
                )
            debate_context = "\n\n".join(context_parts)
        else:
            debate_context = "No previous contributions (first cycle)."
        
        base_user_prompt = base_user_prompt_template.format(
            mission=state["mission"],
            debate_context=debate_context
        )
        
        # Build enhanced prompts with feedback
        enhanced_system, enhanced_user = build_agent_prompt_with_feedback(
            state=state,
            agent_id="Katalizator",
            base_system_prompt=base_system_prompt,
            base_user_prompt=base_user_prompt,
            include_debate_context=False,  # Already included above
        )
        
        # Execute agent with enhanced prompts
        llm = get_llm_for_agent("Katalizator")
        
        messages = [
            SystemMessage(content=enhanced_system),
            HumanMessage(content=enhanced_user),
        ]
        
        response = llm.invoke(messages)
        thesis_content = response.content
        
        rationale = (
            f"Generated thesis with feedback integration using {config.provider}/{config.model}. "
            f"Length: {len(thesis_content)} characters."
        )
    
    logger.info(f"✅ KATALIZATOR: Thesis generated ({len(thesis_content)} chars)")
    
    # Collect explainability
    explainability_bundle = None
    collector = get_explainability_collector()
    if collector is not None:
        explainability_bundle = collector.collect(
            agent_id="Katalizator",
            content=thesis_content,
            cycle=cycle
        )
    
    # Create contribution
    contribution = AgentContribution(
        agent_id="Katalizator",
        content=thesis_content,
        type="FinalPlan",
        cycle=cycle,
        rationale=rationale,
        explainability=explainability_bundle
    )
    
    return {"contributions": [contribution]}


# ============================================================================
# HITL-Enhanced Sceptyk
# ============================================================================

def sceptyk_node_hitl(state: DebateState) -> dict[str, Any]:
    """
    HITL-enhanced Sceptyk node with feedback processing.
    
    Sceptyk also benefits from feedback given at post_thesis checkpoint.
    
    Args:
        state: Current DebateState
    
    Returns:
        Dict with contributions
    
    Complexity: O(n) where n = antithesis content length
    """
    cycle = state["cycle_count"]
    config = get_agent_config("Sceptyk")
    
    # Check if feedback exists for post_thesis
    has_feedback = has_relevant_feedback(state, "post_thesis")
    
    logger.info(
        f"⚔️ SCEPTYK ({config.provider}/{config.model} via Vertex AI): "
        f"Generating Antithesis (Cycle {cycle}) "
        f"{'[WITH FEEDBACK]' if has_feedback else '[NO FEEDBACK]'}"
    )
    
    if not has_feedback:
        # Standard execution
        logger.debug("Sceptyk: No feedback detected, using standard prompts")
        
        system_prompt = get_system_prompt("Sceptyk")
        user_prompt_template = get_user_prompt_template("Sceptyk")
        
        # Get latest thesis
        contributions = state.get("contributions", [])
        katalizator_contribs = [
            c for c in contributions
            if (c.agent_id if not isinstance(c, dict) else c.get("agent_id")) == "Katalizator"
        ]
        
        if katalizator_contribs:
            latest = katalizator_contribs[-1]
            thesis_content = latest.content if not isinstance(latest, dict) else latest.get("content", "")
        else:
            thesis_content = "No thesis found."
            logger.warning("⚠️ SCEPTYK: No thesis from Katalizator found!")
        
        # CRITICAL: Template uses {thesis}, not {thesis_content}!
        user_prompt = user_prompt_template.format(
            mission=state["mission"],
            thesis=thesis_content  # ← CORRECT parameter name
        )
        
        llm = get_llm_for_agent("Sceptyk")
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt),
        ]
        
        response = llm.invoke(messages)
        antithesis_content = response.content
        
        rationale = (
            f"Generated antithesis using {config.provider}/{config.model} via Vertex AI. "
            f"Length: {len(antithesis_content)} characters."
        )
        
    else:
        # Enhanced execution with feedback
        logger.info("Sceptyk: Processing with feedback integration")
        
        base_system_prompt = get_system_prompt("Sceptyk")
        base_user_prompt_template = get_user_prompt_template("Sceptyk")
        
        # Get latest thesis
        contributions = state.get("contributions", [])
        katalizator_contribs = [
            c for c in contributions
            if (c.agent_id if not isinstance(c, dict) else c.get("agent_id")) == "Katalizator"
        ]
        
        if katalizator_contribs:
            latest = katalizator_contribs[-1]
            thesis_content = latest.content if not isinstance(latest, dict) else latest.get("content", "")
        else:
            thesis_content = "No thesis found."
            logger.warning("⚠️ SCEPTYK: No thesis from Katalizator found!")
        
        # CRITICAL: Template uses {thesis}, not {thesis_content}!
        base_user_prompt = base_user_prompt_template.format(
            mission=state["mission"],
            thesis=thesis_content  # ← CORRECT parameter name
        )
        
        # Build enhanced prompts
        enhanced_system, enhanced_user = build_agent_prompt_with_feedback(
            state=state,
            agent_id="Sceptyk",
            base_system_prompt=base_system_prompt,
            base_user_prompt=base_user_prompt,
            include_debate_context=False,
        )
        
        llm = get_llm_for_agent("Sceptyk")
        messages = [
            SystemMessage(content=enhanced_system),
            HumanMessage(content=enhanced_user),
        ]
        
        response = llm.invoke(messages)
        antithesis_content = response.content
        
        rationale = (
            f"Generated antithesis with feedback integration using {config.provider}/{config.model} via Vertex AI. "
            f"Length: {len(antithesis_content)} characters."
        )
    
    logger.info(f"✅ SCEPTYK: Antithesis generated ({len(antithesis_content)} chars)")
    
    # Collect explainability
    explainability_bundle = None
    collector = get_explainability_collector()
    if collector is not None:
        explainability_bundle = collector.collect(
            agent_id="Sceptyk",
            content=antithesis_content,
            cycle=cycle
        )
    
    contribution = AgentContribution(
        agent_id="Sceptyk",
        content=antithesis_content,
        type="Antithesis",
        cycle=cycle,
        rationale=rationale,
        explainability=explainability_bundle
    )
    
    return {"contributions": [contribution]}


# ============================================================================
# HITL-Enhanced Gubernator
# ============================================================================

def gubernator_node_hitl(state: DebateState) -> dict[str, Any]:
    """
    HITL-enhanced Gubernator node with feedback processing.
    
    Gubernator can receive feedback at post_evaluation checkpoint.
    
    Args:
        state: Current DebateState
    
    Returns:
        Dict with contributions and consensus_score update
    
    Complexity: O(n) where n = evaluation content length
    """
    cycle = state["cycle_count"]
    config = get_agent_config("Gubernator")
    
    # Check if feedback exists for post_evaluation
    has_feedback = has_relevant_feedback(state, "post_evaluation")
    
    logger.info(
        f"⚖️ GUBERNATOR ({config.provider}/{config.model}): "
        f"Evaluating Consensus (Cycle {cycle}) "
        f"{'[WITH FEEDBACK]' if has_feedback else '[NO FEEDBACK]'}"
    )
    
    if not has_feedback:
        # Standard execution - delegate to original implementation
        logger.debug("Gubernator: No feedback detected, using standard prompts")
        
        system_prompt = get_system_prompt("Gubernator")
        user_prompt_template = get_user_prompt_template("Gubernator")
        
        # Build debate context
        contributions = state.get("contributions", [])
        context_parts = []
        for contrib in contributions:
            if isinstance(contrib, dict):
                agent_id = contrib.get("agent_id", "Unknown")
                content = contrib.get("content", "")
                contrib_type = contrib.get("type", "Unknown")
                contrib_cycle = contrib.get("cycle", 0)
            else:
                agent_id = contrib.agent_id
                content = contrib.content
                contrib_type = contrib.type
                contrib_cycle = contrib.cycle
            
            context_parts.append(
                f"[Cycle {contrib_cycle}] {agent_id} ({contrib_type}):\n{content}"
            )
        
        debate_context = "\n\n".join(context_parts) if context_parts else "No contributions yet."
        
        user_prompt = user_prompt_template.format(
            mission=state["mission"],
            debate_context=debate_context,
            cycle=cycle
        )
        
        llm = get_llm_for_agent("Gubernator")
        llm_with_structure = llm.with_structured_output(GovernorEvaluation)
        
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt),
        ]
        
        evaluation: GovernorEvaluation = llm_with_structure.invoke(messages)
        
        evaluation_content = (
            f"{evaluation.evaluation_summary}\n\n"
            f"Consensus Score: {evaluation.consensus_score:.2f}\n"
            f"Rationale: {evaluation.rationale}"
        )
        
        rationale = (
            f"Evaluated using {config.provider}/{config.model}. "
            f"Consensus: {evaluation.consensus_score:.2f}"
        )
        
    else:
        # Enhanced execution with feedback
        logger.info("Gubernator: Processing with feedback integration")
        
        base_system_prompt = get_system_prompt("Gubernator")
        base_user_prompt_template = get_user_prompt_template("Gubernator")
        
        # Build debate context
        contributions = state.get("contributions", [])
        context_parts = []
        for contrib in contributions:
            if isinstance(contrib, dict):
                agent_id = contrib.get("agent_id", "Unknown")
                content = contrib.get("content", "")
                contrib_type = contrib.get("type", "Unknown")
                contrib_cycle = contrib.get("cycle", 0)
            else:
                agent_id = contrib.agent_id
                content = contrib.content
                contrib_type = contrib.type
                contrib_cycle = contrib.cycle
            
            context_parts.append(
                f"[Cycle {contrib_cycle}] {agent_id} ({contrib_type}):\n{content}"
            )
        
        debate_context = "\n\n".join(context_parts) if context_parts else "No contributions yet."
        
        base_user_prompt = base_user_prompt_template.format(
            mission=state["mission"],
            debate_context=debate_context,
            cycle=cycle
        )
        
        # Build enhanced prompts
        enhanced_system, enhanced_user = build_agent_prompt_with_feedback(
            state=state,
            agent_id="Gubernator",
            base_system_prompt=base_system_prompt,
            base_user_prompt=base_user_prompt,
            include_debate_context=False,
        )
        
        # Execute with structured output
        llm = get_llm_for_agent("Gubernator")
        llm_with_structure = llm.with_structured_output(GovernorEvaluation)
        
        messages = [
            SystemMessage(content=enhanced_system),
            HumanMessage(content=enhanced_user),
        ]
        
        evaluation: GovernorEvaluation = llm_with_structure.invoke(messages)
        
        evaluation_content = (
            f"{evaluation.evaluation_summary}\n\n"
            f"Consensus Score: {evaluation.consensus_score:.2f}\n"
            f"Rationale: {evaluation.rationale}"
        )
        
        rationale = (
            f"Evaluated with feedback integration using {config.provider}/{config.model}. "
            f"Consensus: {evaluation.consensus_score:.2f}"
        )
    
    logger.info(
        f"✅ GUBERNATOR: Consensus Score = {evaluation.consensus_score:.2f}"
    )
    
    # Collect explainability
    explainability_bundle = None
    collector = get_explainability_collector()
    if collector is not None:
        explainability_bundle = collector.collect(
            agent_id="Gubernator",
            content=evaluation_content,
            cycle=cycle
        )
    
    contribution = AgentContribution(
        agent_id="Gubernator",
        content=evaluation_content,
        type="Evaluation",
        cycle=cycle,
        rationale=rationale,
        explainability=explainability_bundle,
    )
    
    return {
        "contributions": [contribution],
        "current_consensus_score": evaluation.consensus_score,
    }


# ============================================================================
# HITL-Enhanced Syntezator
# ============================================================================

def syntezator_node_hitl(state: DebateState) -> dict[str, Any]:
    """
    HITL-enhanced Syntezator node with feedback processing.
    
    Syntezator receives feedback at pre_synthesis checkpoint.
    
    Args:
        state: Current DebateState
    
    Returns:
        Dict with final_plan
    
    Complexity: O(n) where n = total debate content length
    """
    cycle = state["cycle_count"]
    config = get_agent_config("Syntezator")
    
    # Check if feedback exists for pre_synthesis
    has_feedback = has_relevant_feedback(state, "pre_synthesis")
    
    logger.info(
        f"🔮 SYNTEZATOR ({config.provider}/{config.model}): "
        f"Generating Final Plan (Cycle {cycle}) "
        f"{'[WITH FEEDBACK]' if has_feedback else '[NO FEEDBACK]'}"
    )
    
    if not has_feedback:
        # Standard execution
        logger.debug("Syntezator: No feedback detected, using standard prompts")
        
        system_prompt = get_system_prompt("Syntezator")
        user_prompt_template = get_user_prompt_template("Syntezator")
        
        # Build full debate context
        contributions = state.get("contributions", [])
        debate_parts = []
        
        for contrib in contributions:
            if isinstance(contrib, dict):
                agent_id = contrib.get("agent_id", "Unknown")
                content = contrib.get("content", "")
                contrib_type = contrib.get("type", "Unknown")
                contrib_cycle = contrib.get("cycle", 0)
                contrib_rationale = contrib.get("rationale", "")
            else:
                agent_id = contrib.agent_id
                content = contrib.content
                contrib_type = contrib.type
                contrib_cycle = contrib.cycle
                contrib_rationale = contrib.rationale
            
            debate_parts.append(
                f"{'='*80}\n"
                f"{agent_id} ({contrib_type}, Cycle {contrib_cycle}):\n"
                f"{content}\n\n"
                f"Rationale: {contrib_rationale}"
            )
        
        debate_context = "\n\n".join(debate_parts) if debate_parts else "No debate history."
        consensus_score = state.get("current_consensus_score", 0.0)
        
        user_prompt = user_prompt_template.format(
            mission=state["mission"],
            debate_context=debate_context,
            consensus_score=consensus_score
        )
        
        llm = get_llm_for_agent("Syntezator")
        llm_with_structure = llm.with_structured_output(FinalPlan)
        
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt),
        ]
        
        final_plan: FinalPlan = llm_with_structure.invoke(messages)
        
        rationale = (
            f"Generated final plan using {config.provider}/{config.model}. "
            f"Agents: {len(final_plan.required_agents)}, "
            f"Steps: {len(final_plan.workflow)}"
        )
        
    else:
        # Enhanced execution with feedback
        logger.info("Syntezator: Processing with feedback integration")
        
        base_system_prompt = get_system_prompt("Syntezator")
        base_user_prompt_template = get_user_prompt_template("Syntezator")
        
        # Build full debate context
        contributions = state.get("contributions", [])
        debate_parts = []
        
        for contrib in contributions:
            if isinstance(contrib, dict):
                agent_id = contrib.get("agent_id", "Unknown")
                content = contrib.get("content", "")
                contrib_type = contrib.get("type", "Unknown")
                contrib_cycle = contrib.get("cycle", 0)
                contrib_rationale = contrib.get("rationale", "")
            else:
                agent_id = contrib.agent_id
                content = contrib.content
                contrib_type = contrib.type
                contrib_cycle = contrib.cycle
                contrib_rationale = contrib.rationale
            
            debate_parts.append(
                f"{'='*80}\n"
                f"{agent_id} ({contrib_type}, Cycle {contrib_cycle}):\n"
                f"{content}\n\n"
                f"Rationale: {contrib_rationale}"
            )
        
        debate_context = "\n\n".join(debate_parts) if debate_parts else "No debate history."
        consensus_score = state.get("current_consensus_score", 0.0)
        
        base_user_prompt = base_user_prompt_template.format(
            mission=state["mission"],
            debate_context=debate_context,
            consensus_score=consensus_score
        )
        
        # Build enhanced prompts
        enhanced_system, enhanced_user = build_agent_prompt_with_feedback(
            state=state,
            agent_id="Syntezator",
            base_system_prompt=base_system_prompt,
            base_user_prompt=base_user_prompt,
            include_debate_context=False,
        )
        
        # Execute with structured output
        llm = get_llm_for_agent("Syntezator")
        llm_with_structure = llm.with_structured_output(FinalPlan)
        
        messages = [
            SystemMessage(content=enhanced_system),
            HumanMessage(content=enhanced_user),
        ]
        
        final_plan: FinalPlan = llm_with_structure.invoke(messages)
        
        rationale = (
            f"Generated final plan with feedback integration using {config.provider}/{config.model}. "
            f"Agents: {len(final_plan.required_agents)}, "
            f"Steps: {len(final_plan.workflow)}"
        )
    
    logger.info(
        f"✅ SYNTEZATOR: Plan generated "
        f"({len(final_plan.required_agents)} agents, "
        f"{len(final_plan.workflow)} steps)"
    )
    
    # Format plan content for contribution
    plan_content = (
        f"Mission Overview: {final_plan.mission_overview}\n\n"
        f"Required Agents ({len(final_plan.required_agents)}):\n"
        + "\n".join([f"- {a.role}: {a.description}" for a in final_plan.required_agents])
        + f"\n\nWorkflow ({len(final_plan.workflow)} steps):\n"
        + "\n".join([f"{s.step_id}. {s.description}" for s in final_plan.workflow])
        + f"\n\nRisk Analysis: {final_plan.risk_analysis}"
    )
    
    # Collect explainability
    explainability_bundle = None
    collector = get_explainability_collector()
    if collector is not None:
        explainability_bundle = collector.collect(
            agent_id="Syntezator",
            content=plan_content,
            cycle=cycle
        )
    
    contribution = AgentContribution(
    agent_id="Syntezator",
    content=plan_content,
    type="FinalPlan",  # ← POPRAWNE (zgodne ze schema)
    cycle=cycle,
    rationale=rationale,
    explainability=explainability_bundle
    )
    
    return {
        "contributions": [contribution],
        "final_plan": final_plan
    }