# 🎯 HEGEMON Phase 2.4 - Instrukcja Użycia

## Co to jest Phase 2.4?

Phase 2.4 to warstwa **Human-in-the-Loop (HITL)**, która pozwala Ci uczestniczyć w debacie agentów w czasie rzeczywistym. Możesz:

- ✅ **Zatwierdzać** output agentów
- ✏️ **Prosić o rewizje** z własnymi wskazówkami
- ❌ **Odrzucać** i kończyć debatę
- 👀 **Obserwować** bez ingerencji

## 🛠️ Co zostało naprawione?

### Problem #1: Stare wartości w formularzach ❌
**Przed:** Gdy przechodziłeś do nowego checkpointu, w formularzu widniały wartości z poprzedniego.

**Teraz:** ✅ Każdy checkpoint ma czysty formularz - session state resetuje się automatycznie.

### Problem #2: Zawieszający się Jupyter kernel ❌
**Przed:** Jupyter kernel mógł się zawiesić podczas czekania na input, przyciski nie działały.

**Teraz:** ✅ Nowy mechanizm polling + przycisk "Auto-Approve" dla szybkiego przejścia dalej.

### Problem #3: Błędy przy niezdefiniowanych zmiennych ❌
**Przed:** Jeśli nie rozwinąłeś sekcji "Advanced", mogły wystąpić błędy.

**Teraz:** ✅ Defensywne sprawdzanie wszystkich wartości + graceful error handling.

---

## 🚀 Szybki Start

### 1. Pobierz najnowszą wersję z Git

```bash
cd /path/to/Hegemon
git pull origin claude/architect-design-principles-011CUNYjrhH2ZkoSzctJQCcS
```

### 2. Zainstaluj wymagane pakiety

```bash
pip install -r requirements.txt
pip install ipywidgets  # Jeśli jeszcze nie masz
```

### 3. Uruchom przykładowy notebook

```bash
jupyter notebook phase_2_4_example.ipynb
```

### 4. Wykonaj komórki po kolei

Notebook zawiera **10 kroków** z dokładnymi wyjaśnieniami.

---

## 📋 Tryby Interwencji

### `observer` 👀
- Oglądasz checkpointy, ale **nie możesz** ingerować
- Wszystko jest automatycznie zatwierdzane
- Świetne do nauki jak działa system

### `reviewer` ✅❌
- Możesz **zatwierdzać** lub **odrzucać** output
- Nie możesz prosić o rewizje
- Szybka kontrola jakości

### `collaborator` ✏️ (PEŁNA KONTROLA)
- Pełna kontrola: approve/revise/reject
- Możesz dodawać **guidance** dla agentów
- Flagować **priority claims** i **concerns**
- Najbardziej interaktywny tryb

---

## 🎮 Jak używać podczas debaty?

### Krok 1: Checkpoint się pojawia

Widzisz:
- 📊 **Review Package** - podsumowanie output agenta
- 🔍 **Key Points** - najważniejsze twierdzenia
- ⚠️ **Important Claims** - kluczowe fragmenty
- 💡 **Suggested Actions** - co możesz zrobić

### Krok 2: Podejmij decyzję

**Opcja A: Approve ✅**
```
1. Wybierz radio button "✅ Approve"
2. Kliknij "Submit Feedback"
3. Debata kontynuuje z tym outputem
```

**Opcja B: Request Revision ✏️**
```
1. Wybierz "✏️ Request Revision"
2. W text area wpisz SZCZEGÓŁOWE wskazówki (min 10 znaków)
   Przykład:
   "- Dodaj więcej danych liczbowych dla prognozy ROI
    - Uwzględnij GDPR compliance w każdej fazie
    - Rozszerz timeline z 3 do 4-5 miesięcy"
3. Opcjonalnie rozwiń "Advanced: Priority Claims"
4. Kliknij "Submit Feedback"
5. Agent dostanie Twoje wskazówki i przerobiagent output
```

**Opcja C: Reject ❌**
```
1. Wybierz "❌ Reject"
2. Kliknij "Submit Feedback"
3. Debata kończy się natychmiast
```

**Opcja D: Auto-Approve ⏩**
```
1. Jeśli nie chcesz czekać/decydować
2. Kliknij "Auto-Approve"
3. System automatycznie zatwierdza i kontynuuje
```

### Krok 3: Zaawansowane opcje (opcjonalne)

#### Priority Claims ⭐
Rozwiń sekcję i wpisz kluczowe twierdzenia (jedno na linię):
```
Konwersja 15% wymaga walidacji
GDPR musi być explicite w planie
```

#### Flagged Concerns 🚩
Zaznacz wątpliwości dla Sceptyka:
```
Timeline wydaje się zbyt optymistyczny
Budżet na fazę 2 niejasny
```

---

## 💡 Wskazówki i Best Practices

### ✅ DO:
1. **Pisz konkretne wskazówki** przy "Request Revision"
   - ❌ ZŁE: "Popraw to"
   - ✅ DOBRE: "Dodaj analizę kosztów dla każdej fazy workflow"

2. **Używaj Priority Claims** dla kluczowych twierdzeń
   - Pomaga agentom skupić się na najważniejszych rzeczach

3. **Testuj różne tryby**
   - Zacznij od `observer` żeby zobaczyć jak działa
   - Przejdź do `collaborator` dla pełnej kontroli

4. **Korzystaj z "Auto-Approve"**
   - Gdy checkpoint nie wymaga Twojej uwagi
   - Oszczędza czas zamiast czekać 10 min timeout

### ❌ DON'T:
1. **Nie zostawiaj pustego guidance** przy "Request Revision"
   - System wymaga min 10 znaków
   - Pusty guidance nie pomoże agentowi

2. **Nie ignoruj "Low Confidence Claims"**
   - Jeśli widzisz claim z niską pewnością, to dobry moment na ingerencję

3. **Nie używaj `reject` bez powodu**
   - To kończy całą debatę
   - Lepiej użyć `revise` jeśli chcesz poprawek

---

## 🔧 Rozwiązywanie Problemów

### Problem: Widget callbacks nie działają

**Rozwiązanie:**
1. Zrestartuj kernel: `Kernel → Restart & Clear Output`
2. Wykonaj wszystkie komórki ponownie od początku
3. Upewnij się, że `ipywidgets` jest zainstalowane

### Problem: Stare wartości w formularzach

**To powinno być już naprawione!** Ale jeśli nadal występuje:
1. Sprawdź czy używasz najnowszej wersji z git
2. Zrestartuj kernel i uruchom ponownie
3. Sprawdź logi - powinno być widać reset session state

### Problem: Timeout po 10 minutach

**Rozwiązanie:**
1. Użyj przycisku "Auto-Approve" zamiast czekać
2. Lub zmniejsz timeout w `jupyter_ui.py` (linia 444):
   ```python
   timeout_seconds = 300  # 5 minut zamiast 10
   ```

### Problem: Jupyter kernel się zawiesza

**To też powinno być naprawione!** Nowy polling mechanism zapobiega deadlockom.

Jeśli nadal występuje:
1. Zrestartuj kernel
2. Sprawdź czy nie masz innych procesów blokujących kernel
3. Zaktualizuj `ipywidgets` do najnowszej wersji

---

## 📊 Przykład Sesji

```
🎭 DEBATA STARTUJE

Cykl 1:
  ├─ Katalizator generuje tezę
  ├─ 🔴 CHECKPOINT: post_thesis
  │   └─ Ty: "✅ Approve" (dobra teza, kontynuuj)
  ├─ Sceptyk generuje antytezę
  ├─ Gubernator ocenia
  └─ 🔴 CHECKPOINT: post_evaluation
      └─ Ty: "✏️ Revise" + guidance: "Dodaj koszty dla każdej fazy"

Cykl 2:
  ├─ Katalizator uwzględnia Twoje wskazówki
  ├─ 🔴 CHECKPOINT: post_thesis (nowy output)
  │   └─ Ty: "✅ Approve" (super, teraz lepiej!)
  ├─ ... debata kontynuuje ...

Cykl N:
  └─ Syntezator tworzy finalny plan
      └─ 🔴 CHECKPOINT: pre_synthesis
          └─ Ty: "✅ Approve" (zatwierdź synthesis)

✅ KONIEC - Masz finalny plan!
```

---

## 📁 Struktura Plików

```
Hegemon/
├── phase_2_4_example.ipynb          # ← ZACZNIJ TUTAJ
├── PHASE_2_4_INSTRUKCJA.md          # ← TEN PLIK
├── hegemon/
│   ├── hitl/
│   │   ├── jupyter_ui.py            # Naprawiony UI (polling mechanism)
│   │   ├── checkpoint_handler.py    # Obsługa checkpointów
│   │   └── models.py                # Modele danych
│   └── graph_hitl_v3.py             # Graf z checkpointami
└── streamlit_app/
    └── components/
        └── feedback_form.py         # Naprawiony Streamlit form
```

---

## 🎓 Następne Kroki

1. **Przeczytaj notebook** `phase_2_4_example.ipynb` - ma szczegółowe komentarze
2. **Uruchom przykład** z prostą misją testową
3. **Eksperymentuj** z różnymi trybami i guidance
4. **Użyj własnej misji** - zmień `MISSION` na swój case
5. **Sprawdź Streamlit UI** - uruchom `streamlit run streamlit_app/app.py` dla webowego interfejsu

---

## 📞 Pomoc

Jeśli coś nie działa:
1. Sprawdź logi w konsoli
2. Zobacz sekcję "Rozwiązywanie Problemów" powyżej
3. Sprawdź czy masz najnowszą wersję z git

**Dobrej zabawy z HEGEMON Phase 2.4!** 🚀
