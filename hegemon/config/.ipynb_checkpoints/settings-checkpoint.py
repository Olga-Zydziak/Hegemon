"""
HEGEMON Configuration - Multi-Provider Support (Claude + Gemini).

Supports:
- Anthropic Claude (claude-sonnet-4.5)
- Google Gemini (gemini-2.0-pro-exp)
- OpenAI GPT (gpt-4o) - fallback
"""

from __future__ import annotations

from pathlib import Path
from typing import Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


# ============================================================================
# Provider-Specific Settings
# ============================================================================

class ProviderSettings(BaseSettings):
    """API keys for different providers."""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )
    
    # API Keys
    anthropic_api_key: str | None = Field(
        default=None,
        description="Anthropic API Key for Claude models"
    )
    
    google_api_key: str | None = Field(
        default=None,
        description="Google API Key for Gemini models"
    )
    
    openai_api_key: str | None = Field(
        default=None,
        description="OpenAI API Key (fallback)"
    )
    
    @field_validator("anthropic_api_key", "google_api_key", "openai_api_key")
    @classmethod
    def validate_at_least_one_key(cls, v, info):
        """Ensure at least one API key is provided."""
        # This will be validated in HegemonSettings
        return v


# ============================================================================
# Agent Configuration (Provider-Aware)
# ============================================================================

class AgentConfig(BaseSettings):
    """
    Base configuration for an agent with provider support.
    
    Attributes:
        name: Agent name
        provider: LLM provider (anthropic, google, openai)
        model: Model identifier
        temperature: Sampling temperature
        max_tokens: Maximum response length
        timeout: API timeout (seconds)
        max_retries: Retry attempts on failure
    """
    
    name: str
    provider: Literal["anthropic", "google", "openai"]
    model: str
    temperature: float = Field(ge=0.0, le=1.0)
    max_tokens: int = Field(default=2000, ge=100, le=16000)
    timeout: int = Field(default=60, ge=10, le=300)
    max_retries: int = Field(default=2, ge=0, le=5)


# ============================================================================
# RECOMMENDED CONFIGURATION (Claude + Gemini)
# ============================================================================

class KatalizatorConfig(AgentConfig):
    """
    Katalizator: Claude Sonnet 4.5.
    
    Rationale:
    - Zadanie: Kreatywne generowanie tez (divergent thinking)
    - Claude jest znany z kreatywności i długich, spójnych outputów
    - Temperature 0.8 dla wysokiej kreatywności
    - Cost: $3/MTok input, $15/MTok output
    """
    
    name: str = "Katalizator"
    provider: Literal["anthropic", "google", "openai"] = "anthropic"
    model: str = "claude-sonnet-4-5-20250929"  # Latest Claude
    temperature: float = 0.8
    max_tokens: int = 2000


class SceptyKConfig(AgentConfig):
    """
    Sceptyk: Gemini 2.0 Pro.
    
    Rationale:
    - Zadanie: Analityczne myślenie, znajdowanie wad
    - Gemini 2.0 Pro ma świetny reasoning przy niskim koszcie
    - 3x tańszy niż Claude ($1.25 vs $3 per MTok)
    - Cost-effective dla intermediate output
    """
    
    name: str = "Sceptyk"
    provider: Literal["anthropic", "google", "openai"] = "google"
    model: str = "gemini-2.0-flash-exp"  # Gemini 2.0 Pro Experimental
    temperature: float = 0.6
    max_tokens: int = 2000


class GubernatorConfig(AgentConfig):
    """
    Gubernator: Claude Sonnet 4.5.
    
    Rationale:
    - KRYTYCZNA rola: Meta-cognitive evaluation + routing
    - Claude ma precyzyjny structured output
    - Niższa temperatura (0.3) dla deterministycznych decyzji
    - Worth premium cost dla critical path
    """
    
    name: str = "Gubernator"
    provider: Literal["anthropic", "google", "openai"] = "anthropic"
    model: str = "claude-sonnet-4-5-20250929"
    temperature: float = 0.3
    max_tokens: int = 1500


class SyntezatorConfig(AgentConfig):
    """
    Syntezator: Claude Sonnet 4.5.
    
    Rationale:
    - KRYTYCZNA rola: Final synthesis (user-facing output)
    - Claude jest najlepszy w tworzeniu spójnych, długich tekstów
    - Synthesis wymaga głębokiego zrozumienia kontekstu
    - Worth premium cost dla quality finalnego planu
    """
    
    name: str = "Syntezator"
    provider: Literal["anthropic", "google", "openai"] = "anthropic"
    model: str = "claude-sonnet-4-5-20250929"
    temperature: float = 0.5
    max_tokens: int = 3000


# ============================================================================
# Debate Configuration
# ============================================================================

class DebateConfig(BaseSettings):
    """Configuration for dialectical debate process."""
    
    consensus_threshold: float = Field(
        default=0.7,
        ge=0.0,
        le=1.0,
        description="Consensus threshold for debate termination"
    )
    max_cycles: int = Field(
        default=5,
        ge=1,
        le=10,
        description="Maximum debate cycles"
    )
    min_cycles: int = Field(
        default=1,
        ge=1,
        le=3,
        description="Minimum cycles (even with high consensus)"
    )
    enable_early_stopping: bool = Field(
        default=True,
        description="Stop early if consensus reached"
    )


# ============================================================================
# Main Settings
# ============================================================================

class HegemonSettings(BaseSettings):
    """Main HEGEMON system configuration."""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        env_prefix="HEGEMON_",
    )
    
    # Provider API Keys
    providers: ProviderSettings = Field(
        default_factory=ProviderSettings
    )
    
    # Logging
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = Field(
        default="INFO",
        description="Logging level"
    )
    
    # Agent Configurations
    katalizator: KatalizatorConfig = Field(
        default_factory=KatalizatorConfig
    )
    sceptyk: SceptyKConfig = Field(
        default_factory=SceptyKConfig
    )
    gubernator: GubernatorConfig = Field(
        default_factory=GubernatorConfig
    )
    syntezator: SyntezatorConfig = Field(
        default_factory=SyntezatorConfig
    )
    
    # Debate Configuration
    debate: DebateConfig = Field(
        default_factory=DebateConfig
    )
    
    # Paths
    output_dir: Path = Field(
        default=Path("output"),
        description="Output directory"
    )
    
    def validate_providers(self) -> None:
        """Validate that required API keys are present."""
        required_providers = set()
        
        for agent_config in [self.katalizator, self.sceptyk, 
                             self.gubernator, self.syntezator]:
            required_providers.add(agent_config.provider)
        
        for provider in required_providers:
            if provider == "anthropic" and not self.providers.anthropic_api_key:
                raise ValueError(
                    "ANTHROPIC_API_KEY required (used by Katalizator, Gubernator, Syntezator)"
                )
            if provider == "google" and not self.providers.google_api_key:
                raise ValueError(
                    "GOOGLE_API_KEY required (used by Sceptyk)"
                )
            if provider == "openai" and not self.providers.openai_api_key:
                raise ValueError(
                    "OPENAI_API_KEY required"
                )


# Singleton
_settings: HegemonSettings | None = None


def get_settings() -> HegemonSettings:
    """Get singleton HegemonSettings instance."""
    global _settings
    
    if _settings is None:
        _settings = HegemonSettings()
        _settings.validate_providers()
    
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