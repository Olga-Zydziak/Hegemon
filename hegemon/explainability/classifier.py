"""
Concept Classifier using LLM via Vertex AI.

Classifies text into 100-dimensional semantic space via prompted LLM.
Uses Vertex AI (no API key required - uses Application Default Credentials).

Complexity:
- classify(): O(n) where n = text length (LLM call)
- Cache hit: O(1)
"""

from __future__ import annotations

import hashlib
import json
import logging
import time
from typing import Any

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_google_vertexai import ChatVertexAI  # ← ZMIANA: Vertex AI zamiast Generative AI

from hegemon.explainability.concepts import get_concept_dictionary
from hegemon.explainability.exceptions import ClassificationError
from hegemon.explainability.schemas import ConceptVector

logger = logging.getLogger(__name__)

# Constants
MAX_TEXT_LENGTH: int = 50_000
RETRY_ATTEMPTS: int = 3
RETRY_DELAY_SECONDS: float = 2.0
DEFAULT_TEMPERATURE: float = 0.0


class ConceptClassifier:
    """
    LLM-based concept classifier using Vertex AI.

    Analyzes text and assigns activation scores (0.0-1.0) to 100 concepts.
    Uses Gemini Flash via Vertex AI for cost-efficiency.

    Attributes:
        llm: LangChain chat model (Vertex AI)
        model_name: Identifier of LLM used
        cache: LRU cache for classification results

    Complexity:
        - classify: O(n) where n = text length + O(API latency)
        - Cache hit: O(1)
    """

    def __init__(
        self,
        project_id: str,
        location: str,
        model_name: str = "gemini-2.0-flash-exp",
        temperature: float = DEFAULT_TEMPERATURE,
        cache_size: int = 1000,
    ) -> None:
        """
        Initialize classifier with Vertex AI.

        Args:
            project_id: GCP project ID
            location: GCP location (e.g., 'us-central1')
            model_name: Gemini model identifier
            temperature: LLM temperature (0.0 for deterministic)
            cache_size: Max number of cached classifications

        Complexity: O(1)
        """
        self.model_name = model_name
        self.project_id = project_id
        self.location = location
        
        # Initialize Vertex AI client (uses Application Default Credentials)
        self.llm: BaseChatModel = ChatVertexAI(
            model=model_name,
            project=project_id,
            location=location,
            temperature=temperature,
        )

        # Build prompt template (cached across classifications)
        self._system_prompt = self._build_system_prompt()

        # Initialize cache
        self._cache: dict[str, ConceptVector] = {}
        self._cache_size = cache_size

        logger.info(
            f"✅ ConceptClassifier initialized: Vertex AI {model_name} "
            f"(project={project_id}, location={location}), cache_size={cache_size}"
        )

    def _build_system_prompt(self) -> str:
        """
        Build system prompt with concept definitions.

        Complexity: O(n) where n = 100 concepts (one-time cost)
        """
        concept_dict = get_concept_dictionary()

        prompt = """You are a cognitive profiler and semantic analyzer.

TASK: Analyze the provided text and score how strongly each cognitive concept is present (0.0 to 1.0).

SCORING RUBRIC:
- 0.0-0.2: Concept is absent or irrelevant
- 0.2-0.4: Concept is weakly present (mentioned but not central)
- 0.4-0.6: Concept is moderately present (notable theme)
- 0.6-0.8: Concept is strongly present (dominant theme)
- 0.8-1.0: Concept is extremely present (central to entire text)

CRITICAL INSTRUCTIONS (FOLLOW STRICTLY):
1. Base scores ONLY on ACTUAL TEXT CONTENT, not assumptions
2. SPARSE ACTIVATION IS REQUIRED: 70-80 concepts MUST be 0.0-0.3
3. ONLY 10-20 concepts should exceed 0.5 (not more!)
4. ONLY 3-7 concepts should exceed 0.7
5. ONLY 0-2 concepts should be 0.8 or higher
6. Be VERY conservative: when in doubt, score LOWER
7. High scores (>0.7) require EXPLICIT, REPEATED evidence in text
8. If a concept is merely mentioned once, score 0.2-0.4 MAX
9. If a concept is a major theme appearing 3+ times, score 0.5-0.7
10. Reserve 0.8+ for concepts that are THE CENTRAL focus of entire text

REMEMBER: The goal is DISCRIMINATIVE scoring. If everything is high, nothing is meaningful.

"""
        prompt += concept_dict.to_prompt_section()

        prompt += """

OUTPUT FORMAT: Respond with ONLY a valid JSON object mapping concept IDs to scores.
No markdown, no explanation, just the JSON object.

Example:
{
  "risk_aversion": 0.85,
  "innovation_bias": 0.15,
  "analytical_thinking": 0.70,
  ...
}
"""
        return prompt

    def classify(self, text: str) -> ConceptVector | None:
        """
        Classify text into concept vector.

        Args:
            text: Input text to classify

        Returns:
            ConceptVector with scores, or None if classification fails

        Complexity: O(n) where n = len(text), dominated by LLM call
        """
        # Validate input
        if not text or len(text.strip()) < 10:
            logger.warning("Text too short for classification (<10 chars)")
            return self._zero_vector("text_too_short")

        # Truncate if too long
        if len(text) > MAX_TEXT_LENGTH:
            logger.warning(
                f"Text truncated from {len(text)} to {MAX_TEXT_LENGTH} chars"
            )
            text = text[:MAX_TEXT_LENGTH]

        # Check cache
        cache_key = self._compute_cache_key(text)
        if cache_key in self._cache:
            logger.debug(f"✅ Cache HIT for text (key={cache_key[:8]}...)")
            cached = self._cache[cache_key]
            # Return copy with updated cache_hit flag
            return ConceptVector(
                concept_scores=cached.concept_scores,
                timestamp=cached.timestamp,
                model_used=cached.model_used,
                processing_time_ms=0,
                cache_hit=True,
            )

        # Classify with retry logic
        start_time = time.time()
        
        for attempt in range(1, RETRY_ATTEMPTS + 1):
            try:
                concept_scores = self._classify_with_llm(text)
                processing_time_ms = int((time.time() - start_time) * 1000)

                # Create ConceptVector
                vector = ConceptVector(
                    concept_scores=concept_scores,
                    model_used=f"{self.model_name} (Vertex AI)",
                    processing_time_ms=processing_time_ms,
                    cache_hit=False,
                )

                # Cache result
                self._cache_result(cache_key, vector)

                logger.info(
                    f"✅ Classification successful: {processing_time_ms}ms, "
                    f"top_concept={vector.top_k(1)[0]}"
                )
                return vector

            except Exception as e:
                logger.warning(
                    f"Classification attempt {attempt}/{RETRY_ATTEMPTS} failed: {e}"
                )
                if attempt < RETRY_ATTEMPTS:
                    time.sleep(RETRY_DELAY_SECONDS)
                else:
                    logger.error(
                        f"❌ Classification failed after {RETRY_ATTEMPTS} attempts"
                    )
                    return None

        return None

    def _classify_with_llm(self, text: str) -> dict[str, float]:
        """
        Perform actual LLM classification via Vertex AI.

        Args:
            text: Input text

        Returns:
            Dict of concept_id → score

        Raises:
            ClassificationError: If LLM call fails or response is invalid

        Complexity: O(n) + O(API latency)
        """
        # Prepare messages
        messages = [
            SystemMessage(content=self._system_prompt),
            HumanMessage(content=f"TEXT TO ANALYZE:\n\n{text}"),
        ]

        # Call LLM via Vertex AI
        try:
            response = self.llm.invoke(messages)
            response_text = response.content
        except Exception as e:
            raise ClassificationError(
                f"Vertex AI invocation failed: {e}",
                details={
                    "model": self.model_name,
                    "project": self.project_id,
                    "location": self.location,
                    "text_length": len(text)
                },
            ) from e

        # Parse JSON
        try:
            # Clean response (remove markdown if present)
            response_text = response_text.strip()
            if response_text.startswith("```json"):
                response_text = response_text.split("```json")[1]
            if response_text.startswith("```"):
                response_text = response_text.split("```")[1]
            if response_text.endswith("```"):
                response_text = response_text.rsplit("```", 1)[0]
            response_text = response_text.strip()

            concept_scores = json.loads(response_text)
        except json.JSONDecodeError as e:
            raise ClassificationError(
                f"Invalid JSON in LLM response: {e}",
                details={"response": response_text[:500]},
            ) from e

        # Validate structure
        if not isinstance(concept_scores, dict):
            raise ClassificationError(
                "LLM response is not a JSON object",
                details={"type": type(concept_scores).__name__},
            )

        # Validate all concepts present
        expected_ids = get_concept_dictionary().get_all_concept_ids()
        if len(concept_scores) != len(expected_ids):
            # Attempt repair: fill missing with 0.0
            logger.warning(
                f"LLM returned {len(concept_scores)} concepts, "
                f"expected {len(expected_ids)}. Filling missing with 0.0"
            )
            for concept_id in expected_ids:
                if concept_id not in concept_scores:
                    concept_scores[concept_id] = 0.0

        # Validate scores in range
        for concept_id, score in concept_scores.items():
            if not isinstance(score, (int, float)):
                raise ClassificationError(
                    f"Score for '{concept_id}' is not numeric: {score}",
                    details={"concept_id": concept_id, "score": score},
                )
            # Clamp to [0, 1]
            if score < 0.0:
                logger.warning(f"Clamping negative score for '{concept_id}': {score}")
                concept_scores[concept_id] = 0.0
            elif score > 1.0:
                logger.warning(f"Clamping high score for '{concept_id}': {score}")
                concept_scores[concept_id] = 1.0

        return concept_scores

    def _compute_cache_key(self, text: str) -> str:
        """
        Compute cache key for text.

        Uses SHA256 hash of text for collision-free caching.

        Args:
            text: Input text

        Returns:
            64-char hex hash

        Complexity: O(n) where n = len(text)
        """
        return hashlib.sha256(text.encode("utf-8")).hexdigest()

    def _cache_result(self, key: str, vector: ConceptVector) -> None:
        """
        Cache classification result with LRU eviction.

        Args:
            key: Cache key
            vector: ConceptVector to cache

        Complexity: O(1) average
        """
        # Simple LRU: if cache full, remove oldest
        if len(self._cache) >= self._cache_size:
            # Remove first item (oldest in insertion order for dict)
            oldest_key = next(iter(self._cache))
            del self._cache[oldest_key]
            logger.debug(f"Cache eviction: removed {oldest_key[:8]}...")

        self._cache[key] = vector

    def _zero_vector(self, reason: str) -> ConceptVector:
        """
        Create zero vector (all concepts = 0.0).

        Args:
            reason: Reason for zero vector (for logging)

        Returns:
            ConceptVector with all zeros

        Complexity: O(n) where n = 100
        """
        logger.info(f"Returning zero vector: {reason}")
        concept_ids = get_concept_dictionary().get_all_concept_ids()
        
        return ConceptVector(
            concept_scores={cid: 0.0 for cid in concept_ids},
            model_used=f"{self.model_name} (Vertex AI)",
            processing_time_ms=0,
            cache_hit=False,
        )

    def get_cache_stats(self) -> dict[str, Any]:
        """
        Get cache statistics.

        Returns:
            Dict with cache metrics

        Complexity: O(1)
        """
        return {
            "cache_size": len(self._cache),
            "cache_max_size": self._cache_size,
            "cache_utilization": len(self._cache) / self._cache_size,
        }