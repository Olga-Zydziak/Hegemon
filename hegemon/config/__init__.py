"""
HEGEMON Configuration Package.

Exports all configuration classes and functions.
"""

from hegemon.config.prompts import (
    GOVERNOR_SYSTEM_PROMPT,
    GOVERNOR_USER_PROMPT_TEMPLATE,
    CATALYST_SYSTEM_PROMPT,
    CATALYST_USER_PROMPT_TEMPLATE,
    SKEPTIC_SYSTEM_PROMPT,
    SKEPTIC_USER_PROMPT_TEMPLATE,
    SYNTHESIZER_SYSTEM_PROMPT,
    SYNTHESIZER_USER_PROMPT_TEMPLATE,
    get_system_prompt,
    get_user_prompt_template,
)
from hegemon.config.settings import (
    AgentConfig,
    DebateConfig,
    GubernatorConfig,
    HegemonSettings,
    KatalizatorConfig,
    SceptyKConfig,
    SyntezatorConfig,
    basic_config_agent,
    get_agent_config,
    get_api_key_for_provider,
    get_basic_config_for_agent,
    get_settings,
)

__all__ = [
    # Settings
    "HegemonSettings",
    "AgentConfig",
    "DebateConfig",
    "KatalizatorConfig",
    "SceptyKConfig",
    "GubernatorConfig",
    "SyntezatorConfig",
    "get_settings",
    "get_agent_config",
    "get_api_key_for_provider",
    "get_basic_config_for_agent",
    "basic_config_agent",
    # Prompts
    "KATALIZATOR_SYSTEM_PROMPT",
    "KATALIZATOR_USER_PROMPT_TEMPLATE",
    "SCEPTYK_SYSTEM_PROMPT",
    "SCEPTYK_USER_PROMPT_TEMPLATE",
    "GUBERNATOR_SYSTEM_PROMPT",
    "GUBERNATOR_USER_PROMPT_TEMPLATE",
    "SYNTEZATOR_SYSTEM_PROMPT",
    "SYNTEZATOR_USER_PROMPT_TEMPLATE",
    "get_system_prompt",
    "get_user_prompt_template",
]