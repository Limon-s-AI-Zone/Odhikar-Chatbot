"""
LLM Model Connection and Health Check Utilities.
Strictly supports:
1. Local LLMs (Ollama, LM Studio, vLLM - requires no API key!)
2. Google Cloud Vertex AI (Google Cloud enterprise platform)
3. OpenRouter (Multi-model gateway)
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

# 1. OpenRouter
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "").strip()

# 2. Google Cloud Vertex AI
GOOGLE_CLOUD_PROJECT = (os.getenv("GOOGLE_CLOUD_PROJECT", "").strip() or os.getenv("VERTEX_PROJECT_ID", "").strip() or os.getenv("PROJECT_ID", "").strip())
GOOGLE_CLOUD_REGION = (os.getenv("GOOGLE_CLOUD_REGION", "").strip() or os.getenv("VERTEX_LOCATION", "").strip() or "us-central1")
GOOGLE_API_KEY = (os.getenv("GOOGLE_API_KEY", "").strip() or os.getenv("VERTEX_API_KEY", "").strip())

# Shared Generation Parameters
MODEL_NAME = os.getenv("MODEL_NAME", "").strip()
MAX_TOKENS = int(os.getenv("MAX_TOKENS", "2000"))
TEMPERATURE = float(os.getenv("TEMPERATURE", "0"))
REASONING_MAX_TOKENS = int(os.getenv("REASONING_MAX_TOKENS", "0"))

# Token continuation threshold for conversation budget
TOKEN_BUDGET_LIMIT = int(os.getenv("TOKEN_BUDGET_LIMIT", "180"))


def resolve_vertex_token() -> str:
    """
    Resolves the Vertex AI access token.
    First checks if explicit GOOGLE_API_KEY/VERTEX_API_KEY is provided.
    If not or if using service account, attempts resolving OAuth 2 credentials via google.auth.
    """
    key = GOOGLE_API_KEY or LLM_API_KEY_RAW

    # Try resolving ADC or service account credentials via google.auth
    try:
        import google.auth
        from google.auth.transport.requests import Request
        credentials, _ = google.auth.default(scopes=["https://www.googleapis.com/auth/cloud-platform"])
        if not credentials.valid:
            credentials.refresh(Request())
        if credentials.token:
            return credentials.token
    except Exception:
        pass

    return key


def get_provider_info(provider_override: Optional[str] = None) -> Dict[str, Any]:
    """
    Detects and returns active provider metadata.
    Supported: 'local' (Ollama/LM Studio), 'vertex' (Google Cloud), 'openrouter'.
    """
    prov = (provider_override or LLM_PROVIDER_RAW or "").lower()
    base_url = LLM_BASE_URL_RAW

    # 1. Google Cloud Vertex AI
    if prov in ("vertex", "vertexai"):
        key = resolve_vertex_token()
        model = MODEL_NAME or "google/gemini-2.0-flash"
        region = GOOGLE_CLOUD_REGION or "us-central1"
        project = GOOGLE_CLOUD_PROJECT or ""

        if base_url:
            url = base_url
        elif project:
            url = f"https://{region}-aiplatform.googleapis.com/v1beta1/projects/{project}/locations/{region}/endpoints/openapi/"
        else:
            url = f"https://{region}-aiplatform.googleapis.com/v1beta1/locations/{region}/endpoints/openapi/"

        return {
            "provider": "vertex",
            "display_name": "Google Cloud Vertex AI",
            "requires_api_key": True,
            "api_key_env": "GOOGLE_API_KEY",
            "api_key": key,
            "base_url": url,
            "model": model,
            "project": project,
            "region": region
        }

    # 2. Local LLM (Ollama, LM Studio, vLLM - No API Key Required)
    if prov in ("local", "ollama", "lmstudio", "vllm"):
        is_ollama = (prov == "ollama") or ("11434" in base_url)
        default_url = "http://localhost:11434/v1" if is_ollama else "http://localhost:1234/v1"
        default_model = "mistral" if is_ollama else "local-model"
        display = "Ollama (Local LLM)" if is_ollama else "Local LLM (LM Studio / vLLM)"

        return {
            "provider": "local",
            "display_name": display,
            "requires_api_key": False,
            "api_key_env": "LLM_API_KEY",
            "api_key": LLM_API_KEY_RAW or "local",
            "base_url": base_url or default_url,
            "model": MODEL_NAME or default_model
        }

    # 3. OpenRouter
    if prov in ("openrouter",):
        key = OPENROUTER_API_KEY or LLM_API_KEY_RAW
        model = MODEL_NAME or "nex-agi/nex-n2.5-mini:free"
        return {
            "provider": "openrouter",
            "display_name": "OpenRouter",
            "requires_api_key": True,
            "api_key_env": "OPENROUTER_API_KEY",
            "api_key": key,
            "base_url": base_url or "https://openrouter.ai/api/v1",
            "model": model
        }

    # Auto-detection when LLM_PROVIDER is not explicitly specified:
    if base_url:
        if any(h in base_url for h in ("localhost", "127.0.0.1", "11434", "1234")):
            return {
                "provider": "local",
                "display_name": "Local LLM",
                "requires_api_key": False,
                "api_key_env": "LLM_API_KEY",
                "api_key": LLM_API_KEY_RAW or "local",
                "base_url": base_url,
                "model": MODEL_NAME or "mistral"
            }
        if "aiplatform.googleapis.com" in base_url:
            return {
                "provider": "vertex",
                "display_name": "Google Cloud Vertex AI",
                "requires_api_key": True,
                "api_key_env": "GOOGLE_API_KEY",
                "api_key": resolve_vertex_token(),
                "base_url": base_url,
                "model": MODEL_NAME or "google/gemini-2.0-flash",
                "project": GOOGLE_CLOUD_PROJECT,
                "region": GOOGLE_CLOUD_REGION
            }

    if GOOGLE_CLOUD_PROJECT and not OPENROUTER_API_KEY:
        return {
            "provider": "vertex",
            "display_name": "Google Cloud Vertex AI",
            "requires_api_key": True,
            "api_key_env": "GOOGLE_API_KEY",
            "api_key": resolve_vertex_token(),
            "base_url": f"https://{GOOGLE_CLOUD_REGION}-aiplatform.googleapis.com/v1beta1/projects/{GOOGLE_CLOUD_PROJECT}/locations/{GOOGLE_CLOUD_REGION}/endpoints/openapi/",
            "model": MODEL_NAME or "google/gemini-2.0-flash",
            "project": GOOGLE_CLOUD_PROJECT,
            "region": GOOGLE_CLOUD_REGION
        }

    # Default fallback: OpenRouter
    return {
        "provider": "openrouter",
        "display_name": "OpenRouter",
        "requires_api_key": True,
        "api_key_env": "OPENROUTER_API_KEY",
        "api_key": OPENROUTER_API_KEY or LLM_API_KEY_RAW,
        "base_url": "https://openrouter.ai/api/v1",
        "model": MODEL_NAME or "nex-agi/nex-n2.5-mini:free"
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
    Factory function to dynamically create the configured ChatOpenAI client.
    Points to Local LLM, Google Cloud Vertex AI, or OpenRouter.
    """
    info = get_provider_info(provider_override)
    provider = info["provider"]
    key = api_key if api_key is not None else info.get("api_key", "")
    model = model_name if model_name is not None else info.get("model", "")
    url = base_url if base_url is not None else info.get("base_url", "")
    tokens = max_tokens if max_tokens is not None else MAX_TOKENS
    temp = temperature if temperature is not None else TEMPERATURE

    # Reasoning tokens for OpenRouter models that support it
    eb = extra_body_params
    if eb is None and REASONING_MAX_TOKENS > 0 and provider == "openrouter":
        eb = {"reasoning": {"max_tokens": REASONING_MAX_TOKENS}}

    default_url = "https://openrouter.ai/api/v1"
    if provider == "vertex":
        region = info.get("region") or GOOGLE_CLOUD_REGION or "us-central1"
        project = info.get("project") or GOOGLE_CLOUD_PROJECT or ""
        default_url = f"https://{region}-aiplatform.googleapis.com/v1beta1/projects/{project}/locations/{region}/endpoints/openapi/" if project else f"https://{region}-aiplatform.googleapis.com/v1beta1/locations/{region}/endpoints/openapi/"
    elif provider == "local":
        default_url = "http://localhost:11434/v1"

    target_base_url = url or default_url
    target_api_key = key or ("local" if provider == "local" else "dummy")

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
    For Vertex AI and OpenRouter, ensures an API key / token is provided and valid.
    """
    info = get_provider_info()
    if not info.get("requires_api_key", True):
        return True

    key = (info.get("api_key") or "").strip()
    if not key:
        return False
    if key in ("sk-or-v1-...", "your-key-here", "sk-..."):
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
        # Quick 1-token probe to verify connectivity, auth, and quota using active client
        active_llm = create_llm_client()
        probe_prompt = ChatPromptTemplate.from_messages([("user", "hi")])
        probe_res = active_llm.invoke(probe_prompt.format_messages())
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
