# Epistemic Uncertainty Analysis

Comparison of claim confidence across agents and debate cycles.

## Summary by Agent

### Gubernator

| Cycle | Claims | Avg Conf | High | Med | Low |
|-------|--------|----------|------|-----|-----|
| 1 | 10 | 0.82 | 9 | 1 | 0 |
| 2 | 11 | 0.73 | 7 | 4 | 0 |
| 3 | 8 | 0.79 | 7 | 1 | 0 |
| 4 | 11 | 0.75 | 9 | 2 | 0 |
| 5 | 8 | 0.76 | 6 | 2 | 0 |

### Katalizator

| Cycle | Claims | Avg Conf | High | Med | Low |
|-------|--------|----------|------|-----|-----|
| 1 | 14 | 0.56 | 5 | 6 | 3 |
| 2 | 15 | 0.73 | 12 | 2 | 1 |
| 3 | 14 | 0.67 | 10 | 4 | 0 |
| 4 | 11 | 0.66 | 6 | 5 | 0 |
| 5 | 14 | 0.63 | 7 | 7 | 0 |

### Sceptyk

| Cycle | Claims | Avg Conf | High | Med | Low |
|-------|--------|----------|------|-----|-----|
| 1 | 3 | 0.57 | 1 | 1 | 1 |
| 2 | 4 | 0.75 | 3 | 1 | 0 |
| 3 | 3 | 0.57 | 1 | 1 | 1 |
| 4 | 10 | 0.63 | 4 | 6 | 0 |
| 5 | 9 | 0.76 | 9 | 0 | 0 |

### Syntezator

| Cycle | Claims | Avg Conf | High | Med | Low |
|-------|--------|----------|------|-----|-----|
| 5 | 15 | 0.66 | 10 | 4 | 1 |

## Summary by Cycle

### Cycle 1

| Agent | Claims | Avg Conf | Evidence Basis |
|-------|--------|----------|----------------|
| Gubernator | 10 | 0.82 | EvidenceBasis.FACTS(4), EvidenceBasis.REASONING(6) |
| Katalizator | 14 | 0.56 | EvidenceBasis.DOMAIN_KNOWLEDGE(8), EvidenceBasis.HEURISTICS(1), EvidenceBasis.REASONING(4), EvidenceBasis.SPECULATION(1) |
| Sceptyk | 3 | 0.57 | EvidenceBasis.REASONING(3) |

### Cycle 2

| Agent | Claims | Avg Conf | Evidence Basis |
|-------|--------|----------|----------------|
| Gubernator | 11 | 0.73 | EvidenceBasis.FACTS(4), EvidenceBasis.REASONING(7) |
| Katalizator | 15 | 0.73 | EvidenceBasis.DOMAIN_KNOWLEDGE(6), EvidenceBasis.FACTS(7), EvidenceBasis.HEURISTICS(1), EvidenceBasis.REASONING(1) |
| Sceptyk | 4 | 0.75 | EvidenceBasis.DOMAIN_KNOWLEDGE(3), EvidenceBasis.REASONING(1) |

### Cycle 3

| Agent | Claims | Avg Conf | Evidence Basis |
|-------|--------|----------|----------------|
| Gubernator | 8 | 0.79 | EvidenceBasis.DOMAIN_KNOWLEDGE(1), EvidenceBasis.FACTS(6), EvidenceBasis.REASONING(1) |
| Katalizator | 14 | 0.67 | EvidenceBasis.DOMAIN_KNOWLEDGE(10), EvidenceBasis.HEURISTICS(3), EvidenceBasis.REASONING(1) |
| Sceptyk | 3 | 0.57 | EvidenceBasis.DOMAIN_KNOWLEDGE(1), EvidenceBasis.HEURISTICS(1), EvidenceBasis.REASONING(1) |

### Cycle 4

| Agent | Claims | Avg Conf | Evidence Basis |
|-------|--------|----------|----------------|
| Gubernator | 11 | 0.75 | EvidenceBasis.DOMAIN_KNOWLEDGE(2), EvidenceBasis.FACTS(3), EvidenceBasis.REASONING(6) |
| Katalizator | 11 | 0.66 | EvidenceBasis.DOMAIN_KNOWLEDGE(8), EvidenceBasis.HEURISTICS(2), EvidenceBasis.REASONING(1) |
| Sceptyk | 10 | 0.63 | EvidenceBasis.DOMAIN_KNOWLEDGE(5), EvidenceBasis.REASONING(5) |

### Cycle 5

| Agent | Claims | Avg Conf | Evidence Basis |
|-------|--------|----------|----------------|
| Gubernator | 8 | 0.76 | EvidenceBasis.DOMAIN_KNOWLEDGE(1), EvidenceBasis.FACTS(3), EvidenceBasis.REASONING(4) |
| Katalizator | 14 | 0.63 | EvidenceBasis.DOMAIN_KNOWLEDGE(7), EvidenceBasis.FACTS(1), EvidenceBasis.REASONING(6) |
| Sceptyk | 9 | 0.76 | EvidenceBasis.DOMAIN_KNOWLEDGE(2), EvidenceBasis.REASONING(7) |
| Syntezator | 15 | 0.66 | EvidenceBasis.DOMAIN_KNOWLEDGE(14), EvidenceBasis.REASONING(1) |

## Low Confidence Claims (Risk Flags)

Claims with confidence < 0.5 requiring verification:

### Katalizator (Cycle 1)

- **[0.40]** Heuristics: ROI for the 'platform team of one' model appears after the third deployed model.
- **[0.40]** Reasoning: Within 12 months, a 70% reduction in time-to-production is expected.
- **[0.30]** Speculation: Within 12 months, a 3-4x increase in the number of experiments is expected due to reduced friction.

### Sceptyk (Cycle 1)

- **[0.40]** Reasoning: The proposal drastically underestimates initial...

### Katalizator (Cycle 2)

- **[0.40]** Reasoning: Expected results after 18 months include idea-to-production time below 1 week, 15+ models in production, 50% reduction in ML infrastructure maintenanc...

### Sceptyk (Cycle 3)

- **[0.40]** Heuristics: Planowane 8 tygodni na wdrożenie produkcyjnej warstwy Reproducibility & Observability (MLflow, Prometheus) dla 3-

### Syntezator (Cycle 5)

- **[0.40]** Reasoning: The expected outcome is a 70% reduction in deployment time and 15+ models by year-end.
