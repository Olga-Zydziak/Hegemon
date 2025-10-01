"""
HEGEMON MVP - Punkt Wejścia (Zgodny z phase_1_details.txt).

Ten skrypt inicjalizuje środowisko, tworzy graf,
i wykonuje przykładowy cykl debaty dialektycznej.

Usage:
    python main.py

Zmienne Środowiskowe:
    OPENAI_API_KEY: Wymagane do dostępu LLM
"""

from __future__ import annotations

import json
import logging
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

from hegemon.graph import create_hegemon_graph
from hegemon.schemas import DebateState, MissionInput

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("hegemon.log", encoding="utf-8"),
    ]
)
logger = logging.getLogger(__name__)


# ============================================================================
# Environment Setup
# ============================================================================

def setup_environment() -> None:
    """
    Ładuje zmienne środowiskowe i waliduje konfigurację.
    
    Raises:
        ValueError: Jeśli brakuje wymaganych zmiennych środowiskowych
    
    Complexity: O(1)
    """
    # Załaduj plik .env (jeśli istnieje)
    env_path = Path(".") / ".env"
    load_dotenv(dotenv_path=env_path)
    
    # Waliduj wymagane zmienne
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError(
            "OPENAI_API_KEY nie znaleziony w środowisku. "
            "Proszę ustawić go w pliku .env lub wyeksportować."
        )
    
    logger.info("✅ Środowisko skonfigurowane pomyślnie")


# ============================================================================
# Main Execution
# ============================================================================

def run_hegemon(mission: str, max_cycles: int = 3) -> dict:
    """
    Wykonuje cykl debaty dialektycznej HEGEMON.
    
    Args:
        mission: Cel strategiczny od użytkownika
        max_cycles: Maksymalna liczba iteracji debaty (1-10)
    
    Returns:
        Finalny słownik stanu z zsyntetyzowanym planem
    
    Complexity: O(max_cycles * 4 * LLM_latency)
    
    Raises:
        ValueError: Jeśli walidacja wejścia zawiedzie
        RuntimeError: Jeśli wykonanie grafu zawiedzie
    """
    logger.info("=" * 80)
    logger.info("🚀 HEGEMON MVP - SYSTEM DIALEKTYCZNEGO BOOTSTRAPPINGU")
    logger.info("=" * 80)
    
    # Waliduj wejście
    try:
        mission_input = MissionInput(mission=mission, max_cycles=max_cycles)
    except Exception as e:
        logger.error(f"❌ Walidacja wejścia nie powiodła się: {e}")
        raise ValueError(f"Nieprawidłowe wejście misji: {e}") from e
    
    logger.info(f"📋 Misja: {mission_input.mission}")
    logger.info(f"🔢 Maksymalne Cykle: {mission_input.max_cycles}")
    logger.info("-" * 80)
    
    # Utwórz graf
    graph = create_hegemon_graph()
    
    # Inicjalizuj stan (zgodnie z DebateState z phase_1_details.txt)
    initial_state: DebateState = {
        "mission": mission_input.mission,
        "contributions": [],  # Pusta lista na start
        "cycle_count": 1,     # Zaczynamy od cyklu 1
        "current_consensus_score": 0.0,
        "final_plan": None,
    }
    
    # Wykonaj graf
    try:
        logger.info("🎬 Rozpoczynam cykl dialektyczny...")
        final_state = graph.invoke(initial_state)
        logger.info("✅ Cykl dialektyczny zakończony pomyślnie!")
    except Exception as e:
        logger.error(f"❌ Wykonanie grafu nie powiodło się: {e}")
        raise RuntimeError(f"Wykonanie HEGEMON nie powiodło się: {e}") from e
    
    # Loguj finalny stan
    logger.info("=" * 80)
    logger.info("📊 PODSUMOWANIE FINALNEGO STANU")
    logger.info("=" * 80)
    logger.info(f"Całkowite Cykle: {final_state['cycle_count']}")
    logger.info(f"Finalny Consensus Score: {final_state['current_consensus_score']:.2f}")
    logger.info(f"Wkłady w Debacie: {len(final_state['contributions'])}")
    
    if final_state["final_plan"]:
        logger.info("✅ Finalny plan wygenerowany pomyślnie")
        
        # Pretty-print finalnego planu (konwertuj Pydantic → dict)
        final_plan_dict = final_state["final_plan"].model_dump()
        logger.info("\n📋 PLAN STRATEGICZNY:")
        logger.info(json.dumps(final_plan_dict, indent=2, ensure_ascii=False))
    else:
        logger.warning("⚠️ Brak finalnego planu (nieoczekiwany stan)")
    
    return final_state


def main() -> None:
    """
    Główny punkt wejścia dla HEGEMON MVP.
    
    Complexity: O(1) + O(run_hegemon)
    """
    try:
        # Setup
        setup_environment()
        
        # Przykładowa misja (po polsku dla spójności)
        sample_mission = """
        Zaprojektuj kompleksową strategię redukcji śladu węglowego naszej firmy
        o 50% w ciągu najbliższych 3 lat, jednocześnie utrzymując rentowność i
        przewagę konkurencyjną w sektorze energii odnawialnej.
        """
        
        # Wykonaj HEGEMON
        final_state = run_hegemon(
            mission=sample_mission.strip(),
            max_cycles=3
        )
        
        # Eksportuj wyniki do JSON (konwertuj AgentContribution i FinalPlan)
        output_data = {
            "mission": final_state["mission"],
            "cycle_count": final_state["cycle_count"],
            "consensus_score": final_state["current_consensus_score"],
            "contributions": [
                contrib.model_dump() for contrib in final_state["contributions"]
            ],
            "final_plan": final_state["final_plan"].model_dump() if final_state["final_plan"] else None,
        }
        
        output_path = Path("hegemon_output.json")
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"💾 Wyniki zapisane do: {output_path}")
        logger.info("=" * 80)
        logger.info("🎉 Wykonanie HEGEMON MVP zakończone pomyślnie!")
        
    except Exception as e:
        logger.error(f"💥 Błąd krytyczny: {e}")
        sys.exit(1)


    # Generate heatmaps for each agent
    visualizer = HeatmapGenerator()
    
    logger.info("\n" + "=" * 80)
    logger.info("📊 EXPLAINABILITY VISUALIZATIONS")
    logger.info("=" * 80 + "\n")
    
    for contribution in final_state["contributions"]:
        if contribution.explainability and contribution.explainability.semantic_fingerprint:
            vector = contribution.explainability.semantic_fingerprint
            
            logger.info(f"\n{'=' * 80}")
            logger.info(f"{contribution.agent_id} - Cycle {contribution.cycle}")
            logger.info('=' * 80)
            
            heatmap = visualizer.generate_text_heatmap(vector, top_k=15)
            print(heatmap)
            
            # Save heatmap to file
            heatmap_file = output_dir / f"heatmap_{contribution.agent_id}_cycle{contribution.cycle}.txt"
            with open(heatmap_file, "w", encoding="utf-8") as f:
                f.write(heatmap)
            logger.info(f"💾 Heatmap saved to: {heatmap_file}")
    
    # Generate comparison: Katalizator vs Sceptyk (last cycle)
    kataliz_last = [c for c in final_state["contributions"] if c.agent_id == "Katalizator"][-1]
    sceptyk_last = [c for c in final_state["contributions"] if c.agent_id == "Sceptyk"][-1]
    
    if (kataliz_last.explainability and sceptyk_last.explainability and
        kataliz_last.explainability.semantic_fingerprint and 
        sceptyk_last.explainability.semantic_fingerprint):
        
        logger.info("\n" + "=" * 80)
        logger.info("🔄 COMPARISON: Katalizator vs Sceptyk")
        logger.info("=" * 80 + "\n")
        
        comparison = visualizer.generate_comparison_text(
            kataliz_last.explainability.semantic_fingerprint,
            sceptyk_last.explainability.semantic_fingerprint,
            label1="Katalizator (Thesis)",
            label2="Sceptyk (Antithesis)",
            top_k=10
        )
        print(comparison)
        
        comparison_file = output_dir / "comparison_katalizator_vs_sceptyk.txt"
        with open(comparison_file, "w", encoding="utf-8") as f:
            f.write(comparison)
        logger.info(f"💾 Comparison saved to: {comparison_file}")
    
    logger.info("\n" + "=" * 80)
    logger.info("✅ Hegemon completed successfully with Explainability!")
    logger.info("=" * 80)
        
        
        
        
if __name__ == "__main__":
    main()