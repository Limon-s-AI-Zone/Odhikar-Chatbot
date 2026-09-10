"""
LLM Model Connection and Health Check Utilities.
Provides dynamic, decoupled multi-provider support:
- Google Gemini (native direct API via langchain_google_genai)
- Local LLMs (Ollama, LM Studio, vLLM, LocalAI - requires no API key!)
- OpenAI (official direct API)
- OpenRouter (multi-model gateway)
- Custom OpenAI-compatible endpoints
"""

import os
from typing import Dict, Any, Optional
from dotenv import load_dotenv

load_dotenv()

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from .error_messages import parse_llm_error, get_error_message

# General and Provider-Specific Environment Variables
LLM_PROVIDER_RAW = os.getenv("LLM_PROVIDER", "").strip().lower()
LLM_API_KEY_RAW = os.getenv("LLM_API_KEY", "").strip()
LLM_BASE_URL_RAW = (os.getenv("LLM_BASE_URL", "").strip() or os.getenv("OPENAI_API_BASE", "").strip()).rstrip("/")

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "").strip()
GOOGLE_API_KEY = (os.getenv("GOOGLE_API_KEY", "").strip() or os.getenv("GEMINI_API_KEY", "").strip())
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "").strip()

MODEL_NAME = os.getenv("MODEL_NAME", "").strip()
MAX_TOKENS = int(os.getenv("MAX_TOKENS", "2000"))
TEMPERATURE = float(os.getenv("TEMPERATURE", "0"))
REASONING_MAX_TOKENS = int(os.getenv("REASONING_MAX_TOKENS", "0"))

# Token continuation threshold for conversation budget
TOKEN_BUDGET_LIMIT = int(os.getenv("TOKEN_BUDGET_LIMIT", "180"))


def get_provider_info(provider_override: Optional[str] = None) -> Dict[str, Any]:
    """
    Detects and returns active provider metadata including display name,
    base URL, API key, model, and whether an API key is strictly required.
    """
    prov = (provider_override or LLM_PROVIDER_RAW or "").lower()
    base_url = LLM_BASE_URL_RAW

    # 1. Google Gemini (Official API via OpenAI-compatible endpoint)
    if prov in ("google", "gemini"):
        key = GOOGLE_API_KEY or LLM_API_KEY_RAW
        model = MODEL_NAME or "gemini-2.5-pro"
        url = base_url or "https://generativelanguage.googleapis.com/v1beta/openai/"
        return {
            "provider": "google",
            "display_name": "Google Gemini",
            "requires_api_key": True,
            "api_key_env": "GOOGLE_API_KEY",
            "api_key": key,
            "base_url": url,
            "model": model
        }

    # 2. Ollama (Local LLM, default port 11434)
    if prov in ("ollama",):
        url = base_url or "http://localhost:11434/v1"
        model = MODEL_NAME or "mistral"
        return {
            "provider": "ollama",
            "display_name": "Ollama (Local LLM)",
            "requires_api_key": False,
            "api_key_env": "LLM_API_KEY",
            "api_key": LLM_API_KEY_RAW or "ollama",
            "base_url": url,
            "model": model
        }

    # 3. LM Studio / Local OpenAI-compatible server (default port 1234)
    if prov in ("local", "lmstudio", "vllm"):
        url = base_url or "http://localhost:1234/v1"
        model = MODEL_NAME or "local-model"
        return {
            "provider": "local",
            "display_name": "Local LLM (LM Studio / vLLM)",
            "requires_api_key": False,
            "api_key_env": "LLM_API_KEY",
            "api_key": LLM_API_KEY_RAW or "lm-studio",
            "base_url": url,
            "model": model
        }

    # 4. OpenAI (Official Direct API)
    if prov in ("openai",):
        key = OPENAI_API_KEY or LLM_API_KEY_RAW
        model = MODEL_NAME or "gpt-4o-mini"
        return {
            "provider": "openai",
            "display_name": "OpenAI",
            "requires_api_key": True,
            "api_key_env": "OPENAI_API_KEY",
            "api_key": key,
            "base_url": base_url or "https://api.openai.com/v1",
            "model": model
        }

    # 5. OpenRouter
    if prov in ("openrouter",):
        key = OPENROUTER_API_KEY or LLM_API_KEY_RAW
        model = MODEL_NAME or "google/gemini-2.0-flash-001"
        return {
            "provider": "openrouter",
            "display_name": "OpenRouter",
            "requires_api_key": True,
            "api_key_env": "OPENROUTER_API_KEY",
            "api_key": key,
            "base_url": base_url or "https://openrouter.ai/api/v1",
            "model": model
        }

    # 6. Automatic Detection when LLM_PROVIDER is not set:
    if base_url:
        if "11434" in base_url:
            return {
                "provider": "ollama",
                "display_name": "Ollama (Local LLM)",
                "requires_api_key": False,
                "api_key_env": "LLM_API_KEY",
                "api_key": LLM_API_KEY_RAW or "ollama",
                "base_url": base_url,
                "model": MODEL_NAME or "mistral"
            }
        if any(h in base_url for h in ("1234", "localhost", "127.0.0.1", "0.0.0.0")):
            return {
                "provider": "local",
                "display_name": "Local LLM",
                "requires_api_key": False,
                "api_key_env": "LLM_API_KEY",
                "api_key": LLM_API_KEY_RAW or "local",
                "base_url": base_url,
                "model": MODEL_NAME or "local-model"
            }
        if "googleapis.com" in base_url:
            return {
                "provider": "google",
                "display_name": "Google Gemini",
                "requires_api_key": True,
                "api_key_env": "GOOGLE_API_KEY",
                "api_key": GOOGLE_API_KEY or LLM_API_KEY_RAW,
                "base_url": base_url,
                "model": MODEL_NAME or "gemini-1.5-flash"
            }
        return {
            "provider": "custom",
            "display_name": f"Custom LLM ({base_url})",
            "requires_api_key": bool(LLM_API_KEY_RAW),
            "api_key_env": "LLM_API_KEY",
            "api_key": LLM_API_KEY_RAW or "custom",
            "base_url": base_url,
            "model": MODEL_NAME or "custom-model"
        }

    # Key-based detection:
    if GOOGLE_API_KEY and not OPENROUTER_API_KEY:
        return {
            "provider": "google",
            "display_name": "Google Gemini",
            "requires_api_key": True,
            "api_key_env": "GOOGLE_API_KEY",
            "api_key": GOOGLE_API_KEY,
            "base_url": "",
            "model": MODEL_NAME or "gemini-1.5-flash"
        }

    if OPENAI_API_KEY and not OPENROUTER_API_KEY:
        return {
            "provider": "openai",
            "display_name": "OpenAI",
            "requires_api_key": True,
            "api_key_env": "OPENAI_API_KEY",
            "api_key": OPENAI_API_KEY,
            "base_url": "https://api.openai.com/v1",
            "model": MODEL_NAME or "gpt-4o-mini"
        }

    # Default fallback: OpenRouter
    return {
        "provider": "openrouter",
        "display_name": "OpenRouter",
        "requires_api_key": True,
        "api_key_env": "OPENROUTER_API_KEY",
        "api_key": OPENROUTER_API_KEY or LLM_API_KEY_RAW,
        "base_url": "https://openrouter.ai/api/v1",
        "model": MODEL_NAME or "google/gemma-4-31b-it:free"
    }


def create_llm_client(
    provider_override: Optional[str] = None,
    api_key: Optional[str] = None,
    model_name: Optional[str] = None,
    base_url: Optional[str] = None,
    max_tokens: Optional[int] = None,
    temperature: Optional[float] = None,
    extra_body_params: Optional[Dict[str, Any]] = None
) -> BaseChatModel:
    """
    Factory function to dynamically create the appropriate LangChain chat model.
    Instantiates ChatGoogleGenerativeAI for Google Gemini, or ChatOpenAI with appropriate
    base_url and auth for Ollama, LM Studio, OpenAI, OpenRouter, and Custom endpoints.
    """
    info = get_provider_info(provider_override)
    provider = info["provider"]
    key = api_key if api_key is not None else info.get("api_key", "")
    model = model_name if model_name is not None else info.get("model", "")
    url = base_url if base_url is not None else info.get("base_url", "")
    tokens = max_tokens if max_tokens is not None else MAX_TOKENS
    temp = temperature if temperature is not None else TEMPERATURE

    # Extra body parameters (e.g. reasoning tokens)
    eb = extra_body_params
    if eb is None and REASONING_MAX_TOKENS > 0 and provider in ("openrouter", "openai"):
        eb = {"reasoning": {"max_tokens": REASONING_MAX_TOKENS}}

    # OpenAI-compatible clients (Google Gemini, Ollama, LM Studio, OpenAI, OpenRouter, Custom)
    default_url = "https://generativelanguage.googleapis.com/v1beta/openai/" if provider == "google" else "https://openrouter.ai/api/v1"
    target_base_url = url or default_url
    target_api_key = key or ("ollama" if provider == "ollama" else ("local" if provider == "local" else "dummy"))

    kwargs: Dict[str, Any] = {
        "base_url": target_base_url,
        "api_key": target_api_key,
        "model": model,
        "max_tokens": tokens,
        "temperature": temp
    }
    if eb:
        kwargs["extra_body"] = eb

    return ChatOpenAI(**kwargs)


# Initialize default dynamic singleton LLM instance
llm = create_llm_client()


def is_model_configured() -> bool:
    """
    Checks if the active model provider is properly configured.
    For local LLMs (Ollama, LM Studio), returns True without requiring an API key.
    For cloud providers (Google, OpenAI, OpenRouter), ensures an API key is provided and valid.
    """
    info = get_provider_info()
    if not info.get("requires_api_key", True):
        return True

    key = (info.get("api_key") or "").strip()
    if not key:
        return False
    if key in ("sk-or-v1-...", "your-key-here", "sk-...", "AIzaSy..."):
        return False
    return True


def check_llm_status() -> Dict[str, Any]:
    """
    Checks LLM connectivity, authentication, and quota status dynamically.
    Returns a status dictionary suitable for health-check APIs and frontend indicators.
    """
    info = get_provider_info()
    provider_name = info.get("display_name", "LLM")
    model_name = info.get("model", MODEL_NAME)

    if not is_model_configured():
        err = get_error_message("missing_api_key", provider_info=info)
        err["connected"] = False
        err["provider"] = info.get("provider")
        err["model"] = model_name
        return err

    try:
        # Quick 1-token probe to verify connectivity, auth, and quota
        probe_prompt = ChatPromptTemplate.from_messages([("user", "hi")])
        probe_res = llm.invoke(probe_prompt.format_messages())
        return {
            "connected": True,
            "status_code": 200,
            "provider": info.get("provider"),
            "provider_name": provider_name,
            "model": model_name,
            "title": f"{provider_name} সংযুক্ত (Connected)",
            "message_bn": f"{provider_name} মডেল '{model_name}' সফলভাবে সংযুক্ত ও সক্রিয় আছে।",
            "message_en": f"{provider_name} model '{model_name}' is connected and active."
        }
    except Exception as exc:
        err = parse_llm_error(exc, provider_info=info)
        err["connected"] = False
        err["provider"] = info.get("provider")
        err["provider_name"] = provider_name
        err["model"] = model_name
        return err
