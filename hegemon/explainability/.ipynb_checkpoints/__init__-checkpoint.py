"""
Hegemon Explainability Package.

Public API for explainability features (Layer 6: Semantic Fingerprint).

Usage:
    from hegemon.explainability import get_explainability_collector

    collector = get_explainability_collector(settings)
    bundle = collector.collect(agent_id="Katalizator", content="...", cycle=1)
"""

from hegemon.explainability.classifier import ConceptClassifier
from hegemon.explainability.collector import ExplainabilityCollector
from hegemon.explainability.concepts import get_concept_dictionary
from hegemon.explainability.exceptions import (
    CacheError,
    ClassificationError,
    ConceptDictionaryError,
    ExplainabilityError,
    ValidationError,
)
from hegemon.explainability.schemas import (
    Concept,
    ConceptVector,
    ExplainabilityBundle,
)
from hegemon.explainability.visualizer import HeatmapGenerator

__all__ = [
    # Core classes
    "ConceptClassifier",
    "ExplainabilityCollector",
    "HeatmapGenerator",
    # Schemas
    "Concept",
    "ConceptVector",
    "ExplainabilityBundle",
    # Exceptions
    "ExplainabilityError",
    "ClassificationError",
    "ValidationError",
    "ConceptDictionaryError",
    "CacheError",
    # Utilities
    "get_concept_dictionary",
]