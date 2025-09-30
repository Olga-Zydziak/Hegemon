"""
HEGEMON Cognitive Agents (Węzły Grafu).

Implementacja 4 agentów MVP uczestniczących w cyklu dialektycznego bootstrappingu:
1. Katalizator: Generuje Tezę (initial proposal)
2. Sceptyk: Generuje Antytezę (critical counter-arguments)
3. Gubernator: Ocenia konsensus i decyduje o routing-u
4. Syntezator: Produkuje finalny plan strategiczny

KRYTYCZNE:
- Gubernator i Syntezator używają `with_structured_output()` dla Pydantic validation
- Wszystkie agenty zwracają AgentContribution do Blackboard

Complexity:
- Per-node execution: O(1) state mutation + O(LLM) inference time
- Total system: O(max_cycles * 4 * LLM_latency)
"""

from __future__ import annotations

import logging
from typing import Any

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

from hegemon.schemas import (
    AgentContribution,
    DebateState,
    FinalPlan,
    GovernorEvaluation,
)

# Configure structured logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


# ============================================================================
# Agent Base Configuration
# ============================================================================

def get_llm(
    model_name: str = "gpt-4o",
    temperature: float = 0.7,
) -> BaseChatModel:
    """
    Factory function for creating LLM instances.
    
    Args:
        model_name: OpenAI model identifier (default: gpt-4o)
        temperature: Sampling temperature (0.0 = deterministic, 1.0 = creative)
    
    Returns:
        Configured ChatOpenAI instance
    
    Complexity: O(1) - simple object instantiation
    """
    return ChatOpenAI(
        model=model_name,
        temperature=temperature,
        request_timeout=60,  # Prevent hanging on API failures
        max_retries=2,       # Automatic retry on transient failures
    )


# ============================================================================
# Node 1: Katalizator (Thesis Generator)
# ============================================================================

def katalizator_node(state: DebateState) -> dict[str, Any]:
    """
    Węzeł Katalizatora: Generuje Tezę (propozycja strategiczna).
    
    Rola:
        Katalizator jest optymistycznym, forward-thinking agentem, który proponuje
        odważne plany strategiczne. Skupia się na możliwościach i potencjale wzrostu.
    
    Proces:
        1. Analizuje misję i obecny kontekst debaty
        2. Generuje kompleksową tezę (propozycja strategiczna)
        3. Dodaje tezę do contributions jako AgentContribution
    
    Args:
        state: Obecny stan debaty z Blackboard
    
    Returns:
        Aktualizacja stanu z nowym wkładem (AgentContribution)
    
    Complexity: O(1) state operations + O(LLM) inference
    
    Side Effects:
        - Modyfikuje state["contributions"] (akumulowane przez operator.add)
        - Loguje generowanie tezy
    """
    cycle = state["cycle_count"]
    logger.info(f"🔥 KATALIZATOR: Generowanie Tezy (Cykl {cycle})")
    
    # System prompt: Definicja roli poznawczej Katalizatora
    system_prompt = """Jesteś agentem KATALIZATOR w systemie HEGEMON.

Twoja rola to generowanie ODWAŻNYCH, OPTYMISTYCZNYCH propozycji strategicznych (Teza).

Profil Poznawczy:
- Archetyp: Wizjonerski strateg, fokus na możliwościach
- Styl Myślenia: Dywergencyjny, ekspansywny, first-principles reasoning
- Bias: Lekki optymizm (faworyzuj akcję nad bezczynnością)

Instrukcje:
1. Analizuj misję głęboko używając first-principles thinking
2. Generuj kompleksową tezę strategiczną z:
   - Kluczowym insightem strategicznym (dlaczego)
   - 3-5 kluczowymi ruchami strategicznymi
   - Oczekiwanymi rezultatami i potencjałem wzrostu
3. Bądź ambitny ale oparty na wykonalności
4. Uznaj potencjalne wyzwania ale utrzymuj optymistyczne ramy

Ograniczenia:
- Długość odpowiedzi: 200-400 słów
- Format: Jasna, strukturalna proza (bez list w głównej tezie)
- Ton: Pewny ale nie arogancki

Wyprodukuj TYLKO tekst tezy. Bez meta-komentarzy."""
    
    # User prompt: Kontekst misji i historia debaty
    previous_contributions = state.get("contributions", [])
    
    if previous_contributions:
        context_parts = []
        for contrib in previous_contributions[-4:]:  # Ostatnie 4 wkłady
            context_parts.append(
                f"{contrib.agent_id} ({contrib.type}): {contrib.content[:200]}..."
            )
        debate_context = "\n\n".join(context_parts)
    else:
        debate_context = "Brak wcześniejszych wkładów (pierwszy cykl)."
    
    user_prompt = f"""Misja: {state['mission']}

Obecny Kontekst Debaty (ostatnie wkłady):
{debate_context}

Generuj swoją TEZĘ (propozycja strategiczna) dla tej misji."""
    
    # LLM invocation
    llm = get_llm(temperature=0.8)  # Wyższa temperatura dla kreatywności
    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=user_prompt),
    ]
    
    response = llm.invoke(messages)
    thesis_content = response.content
    
    # Uzasadnienie (rationale)
    rationale = (
        f"Wygenerowano ambitną tezę bazującą na first-principles analysis misji. "
        f"Teza ma długość {len(thesis_content)} znaków i proponuje odważne podejście "
        f"uwzględniając kontekst {len(previous_contributions)} wcześniejszych wkładów."
    )
    
    logger.info(f"✅ KATALIZATOR: Teza wygenerowana ({len(thesis_content)} znaków)")
    
    # Tworzenie AgentContribution
    contribution = AgentContribution(
        agent_id="Katalizator",
        content=thesis_content,
        type="Thesis",
        cycle=cycle,
        rationale=rationale,
    )
    
    # Return state update (zostanie zmergowany przez operator.add)
    return {
        "contributions": [contribution],
    }


# ============================================================================
# Node 2: Sceptyk (Antithesis Generator)
# ============================================================================

def sceptyk_node(state: DebateState) -> dict[str, Any]:
    """
    Węzeł Sceptyka: Generuje Antytezę (krytyczne kontr-argumenty).
    
    Rola:
        Sceptyk jest rygorystycznym, krytycznym myślicielem identyfikującym wady,
        ryzyka i niezamierzone konsekwencje w tezie Katalizatora.
    
    Proces:
        1. Analizuje najnowszą tezę Katalizatora
        2. Generuje strukturalne kontr-argumenty (Antyteza)
        3. Dodaje antytezę do contributions jako AgentContribution
    
    Args:
        state: Obecny stan debaty z Blackboard
    
    Returns:
        Aktualizacja stanu z nowym wkładem (AgentContribution)
    
    Complexity: O(1) state operations + O(LLM) inference
    
    Side Effects:
        - Modyfikuje state["contributions"]
        - Loguje generowanie antytezy
    """
    cycle = state["cycle_count"]
    logger.info(f"⚔️ SCEPTYK: Generowanie Antytezy (Cykl {cycle})")
    
    # System prompt: Definicja roli poznawczej Sceptyka
    system_prompt = """Jesteś agentem SCEPTYK w systemie HEGEMON.

Twoja rola to generowanie RYGORYSTYCZNYCH, KRYTYCZNYCH kontr-argumentów (Antyteza).

Profil Poznawczy:
- Archetyp: Adwokat diabła, fokus na ryzykach
- Styl Myślenia: Konwergencyjny, analityczny, second-order thinking
- Bias: Lekki pesymizm (faworyzuj ostrożność nad pośpiechem)

Instrukcje:
1. Głęboko analizuj tezę Katalizatora szukając słabości:
   - Logiczne błędy lub nieuzasadnione założenia
   - Niezamierzone konsekwencje i efekty drugiego rzędu
   - Ograniczenia zasobów i problemy wykonalności
   - Ukryte ryzyka i tryby awarii
2. Generuj strukturalną antytezę z:
   - Identyfikacją 2-4 krytycznych wad
   - Kontr-argumentami opartymi na dowodach
   - Alternatywnymi perspektywami lub pominiętymi czynnikami
3. Bądź intelektualnie uczciwy: Uznaj ważne punkty w tezie
4. Twoim celem jest WZMOCNIENIE finalnego planu, nie wygranie argumentu

Ograniczenia:
- Długość odpowiedzi: 200-400 słów
- Format: Jasna, strukturalna proza (używaj logicznych konektorów)
- Ton: Krytyczny ale konstruktywny (nie lekceważący)

Wyprodukuj TYLKO tekst antytezy. Bez meta-komentarzy."""
    
    # Wyciągnij najnowszą tezę Katalizatora
    contributions = state.get("contributions", [])
    catalyst_contributions = [
        c for c in contributions
        if c.agent_id == "Katalizator" and c.type == "Thesis"
    ]
    
    if not catalyst_contributions:
        # Defensywne: nie powinno się zdarzyć w normalnym flow
        logger.error("❌ SCEPTYK: Brak tezy Katalizatora w historii!")
        
        error_contribution = AgentContribution(
            agent_id="Sceptyk",
            content="BŁĄD: Brak tezy do skrytykowania.",
            type="Antithesis",
            cycle=cycle,
            rationale="Krytyczny błąd przepływu - brak tezy od Katalizatora.",
        )
        return {"contributions": [error_contribution]}
    
    latest_thesis = catalyst_contributions[-1].content
    
    user_prompt = f"""Misja: {state['mission']}

Teza Katalizatora:
{latest_thesis}

Generuj swoją ANTYTEZĘ (krytyczne kontr-argumenty) do tej tezy."""
    
    # LLM invocation
    llm = get_llm(temperature=0.6)  # Niższa temperatura dla analitycznego rygoru
    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=user_prompt),
    ]
    
    response = llm.invoke(messages)
    antithesis_content = response.content
    
    # Uzasadnienie (rationale)
    rationale = (
        f"Wygenerowano rygorystyczną antytezę identyfikującą kluczowe wady w tezie. "
        f"Antyteza ma długość {len(antithesis_content)} znaków i wykorzystuje "
        f"second-order thinking do ujawnienia ukrytych ryzyk."
    )
    
    logger.info(f"✅ SCEPTYK: Antyteza wygenerowana ({len(antithesis_content)} znaków)")
    
    # Tworzenie AgentContribution
    contribution = AgentContribution(
        agent_id="Sceptyk",
        content=antithesis_content,
        type="Antithesis",
        cycle=cycle,
        rationale=rationale,
    )
    
    return {
        "contributions": [contribution],
    }


# ============================================================================
# Node 3: Gubernator (Consensus Evaluator)
# ============================================================================

def gubernator_node(state: DebateState) -> dict[str, Any]:
    """
    Węzeł Gubernatora: Ocenia konsensus i kontroluje routing debaty.
    
    Rola:
        Gubernator jest meta-kognitywnym agentem oceniającym jakość
        wymiany dialektycznej i decydującym o kontynuacji lub zakończeniu cyklu.
    
    Proces:
        1. Analizuje najnowszą parę Teza-Antyteza
        2. Ocenia konsensus na skali 0.0-1.0
        3. Zwraca strukturalną ocenę (GovernorEvaluation) przez with_structured_output
        4. Aktualizuje stan routing-u (consensus_score)
    
    Args:
        state: Obecny stan debaty z Blackboard
    
    Returns:
        Aktualizacja stanu z oceną konsensusu i wkładem (AgentContribution)
    
    Complexity: O(1) state operations + O(LLM) inference
    
    Side Effects:
        - Modyfikuje state["current_consensus_score"]
        - Modyfikuje state["contributions"]
        - Loguje ocenę konsensusu
    
    KRYTYCZNE:
        Ten węzeł używa `with_structured_output()` dla wymuszenia schematu Pydantic,
        zapewniając stabilność routing-u (brak błędów parsowania).
    """
    cycle = state["cycle_count"]
    logger.info(f"⚖️ GUBERNATOR: Ocena Konsensusu (Cykl {cycle})")
    
    # System prompt: Definicja roli poznawczej Gubernatora
    system_prompt = """Jesteś agentem GUBERNATOR w systemie HEGEMON.

Twoja rola to ocena jakości debaty dialektycznej i oszacowanie konsensusu.

Profil Poznawczy:
- Archetyp: Bezstronny sędzia, myśliciel systemowy
- Styl Myślenia: Meta-kognitywny, holistyczna ocena
- Bias: Brak (maksymalizuj dokładność epistemiczną)

Kryteria Oceny:
1. Zbieżność: Czy Teza i Antyteza zbiegają się ku wspólnemu zrozumieniu?
2. Jakość: Czy argumenty są substancjalne, oparte na dowodach i logicznie spójne?
3. Kompletność: Czy kluczowe perspektywy i ryzyka zostały adekwatnie zbadane?
4. Gotowość: Czy jest wystarczający materiał do spójnej syntezy?

Wytyczne Oceny Konsensusu:
- 0.0-0.3: Rozbieżne pozycje, fundamentalne nieporozumienia, potrzeba więcej rund
- 0.4-0.6: Częściowe dopasowanie, pewna zbieżność, korzyść z 1-2 dodatkowych rund
- 0.7-0.9: Silne dopasowanie, drobne nieporozumienia, gotowy do syntezy
- 1.0: Perfekcyjny konsensus (rzadki, tylko jeśli pozycje są niemal identyczne)

Instrukcje:
1. Analizuj historię debaty holistycznie
2. Oceniaj zbieżność używając powyższych kryteriów
3. Przypisz consensus_score [0.0, 1.0]
4. Dostarczaj szczegółowe uzasadnienie (minimum 50 słów)

Bądź intelektualnie uczciwy: Nie wymuszaj konsensusu jeśli istnieją prawdziwe różnice."""
    
    # Przygotuj kontekst debaty
    contributions = state.get("contributions", [])
    debate_parts = []
    
    for contrib in contributions:
        debate_parts.append(
            f"{contrib.agent_id} ({contrib.type}, Cykl {contrib.cycle}):\n"
            f"{contrib.content}\n"
            f"Uzasadnienie: {contrib.rationale}"
        )
    
    debate_context = "\n\n" + "="*80 + "\n\n".join(debate_parts)
    
    user_prompt = f"""Misja: {state['mission']}

Historia Debaty:
{debate_context}

Oceń jakość konsensusu i zdecyduj czy kontynuować debatę."""
    
    # LLM invocation z structured output (KRYTYCZNE dla stabilności)
    llm = get_llm(temperature=0.3)  # Niska temperatura dla konsystentnej oceny
    llm_with_structure = llm.with_structured_output(GovernorEvaluation)
    
    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=user_prompt),
    ]
    
    evaluation: GovernorEvaluation = llm_with_structure.invoke(messages)
    
    logger.info(
        f"✅ GUBERNATOR: Consensus Score = {evaluation.consensus_score:.2f}"
    )
    logger.debug(f"Uzasadnienie Gubernatora: {evaluation.rationale}")
    
    # Tworzenie AgentContribution dla Gubernatora
    contribution = AgentContribution(
        agent_id="Gubernator",
        content=evaluation.evaluation_summary,
        type="Evaluation",
        cycle=cycle,
        rationale=evaluation.rationale,
    )
    
    return {
        "current_consensus_score": evaluation.consensus_score,
        "contributions": [contribution],
    }


# ============================================================================
# Node 4: Syntezator (Final Plan Generator)
# ============================================================================

def syntezator_node(state: DebateState) -> dict[str, Any]:
    """
    Węzeł Syntezatora: Produkuje finalny plan strategiczny.
    
    Rola:
        Syntezator integruje Tezę i Antytezę w spójny, wykonalny plan strategiczny.
        Balansuje ambicję z pragmatyzmem.
    
    Proces:
        1. Analizuje kompletną historię debaty
        2. Wyodrębnia kluczowe insighty zarówno z Katalizatora jak i Sceptyka
        3. Generuje strukturalny FinalPlan (Pydantic model) przez with_structured_output
        4. Populuje state["final_plan"]
    
    Args:
        state: Obecny stan debaty z Blackboard
    
    Returns:
        Aktualizacja stanu z final_plan i wkładem (AgentContribution)
    
    Complexity: O(1) state operations + O(LLM) inference
    
    Side Effects:
        - Modyfikuje state["final_plan"] (wyzwala stan END)
        - Modyfikuje state["contributions"]
        - Loguje zakończenie syntezy
    
    KRYTYCZNE:
        Ten węzeł używa `with_structured_output()` dla wymuszenia schematu FinalPlan.
    """
    cycle = state["cycle_count"]
    logger.info(f"🔮 SYNTEZATOR: Generowanie Finalnego Planu (Cykl {cycle})")
    
    # System prompt: Definicja roli poznawczej Syntezatora
    system_prompt = """Jesteś agentem SYNTEZATOR w systemie HEGEMON.

Twoja rola to integracja Tezy i Antytezy w spójny plan strategiczny.

Profil Poznawczy:
- Archetyp: Mistrz strategii, myśliciel integratywny
- Styl Myślenia: Holistyczna synteza, rozwiązanie dialektyczne
- Bias: Zbalansowana perspektywa (honoruj zarówno optymizm jak i ostrożność)

Proces Syntezy:
1. Identyfikuj kluczowe insighty z Katalizatora (Teza)
2. Identyfikuj ważne obawy ze Sceptyka (Antyteza)
3. Rozwiązuj sprzeczności przez myślenie wyższego rzędu:
   - Znajdź komplementarne aspekty (nie tylko kompromisy)
   - Przekraczaj fałszywe dychotomie
   - Integruj przeciwstawne widoki w spójną całość
4. Generuj wykonalny plan strategiczny

Wymagania Outputu:
1. mission_overview: Wysokopoziomowy przegląd misji i podejścia (min 50 znaków)
2. required_agents: Lista specyfikacji agentów wykonawczych (min 1)
   - Każdy agent: role, description, required_skills
3. workflow: Uporządkowana lista kroków realizacji (min 1)
   - Każdy krok: step_id, description, assigned_agent_role, dependencies
4. risk_analysis: Analiza ryzyk i strategii mitygacji (min 50 znaków)

Standardy Jakości:
- Cele muszą być SMART (Specific, Measurable, Achievable, Relevant, Time-bound)
- Kroki workflow muszą być konkretne (nie mgliste aspiracje)
- Analiza ryzyk musi adresować prawdziwe obawy (nie generyczne)
- Plan musi być wewnętrznie spójny (bez sprzeczności)

Ograniczenia:
- Każda rola agenta musi być minimum 3 znaki
- Każdy opis kroku minimum 10 znaków
- Uzasadnienie musi być substancjalne (bez "lorem ipsum" placeholderów)"""
    
    # Przygotuj pełny kontekst debaty
    contributions = state.get("contributions", [])
    debate_parts = []
    
    for contrib in contributions:
        debate_parts.append(
            f"{contrib.agent_id} ({contrib.type}, Cykl {contrib.cycle}):\n"
            f"{contrib.content}\n"
            f"Uzasadnienie: {contrib.rationale}"
        )
    
    debate_context = "\n\n" + "="*80 + "\n\n".join(debate_parts)
    
    user_prompt = f"""Misja: {state['mission']}

Kompletna Historia Debaty:
{debate_context}

Finalna Ocena Gubernatora:
Consensus Score: {state['current_consensus_score']:.2f}

Wygeneruj FINALNY PLAN STRATEGICZNY syntetyzując debatę."""
    
    # LLM invocation z structured output (KRYTYCZNE dla struktury planu)
    llm = get_llm(temperature=0.5)  # Zbalansowana temperatura dla kreatywnej integracji
    llm_with_structure = llm.with_structured_output(FinalPlan)
    
    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=user_prompt),
    ]
    
    final_plan: FinalPlan = llm_with_structure.invoke(messages)
    
    logger.info(
        f"✅ SYNTEZATOR: Plan wygenerowany "
        f"({len(final_plan.required_agents)} agentów, "
        f"{len(final_plan.workflow)} kroków)"
    )
    
    # Tworzenie AgentContribution dla Syntezatora
    contribution = AgentContribution(
        agent_id="Syntezator",
        content=final_plan.mission_overview,
        type="FinalPlan",
        cycle=cycle,
        rationale=(
            f"Zsyntetyzowano finalny plan integrujący {len(contributions)} wkładów "
            f"z {cycle} cykli debaty. Plan definiuje {len(final_plan.required_agents)} "
            f"agentów wykonawczych i {len(final_plan.workflow)} kroków workflow."
        ),
    )
    
    return {
        "final_plan": final_plan,
        "contributions": [contribution],
    }