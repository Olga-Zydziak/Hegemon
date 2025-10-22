# 🚀 HEGEMON na Vertex AI - Rozwiązanie Problemu z Widgetami

## 🔴 Problem

**ipywidgets NIE DZIAŁAJĄ na Vertex AI JupyterLab!**

Przyczyny:
- Brak rozszerzenia `jupyterlab-widgets`
- Problemy z WebSocket communication
- Thread callbacks nie działają w środowisku cloud
- Przyciski się nie klikają, formularz się zawiesza

## ✅ Rozwiązanie: Simple Text-Based UI

Stworzyłem **alternatywną wersję** która używa zwykłego `input()` zamiast widgetów.

**Działa WSZĘDZIE:**
- ✅ Vertex AI JupyterLab
- ✅ Google Colab
- ✅ Kaggle Notebooks
- ✅ Lokalne Jupyter
- ✅ Każde środowisko Pythona

---

## 📦 Jak Używać?

### Opcja 1: Vertex AI (RECOMMENDED)

```python
# Import
from hegemon.graph_hitl_v3 import create_hegemon_graph_hitl_v3

# ⚡ KLUCZOWE: use_simple_ui=True dla Vertex AI
graph = create_hegemon_graph_hitl_v3(use_simple_ui=True)

# Uruchom
final_state = graph.invoke(initial_state)
```

**W checkpointach zobaczysz:**
```
================================================================================
👤 YOUR FEEDBACK
================================================================================

Options:
  1 - ✅ Approve (continue with this output)
  2 - ✏️ Request Revision (provide guidance for improvement)
  3 - ❌ Reject (end debate - critical issue)

Enter your choice (1/2/3): █
```

**Wpisujesz:** `1` (lub `2`, lub `3`) i klikasz Enter. Gotowe!

---

### Opcja 2: Lokalne Jupyter z ipywidgets (Jeśli masz zainstalowane rozszerzenia)

```python
# Import
from hegemon.graph_hitl_v3 import create_hegemon_graph_hitl_v3

# Domyślnie używa ipywidgets (radio buttons, text areas)
graph = create_hegemon_graph_hitl_v3(use_simple_ui=False)

# Uruchom
final_state = graph.invoke(initial_state)
```

---

## 📊 Porównanie

| Feature | ipywidgets UI | Simple Text UI |
|---------|--------------|----------------|
| **Środowisko** | Tylko lokalne Jupyter | WSZĘDZIE |
| **Vertex AI** | ❌ NIE DZIAŁA | ✅ DZIAŁA |
| **Google Colab** | ❌ NIE DZIAŁA | ✅ DZIAŁA |
| **Wymaga rozszerzeń** | ✅ Tak (`jupyterlab-widgets`) | ❌ Nie |
| **Interfejs** | Przyciski, dropdowns | Text prompt |
| **Zawieszanie** | 🟡 Możliwe | ✅ Nigdy |
| **Setup** | Skomplikowany | Zero setup |
| **Threading issues** | 🟡 Tak | ❌ Nie |

---

## 🎯 Przykłady Notebooków

### 1. `vertex_ai_example.ipynb` ⭐ **START TUTAJ!**
- Zoptymalizowany dla Vertex AI
- Używa `use_simple_ui=True`
- Pełny tutorial krok po kroku
- **Polecam dla Vertex AI!**

### 2. `phase_2_4_example.ipynb`
- Wersja z ipywidgets (dla lokalnego Jupyter)
- Wymaga zainstalowanego `ipywidgets`
- Może nie działać na Vertex AI

---

## 🛠️ Szybki Start (Vertex AI)

### Krok 1: Pobierz kod
```bash
git clone <repo>
cd Hegemon
git checkout claude/architect-design-principles-011CUNYjrhH2ZkoSzctJQCcS
```

### Krok 2: Zainstaluj pakiety
```bash
pip install -r requirements.txt
```

### Krok 3: Otwórz notebook
```bash
# Na Vertex AI JupyterLab:
# File → Open → vertex_ai_example.ipynb
```

### Krok 4: Wykonaj komórki
- Czytaj instrukcje w notebooku
- W checkpointach wpisuj `1`, `2` lub `3`
- Kliknij Enter
- Ciesz się działającym HITL! 🎉

---

## 💡 Przykład Użycia w Kodzie

```python
from hegemon.graph_hitl_v3 import create_hegemon_graph_hitl_v3
from hegemon.hitl import InterventionMode

# Stwórz graf dla Vertex AI
graph = create_hegemon_graph_hitl_v3(use_simple_ui=True)

# Stan początkowy
initial_state = {
    "mission": "Zaprojektuj ML pipeline...",
    "contributions": [],
    "cycle_count": 1,
    "current_consensus_score": 0.0,
    "final_plan": None,
    # HITL config
    "intervention_mode": "reviewer",
    "current_checkpoint": None,
    "human_feedback_history": [],
    "paused_at": None,
    "revision_count_per_checkpoint": {},
    "checkpoint_snapshots": {},
}

# Uruchom
final_state = graph.invoke(initial_state, config={"recursion_limit": 100})

# W checkpointach zobaczysz:
#   Enter your choice (1/2/3): _
# Wpisz numer, kliknij Enter, gotowe!
```

---

## 🔧 Jak to Działa Pod Spodem?

### SimpleCheckpointUI (`hegemon/hitl/simple_ui.py`)

```python
# Zamiast ipywidgets:
# submit_button = widgets.Button(...)
# submit_button.on_click(callback)

# Używa prostego input():
choice = input("Enter your choice (1/2/3): ").strip()

if choice == "1":
    decision = FeedbackDecision.APPROVE
elif choice == "2":
    decision = FeedbackDecision.REVISE
    guidance = input("Your guidance: ").strip()
elif choice == "3":
    decision = FeedbackDecision.REJECT
```

**Zero threading, zero callbacks, zero problemów!**

---

## ❓ FAQ

### Q: Dlaczego ipywidgets nie działają na Vertex AI?
**A:** Vertex AI JupyterLab nie ma zainstalowanego rozszerzenia `jupyterlab-widgets`. Instalacja wymaga restartowania całego środowiska i uprawnień admina.

### Q: Czy Simple UI ma wszystkie funkcje?
**A:** Tak! Ma approve/revise/reject. Jedyna różnica to brak "Advanced Options" (Priority Claims, Flagged Concerns), ale te są opcjonalne.

### Q: Która wersja jest lepsza?
**A:** Dla Vertex AI/Colab: **Simple UI** (100% niezawodne). Dla lokalnego Jupyter z rozszerzeniami: ipywidgets (ładniejsze wizualnie).

### Q: Czy mogę przełączać między wersjami?
**A:** Tak! Zmień parametr `use_simple_ui`:
```python
# Simple UI (text)
graph = create_hegemon_graph_hitl_v3(use_simple_ui=True)

# ipywidgets UI (buttons)
graph = create_hegemon_graph_hitl_v3(use_simple_ui=False)
```

### Q: Co jeśli nadal nie działa?
**A:** Sprawdź:
1. Czy używasz `use_simple_ui=True`?
2. Czy widzisz prompt `Enter your choice (1/2/3):`?
3. Czy wpisujesz `1`, `2` lub `3` i klikasz Enter?

Jeśli nadal problem - to może być inny issue, nie związany z UI.

---

## 📝 Podsumowanie

### ✅ DO (Vertex AI):
```python
graph = create_hegemon_graph_hitl_v3(use_simple_ui=True)  # ✅ DZIAŁA
```

### ❌ DON'T (Vertex AI):
```python
graph = create_hegemon_graph_hitl_v3(use_simple_ui=False)  # ❌ ZAWIESZA SIĘ
graph = create_hegemon_graph_hitl_v3()  # ❌ Domyślnie False
```

---

## 🎉 Gotowe!

Teraz HEGEMON Phase 2.4 działa na **Vertex AI bez problemów**!

**Użyj:** `vertex_ai_example.ipynb`

**Miłej zabawy!** 🚀
