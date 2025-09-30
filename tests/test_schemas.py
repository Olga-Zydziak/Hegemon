"""
Testy jednostkowe dla schematów HEGEMON (modele Pydantic).

Pokrycie:
- Walidacja wejścia (MissionInput)
- Strukturalne outputy (GovernorEvaluation, FinalPlan)
- AgentContribution validation
- Przypadki brzegowe i złośliwe wejścia
"""

import pytest
from pydantic import ValidationError

from hegemon.schemas import (
    AgentContribution,
    ExecutionAgentSpec,
    FinalPlan,
    GovernorEvaluation,
    MissionInput,
    WorkflowStep,
)


class TestAgentContribution:
    """Suite testów dla AgentContribution."""
    
    def test_valid_contribution(self):
        """Prawidłowy wkład przechodzi walidację."""
        contrib = AgentContribution(
            agent_id="Katalizator",
            content="To jest substancjalny wkład z wystarczającą ilością treści do walidacji.",
            type="Thesis",
            cycle=1,
            rationale="Uzasadnienie z minimum 30 znaków dla walidacji Pydantic.",
        )
        assert contrib.agent_id == "Katalizator"
        assert contrib.type == "Thesis"
        assert contrib.cycle == 1
    
    def test_content_too_short(self):
        """Content < 20 znaków wywołuje ValidationError."""
        with pytest.raises(ValidationError, match="at least 20 characters"):
            AgentContribution(
                agent_id="Sceptyk",
                content="Zbyt krótki",
                type="Antithesis",
                cycle=1,
                rationale="Uzasadnienie z wystarczającą długością do walidacji.",
            )
    
    def test_rationale_too_short(self):
        """Rationale < 30 znaków wywołuje ValidationError."""
        with pytest.raises(ValidationError, match="at least 30 characters"):
            AgentContribution(
                agent_id="Gubernator",
                content="To jest wystarczająco długi content dla walidacji schema.",
                type="Evaluation",
                cycle=2,
                rationale="Zbyt krótkie",
            )
    
    def test_placeholder_content_rejected(self):
        """Placeholder text jak 'lorem ipsum' jest odrzucany."""
        with pytest.raises(ValidationError, match="placeholder"):
            AgentContribution(
                agent_id="Syntezator",
                content="Lorem ipsum dolor sit amet, consectetur adipiscing elit.",
                type="FinalPlan",
                cycle=3,
                rationale="To jest właściwe uzasadnienie z wystarczającą długością.",
            )


class TestGovernorEvaluation:
    """Suite testów dla GovernorEvaluation model."""
    
    def test_valid_evaluation(self):
        """Prawidłowa ocena przechodzi walidację."""
        eval_data = {
            "evaluation_summary": "Katalizator i Sceptyk zbiegli się w kluczowych punktach z drobnymi różnicami pozostałymi do rozwiązania.",
            "consensus_score": 0.75,
            "rationale": "Ocena oparta na analizie zbieżności argumentów i jakości rozumowania przedstawionego przez obydwu agentów.",
        }
        evaluation = GovernorEvaluation(**eval_data)
        assert evaluation.consensus_score == 0.75
    
    def test_consensus_score_out_of_range(self):
        """consensus_score poza [0.0, 1.0] wywołuje ValidationError."""
        with pytest.raises(ValidationError):
            GovernorEvaluation(
                evaluation_summary="Prawidłowy tekst podsumowania z wystarczającą długością do walidacji.",
                consensus_score=1.5,
                rationale="Prawidłowe uzasadnienie z wystarczającą długością do walidacji schema.",
            )
    
    def test_evaluation_summary_too_short(self):
        """Evaluation summary < 50 znaków wywołuje ValidationError."""
        with pytest.raises(ValidationError, match="at least 50 characters"):
            GovernorEvaluation(
                evaluation_summary="Zbyt krótkie",
                consensus_score=0.8,
                rationale="Prawidłowe uzasadnienie z wystarczającą długością dla Pydantic validation.",
            )
    
    def test_placeholder_rejected(self):
        """Placeholder text jest odrzucany."""
        with pytest.raises(ValidationError, match="placeholder"):
            GovernorEvaluation(
                evaluation_summary="Lorem ipsum dolor sit amet consectetur adipiscing elit sed do eiusmod tempor.",
                consensus_score=0.8,
                rationale="Lorem ipsum dolor sit amet consectetur adipiscing elit sed do eiusmod tempor incididunt.",
            )


class TestExecutionAgentSpec:
    """Suite testów dla ExecutionAgentSpec."""
    
    def test_valid_agent_spec(self):
        """Prawidłowa specyfikacja agenta przechodzi walidację."""
        spec = ExecutionAgentSpec(
            role="Data Engineer",
            description="Odpowiedzialny za budowanie data pipeline i zarządzanie infrastrukturą.",
            required_skills=["Apache Spark", "Python", "SQL"],
        )
        assert spec.role == "Data Engineer"
        assert len(spec.required_skills) == 3
    
    def test_empty_skills_rejected(self):
        """Pusta lista umiejętności wywołuje ValidationError."""
        with pytest.raises(ValidationError):
            ExecutionAgentSpec(
                role="ML Engineer",
                description="Odpowiedzialny za budowanie i wdrażanie modeli uczenia maszynowego.",
                required_skills=[],
            )
    
    def test_vague_skill_rejected(self):
        """Mgliste umiejętności (single-word placeholders) są odrzucane."""
        with pytest.raises(ValidationError, match="too vague"):
            ExecutionAgentSpec(
                role="Developer",
                description="Odpowiedzialny za rozwój aplikacji i integracje systemowe.",
                required_skills=["Python", "TODO", "SQL"],
            )


class TestWorkflowStep:
    """Suite testów dla WorkflowStep."""
    
    def test_valid_workflow_step(self):
        """Prawidłowy krok workflow przechodzi walidację."""
        step = WorkflowStep(
            step_id=1,
            description="Przeprowadź audyt energetyczny i zbierz baseline metrics.",
            assigned_agent_role="Data Analyst",
            dependencies=[],
        )
        assert step.step_id == 1
        assert step.dependencies == []
    
    def test_self_dependency_rejected(self):
        """Krok nie może zależeć od samego siebie."""
        with pytest.raises(ValidationError, match="cannot depend on itself"):
            WorkflowStep(
                step_id=2,
                description="Analizuj zebrane dane i generuj raporty insights.",
                assigned_agent_role="Data Scientist",
                dependencies=[1, 2],  # Self-reference!
            )


class TestFinalPlan:
    """Suite testów dla FinalPlan model."""
    
    def test_valid_plan(self):
        """Prawidłowy plan przechodzi walidację."""
        plan_data = {
            "mission_overview": "Strategia redukcji śladu węglowego balansująca ambicję środowiskową z realiami biznesowymi.",
            "required_agents": [
                {
                    "role": "Sustainability Manager",
                    "description": "Zarządza inicjatywami zrównoważonego rozwoju i raportowaniem ESG.",
                    "required_skills": ["ESG Reporting", "Sustainability Strategy"],
                },
            ],
            "workflow": [
                {
                    "step_id": 1,
                    "description": "Przeprowadź kompleksowy audyt energetyczny.",
                    "assigned_agent_role": "Sustainability Manager",
                    "dependencies": [],
                },
            ],
            "risk_analysis": "Kluczowe ryzyka obejmują wysokie koszty początkowe i potencjalną przestarzałość technologii.",
        }
        plan = FinalPlan(**plan_data)
        assert len(plan.required_agents) == 1
        assert len(plan.workflow) == 1
    
    def test_empty_agents_rejected(self):
        """Pusta lista agentów wywołuje ValidationError."""
        with pytest.raises(ValidationError):
            FinalPlan(
                mission_overview="Prawidłowy overview z wystarczającą długością do walidacji schema.",
                required_agents=[],  # Empty!
                workflow=[
                    WorkflowStep(
                        step_id=1,
                        description="Jakiś krok workflow",
                        assigned_agent_role="Role",
                        dependencies=[],
                    )
                ],
                risk_analysis="Prawidłowa analiza ryzyk z wystarczającą długością.",
            )
    
    def test_workflow_dependency_validation(self):
        """Workflow z nieistniejącymi zależnościami jest odrzucany."""
        with pytest.raises(ValidationError, match="non-existent step"):
            FinalPlan(
                mission_overview="Prawidłowy overview misji z wystarczającą długością do walidacji.",
                required_agents=[
                    ExecutionAgentSpec(
                        role="Engineer",
                        description="Jakiś opis z wystarczającą długością",
                        required_skills=["Skill One"],
                    )
                ],
                workflow=[
                    WorkflowStep(
                        step_id=1,
                        description="Pierwszy krok workflow",
                        assigned_agent_role="Engineer",
                        dependencies=[999],  # Nieistniejący krok!
                    ),
                ],
                risk_analysis="Prawidłowa analiza ryzyk z wystarczającą długością do walidacji.",
            )