# 🤖 HEGEMON MVP - Dialectical Bootstrapping System

System wieloagentowy wykorzystujący debatę dialektyczną (Teza → Antyteza → Synteza) do generowania strategicznych planów.

## 🏗️ Architektura
┌─────────────────────────────────────────────────────┐
│ HEGEMON Multi-Provider Architecture                 │
├─────────────────────────────────────────────────────┤
│                                                      │
│  Katalizator:  Claude Sonnet 4.5  (kreatywność)    │
│  Sceptyk:      Gemini 2.0 Pro     (reasoning)      │
│  Gubernator:   Claude Sonnet 4.5  (evaluation)     │
│  Syntezator:   Claude Sonnet 4.5  (synthesis)      │
│                                                      │
└─────────────────────────────────────────────────────┘

## 🚀 Szybki Start

### 1. Instalacja
```bash
# Stwórz virtual environment
python3 -m venv venv
source venv/bin/activate

# Zainstaluj zależności
pip install -r requirements.txt
2. Konfiguracja
bash# Skopiuj przykładowy plik konfiguracyjny
cp .env.example .env

# Edytuj .env i dodaj swoje API keys
nano .env
3. Uruchomienie
bashpython main.py
4. Sprawdź wyniki
bashcat output/hegemon_output.json
📁 Struktura Projektu
hegemon_mvp/
├── hegemon/              # Główny pakiet
│   ├── config/          # Konfiguracja agentów i prompts
│   ├── schemas.py       # Modele danych (Pydantic)
│   ├── agents.py        # Logika agentów (4 węzły)
│   └── graph.py         # Orkiestracja (LangGraph)
├── tests/               # Testy jednostkowe
├── output/              # Pliki wyjściowe (JSON)
├── main.py              # Punkt wejścia
└── requirements.txt     # Zależności
🧪 Testowanie
bash# Uruchom wszystkie testy
pytest tests/ -v

# Z pokryciem kodu
pytest tests/ -v --cov=hegemon --cov-report=html

# Tylko szybkie testy (bez integration)
pytest tests/ -v -m "not slow"
🎯 Przykład Użycia
pythonfrom hegemon.graph import create_hegemon_graph

# Stwórz graf
graph = create_hegemon_graph()

# Zdefiniuj misję
initial_state = {
    "mission": "Zaprojektuj strategię cyfrowej transformacji...",
    "contributions": [],
    "cycle_count": 1,
    "current_consensus_score": 0.0,
    "final_plan": None,
}

# Wykonaj debatę
final_state = graph.invoke(initial_state)

# Wynik w final_state["final_plan"]
📊 Output
System generuje plik JSON zawierający:

✅ Pełna historia debaty (wszystkie cykle)
✅ Finalny plan strategiczny:

Mission Overview
Required Agents (role, skills)
Workflow (12+ kroków z zależnościami)
Risk Analysis



🔧 Konfiguracja Zaawansowana
Zmiana Modeli
bash# W .env
HEGEMON_KATALIZATOR__MODEL=claude-3-opus-20240229
HEGEMON_SCEPTYK__MODEL=gemini-2.0-flash-exp
Zmiana Parametrów Debaty
bashHEGEMON_CONSENSUS_THRESHOLD=0.8  # Wyższy próg = więcej cykli
HEGEMON_MAX_CYCLES=7             # Max 7 cykli
📝 Licencja
MIT License
👥 Autorzy
HEGEMON MVP by Olga Żydziak
