# Epistemic Uncertainty Analysis

Comparison of claim confidence across agents and debate cycles.

## Summary by Agent

### Gubernator

| Cycle | Claims | Avg Conf | High | Med | Low |
|-------|--------|----------|------|-----|-----|
| 1 | 10 | 0.74 | 9 | 1 | 0 |
| 2 | 10 | 0.69 | 7 | 3 | 0 |
| 3 | 10 | 0.76 | 8 | 2 | 0 |

### Katalizator

| Cycle | Claims | Avg Conf | High | Med | Low |
|-------|--------|----------|------|-----|-----|
| 1 | 13 | 0.78 | 11 | 2 | 0 |
| 2 | 13 | 0.72 | 9 | 3 | 1 |
| 3 | 15 | 0.61 | 7 | 5 | 3 |

### Sceptyk

| Cycle | Claims | Avg Conf | High | Med | Low |
|-------|--------|----------|------|-----|-----|
| 1 | 9 | 0.63 | 4 | 5 | 0 |
| 2 | 5 | 0.66 | 3 | 2 | 0 |
| 3 | 14 | 0.65 | 7 | 7 | 0 |

### Syntezator

| Cycle | Claims | Avg Conf | High | Med | Low |
|-------|--------|----------|------|-----|-----|
| 3 | 15 | 0.77 | 14 | 1 | 0 |

## Summary by Cycle

### Cycle 1

| Agent | Claims | Avg Conf | Evidence Basis |
|-------|--------|----------|----------------|
| Gubernator | 10 | 0.74 | EvidenceBasis.FACTS(2), EvidenceBasis.REASONING(8) |
| Katalizator | 13 | 0.78 | EvidenceBasis.DOMAIN_KNOWLEDGE(3), EvidenceBasis.FACTS(8), EvidenceBasis.REASONING(2) |
| Sceptyk | 9 | 0.63 | EvidenceBasis.DOMAIN_KNOWLEDGE(4), EvidenceBasis.REASONING(5) |

### Cycle 2

| Agent | Claims | Avg Conf | Evidence Basis |
|-------|--------|----------|----------------|
| Gubernator | 10 | 0.69 | EvidenceBasis.FACTS(1), EvidenceBasis.REASONING(9) |
| Katalizator | 13 | 0.72 | EvidenceBasis.DOMAIN_KNOWLEDGE(4), EvidenceBasis.FACTS(6), EvidenceBasis.REASONING(3) |
| Sceptyk | 5 | 0.66 | EvidenceBasis.DOMAIN_KNOWLEDGE(2), EvidenceBasis.REASONING(3) |

### Cycle 3

| Agent | Claims | Avg Conf | Evidence Basis |
|-------|--------|----------|----------------|
| Gubernator | 10 | 0.76 | EvidenceBasis.FACTS(3), EvidenceBasis.REASONING(7) |
| Katalizator | 15 | 0.61 | EvidenceBasis.DOMAIN_KNOWLEDGE(5), EvidenceBasis.FACTS(3), EvidenceBasis.HEURISTICS(3), EvidenceBasis.REASONING(4) |
| Sceptyk | 14 | 0.65 | EvidenceBasis.DOMAIN_KNOWLEDGE(8), EvidenceBasis.REASONING(6) |
| Syntezator | 15 | 0.77 | EvidenceBasis.DOMAIN_KNOWLEDGE(1), EvidenceBasis.FACTS(7), EvidenceBasis.REASONING(7) |

## Low Confidence Claims (Risk Flags)

Claims with confidence < 0.5 requiring verification:

### Katalizator (Cycle 2)

- **[0.40]** Reasoning: Customer satisfaction scores should increase by 8-12 points through faster response times and reduced wait periods.

### Katalizator (Cycle 3)

- **[0.40]** Heuristics: Expected outcome of phase one: 15% cost reduction from volume deflection, baseline CSAT maintenance.
- **[0.40]** Heuristics: Expected outcome of phase two: additional 12% cost reduction from improved agent productivity, 5-8 point CSAT improvement from faster, more consistent...
- **[0.40]** Heuristics: This approach delivers 32% total cost reduction ($480K annual savings) while improving CSAT by 6-10 points through faster resolution and 24/7 availabi...
