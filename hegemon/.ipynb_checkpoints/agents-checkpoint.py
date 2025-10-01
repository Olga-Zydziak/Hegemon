"""
HEGEMON Cognitive Agents - Multi-Provider Support.

Google Gemini ALWAYS uses Vertex AI (no API key needed).
"""

from __future__ import annotations

import logging
from typing import Any

from langchain_anthropic import ChatAnthropic
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_google_vertexai import ChatVertexAI  # ← VERTEX AI (ADC)
from langchain_openai import ChatOpenAI

from hegemon.config import (
    get_agent_config,
    get_api_key_for_provider,
    get_settings,
    get_system_prompt,
    get_user_prompt_template,
)
from hegemon.schemas import (
    AgentContribution,
    DebateState,
    FinalPlan,
    GovernorEvaluation,
)

logger = logging.getLogger(__name__)
from hegemon.explainability import ExplainabilityCollector, ConceptClassifier
from hegemon.config.settings import get_settings

# Singleton collector instance
from hegemon.explainability import ExplainabilityCollector, ConceptClassifier

# Singleton collector instance
_explainability_collector: ExplainabilityCollector | None = None


def get_explainability_collector() -> ExplainabilityCollector | None:
    """
    Get or create singleton ExplainabilityCollector.
    
    Uses Vertex AI (no API key required - uses Application Default Credentials).
    
    Returns:
        Collector instance or None if explainability disabled
        
    Complexity: O(1) after first call
    """
    global _explainability_collector
    
    settings = get_settings()
    
    if not settings.explainability_enabled:
        return None
    
    if _explainability_collector is None:
        # Initialize classifier with Vertex AI credentials
        try:
            classifier = ConceptClassifier(
                project_id=settings.gcp_project_id,
                location=settings.gcp_location,
                model_name=settings.explainability_classifier_model,
                cache_size=settings.explainability_cache_size,
            )
            
            _explainability_collector = ExplainabilityCollector(
                settings=settings,
                classifier=classifier,
            )
            
            logger.info(
                f"✅ Explainability collector initialized: "
                f"Vertex AI {settings.explainability_classifier_model} "
                f"(project={settings.gcp_project_id}, location={settings.gcp_location})"
            )
        except Exception as e:
            logger.error(f"❌ Failed to initialize explainability: {e}")
            return None
    
    return _explainability_collector


# ============================================================================
# LLM Factory (Multi-Provider with Vertex AI ONLY)
# ============================================================================

def get_llm_for_agent(agent_name: str) -> BaseChatModel:
    """
    Factory function for creating LLM instances.
    
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
# Nodes (unchanged)
# ============================================================================

def katalizator_node(state: DebateState) -> dict[str, Any]:
    """Katalizator Node - Claude Sonnet 4.5."""
    cycle = state["cycle_count"]
    config = get_agent_config("Katalizator")
    
    logger.info(
        f"🔥 KATALIZATOR ({config.provider}/{config.model}): "
        f"Generating Thesis (Cycle {cycle})"
    )
    
    system_prompt = get_system_prompt("Katalizator")
    user_prompt_template = get_user_prompt_template("Katalizator")
    
    previous_contributions = state.get("contributions", [])
    
    if previous_contributions:
        context_parts = []
        for contrib in previous_contributions[-4:]:
            context_parts.append(
                f"{contrib.agent_id} ({contrib.type}, Cycle {contrib.cycle}):\n"
                f"{contrib.content[:200]}..."
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
    
    logger.info(f"✅ KATALIZATOR: Thesis generated ({len(thesis_content)} chars)")
    
    explainability_bundle = None
    collector = get_explainability_collector()
    if collector is not None:
        explainability_bundle = collector.collect(
            agent_id="Katalizator",
            content=thesis_content,
            cycle=cycle
        )
    
    
    contribution = AgentContribution(
        agent_id="Katalizator",
        content=thesis_content,
        type="Thesis",
        cycle=cycle,
        rationale=rationale,
    )
    
    return {"contributions": [contribution]}


def sceptyk_node(state: DebateState) -> dict[str, Any]:
    """Sceptyk Node - Gemini 2.0 Flash via Vertex AI."""
    cycle = state["cycle_count"]
    config = get_agent_config("Sceptyk")
    
    logger.info(
        f"⚔️ SCEPTYK ({config.provider}/{config.model} via Vertex AI): "
        f"Generating Antithesis (Cycle {cycle})"
    )
    
    system_prompt = get_system_prompt("Sceptyk")
    user_prompt_template = get_user_prompt_template("Sceptyk")
    
    contributions = state.get("contributions", [])
    catalyst_contributions = [
        c for c in contributions
        if c.agent_id == "Katalizator" and c.type == "Thesis"
    ]
    
    if not catalyst_contributions:
        logger.error("❌ SCEPTYK: No thesis from Katalizator found!")
        error_contribution = AgentContribution(
            agent_id="Sceptyk",
            content="ERROR: No thesis to critique.",
            type="Antithesis",
            cycle=cycle,
            rationale="Workflow error - missing thesis.",
        )
        return {"contributions": [error_contribution]}
    
    latest_thesis = catalyst_contributions[-1].content
    
    user_prompt = user_prompt_template.format(
        mission=state["mission"],
        thesis=latest_thesis
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
    
    logger.info(f"✅ SCEPTYK: Antithesis generated ({len(antithesis_content)} chars)")
    
    
    
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
    )
    
    return {"contributions": [contribution]}


def gubernator_node(state: DebateState) -> dict[str, Any]:
    """Gubernator Node - Claude Sonnet 4.5 (with structured output)."""
    cycle = state["cycle_count"]
    config = get_agent_config("Gubernator")
    
    logger.info(
        f"⚖️ GUBERNATOR ({config.provider}/{config.model}): "
        f"Evaluating Consensus (Cycle {cycle})"
    )
    
    system_prompt = get_system_prompt("Gubernator")
    user_prompt_template = get_user_prompt_template("Gubernator")
    
    contributions = state.get("contributions", [])
    debate_context = "\n\n".join(
        [
            f"[Cycle {c.cycle}] {c.agent_id} ({c.type}):\n{c.content}"
            for c in contributions
        ]
    )
    
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
    
    # IMPORTANT: Define ALL variables BEFORE explainability collection
    evaluation_content = (
        f"{evaluation.evaluation_summary}\n\n"
        f"Consensus Score: {evaluation.consensus_score:.2f}\n"
        f"Rationale: {evaluation.rationale}"
    )
    
    rationale = (
        f"Evaluated using {config.provider}/{config.model}. "
        f"Consensus: {evaluation.consensus_score:.2f}"
    )
    
    logger.info(
        f"✅ GUBERNATOR: Consensus Score = {evaluation.consensus_score:.2f}"
    )
    
    # NEW: Collect explainability (after all variables are defined)
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
        rationale=rationale,  # Now this variable exists
        explainability=explainability_bundle,
    )
    
    return {
        "contributions": [contribution],
        "current_consensus_score": evaluation.consensus_score,
    }


def syntezator_node(state: DebateState) -> dict[str, Any]:
    """Syntezator Node - Claude Sonnet 4.5 (with structured output)."""
    cycle = state["cycle_count"]
    config = get_agent_config("Syntezator")
    
    logger.info(
        f"🔮 SYNTEZATOR ({config.provider}/{config.model}): "
        f"Generating Final Plan (Cycle {cycle})"
    )
    
    system_prompt = get_system_prompt("Syntezator")
    user_prompt_template = get_user_prompt_template("Syntezator")
    
    contributions = state.get("contributions", [])
    debate_parts = []
    
    for contrib in contributions:
        debate_parts.append(
            f"{'='*80}\n"
            f"{contrib.agent_id} ({contrib.type}, Cycle {contrib.cycle}):\n"
            f"{contrib.content}\n\n"
            f"Rationale: {contrib.rationale}"
        )
    
    debate_context = "\n\n".join(debate_parts)
    
    user_prompt = user_prompt_template.format(
        mission=state["mission"],
        debate_context=debate_context,
        consensus_score=state["current_consensus_score"]
    )
    
    llm = get_llm_for_agent("Syntezator")
    llm_with_structure = llm.with_structured_output(FinalPlan)
    
    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=user_prompt),
    ]
    
    final_plan: FinalPlan = llm_with_structure.invoke(messages)
    
    logger.info(
        f"✅ SYNTEZATOR: Plan generated "
        f"({len(final_plan.required_agents)} agents, "
        f"{len(final_plan.workflow)} steps)"
    )
    plan_content = (
    f"Mission Overview: {final_plan.mission_overview}\n\n"
    f"Required Agents ({len(final_plan.required_agents)}):\n"
    + "\n".join([f"- {a.role}: {a.description}" for a in final_plan.required_agents])
    + f"\n\nWorkflow ({len(final_plan.workflow)} steps):\n"
    + "\n".join([f"{s.step_id}. {s.description}" for s in final_plan.workflow])
    + f"\n\nRisk Analysis: {final_plan.risk_analysis}"
    )
    
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
        content=plan_content,  # ← ZMIANA: użyj plan_content
        type="FinalPlan",
        cycle=cycle,
        rationale=rationale,
        explainability=explainability_bundle,
    )
    
    return {
        "final_plan": final_plan,
        "contributions": [contribution],
    }