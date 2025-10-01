"""
HEGEMON Configuration - Google Secret Manager + Vertex AI.

Supports:
- Anthropic Claude (API key from Secret Manager)
- Google Gemini via Vertex AI (NO API key - uses ADC)
- OpenAI (optional, API key from Secret Manager)
"""

from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Literal

from google.cloud import secretmanager
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


# ============================================================================
# Google Secret Manager (from api_config.py)
# ============================================================================

def get_secret(project_id: str, secret_id: str, version_id: str = "latest") -> str:
    """Pobiera wartość sekretu z Google Secret Manager."""
    client = secretmanager.SecretManagerServiceClient()
    name = f"projects/{project_id}/secrets/{secret_id}/versions/{version_id}"
    response = client.access_secret_version(request={"name": name})
    return response.payload.data.decode("UTF-8")


# ============================================================================
# GCP Configuration (from api_config.py)
# ============================================================================

LOCATION = "us-central1"
PROJECT_ID = "dark-data-discovery"


# ============================================================================
# API Keys - Loaded from Secret Manager
# ============================================================================

# Anthropic Claude - REQUIRED (used by 3 agents)
ANTHROPIC_API_KEY = get_secret(PROJECT_ID, "ANTHROPIC_API_KEY")
logger.info("✅ ANTHROPIC_API_KEY loaded from Secret Manager")

# Google Gemini via Vertex AI - NO API KEY NEEDED!
# Vertex AI uses Application Default Credentials (ADC)
GOOGLE_API_KEY = None  # Not needed for Vertex AI
logger.info("✅ Google Gemini will use Vertex AI (ADC authentication)")

# OpenAI - OPTIONAL (backup provider)
try:
    OPENAI_API_KEY = get_secret(PROJECT_ID, "OPENAI_API_KEY")
    logger.info("✅ OPENAI_API_KEY loaded from Secret Manager")
except Exception:
    OPENAI_API_KEY = None
    logger.info("ℹ️ OPENAI_API_KEY not found (optional)")


# ============================================================================
# Agent Configuration
# ============================================================================

class AgentConfig(BaseModel):
    """Base configuration for an agent."""
    
    name: str
    provider: Literal["anthropic", "google", "openai"]
    model: str
    temperature: float = Field(ge=0.0, le=1.0)
    max_tokens: int = Field(default=2000, ge=100, le=16000)
    timeout: int = Field(default=60, ge=10, le=300)
    max_retries: int = Field(default=2, ge=0, le=5)
    
    # Vertex AI specific (for Google provider)
    use_vertex_ai: bool = Field(
        default=True,
        description="Use Vertex AI (ADC auth) instead of Google AI API (API key)"
    )


# ============================================================================
# Agent Configurations (Claude + Gemini via Vertex AI)
# ============================================================================

class KatalizatorConfig(AgentConfig):
    """Katalizator: Claude Sonnet 4.5."""
    name: str = "Katalizator"
    provider: Literal["anthropic", "google", "openai"] = "anthropic"
    model: str = "claude-sonnet-4-5-20250929"
    temperature: float = 0.8
    max_tokens: int = 2000


class SceptyKConfig(AgentConfig):
    """Sceptyk: Gemini 2.0 Flash via Vertex AI."""
    name: str = "Sceptyk"
    provider: Literal["anthropic", "google", "openai"] = "google"
    model: str = "gemini-2.5-pro"
    temperature: float = 0.6
    max_tokens: int = 2000
    use_vertex_ai: bool = True  # Use Vertex AI (no API key)


class GubernatorConfig(AgentConfig):
    """Gubernator: Claude Sonnet 4.5."""
    name: str = "Gubernator"
    provider: Literal["anthropic", "google", "openai"] = "anthropic"
    model: str = "claude-sonnet-4-5-20250929"
    temperature: float = 0.3
    max_tokens: int = 1500


class SyntezatorConfig(AgentConfig):
    """Syntezator: Claude Sonnet 4.5."""
    name: str = "Syntezator"
    provider: Literal["anthropic", "google", "openai"] = "anthropic"
    model: str = "claude-opus-4-1-20250805"
    temperature: float = 0.5
    max_tokens: int = 3000


# ============================================================================
# Debate Configuration
# ============================================================================

class DebateConfig(BaseModel):
    """Configuration for dialectical debate process."""
    
    consensus_threshold: float = Field(default=0.7, ge=0.0, le=1.0)
    max_cycles: int = Field(default=5, ge=1, le=10)
    min_cycles: int = Field(default=1, ge=1, le=3)
    enable_early_stopping: bool = Field(default=True)


# ============================================================================
# Main Settings
# ============================================================================

class HegemonSettings(BaseModel):
    """Main HEGEMON system configuration."""
    
    # GCP Configuration
    gcp_project_id: str = PROJECT_ID
    gcp_location: str = LOCATION
    
    # API Keys
    anthropic_api_key: str = ANTHROPIC_API_KEY
    google_api_key: str | None = GOOGLE_API_KEY  # None for Vertex AI
    openai_api_key: str | None = OPENAI_API_KEY
    
    # Logging
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "INFO"
    
    # Agent Configurations
    katalizator: KatalizatorConfig = Field(default_factory=KatalizatorConfig)
    sceptyk: SceptyKConfig = Field(default_factory=SceptyKConfig)
    gubernator: GubernatorConfig = Field(default_factory=GubernatorConfig)
    syntezator: SyntezatorConfig = Field(default_factory=SyntezatorConfig)
    
    # Debate Configuration
    debate: DebateConfig = Field(default_factory=DebateConfig)
    
    # Paths
    output_dir: Path = Field(default=Path("output"))
    
    def validate_api_keys(self) -> None:
        """Validate that required API keys/auth are present."""
        # Anthropic required
        if not self.anthropic_api_key:
            raise ValueError(
                "ANTHROPIC_API_KEY not found in Secret Manager. "
                "Required for: Katalizator, Gubernator, Syntezator"
            )
        
        # Google: Either API key OR Vertex AI (ADC)
        if self.sceptyk.provider == "google":
            if self.sceptyk.use_vertex_ai:
                logger.info(
                    "✅ Sceptyk will use Vertex AI (Application Default Credentials)"
                )
            elif not self.google_api_key:
                raise ValueError(
                    "GOOGLE_API_KEY not found and use_vertex_ai=False. "
                    "Either set GOOGLE_API_KEY or use Vertex AI."
                )
        
        logger.info("✅ All required authentication validated")
    # ========================================================================
    # EXPLAINABILITY SETTINGS (Layer 6)
    # ========================================================================
    
    explainability_enabled: bool = Field(
        default=False,
        description="Master switch for explainability features"
    )
    
    explainability_semantic_fingerprint: bool = Field(
        default=True,
        description="Enable Layer 6: Semantic Fingerprint (concept classification)"
    )
    
    explainability_classifier_model: str = Field(
        default="gemini-2.0-flash-exp",
        description="LLM model for concept classification"
    )
    
    explainability_cache_size: int = Field(
        default=1000,
        ge=100,
        le=10000,
        description="Max number of cached classification results (LRU eviction)"
    )
    
    explainability_timeout_seconds: int = Field(
        default=30,
        ge=5,
        le=120,
        description="Timeout for single classification request"
    )
    
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_prefix="HEGEMON_",
        extra="ignore",
    )
    
    @model_validator(mode="after")
    def validate_explainability_config(self) -> HegemonSettings:
        """
        Validate explainability configuration.
        
        Complexity: O(1)
        """
        if self.explainability_enabled:
            # Check API key available
            if not self.google_api_key:
                logger.warning(
                    "Explainability enabled but no Google API key found. "
                    "Classifier will fail."
                )
        
        return self

# ============================================================================
# Basic Config Agent (from api_config.py)
# ============================================================================

def basic_config_agent(
    agent_name: str,
    api_type: str,
    location: str | None = None,
    project_id: str | None = None,
    api_key: str | None = None,
) -> list[dict]:
    """
    Generate agent configuration dict (from api_config.py).
    
    Identical to api_config.py implementation.
    """
    try:
        configuration = {"model": agent_name}
        configuration.update({"api_type": api_type})
        
        if api_key:
            configuration["api_key"] = api_key
        if project_id:
            configuration["project_id"] = project_id
        if location:
            configuration["location"] = location
        
        logger.info(f"Model configuration: {configuration}")
        return [configuration]
    
    except Exception as e:
        logger.error(f"Failed to configure agent {agent_name}: {e}")
        print(
            f"Error: Failed to configure LLM. "
            f"Check your project ID, region, and permissions. Details: {e}"
        )
        raise


# ============================================================================
# Singleton Instance
# ============================================================================

_settings: HegemonSettings | None = None


def get_settings() -> HegemonSettings:
    """Get singleton HegemonSettings instance."""
    global _settings
    
    if _settings is None:
        _settings = HegemonSettings()
        _settings.validate_api_keys()
        
        logger.info(
            f"✅ HEGEMON Settings initialized "
            f"(GCP Project: {_settings.gcp_project_id})"
        )
    
    return _settings


def get_agent_config(
    agent_name: Literal["Katalizator", "Sceptyk", "Gubernator", "Syntezator"]
) -> AgentConfig:
    """Get configuration for specific agent."""
    settings = get_settings()
    
    config_map = {
        "Katalizator": settings.katalizator,
        "Sceptyk": settings.sceptyk,
        "Gubernator": settings.gubernator,
        "Syntezator": settings.syntezator,
    }
    
    return config_map[agent_name]


def get_api_key_for_provider(provider: str) -> str | None:
    """
    Get API key for specified provider.
    
    Returns None for Google provider if using Vertex AI.
    """
    settings = get_settings()
    
    if provider == "anthropic":
        return settings.anthropic_api_key
    elif provider == "google":
        return settings.google_api_key  # None if using Vertex AI
    elif provider == "openai":
        return settings.openai_api_key
    else:
        raise ValueError(f"Unknown provider: {provider}")


def get_basic_config_for_agent(
    agent_name: Literal["Katalizator", "Sceptyk", "Gubernator", "Syntezator"]
) -> list[dict]:
    """Get basic_config_agent format for specified agent."""
    settings = get_settings()
    agent_config = get_agent_config(agent_name)
    
    # Get API key (None for Vertex AI)
    api_key = get_api_key_for_provider(agent_config.provider)
    
    # For Google provider using Vertex AI, pass project_id and location
    if agent_config.provider == "google" and agent_config.use_vertex_ai:
        return basic_config_agent(
            agent_name=agent_config.model,
            api_type=agent_config.provider,
            location=settings.gcp_location,
            project_id=settings.gcp_project_id,
            api_key=None,  # No API key for Vertex AI
        )
    else:
        return basic_config_agent(
            agent_name=agent_config.model,
            api_type=agent_config.provider,
            location=None,
            project_id=None,
            api_key=api_key,
        )