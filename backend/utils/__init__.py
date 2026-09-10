"""
Utils package for Odhikar backend.
Provides model connection management and error message handling.
"""

from .error_messages import (
    parse_llm_error,
    get_error_message,
    ERROR_MESSAGES,
)

from .model_connection import (
    llm,
    create_llm_client,
    check_llm_status,
    is_model_configured,
    OPENROUTER_API_KEY,
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
    "OPENROUTER_API_KEY",
    "MODEL_NAME",
    "MAX_TOKENS",
    "TEMPERATURE",
    "TOKEN_BUDGET_LIMIT",
    "parse_llm_error",
    "get_error_message",
    "ERROR_MESSAGES",
]
