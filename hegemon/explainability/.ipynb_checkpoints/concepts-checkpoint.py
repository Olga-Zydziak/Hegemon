"""
Concept Dictionary Loader and Manager.

Handles loading, validation, and access to the 100-concept dictionary.
Implements singleton pattern for efficient memory usage.

Complexity:
- Loading: O(n) where n = 100 concepts (one-time cost)
- Access: O(1) via dict lookup
"""

from __future__ import annotations

import json
import logging
from functools import lru_cache
from pathlib import Path
from typing import Final

from hegemon.explainability.exceptions import ConceptDictionaryError
from hegemon.explainability.schemas import Concept

logger = logging.getLogger(__name__)

# Constants
EXPECTED_CONCEPT_COUNT: Final[int] = 100
CONCEPTS_FILE_NAME: Final[str] = "concepts.json"


class ConceptDictionary:
    """
    Manager for concept dictionary.

    Loads concepts from JSON file and provides efficient access.
    Implements singleton pattern via module-level caching.

    Attributes:
        concepts: List of all Concept objects
        concepts_by_id: Dict for O(1) lookup by concept ID
        concepts_by_category: Dict grouping concepts by category

    Complexity:
        - __init__: O(n) where n = 100
        - get_concept: O(1)
        - get_concepts_by_category: O(1)
    """

    def __init__(self, concepts_file_path: Path) -> None:
        """
        Initialize concept dictionary from JSON file.

        Args:
            concepts_file_path: Path to concepts.json

        Raises:
            ConceptDictionaryError: If file not found, invalid JSON, or validation fails

        Complexity: O(n) where n = 100 concepts
        """
        self.concepts: list[Concept] = []
        self.concepts_by_id: dict[str, Concept] = {}
        self.concepts_by_category: dict[str, list[Concept]] = {}

        try:
            self._load_concepts(concepts_file_path)
            self._validate_dictionary()
            self._build_indices()
            logger.info(
                f"✅ Loaded {len(self.concepts)} concepts from {concepts_file_path}"
            )
        except Exception as e:
            raise ConceptDictionaryError(
                f"Failed to load concept dictionary: {e}",
                details={"file_path": str(concepts_file_path)},
            ) from e

    def _load_concepts(self, file_path: Path) -> None:
        """
        Load concepts from JSON file.

        Complexity: O(n)
        """
        if not file_path.exists():
            raise FileNotFoundError(f"Concepts file not found: {file_path}")

        with open(file_path, "r", encoding="utf-8") as f:
            concepts_data = json.load(f)

        if not isinstance(concepts_data, list):
            raise ValueError("Concepts file must contain a JSON array")

        # Parse and validate with Pydantic
        for i, concept_dict in enumerate(concepts_data):
            try:
                concept = Concept(**concept_dict)
                self.concepts.append(concept)
            except Exception as e:
                raise ValueError(
                    f"Invalid concept at index {i}: {e}. Data: {concept_dict}"
                ) from e

    def _validate_dictionary(self) -> None:
        """
        Validate dictionary completeness and consistency.

        Complexity: O(n)
        """
        # Check count
        if len(self.concepts) != EXPECTED_CONCEPT_COUNT:
            raise ValueError(
                f"Expected {EXPECTED_CONCEPT_COUNT} concepts, "
                f"got {len(self.concepts)}"
            )

        # Check uniqueness
        concept_ids = [c.id for c in self.concepts]
        if len(concept_ids) != len(set(concept_ids)):
            duplicates = [
                cid for cid in concept_ids if concept_ids.count(cid) > 1
            ]
            raise ValueError(f"Duplicate concept IDs found: {duplicates}")

        # Check category distribution (each should have ~10 concepts)
        categories = [c.category for c in self.concepts]
        category_counts = {cat: categories.count(cat) for cat in set(categories)}
        
        for cat, count in category_counts.items():
            if count < 8 or count > 12:
                logger.warning(
                    f"Category '{cat}' has {count} concepts "
                    f"(expected 8-12 for balance)"
                )

    def _build_indices(self) -> None:
        """
        Build lookup dictionaries for efficient access.

        Complexity: O(n)
        """
        # By ID
        self.concepts_by_id = {c.id: c for c in self.concepts}

        # By category
        for concept in self.concepts:
            if concept.category not in self.concepts_by_category:
                self.concepts_by_category[concept.category] = []
            self.concepts_by_category[concept.category].append(concept)

    def get_concept(self, concept_id: str) -> Concept | None:
        """
        Get concept by ID.

        Args:
            concept_id: Concept identifier

        Returns:
            Concept object or None if not found

        Complexity: O(1)
        """
        return self.concepts_by_id.get(concept_id)

    def get_concepts_by_category(self, category: str) -> list[Concept]:
        """
        Get all concepts in a category.

        Args:
            category: Category name

        Returns:
            List of concepts in category (empty if category not found)

        Complexity: O(1)
        """
        return self.concepts_by_category.get(category, [])

    def get_all_concept_ids(self) -> list[str]:
        """
        Get ordered list of all concept IDs.

        Returns:
            List of 100 concept IDs (sorted alphabetically for consistency)

        Complexity: O(n log n) for sorting
        """
        return sorted(self.concepts_by_id.keys())

    def to_prompt_section(self) -> str:
        """
        Generate formatted string for LLM prompt.

        Returns:
            Multi-line string with all concepts and definitions

        Complexity: O(n)
        """
        lines = ["CONCEPTS (100 total):", ""]

        for category, concepts in self.concepts_by_category.items():
            lines.append(f"## {category}")
            for concept in concepts:
                lines.append(
                    f"- {concept.id}: {concept.definition}"
                )
            lines.append("")

        return "\n".join(lines)


@lru_cache(maxsize=1)
def get_concept_dictionary() -> ConceptDictionary:
    """
    Get singleton ConceptDictionary instance.

    Uses functools.lru_cache for thread-safe singleton.
    Dictionary is loaded once per process.

    Returns:
        Singleton ConceptDictionary instance

    Raises:
        ConceptDictionaryError: If loading fails

    Complexity: O(n) first call, O(1) subsequent calls
    """
    # Determine path to concepts.json
    # Assumes concepts.json is in same directory as this file
    concepts_dir = Path(__file__).parent / "data"
    concepts_file = concepts_dir / CONCEPTS_FILE_NAME

    return ConceptDictionary(concepts_file)