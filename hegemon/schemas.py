"""
HEGEMON Data Schemas and State Definitions (Zgodne z phase_1_details.txt).

Ten moduł definiuje struktury danych dla systemu HEGEMON zgodnie z
oficjalną specyfikacją MVP Stage 1.

KRYTYCZNE ZMIANY:
- Dodano AgentContribution (Pydantic) zamiast prostych dict-ów
- Przepisano FinalPlan z ExecutionAgentSpec i WorkflowStep
- DebateState używa 'contributions' z operator.add (nie 'debate_history')

Complexity:
- State updates: O(1) dla key-value operations
- History accumulation: O(1) amortized (list append z operator.add)
"""

from __future__ import annotations

import operator
from typing import Annotated, Literal

from pydantic import BaseModel, Field, field_validator
from typing_extensions import TypedDict


# ============================================================================
# 1. Agent Contribution (Wkład Agenta do Blackboard)
# ============================================================================

class AgentContribution(BaseModel):
    """
    Wkład agenta do Blackboard (wspólnej pamięci).
    
    Każdy agent (Katalizator, Sceptyk, Gubernator, Syntezator) dodaje
    swój wkład do historii debaty poprzez tę strukturę.
    
    Attributes:
        agent_id: Identyfikator agenta (Literal dla type-safety)
        content: Treść wkładu (Teza, Antyteza, Ocena, Plan)
        type: Typ wkładu (mapowany na agent_id)
        cycle: Numer cyklu debaty (1-indexed)
        rationale: Uzasadnienie decyzji/rozumowania agenta
    
    Validation:
        - content: min 20 znaków (substancjalny wkład)
        - rationale: min 30 znaków (szczegółowe uzasadnienie)
    
    Complexity: O(1) dla tworzenia instancji
    """
    
    agent_id: Literal["Katalizator", "Sceptyk", "Gubernator", "Syntezator"] = Field(
        ...,
        description="Identyfikator agenta generującego wkład"
    )
    content: str = Field(
        ...,
        min_length=20,
        description="Treść wkładu agenta (Teza, Antyteza, Ocena, Plan)"
    )
    type: Literal["Thesis", "Antithesis", "Evaluation", "FinalPlan"] = Field(
        ...,
        description="Typ wkładu odpowiadający roli agenta"
    )
    cycle: int = Field(
        ...,
        ge=1,
        description="Numer cyklu debaty (1-indexed)"
    )
    rationale: str = Field(
        ...,
        min_length=30,
        description="Uzasadnienie decyzji lub rozumowania agenta"
    )
    
    @field_validator("content")
    @classmethod
    def validate_content_quality(cls, v: str) -> str:
        """
        Walidacja jakości treści (nie może być placeholder).
        
        Complexity: O(n) gdzie n = długość content
        """
        forbidden = ["lorem ipsum", "todo", "placeholder", "test content"]
        v_lower = v.lower()
        
        if any(phrase in v_lower for phrase in forbidden):
            raise ValueError(
                "Content must be genuine, not placeholder text"
            )
        
        return v.strip()


# ============================================================================
# 2. Governor Evaluation (Wyjście Gubernatora)
# ============================================================================

class GovernorEvaluation(BaseModel):
    """
    Strukturalne wyjście z węzła Gubernatora (Ocena Konsensusu).
    
    Gubernator ocenia postęp debaty i decyduje o routing-u:
    - Niska ocena (< 0.7) → Kontynuuj debatę
    - Wysoka ocena (>= 0.7) → Przejdź do syntezy
    
    Attributes:
        evaluation_summary: Podsumowanie postępu debaty i synteza Tezy/Antytezy
        consensus_score: Ocena gotowości planu [0.0, 1.0]
            - 0.0: Krytyczne wady, fundamentalne różnice
            - 0.5: Częściowa zbieżność, potrzeba więcej iteracji
            - 1.0: Gotowy do wdrożenia, pełny konsensus
        rationale: Szczegółowe uzasadnienie oceny konsensusu
    
    Validation:
        - consensus_score w przedziale [0.0, 1.0]
        - evaluation_summary: min 50 znaków
        - rationale: min 50 znaków
    
    KRYTYCZNE:
        Ta klasa jest używana z `with_structured_output()` dla stabilności routing-u.
    """
    
    evaluation_summary: str = Field(
        ...,
        min_length=50,
        description="Podsumowanie postępu debaty i synteza argumentów"
    )
    consensus_score: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description=(
            "Ocena gotowości planu: "
            "0.0 = krytyczne wady, 1.0 = gotowy do wdrożenia"
        )
    )
    rationale: str = Field(
        ...,
        min_length=50,
        description="Uzasadnienie oceny konsensusu"
    )
    
    @field_validator("evaluation_summary", "rationale")
    @classmethod
    def validate_no_placeholders(cls, v: str) -> str:
        """
        Zapewnia, że podsumowanie i uzasadnienie nie są placeholder-ami.
        
        Complexity: O(n)
        """
        forbidden_phrases = ["lorem ipsum", "todo", "placeholder", "n/a", "tbd"]
        v_lower = v.lower()
        
        if any(phrase in v_lower for phrase in forbidden_phrases):
            raise ValueError(
                "Field must contain genuine analysis, not placeholder text"
            )
        
        return v.strip()


# ============================================================================
# 3. Final Plan Components (Syntezator Output)
# ============================================================================

class ExecutionAgentSpec(BaseModel):
    """
    Specyfikacja agenta wykonawczego w finalnym planie.
    
    Opisuje rolę, odpowiedzialności i wymagane umiejętności
    dla agenta, który będzie realizował część strategii.
    
    Attributes:
        role: Nazwa roli (np. "Data Engineer", "ML Specialist")
        description: Szczegółowy opis odpowiedzialności
        required_skills: Lista wymaganych kompetencji
    
    Validation:
        - role: min 3 znaki
        - description: min 20 znaków
        - required_skills: min 1 umiejętność
    """
    
    role: str = Field(
        ...,
        min_length=3,
        description="Nazwa roli agenta wykonawczego"
    )
    description: str = Field(
        ...,
        min_length=20,
        description="Szczegółowy opis odpowiedzialności roli"
    )
    required_skills: list[str] = Field(
        ...,
        min_length=1,
        description="Lista wymaganych kompetencji (min 1)"
    )
    
    @field_validator("required_skills")
    @classmethod
    def validate_skills_quality(cls, v: list[str]) -> list[str]:
        """
        Waliduje, że umiejętności nie są single-word placeholders.
        
        Complexity: O(n) gdzie n = liczba umiejętności
        """
        for skill in v:
            if len(skill.split()) < 2 and skill.lower() in ["todo", "tbd", "n/a"]:
                raise ValueError(
                    f"Skill '{skill}' is too vague. Provide specific competencies."
                )
        return v


class WorkflowStep(BaseModel):
    """
    Krok w workflow wykonawczym.
    
    Definiuje sekwencyjny krok realizacji strategii z:
    - Identyfikatorem (dla zarządzania zależnościami)
    - Opisem zadania
    - Przypisanym agentem
    - Zależnościami od innych kroków
    
    Attributes:
        step_id: Unikalny identyfikator kroku (1-indexed)
        description: Szczegółowy opis zadania
        assigned_agent_role: Rola agenta odpowiedzialnego za krok
        dependencies: Lista step_id kroków, które muszą być ukończone wcześniej
    
    Validation:
        - step_id: >= 1
        - description: min 10 znaków
        - assigned_agent_role: min 3 znaki
        - dependencies: lista int-ów (może być pusta dla kroków początkowych)
    """
    
    step_id: int = Field(
        ...,
        ge=1,
        description="Unikalny identyfikator kroku (1-indexed)"
    )
    description: str = Field(
        ...,
        min_length=10,
        description="Szczegółowy opis zadania do wykonania"
    )
    assigned_agent_role: str = Field(
        ...,
        min_length=3,
        description="Rola agenta odpowiedzialnego za ten krok"
    )
    dependencies: list[int] = Field(
        default_factory=list,
        description="Lista step_id kroków wymaganych przed tym krokiem"
    )
    
    @field_validator("dependencies")
    @classmethod
    def validate_dependencies(cls, v: list[int], info) -> list[int]:
        """
        Waliduje, że zależności nie zawierają cykli (self-reference).
        
        Complexity: O(n) gdzie n = liczba zależności
        """
        step_id = info.data.get("step_id")
        if step_id and step_id in v:
            raise ValueError(
                f"Step {step_id} cannot depend on itself (circular dependency)"
            )
        return v


class FinalPlan(BaseModel):
    """
    Finalny plan strategiczny wygenerowany przez Syntezatora.
    
    Jest to kulminacja procesu dialektycznego: spójny plan działania
    integrujący Tezę (Katalizator) i Antytezę (Sceptyk).
    
    Attributes:
        mission_overview: Wysokopoziomowy przegląd misji i podejścia
        required_agents: Lista specyfikacji agentów wykonawczych
        workflow: Uporządkowana lista kroków realizacji
        risk_analysis: Analiza zidentyfikowanych ryzyk i strategii mitigacji
    
    Validation:
        - mission_overview: min 50 znaków
        - required_agents: min 1 agent
        - workflow: min 1 krok
        - risk_analysis: min 50 znaków
    
    KRYTYCZNE:
        Ta klasa jest używana z `with_structured_output()` w węźle Syntezatora.
    """
    
    mission_overview: str = Field(
        ...,
        min_length=50,
        description="Wysokopoziomowy przegląd misji i strategii"
    )
    required_agents: list[ExecutionAgentSpec] = Field(
        ...,
        min_length=1,
        description="Lista specyfikacji agentów wykonawczych (min 1)"
    )
    workflow: list[WorkflowStep] = Field(
        ...,
        min_length=1,
        description="Uporządkowana lista kroków realizacji (min 1)"
    )
    risk_analysis: str = Field(
        ...,
        min_length=50,
        description="Analiza ryzyk i strategii mitygacji"
    )
    
    @field_validator("workflow")
    @classmethod
    def validate_workflow_consistency(cls, v: list[WorkflowStep]) -> list[WorkflowStep]:
        """
        Waliduje spójność workflow (wszystkie zależności istnieją).
        
        Complexity: O(n * m) gdzie n = liczba kroków, m = średnia liczba zależności
        """
        step_ids = {step.step_id for step in v}
        
        for step in v:
            for dep_id in step.dependencies:
                if dep_id not in step_ids:
                    raise ValueError(
                        f"Step {step.step_id} depends on non-existent step {dep_id}"
                    )
                if dep_id >= step.step_id:
                    raise ValueError(
                        f"Step {step.step_id} cannot depend on later step {dep_id} "
                        "(workflow must be acyclic)"
                    )
        
        return v


# ============================================================================
# 4. Debate State (Blackboard - TypedDict dla LangGraph)
# ============================================================================

class DebateState(TypedDict):
    """
    Stan Grafu (Blackboard): Wspólna pamięć dla cyklu dialektycznego.
    
    KRYTYCZNE:
        Używa `Annotated` z `operator.add` dla akumulacji historii wkładów.
        LangGraph automatycznie merguje listy zamiast nadpisywać.
    
    Attributes:
        mission: Pierwotny problem wejściowy od użytkownika
        contributions: Akumulowana lista wkładów agentów (AgentContribution)
        current_consensus_score: Ostatni wynik oceny od Gubernatora [0.0, 1.0]
        cycle_count: Bieżący numer cyklu debaty (1-indexed)
        final_plan: Wynik końcowy (FinalPlan) lub None jeśli debata trwa
    
    Memory Complexity:
        O(n) gdzie n = total liczba wkładów = cycle_count * agents_per_cycle
        Typowo: O(3 * 4) = O(12) dla max 3 cykle z 4 agentami
    """
    
    mission: str
    contributions: Annotated[list[AgentContribution], operator.add]
    current_consensus_score: float
    cycle_count: int
    final_plan: FinalPlan | None


# ============================================================================
# 5. Mission Input (Walidacja wejścia użytkownika)
# ============================================================================

class MissionInput(BaseModel):
    """
    Walidowane wejście użytkownika dla systemu HEGEMON.
    
    Attributes:
        mission: Cel strategiczny (min 10 znaków, max 5000 znaków)
        max_cycles: Maksymalna liczba cykli debaty (1-10)
    
    Security:
        - max_length zapobiega DoS przez ekstremalnie długie wejścia
        - min_length zapewnia substancjalne misje
        - Sanityzacja przeciwko prompt injection
    """
    
    mission: str = Field(
        ...,
        min_length=10,
        max_length=5000,
        description="Cel strategiczny dla systemu HEGEMON"
    )
    max_cycles: int = Field(
        default=3,
        ge=1,
        le=10,
        description="Maksymalna liczba cykli debaty"
    )
    
    @field_validator("mission")
    @classmethod
    def sanitize_mission(cls, v: str) -> str:
        """
        Podstawowa sanityzacja przeciwko prompt injection attacks.
        
        Usuwa potencjalne nadpisania system prompt i zapewnia czysty tekst.
        Complexity: O(n) gdzie n = długość mission
        """
        dangerous_patterns = [
            "ignore previous instructions",
            "disregard all prior",
            "system:",
            "assistant:",
            "override",
            "jailbreak",
        ]
        
        v_lower = v.lower()
        if any(pattern in v_lower for pattern in dangerous_patterns):
            raise ValueError(
                "Mission contains potentially malicious content. "
                "Please rephrase without system-level instructions."
            )
        
        return v.strip()