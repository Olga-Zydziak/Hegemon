# 📊 HEGEMON - Example Outputs

This folder contains sample outputs from HEGEMON debates to help you understand what the system produces.

## Files

### `sample_output.json`

Complete output from a 5-cycle debate about designing an ML pipeline for an e-commerce company.

**Mission:** Design ML pipeline with $150k budget, 4-month timeline

**Key Elements:**
- **Mission Overview:** High-level summary of the strategic plan
- **Required Agents:** 5 specialized roles with skills (ML Architect, Data Engineer, MLOps, etc.)
- **Workflow:** 12 sequential steps with dependencies
- **Risk Analysis:** Detailed risk assessment with mitigation strategies
- **Debate History:** 16 contributions from 4 agents across 5 cycles
- **Human Interventions:** 2 HITL checkpoint decisions

**Metadata:**
- Consensus Score: 0.85 (reached threshold)
- Debate Time: 240 seconds
- Estimated Cost: $1.25 USD

---

## Understanding the Output

### 1. Mission Overview

A synthesized strategic summary that combines insights from all debate cycles:

```json
{
  "mission_overview": "Design and implement production-ready ML pipeline..."
}
```

### 2. Required Agents

List of specialized roles needed for execution:

```json
{
  "required_agents": [
    {
      "role": "ML Platform Architect",
      "description": "...",
      "required_skills": ["MLflow", "Kubeflow", ...]
    }
  ]
}
```

### 3. Workflow

Step-by-step execution plan with dependencies:

```json
{
  "workflow": [
    {
      "step_id": 1,
      "description": "Identify high-ROI use case...",
      "dependencies": []
    },
    {
      "step_id": 2,
      "description": "Set up infrastructure...",
      "dependencies": [1]
    }
  ]
}
```

**Visualization:**
```
Step 1 (no deps)
  └─> Step 2 (depends on 1)
  └─> Step 3 (depends on 2)
       └─> Step 4 (depends on 3)
            └─> ...
```

### 4. Risk Analysis

Detailed assessment of potential issues and mitigation strategies:

```json
{
  "risk_analysis": "KEY RISKS: (1) Timeline optimism (30% probability)..."
}
```

Includes:
- Risk identification
- Probability estimates
- Mitigation strategies
- Critical success factors

### 5. Debate History

Shows the dialectical process:

```
Cycle 1: Katalizator (Thesis) → Sceptyk (Antithesis) → Gubernator (Evaluation)
         Consensus: 0.45 (below threshold, continue)

Cycle 2: Katalizator (revised Thesis) → Sceptyk (Antithesis) → Gubernator (Evaluation)
         Consensus: 0.62 (improving, continue)

...

Cycle 5: Final Synthesis → Consensus: 0.85 (reached!)
```

### 6. Human Feedback History

Records of HITL interventions:

```json
{
  "human_feedback_history": [
    {
      "checkpoint": "post_thesis",
      "decision": "revise",
      "guidance": "Add budget allocation breakdown...",
      "timestamp": "2025-10-22T12:15:30"
    }
  ]
}
```

**Decisions:**
- `approve` - Continue with current output
- `revise` - Request changes (includes guidance)
- `reject` - End debate (critical issue)

---

## Typical Output Sizes

| Debate Type | File Size | Cycles | Time |
|-------------|-----------|--------|------|
| Simple mission | 50-100 KB | 3-4 | 2-3 min |
| Complex mission | 150-300 KB | 5-7 | 5-8 min |
| With HITL revisions | 200-400 KB | 6-10 | 10-15 min |

---

## Using the Output

### Command Line

```bash
# View full output
cat examples/sample_output.json | jq '.'

# Extract mission overview
cat examples/sample_output.json | jq '.final_plan.mission_overview'

# List required agents
cat examples/sample_output.json | jq '.final_plan.required_agents[].role'

# Show workflow dependencies
cat examples/sample_output.json | jq '.final_plan.workflow[] | {step_id, dependencies}'
```

### Python

```python
import json

with open('examples/sample_output.json', 'r') as f:
    output = json.load(f)

# Access components
print(output['final_plan']['mission_overview'])
print(f"Cycles: {output['debate_summary']['total_cycles']}")
print(f"Consensus: {output['debate_summary']['final_consensus_score']}")

# Iterate through workflow
for step in output['final_plan']['workflow']:
    print(f"Step {step['step_id']}: {step['description']}")
```

---

## Generating Your Own Examples

### Basic Debate

```bash
python main.py --mission "Your mission here" --output examples/my_output.json
```

### With HITL

```bash
jupyter notebook phase_2_4_example.ipynb
# Run all cells, provide feedback at checkpoints
# Output saved to output/hegemon_hitl_*.json
```

### Cloud (Vertex AI)

```bash
jupyter notebook vertex_ai_example.ipynb
# Uses text-based UI, works everywhere
```

---

## Understanding Consensus Scores

| Score Range | Meaning | Action |
|-------------|---------|--------|
| 0.0 - 0.4 | Low consensus, significant disagreement | Continue debate |
| 0.5 - 0.7 | Moderate consensus, some alignment | Continue, nearing synthesis |
| 0.75+ | High consensus, agents agree | Synthesize final plan |

**Threshold:** Configurable via `HEGEMON_CONSENSUS_THRESHOLD` (default: 0.75)

---

## Contributing Examples

Want to add your debate outputs? Please:

1. Anonymize sensitive information
2. Use descriptive mission names
3. Include a brief description
4. Submit PR with output + brief README update

---

## Questions?

See main [README.md](../README.md) for full documentation.
