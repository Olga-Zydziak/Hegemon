"""
HEGEMON Data Schemas and State Definitions - PHASE 2.1 HITL EXTENDED.

Rozszerza istniejące schematy o pola Human-in-the-Loop (HITL).
100% backward compatible z Phase 1 + Explainability (Layer 2).

KRYTYCZNE ZMIANY:
- DebateState rozszerzone o 6 pól HITL
- AgentContribution zachowuje pole explainability (Layer 2)
- Nowe: intervention_mode, current_checkpoint, human_feedback_history
- Zachowana kompatybilność: wszystkie Phase 1 pola bez zmian

Complexity:
- State updates: O(1) dla key-value operations
- History accumulation: O(1) amortized (list append z operator.add)
"""

from __future__ import annotations

import operator
from typing import Annotated, Any, Literal

from pydantic import BaseModel, Field, field_validator
from typing_extensions import TypedDict


# ============================================================================
# 0. Explainability Data (Layer 2 Support)
# ============================================================================

class ExplainabilityData(BaseModel):
    """
    Container for Layer 2 (Epistemic) and Layer 6 (Semantic) explainability data.
    
    CRITICAL: This class enables post-hoc analysis of agent reasoning.
    
    Attributes:
        epistemic_profile: Layer 2 confidence scores and epistemic metadata
        semantic_concepts: Layer 6 semantic concept extraction
        collection_metadata: Timing and diagnostic info
    
    Complexity: O(1) for instantiation
    """
    
    epistemic_profile: dict[str, Any] | None = Field(
        default=None,
        description="Layer 2: Epistemic confidence analysis"
    )
    semantic_concepts: dict[str, Any] | None = Field(
        default=None,
        description="Layer 6: Semantic concept extraction"
    )
    collection_metadata: dict[str, Any] | None = Field(
        default=None,
        description="Collection timing and diagnostics"
    )


# ============================================================================
# 1. Agent Contribution (EXTENDED with Explainability)
# ============================================================================

class AgentContribution(BaseModel):
    """
    Wkład agenta do Blackboard (wspólnej pamięci).
    
    Każdy agent (Katalizator, Sceptyk, Gubernator, Syntezator) dodaje
    swój wkład do historii debaty poprzez tę strukturę.
    
    PHASE 2.1 NOTE:
        Zachowuje pole explainability z Phase 1 dla kompatybilności z Layer 2.
    
    Attributes:
        agent_id: Identyfikator agenta (Literal dla type-safety)
        content: Treść wkładu (Teza, Antyteza, Ocena, Plan)
        type: Typ wkładu (mapowany na agent_id)
        cycle: Numer cyklu debaty (1-indexed)
        rationale: Uzasadnienie decyzji/rozumowania agenta
        explainability: Layer 2 + Layer 6 data (optional)
    
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
    explainability: Any | None = Field(
        default=None,
        description="Layer 2 (Epistemic) and Layer 6 (Semantic) explainability data"
    )
    
    @field_validator("content")
    @classmethod
    def validate_content_quality(cls, v: str) -> str:
        """
        Walidacja jakości treści (nie może być placeholder).
        
        Security: Zapobiega placeholder content typu "lorem ipsum"
        Complexity: O(n) gdzie n = długość content
        """
        forbidden_placeholders = ["lorem ipsum", "todo", "tbd", "xxx"]
        v_lower = v.lower()
        
        if any(placeholder in v_lower for placeholder in forbidden_placeholders):
            raise ValueError(
                f"Content contains placeholder text. "
                f"Provide substantive contribution."
            )
        
        return v


# ============================================================================
# 2. Governor Evaluation (UNCHANGED - Phase 1)
# ============================================================================

class GovernorEvaluation(BaseModel):
    """
    Strukturalne wyjście Gubernatora (Ocena Konsensusu).
    
    Używane z `with_structured_output()` dla robustness.
    
    Attributes:
        evaluation_summary: Podsumowanie postępu debaty (min 50 znaków)
        consensus_score: Ocena gotowości planu [0.0, 1.0]
        rationale: Szczegółowe uzasadnienie oceny (min 50 znaków)
    
    Validation:
        - evaluation_summary: min 50 znaków
        - consensus_score: strict range [0.0, 1.0]
        - rationale: min 50 znaków
    
    Complexity: O(1) dla tworzenia instancji
    """
    
    evaluation_summary: str = Field(
        ...,
        min_length=50,
        description="Podsumowanie postępu debaty i synteza Tezy/Antytezy"
    )
    consensus_score: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Ocena gotowości planu (0.0 = krytyczne wady, 1.0 = gotowy)"
    )
    rationale: str = Field(
        ...,
        min_length=50,
        description="Uzasadnienie oceny konsensusu"
    )


# ============================================================================
# 3. Final Plan Components (UNCHANGED - Phase 1)
# ============================================================================

class ExecutionAgentSpec(BaseModel):
    """
    Specyfikacja agenta wykonawczego w finalnym planie.
    
    Attributes:
        role: Nazwa roli (np. "DataEngineer")
        description: Zakres odpowiedzialności
        required_skills: Lista wymaganych umiejętności
    
    Complexity: O(1) dla tworzenia instancji
    """
    
    role: str = Field(
        ...,
        min_length=3,
        description="Nazwa roli agenta"
    )
    description: str = Field(
        ...,
        min_length=20,
        description="Zakres odpowiedzialności agenta"
    )
    required_skills: list[str] = Field(
        ...,
        min_length=1,
        description="Lista wymaganych umiejętności (min 1)"
    )


class WorkflowStep(BaseModel):
    """
    Krok realizacji w workflow.
    
    Attributes:
        step_id: Unikalny identyfikator kroku (1-indexed)
        description: Opis zadania (min 20 znaków)
        assigned_agent_role: Rola odpowiedzialnego agenta
        dependencies: Lista step_id kroków wymaganych
    
    Validation:
        - step_id: musi być >= 1
        - dependencies: muszą być mniejsze niż step_id (acyclic)
    
    Complexity: O(1) dla tworzenia instancji
    """
    
    step_id: int = Field(
        ...,
        ge=1,
        description="Unikalny identyfikator kroku (1-indexed)"
    )
    description: str = Field(
        ...,
        min_length=20,
        description="Opis zadania do wykonania"
    )
    assigned_agent_role: str = Field(
        ...,
        min_length=3,
        description="Rola agenta odpowiedzialnego za krok"
    )
    dependencies: list[int] = Field(
        default_factory=list,
        description="Lista step_id kroków wymaganych przed tym krokiem"
    )


class FinalPlan(BaseModel):
    """
    Końcowy plan strategiczny (output Syntezatora).
    
    KRYTYCZNE:
        Ta klasa jest używana z `with_structured_output()` w węźle Syntezatora.
    
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
    
    Complexity: O(n * m) dla workflow validation
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
# 4. Debate State (EXTENDED - Phase 2.1 HITL)
# ============================================================================

class DebateState(TypedDict):
    """
    Stan Grafu (Blackboard): Wspólna pamięć dla cyklu dialektycznego.
    
    PHASE 2.1 EXTENSIONS:
        Dodano 6 pól HITL do obsługi Human-in-the-Loop:
        - intervention_mode: Tryb interwencji użytkownika
        - current_checkpoint: Aktywny checkpoint (jeśli pause)
        - human_feedback_history: Akumulowana lista feedbacku
        - paused_at: Timestamp pauzy (ISO format)
        - revision_count_per_checkpoint: Licznik rewizji per checkpoint
        - checkpoint_snapshots: Backupy stanu dla recovery
    
    KRYTYCZNE:
        - Używa `Annotated` z `operator.add` dla list (auto-merge)
        - 100% backward compatible z Phase 1 (dodane pola opcjonalne w runtime)
        - Zachowuje explainability w contributions dla Layer 2
    
    Attributes (Phase 1 - UNCHANGED):
        mission: Pierwotny problem wejściowy od użytkownika
        contributions: Akumulowana lista wkładów agentów (AgentContribution)
        current_consensus_score: Ostatni wynik oceny od Gubernatora [0.0, 1.0]
        cycle_count: Bieżący numer cyklu debaty (1-indexed)
        final_plan: Wynik końcowy (FinalPlan) lub None jeśli debata trwa
    
    Attributes (Phase 2.1 - NEW):
        intervention_mode: Poziom kontroli użytkownika
        current_checkpoint: Identyfikator aktywnego checkpoint (jeśli pause)
        human_feedback_history: Historia wszystkich interwencji użytkownika
        paused_at: ISO timestamp kiedy debata została zapauzowana
        revision_count_per_checkpoint: Mapa checkpoint -> liczba rewizji
        checkpoint_snapshots: Mapa checkpoint -> backup stanu
    
    Memory Complexity:
        Phase 1: O(n) gdzie n = cycle_count * 4 agents
        Phase 2.1: O(n + m + k) gdzie:
            m = liczba feedbacku (typically < 10)
            k = liczba snapshots (= liczba checkpoints ≤ 3 * cycle_count)
    """
    
    # ========================================================================
    # Phase 1 Fields (UNCHANGED)
    # ========================================================================
    
    mission: str
    contributions: Annotated[list[AgentContribution], operator.add]
    current_consensus_score: float
    cycle_count: int
    final_plan: FinalPlan | None
    
    # ========================================================================
    # Phase 2.1 HITL Fields (NEW)
    # ========================================================================
    
    intervention_mode: Literal["observer", "reviewer", "collaborator"]
    current_checkpoint: str | None
    human_feedback_history: Annotated[list[Any], operator.add]  # List[HumanFeedback] at runtime
    paused_at: str | None  # ISO datetime string
    revision_count_per_checkpoint: dict[str, int]
    checkpoint_snapshots: dict[str, dict[str, Any]]


# ============================================================================
# 5. Mission Input (UNCHANGED - Phase 1)
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
    
    Complexity: O(n) dla sanitization (n = długość mission)
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
        
        return v