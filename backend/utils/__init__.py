"""
Utils package for Odhikar backend.
Provides dynamic, multi-provider model connection management and provider-aware error message handling.
Supports Google Gemini, Ollama (Local), LM Studio / LocalAI, OpenAI, and OpenRouter.
"""

from .error_messages import (
    parse_llm_error,
    get_error_message,
    get_provider_templates,
    ERROR_MESSAGES,
)

from .model_connection import (
    llm,
    create_llm_client,
    check_llm_status,
    is_model_configured,
    get_provider_info,
    OPENROUTER_API_KEY,
    GOOGLE_API_KEY,
    OPENAI_API_KEY,
    MODEL_NAME,
    MAX_TOKENS,
    TEMPERATURE,
    TOKEN_BUDGET_LIMIT,
)

__all__ = [
    "llm",
    "create_llm_client",
    "check_llm_status",
    "is_model_configured",
    "get_provider_info",
    "OPENROUTER_API_KEY",
    "GOOGLE_API_KEY",
    "OPENAI_API_KEY",
    "MODEL_NAME",
    "MAX_TOKENS",
    "TEMPERATURE",
    "TOKEN_BUDGET_LIMIT",
    "parse_llm_error",
    "get_error_message",
    "get_provider_templates",
    "ERROR_MESSAGES",
]
