"""
Epistemic Uncertainty Extractor (Layer 2).

Extracts claims with confidence scores and evidence basis from text.
Uses LLM to parse agent output and assign epistemic metadata.

Complexity:
- extract_claims(): O(n) where n = text length (dominated by LLM call)
"""

from __future__ import annotations

import json
import logging
import time
from typing import Any

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_google_vertexai import ChatVertexAI

from hegemon.explainability.exceptions import ClassificationError
from hegemon.explainability.schemas import EpistemicClaim, EpistemicProfile, EvidenceBasis

logger = logging.getLogger(__name__)

# Constants
MAX_TEXT_LENGTH: int = 50_000
RETRY_ATTEMPTS: int = 2
RETRY_DELAY_SECONDS: float = 1.0
DEFAULT_TEMPERATURE: float = 0.0


class ClaimExtractor:
    """
    LLM-based claim extractor for epistemic uncertainty.
    
    Parses agent output into claims with confidence scores and evidence basis.
    Uses Gemini Flash via Vertex AI for cost-efficiency.
    
    Attributes:
        llm: LangChain chat model (Vertex AI)
        model_name: Identifier of LLM used
    
    Complexity:
        - extract_claims: O(n) where n = text length + O(API latency)
    """
    
    def __init__(
        self,
        project_id: str,
        location: str,
        model_name: str = "gemini-2.0-flash-exp",
        temperature: float = DEFAULT_TEMPERATURE,
    ) -> None:
        """
        Initialize claim extractor with Vertex AI.
        
        Args:
            project_id: GCP project ID
            location: GCP location
            model_name: Gemini model identifier
            temperature: LLM temperature (0.0 for deterministic)
        
        Complexity: O(1)
        """
        self.model_name = model_name
        self.project_id = project_id
        self.location = location
        
        # Initialize Vertex AI client
        self.llm: BaseChatModel = ChatVertexAI(
            model=model_name,
            project=project_id,
            location=location,
            temperature=temperature,
        )
        
        # Build prompt
        self._system_prompt = self._build_system_prompt()
        
        logger.info(
            f"ClaimExtractor initialized: Vertex AI {model_name} "
            f"(project={project_id}, location={location})"
        )
    
    def _build_system_prompt(self) -> str:
        """
        Build system prompt for claim extraction.
        
        Complexity: O(1)
        """
        return """You are an epistemic analyst. Your task is to extract claims from text and annotate each with:
1. Confidence score (0.0-1.0): How certain is the claim?
2. Evidence basis: What type of evidence supports it?

CONFIDENCE SCORING RUBRIC:
- 0.8-1.0: Verifiable facts, explicit data (e.g., "Budget is $500k")
- 0.6-0.8: Established best practices, domain knowledge (e.g., "Agile works well for startups")
- 0.4-0.6: Logical reasoning, educated estimates (e.g., "6 months seems feasible based on scope")
- 0.2-0.4: Heuristics, rules of thumb (e.g., "Usually takes 2x longer than planned")
- 0.0-0.2: Pure speculation, assumptions (e.g., "This might work if conditions align")

EVIDENCE BASIS TYPES:
- Facts: Verifiable, objective data (metrics, dates, laws, explicit constraints)
- Domain_Knowledge: Established best practices, industry standards, proven methodologies
- Reasoning: Logical inference from premises, deductive/inductive reasoning
- Heuristics: Rules of thumb, pattern matching, "usually X leads to Y"
- Speculation: Assumptions, guesses, "might", "could", "possibly"

EXTRACTION GUIDELINES:
1. Extract 5-15 key claims (not every sentence)
2. Focus on actionable/substantive claims, skip filler
3. Each claim should be 1-3 sentences max
4. Be honest about confidence - low scores are OK and valuable
5. Claims about future outcomes default to 0.3-0.5 unless strong evidence

OUTPUT FORMAT: Respond with ONLY valid JSON matching this schema:
{
  "claims": [
    {
      "claim_text": "The exact statement from text",
      "confidence": 0.75,
      "evidence_basis": "Domain_Knowledge"
    }
  ]
}

No markdown, no explanation, just JSON."""
    
    def extract_claims(self, text: str) -> EpistemicProfile | None:
        """
        Extract claims with epistemic metadata from text.
        
        Args:
            text: Input text to analyze
        
        Returns:
            EpistemicProfile with claims, or None if extraction fails
        
        Complexity: O(n) where n = len(text), dominated by LLM call
        """
        # Validate input
        if not text or len(text.strip()) < 50:
            logger.warning("Text too short for claim extraction (<50 chars)")
            return self._empty_profile("text_too_short")
        
        # Truncate if too long
        if len(text) > MAX_TEXT_LENGTH:
            logger.warning(
                f"Text truncated from {len(text)} to {MAX_TEXT_LENGTH} chars"
            )
            text = text[:MAX_TEXT_LENGTH]
        
        # Extract with retry
        start_time = time.time()
        
        for attempt in range(1, RETRY_ATTEMPTS + 1):
            try:
                claims = self._extract_with_llm(text)
                processing_time_ms = int((time.time() - start_time) * 1000)
                
                # Create profile
                profile = EpistemicProfile(
                    claims=claims,
                    model_used=f"{self.model_name} (Vertex AI)",
                    processing_time_ms=processing_time_ms,
                )
                
                logger.info(
                    f"Claim extraction successful: {len(claims)} claims, "
                    f"{processing_time_ms}ms, avg_conf={profile.aggregate_confidence:.2f}"
                )
                return profile
            
            except Exception as e:
                logger.warning(
                    f"Extraction attempt {attempt}/{RETRY_ATTEMPTS} failed: {e}"
                )
                if attempt < RETRY_ATTEMPTS:
                    time.sleep(RETRY_DELAY_SECONDS)
                else:
                    logger.error(
                        f"Claim extraction failed after {RETRY_ATTEMPTS} attempts"
                    )
                    return None
        
        return None
    
    def _extract_with_llm(self, text: str) -> list[EpistemicClaim]:
        """
        Perform actual LLM extraction.
        
        Args:
            text: Input text
        
        Returns:
            List of epistemic claims
        
        Raises:
            ClassificationError: If LLM call fails or response invalid
        
        Complexity: O(n) + O(API latency)
        """
        # Prepare messages
        messages = [
            SystemMessage(content=self._system_prompt),
            HumanMessage(content=f"TEXT TO ANALYZE:\n\n{text}"),
        ]
        
        # Call LLM
        try:
            response = self.llm.invoke(messages)
            response_text = response.content
        except Exception as e:
            raise ClassificationError(
                f"Vertex AI invocation failed: {e}",
                details={
                    "model": self.model_name,
                    "text_length": len(text)
                },
            ) from e
        
        # Parse JSON
        try:
            # Clean response
            response_text = response_text.strip()
            if response_text.startswith("```json"):
                response_text = response_text.split("```json")[1]
            if response_text.startswith("```"):
                response_text = response_text.split("```")[1]
            if response_text.endswith("```"):
                response_text = response_text.rsplit("```", 1)[0]
            response_text = response_text.strip()
            
            data = json.loads(response_text)
        except json.JSONDecodeError as e:
            raise ClassificationError(
                f"Invalid JSON in LLM response: {e}",
                details={"response": response_text[:500]},
            ) from e
        
        # Validate structure
        if not isinstance(data, dict) or "claims" not in data:
            raise ClassificationError(
                "LLM response missing 'claims' key",
                details={"response": str(data)[:500]},
            )
        
        claims_data = data["claims"]
        if not isinstance(claims_data, list):
            raise ClassificationError(
                "'claims' is not a list",
                details={"type": type(claims_data).__name__},
            )
        
        # Parse claims
        claims = []
        for i, claim_dict in enumerate(claims_data):
            try:
                # Parse evidence basis (handle string enum)
                basis_str = claim_dict.get("evidence_basis", "Heuristics")
                try:
                    basis = EvidenceBasis(basis_str)
                except ValueError:
                    logger.warning(
                        f"Invalid evidence basis '{basis_str}', defaulting to Heuristics"
                    )
                    basis = EvidenceBasis.HEURISTICS
                
                # Create claim
                claim = EpistemicClaim(
                    claim_text=claim_dict["claim_text"],
                    confidence=float(claim_dict["confidence"]),
                    evidence_basis=basis,
                    sentence_indices=[],  # LLM doesn't provide this
                )
                claims.append(claim)
            
            except (KeyError, ValueError, TypeError) as e:
                logger.warning(f"Skipping invalid claim {i}: {e}")
                continue
        
        if not claims:
            raise ClassificationError(
                "No valid claims extracted",
                details={"claims_data": str(claims_data)[:500]},
            )
        
        return claims
    
    def _empty_profile(self, reason: str) -> EpistemicProfile:
        """
        Create empty profile with reason.
        
        Args:
            reason: Reason for empty profile
        
        Returns:
            EpistemicProfile with no claims
        
        Complexity: O(1)
        """
        logger.info(f"Returning empty epistemic profile: {reason}")
        return EpistemicProfile(
            claims=[],
            model_used=f"{self.model_name} (Vertex AI)",
            processing_time_ms=0,
        )