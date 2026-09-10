"""
Utils package for Odhikar backend.
Provides model connection management and error message handling.
Strictly supports:
1. Local LLMs (Ollama / LM Studio - offline, no key needed)
2. Google Cloud Vertex AI (GCP enterprise platform)
3. OpenRouter (multi-model gateway)
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
    resolve_vertex_token,
    OPENROUTER_API_KEY,
    GOOGLE_API_KEY,
    GOOGLE_CLOUD_PROJECT,
    GOOGLE_CLOUD_REGION,
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
    "resolve_vertex_token",
    "OPENROUTER_API_KEY",
    "GOOGLE_API_KEY",
    "GOOGLE_CLOUD_PROJECT",
    "GOOGLE_CLOUD_REGION",
    "MODEL_NAME",
    "MAX_TOKENS",
    "TEMPERATURE",
    "TOKEN_BUDGET_LIMIT",
    "parse_llm_error",
    "get_error_message",
    "get_provider_templates",
    "ERROR_MESSAGES",
]
