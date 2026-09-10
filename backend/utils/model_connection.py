"""
LLM Model Connection and Health Check Utilities.
Handles OpenRouter client initialization, environment configuration,
and connection health checks.
"""

import os
from typing import Dict, Any, Optional
from dotenv import load_dotenv

load_dotenv()

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from .error_messages import parse_llm_error, get_error_message

# OpenRouter configuration with environment variables
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
MODEL_NAME = os.getenv("MODEL_NAME", "google/gemini-3.8-flash")
MAX_TOKENS = int(os.getenv("MAX_TOKENS", "2000"))
TEMPERATURE = float(os.getenv("TEMPERATURE", "0"))
REASONING_MAX_TOKENS = int(os.getenv("REASONING_MAX_TOKENS", "0"))

# TOKEN THRESHOLD: If estimated tokens exceed this budget, ask user to confirm continuation
TOKEN_BUDGET_LIMIT = int(os.getenv("TOKEN_BUDGET_LIMIT", "180"))

extra_body = {}
if REASONING_MAX_TOKENS > 0:
    extra_body["reasoning"] = {"max_tokens": REASONING_MAX_TOKENS}


def create_llm_client(
    api_key: Optional[str] = None,
    model_name: Optional[str] = None,
    max_tokens: Optional[int] = None,
    temperature: Optional[float] = None,
    extra_body_params: Optional[Dict[str, Any]] = None
) -> ChatOpenAI:
    """
    Factory function to create a configured ChatOpenAI client pointing to OpenRouter.
    """
    key = api_key if api_key is not None else OPENROUTER_API_KEY
    model = model_name if model_name is not None else MODEL_NAME
    tokens = max_tokens if max_tokens is not None else MAX_TOKENS
    temp = temperature if temperature is not None else TEMPERATURE
    eb = extra_body_params if extra_body_params is not None else (extra_body if extra_body else None)

    return ChatOpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=key,
        model=model,
        max_tokens=tokens,
        temperature=temp,
        extra_body=eb
    )


# Default singleton instance
llm = create_llm_client()


def is_model_configured() -> bool:
    """
    Checks if an API key is provided and is not a default placeholder.
    """
    if not OPENROUTER_API_KEY or not OPENROUTER_API_KEY.strip():
        return False
    if OPENROUTER_API_KEY.strip() in ("sk-or-v1-...", "your-key-here"):
        return False
    return True


def check_llm_status() -> Dict[str, Any]:
    """
    Checks LLM connectivity and token status.
    Returns a status dictionary suitable for health-check APIs and frontend indicator.
    """
    if not is_model_configured():
        err = get_error_message("missing_api_key")
        err["connected"] = False
        err["model"] = MODEL_NAME
        return err

    try:
        # Quick 1-token probe to verify connectivity, auth, and quota
        probe_prompt = ChatPromptTemplate.from_messages([("user", "hi")])
        probe_res = llm.invoke(probe_prompt.format_messages(), max_tokens=1)
        return {
            "connected": True,
            "status_code": 200,
            "model": MODEL_NAME,
            "title": "LLM সংযুক্ত (Connected)",
            "message_bn": f"এলএলএম মডেল '{MODEL_NAME}' সফলভাবে সংযুক্ত ও সক্রিয় আছে।",
            "message_en": f"LLM model '{MODEL_NAME}' is connected and active."
        }
    except Exception as exc:
        err = parse_llm_error(exc)
        err["connected"] = False
        err["model"] = MODEL_NAME
        return err
