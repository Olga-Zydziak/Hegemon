"""
Explainability Collector (orchestrates all layers).

Coordinates collection of all explainability layers:
- Layer 6: Semantic Fingerprint (concept activation)
- Layer 2: Epistemic Uncertainty (claim confidence)

Complexity:
- collect(): O(n) where n = content length, dominated by classifier + extractor
"""

from __future__ import annotations

import logging
from typing import Any

from hegemon.config.settings import HegemonSettings
from hegemon.explainability.classifier import ConceptClassifier
from hegemon.explainability.epistemic import ClaimExtractor
from hegemon.explainability.schemas import (
    ConceptVector,
    EpistemicProfile,
    ExplainabilityBundle,
)

logger = logging.getLogger(__name__)


class ExplainabilityCollector:
    """
    Orchestrates collection of all explainability layers.

    Coordinates semantic fingerprinting (Layer 6) and epistemic uncertainty
    (Layer 2) extraction for agent outputs.

    Attributes:
        settings: Application settings
        classifier: Semantic fingerprint classifier
        claim_extractor: Epistemic claim extractor (optional)

    Complexity:
        - collect(): O(n) where n = len(content), parallel layer execution
    """

    def __init__(
        self,
        settings: HegemonSettings,
        classifier: ConceptClassifier,
        claim_extractor: ClaimExtractor | None = None,
    ) -> None:
        """
        Initialize explainability collector.

        Args:
            settings: Application settings
            classifier: Configured classifier instance
            claim_extractor: Optional claim extractor for Layer 2

        Complexity: O(1)
        """
        self.settings = settings
        self.classifier = classifier
        self.claim_extractor = claim_extractor

        logger.info("✅ ExplainabilityCollector initialized")

    def collect(
        self,
        agent_id: str,
        content: str,
        cycle: int,
    ) -> ExplainabilityBundle | None:
        """
        Collect explainability data for agent output.

        Args:
            agent_id: Agent identifier (Katalizator, Sceptyk, etc.)
            content: Agent output text
            cycle: Debate cycle number

        Returns:
            ExplainabilityBundle or None if collection disabled/failed

        Complexity: O(n) where n = len(content), dominated by classification
        """
        # Check if explainability enabled
        if not self.settings.explainability_enabled:
            logger.debug("Explainability disabled, skipping collection")
            return None

        logger.info(
            f"🔍 Collecting explainability for {agent_id} (Cycle {cycle})"
        )

        try:
            # Layer 6: Semantic Fingerprint
            semantic_vector = None
            if self.settings.explainability_semantic_fingerprint:
                semantic_vector = self._collect_semantic_fingerprint(content)
                if semantic_vector is None:
                    logger.warning(
                        f"❌ Semantic fingerprint failed for {agent_id}"
                    )

            # Layer 2: Epistemic Uncertainty
            epistemic_profile = None
            if (
                self.settings.explainability_epistemic_uncertainty
                and self.claim_extractor is not None
            ):
                epistemic_profile = self._collect_epistemic_profile(content)
                if epistemic_profile is None:
                    logger.warning(
                        f"❌ Epistemic profile failed for {agent_id}"
                    )

            # Create bundle (return None if both layers failed)
            if semantic_vector is None and epistemic_profile is None:
                logger.warning(
                    f"⚠️ All explainability layers failed for {agent_id}"
                )
                return None

            bundle = ExplainabilityBundle(
                semantic_fingerprint=semantic_vector,
                epistemic_profile=epistemic_profile,
            )

            # Log success with layer details
            layers_collected = []
            if semantic_vector:
                layers_collected.append(
                    f"L6({semantic_vector.processing_time_ms}ms)"
                )
            if epistemic_profile:
                layers_collected.append(
                    f"L2({epistemic_profile.processing_time_ms}ms, "
                    f"{len(epistemic_profile.claims)} claims)"
                )

            logger.info(
                f"✅ Explainability collected for {agent_id}: "
                f"{', '.join(layers_collected)}"
            )

            return bundle

        except Exception as e:
            logger.error(
                f"❌ Explainability collection failed for {agent_id}: {e}",
                exc_info=True,
            )
            # Graceful degradation: return None, don't block agent
            return None

    def _collect_semantic_fingerprint(
        self, content: str
    ) -> ConceptVector | None:
        """
        Collect semantic fingerprint (Layer 6).

        Args:
            content: Text to classify

        Returns:
            ConceptVector or None if classification fails

        Complexity: O(n) where n = len(content)
        """
        try:
            vector = self.classifier.classify(content)
            return vector
        except Exception as e:
            logger.error(f"Semantic fingerprint classification failed: {e}")
            return None

    def _collect_epistemic_profile(
        self, content: str
    ) -> EpistemicProfile | None:
        """
        Collect epistemic profile (Layer 2).

        Args:
            content: Text to analyze

        Returns:
            EpistemicProfile or None if extraction fails

        Complexity: O(n) where n = len(content)
        """
        try:
            profile = self.claim_extractor.extract_claims(content)
            return profile
        except Exception as e:
            logger.error(f"Epistemic profile extraction failed: {e}")
            return None

    def get_stats(self) -> dict[str, Any]:
        """
        Get collector statistics.

        Returns:
            Dict with collector metrics

        Complexity: O(1)
        """
        stats = {
            "layers_enabled": [],
            "classifier_model": self.classifier.model_name,
        }

        if self.settings.explainability_semantic_fingerprint:
            stats["layers_enabled"].append("Layer 6 (Semantic Fingerprint)")
            stats["classifier_cache"] = self.classifier.get_cache_stats()

        if (
            self.settings.explainability_epistemic_uncertainty
            and self.claim_extractor is not None
        ):
            stats["layers_enabled"].append("Layer 2 (Epistemic Uncertainty)")
            stats["extractor_model"] = self.claim_extractor.model_name

        return stats
    
# ============================================================================
# Global Collector Instance (Singleton Pattern)
# ============================================================================

_collector_instance: ExplainabilityCollector | None = None


def get_explainability_collector() -> ExplainabilityCollector | None:
    """
    Get global explainability collector instance.
    
    Returns singleton instance if explainability is enabled,
    None otherwise.
    
    Returns:
        ExplainabilityCollector instance or None
    
    Complexity: O(1)
    """
    global _collector_instance
    
    try:
        from hegemon.config import get_settings
        
        settings = get_settings()
        
        if not settings.explainability.enabled:
            return None
        
        # Lazy initialization
        if _collector_instance is None:
            _collector_instance = ExplainabilityCollector(settings=settings)
        
        return _collector_instance
        
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.warning(f"Failed to get explainability collector: {e}")
        return None