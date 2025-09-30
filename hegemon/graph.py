"""
HEGEMON Orchestration Layer (LangGraph) - Zgodny z phase_1_details.txt.

Ten moduł definiuje workflow debaty dialektycznej używając abstrakcji StateGraph
z LangGraph. Zarządza:
1. Definicjami węzłów (wywołania agentów)
2. Definicjami krawędzi (przepływ kontroli)
3. Warunkowym routing-iem (kontynuuj debatę vs syntetyzuj)

Struktura grafu:
    START → katalizator → sceptyk → gubernator → [decision]
                                                    ├─ [konsensus niski] → katalizator (loop)
                                                    └─ [konsensus wysoki] → syntezator → END

Complexity:
- Kompilacja grafu: O(1) - stała struktura
- Runtime: O(max_cycles * 4 nodes * LLM_latency)
"""

from __future__ import annotations

import logging
from typing import Literal

from langgraph.graph import END, START, StateGraph

from hegemon.agents import (
    gubernator_node,
    katalizator_node,
    sceptyk_node,
    syntezator_node,
)
from hegemon.schemas import DebateState

logger = logging.getLogger(__name__)


# ============================================================================
# Routing Logic (Conditional Edges)
# ============================================================================

def should_continue_debate(state: DebateState) -> Literal["continue", "synthesize"]:
    """
    Funkcja routing-u: Decyduje czy kontynuować debatę czy syntetyzować.
    
    Logika Decyzyjna:
        1. Jeśli consensus_score >= 0.7 → Syntetyzuj (wysoka pewność)
        2. Jeśli cycle_count >= max_cycles → Syntetyzuj (timeout)
        3. W przeciwnym razie → Kontynuuj (potrzeba więcej iteracji)
    
    Args:
        state: Obecny stan debaty
    
    Returns:
        "continue": Zapętl z powrotem do katalizator_node
        "synthesize": Przejdź do syntezator_node
    
    Complexity: O(1) - proste porównania progów
    
    KRYTYCZNE:
        Ta funkcja jest głównym mechanizmem przepływu kontroli.
        Niepoprawny routing może spowodować nieskończone pętle lub przedwczesne zakończenie.
    """
    consensus_threshold = 0.7
    max_cycles = 5  # Twardy limit bezpieczeństwa (nawet jeśli użytkownik ustawił wyższy)
    
    current_score = state["current_consensus_score"]
    current_cycle = state["cycle_count"]
    
    # Sprawdzenie bezpieczeństwa: Zapobiegaj nieskończonym pętlom
    if current_cycle >= max_cycles:
        logger.warning(
            f"⚠️ ROUTING: Osiągnięto max cykli ({current_cycle}). "
            f"Wymuszam syntezę (score={current_score:.2f})"
        )
        return "synthesize"
    
    # Standardowe sprawdzenie konsensusu
    if current_score >= consensus_threshold:
        logger.info(
            f"✅ ROUTING: Osiągnięto konsensus (score={current_score:.2f}). "
            f"Przechodzę do syntezy."
        )
        return "synthesize"
    
    # Kontynuuj debatę
    logger.info(
        f"🔄 ROUTING: Konsensus niewystarczający (score={current_score:.2f}). "
        f"Kontynuuję debatę (cykl {current_cycle + 1})"
    )
    return "continue"


def increment_cycle(state: DebateState) -> dict[str, int]:
    """
    Funkcja pomocnicza do inkrementacji licznika cykli.
    
    Wywoływana przed zapętleniem z powrotem do katalizator_node.
    
    Args:
        state: Obecny stan debaty
    
    Returns:
        Aktualizacja stanu z zinkrementowanym numerem cyklu
    
    Complexity: O(1)
    """
    new_cycle = state["cycle_count"] + 1
    logger.info(f"📈 INCREMENT: Przechodzę do cyklu {new_cycle}")
    
    return {
        "cycle_count": new_cycle,
    }


# ============================================================================
# Graph Construction
# ============================================================================

def create_hegemon_graph() -> StateGraph:
    """
    Konstruuje graf debaty dialektycznej HEGEMON.
    
    Struktura Grafu:
        START
          ↓
        katalizator (Teza)
          ↓
        sceptyk (Antyteza)
          ↓
        gubernator (Ocena Konsensusu)
          ↓
        [punkt decyzyjny]
          ├─ konsensus niski → increment_cycle → katalizator (loop z cycle++)
          └─ konsensus wysoki → syntezator → END
    
    Returns:
        Skompilowany workflow LangGraph
    
    Complexity:
        - Konstrukcja: O(1) - stała struktura grafu
        - Kompilacja: O(V + E) = O(5 + 6) = O(1)
    
    KRYTYCZNE:
        - Wszystkie węzły muszą być dodane przed krawędziami
        - Warunkowe krawędzie muszą mieć wyczerpujący routing (bez brakujących przypadków)
        - Węzeł START musi mieć dokładnie jedną wychodzącą krawędź
    """
    # Inicjalizuj graf ze schematem DebateState
    workflow = StateGraph(DebateState)
    
    # Dodaj węzły (agentów)
    workflow.add_node("katalizator", katalizator_node)
    workflow.add_node("sceptyk", sceptyk_node)
    workflow.add_node("gubernator", gubernator_node)
    workflow.add_node("syntezator", syntezator_node)
    workflow.add_node("increment_cycle", increment_cycle)
    
    # Zdefiniuj krawędzie (przepływ kontroli)
    
    # Punkt wejścia: START → katalizator
    workflow.add_edge(START, "katalizator")
    
    # Sekwencyjny przepływ: katalizator → sceptyk → gubernator
    workflow.add_edge("katalizator", "sceptyk")
    workflow.add_edge("sceptyk", "gubernator")
    
    # Warunkowy routing po gubernatorze
    workflow.add_conditional_edges(
        "gubernator",
        should_continue_debate,
        {
            "continue": "increment_cycle",      # Zapętl z powrotem
            "synthesize": "syntezator",         # Zakończ
        }
    )
    
    # Zapętl z powrotem do katalizatora po inkrementacji cyklu
    workflow.add_edge("increment_cycle", "katalizator")
    
    # Wyjście: syntezator → END
    workflow.add_edge("syntezator", END)
    
    # Kompiluj graf
    compiled_graph = workflow.compile()
    
    logger.info("🏗️ Graf HEGEMON skompilowany pomyślnie")
    return compiled_graph