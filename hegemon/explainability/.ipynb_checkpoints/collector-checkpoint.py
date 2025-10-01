"""
Explainability Collector.

Orchestrates collection of explainability data for agent outputs.
Acts as facade between agents and classifiers.

Complexity: O(1) orchestration + O(n) for classification
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from hegemon.explainability.classifier import ConceptClassifier
from hegemon.explainability.exceptions import ExplainabilityError
from hegemon.explainability.schemas import ExplainabilityBundle

if TYPE_CHECKING:
    from hegemon.config.settings import HegemonSettings

logger = logging.getLogger(__name__)


class ExplainabilityCollector:
    """
    Collector for explainability data.

    Coordinates classification and bundles results into ExplainabilityBundle.

    Attributes:
        settings: Hegemon settings
        classifier: ConceptClassifier instance

    Complexity: O(1) for orchestration, classification dominates
    """

    def __init__(
        self,
        settings: HegemonSettings,
        classifier: ConceptClassifier,
    ) -> None:
        """
        Initialize collector.

        Args:
            settings: Application settings
            classifier: Configured classifier instance

        Complexity: O(1)
        """
        self.settings = settings
        self.classifier = classifier

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

        # Check if semantic fingerprint layer enabled
        if not self.settings.explainability_semantic_fingerprint:
            logger.debug("Semantic fingerprint disabled, skipping")
            return None

        logger.info(
            f"🔍 Collecting explainability for {agent_id} (Cycle {cycle})"
        )

        try:
            # Collect Layer 6: Semantic Fingerprint
            semantic_vector = self._collect_semantic_fingerprint(content)

            if semantic_vector is None:
                logger.warning(
                    f"❌ Semantic fingerprint collection failed for {agent_id}"
                )
                return None

            # Create bundle (only Layer 6 for now)
            bundle = ExplainabilityBundle(
                semantic_fingerprint=semantic_vector
            )

            logger.info(
                f"✅ Explainability collected for {agent_id}: "
                f"latency={semantic_vector.processing_time_ms}ms, "
                f"cache={'HIT' if semantic_vector.cache_hit else 'MISS'}"
            )

            return bundle

        except Exception as e:
            logger.error(
                f"❌ Explainability collection failed for {agent_id}: {e}",
                exc_info=True,
            )
            # Graceful degradation: return None, don't block agent
            return None

    def _collect_semantic_fingerprint(self, content: str):
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

    def get_stats(self) -> dict[str, any]:
        """
        Get collector statistics.

        Returns:
            Dict with metrics (cache stats, etc.)

        Complexity: O(1)
        """
        return {
            "classifier_cache": self.classifier.get_cache_stats(),
        }