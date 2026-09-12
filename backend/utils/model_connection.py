"""
LLM Model Connection and Health Check Utilities.
Strictly supports:
1. Local LLMs (Ollama, LM Studio, vLLM - requires no API key!)
2. Google Cloud Vertex AI (Google Cloud enterprise platform)
3. OpenRouter (Multi-model gateway)
"""

import os
import urllib.request
import json
from typing import Dict, Any, Optional, List
from dotenv import load_dotenv

env_path = os.path.join(os.path.dirname(__file__), "..", ".env")
if os.path.exists(env_path):
    load_dotenv(dotenv_path=env_path)
else:
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



def get_service_account_path() -> Optional[str]:
    """Resolves path to service_account.json if present in env, backend, or project root."""
    env_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS", "").strip()
    candidates = [
        env_path,
        "service_account.json",
        os.path.join(os.path.dirname(__file__), "..", "service_account.json"),
        os.path.join(os.path.dirname(__file__), "..", "..", "service_account.json"),
    ]
    for path in candidates:
        if path and os.path.exists(path):
            return os.path.abspath(path)
    return None


def resolve_vertex_token() -> str:
    """Resolves Vertex AI token if needed."""
    sa_path = get_service_account_path()
    if sa_path:
        try:
            import google.auth
            from google.auth.transport.requests import Request
            creds, _ = google.auth.load_credentials_from_file(sa_path, scopes=["https://www.googleapis.com/auth/cloud-platform"])
            creds.refresh(Request())
            return creds.token or ""
        except Exception:
            pass
    return GOOGLE_API_KEY or LLM_API_KEY_RAW


def resolve_vertex_project() -> str:
    """Detects GCP Project ID from env or service_account.json."""
    proj = (
        os.getenv("GOOGLE_CLOUD_PROJECT", "").strip()
        or os.getenv("VERTEX_PROJECT_ID", "").strip()
        or os.getenv("PROJECT_ID", "").strip()
    )
    if proj:
        return proj
    sa_path = get_service_account_path()
    if sa_path:
        try:
            import json
            with open(sa_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data.get("project_id") or data.get("quota_project_id") or ""
        except Exception:
            pass
    return ""


def get_provider_info(provider_override: Optional[str] = None) -> Dict[str, Any]:
    """
    Detects and returns active provider metadata.
    Supported: 'local' (Ollama/LM Studio), 'vertex' (Google Cloud), 'openrouter'.
    """
    prov = (provider_override or LLM_PROVIDER_RAW or "").lower()
    base_url = LLM_BASE_URL_RAW

    # 1. Google Cloud Vertex AI
    if prov in ("vertex", "vertexai"):
        model = MODEL_NAME or "gemini-2.5-flash"
        region = GOOGLE_CLOUD_REGION or "us-central1"
        project = resolve_vertex_project()
        sa_path = get_service_account_path()

        return {
            "provider": "vertex",
            "display_name": "Google Cloud Vertex AI",
            "requires_api_key": not bool(sa_path),
            "api_key_env": "GOOGLE_APPLICATION_CREDENTIALS" if sa_path else "GOOGLE_API_KEY",
            "api_key": sa_path or GOOGLE_API_KEY or LLM_API_KEY_RAW or "service_account.json",
            "base_url": base_url,
            "model": model,
            "project": project,
            "region": region,
            "service_account_path": sa_path
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


def get_ollama_base_url() -> str:
    """
    Llama endpoint for the local-llama selector (Ollama or Cloud Run llama.cpp).
    Prefers OLLAMA_* overrides, then LLM_BASE_URL (Cloud Run /v1), else localhost Ollama.
    """
    url = (
        os.getenv("OLLAMA_BASE_URL", "").strip()
        or os.getenv("OLLAMA_MODEL_URL", "").strip()
        or os.getenv("OLLAMA_URL", "").strip()
        or os.getenv("OLLAMA_HOST", "").strip()
        or os.getenv("LOCAL_LLM_URL", "").strip()
        or LLM_BASE_URL_RAW
        or "http://localhost:11434"
    ).rstrip("/")

    if not url.startswith("http://") and not url.startswith("https://"):
        url = f"http://{url}"

    # Strip trailing /v1 so /api/tags and /health work on the service root
    if url.endswith("/v1"):
        url = url[:-3]

    return url


def get_ollama_v1_url() -> str:
    """OpenAI-compatible /v1 endpoint for Llama (Ollama or llama.cpp)."""
    return f"{get_ollama_base_url()}/v1"


def _llama_auth_headers() -> Dict[str, str]:
    headers = {"User-Agent": "Odhikar-AI", "Accept": "application/json"}
    if LLM_API_KEY_RAW:
        headers["Authorization"] = f"Bearer {LLM_API_KEY_RAW}"
    return headers


def _http_get_json(url: str, timeout: float = 8.0) -> Any:
    req = urllib.request.Request(url, headers=_llama_auth_headers())
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


def _extract_model_ids(payload: Any) -> List[str]:
    """Parse Ollama /api/tags or OpenAI /v1/models style responses."""
    if not isinstance(payload, dict):
        return []
    models: List[str] = []
    for m in payload.get("models") or []:
        if isinstance(m, dict):
            name = m.get("name") or m.get("model") or m.get("id")
            if name:
                models.append(str(name))
        elif isinstance(m, str):
            models.append(m)
    for m in payload.get("data") or []:
        if isinstance(m, dict):
            name = m.get("id") or m.get("name") or m.get("model")
            if name:
                models.append(str(name))
        elif isinstance(m, str):
            models.append(m)
    return models


# Thinking Level Configurations for Reasoning Models (Gemini 2.5/3.7/3.8/3.1 Pro)
THINKING_LEVEL_DEFAULT = os.getenv("THINKING_LEVEL", "medium").strip().lower()

THINKING_LEVELS: Dict[str, Dict[str, Any]] = {
    "off": {
        "id": "off",
        "budget": 0,
        "effort": "none",
        "name": "চিন্তা বন্ধ (দ্রুততম রেসপন্স)",
        "badge": "Off",
        "tag": "Fast · ০ টোকেন",
        "description": "চিন্তাভাবনার ধাপ ছাড়াই তাৎক্ষণিক রেসপন্স"
    },
    "low": {
        "id": "low",
        "budget": 1024,
        "effort": "low",
        "name": "সংক্ষিপ্ত চিন্তা (Light Reasoning)",
        "badge": "Light (1K)",
        "tag": "Light · ১,০২৪ টোকেন",
        "description": "প্রাথমিক বিশ্লেষণ ও দ্রুততম আইনি প্রশ্নোত্তর"
    },
    "medium": {
        "id": "medium",
        "budget": 2048,
        "effort": "medium",
        "name": "স্বাভাবিক চিন্তা (Balanced Reasoning)",
        "badge": "Balanced (2K)",
        "tag": "Balanced · ২,০৪৮ টোকেন",
        "description": "ভারসাম্যপূর্ণ গভীরতা ও সর্বোত্তম আইনি সিদ্ধান্ত (ডিফল্ট)"
    },
    "high": {
        "id": "high",
        "budget": 4096,
        "effort": "high",
        "name": "গভীর আইনি বিশ্লেষণ (Deep Thinking)",
        "badge": "Deep (4K)",
        "tag": "Deep · ৪,০৯৬ টোকেন",
        "description": "জটিল ঘটনা, ধারা ও প্রমাণপত্রের সর্বোচ্চ গভীর আইনি পর্যালোচনা"
    }
}


def create_llm_client(
    provider_override: Optional[str] = None,
    api_key: Optional[str] = None,
    model_name: Optional[str] = None,
    base_url: Optional[str] = None,
    max_tokens: Optional[int] = None,
    temperature: Optional[float] = None,
    extra_body_params: Optional[Dict[str, Any]] = None,
    thinking_level: Optional[str] = None,
    thinking_budget: Optional[int] = None
) -> BaseChatModel:
    """
    Factory function to dynamically create the configured ChatOpenAI client.
    Points to Local LLM, Google Cloud Vertex AI, or OpenRouter with Thinking Level support.
    """
    info = get_provider_info(provider_override)
    provider = info["provider"]
    key = api_key if api_key is not None else info.get("api_key", "")
    model = model_name if model_name is not None else info.get("model", "")
    url = base_url if base_url is not None else info.get("base_url", "")
    tokens = max_tokens if max_tokens is not None else MAX_TOKENS
    temp = temperature if temperature is not None else TEMPERATURE

    # Resolve thinking budget and effort
    lvl = (thinking_level or THINKING_LEVEL_DEFAULT or "medium").lower()
    resolved_budget = thinking_budget
    resolved_effort = "medium"
    if lvl in THINKING_LEVELS:
        cfg = THINKING_LEVELS[lvl]
        if resolved_budget is None:
            resolved_budget = cfg["budget"]
        resolved_effort = cfg["effort"]
    elif resolved_budget is None:
        resolved_budget = 2048

    # 1. Google Cloud Vertex AI (Native ChatVertexAI with service_account.json)
    if provider == "vertex":
        from langchain_google_vertexai import ChatVertexAI

        sa_path = get_service_account_path()
        if sa_path:
            os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = sa_path

        clean_model = model.replace("google/", "") if model.startswith("google/") else model
        if not clean_model:
            clean_model = "gemini-2.5-flash"

        region = info.get("region") or GOOGLE_CLOUD_REGION or "us-central1"
        project = info.get("project") or resolve_vertex_project() or "routemap-235819"

        # For Vertex AI Gemini models with thinking, max_output_tokens includes thinking tokens
        actual_max_tokens = tokens
        if resolved_budget is not None and resolved_budget > 0:
            actual_max_tokens = max(tokens + resolved_budget, 4096)

        vertex_kwargs: Dict[str, Any] = {
            "model": clean_model,
            "location": region,
            "temperature": temp,
            "max_output_tokens": actual_max_tokens,
        }
        if project:
            vertex_kwargs["project"] = project
        if resolved_budget is not None and resolved_budget >= 0:
            vertex_kwargs["thinking_budget"] = resolved_budget

        return ChatVertexAI(**vertex_kwargs)

    # Reasoning tokens for OpenRouter models that support it
    eb = extra_body_params
    if eb is None and provider == "openrouter":
        if resolved_budget is not None and resolved_budget > 0:
            eb = {"reasoning": {"max_tokens": resolved_budget, "effort": resolved_effort}}
        elif REASONING_MAX_TOKENS > 0:
            eb = {"reasoning": {"max_tokens": REASONING_MAX_TOKENS}}

    default_url = "https://openrouter.ai/api/v1"
    if provider == "local":
        default_url = get_ollama_v1_url()

    target_base_url = url or default_url
    target_api_key = key or ("local" if provider == "local" else "dummy")

    kwargs: Dict[str, Any] = {
        "base_url": target_base_url,
        "api_key": target_api_key,
        "model": model,
        "max_tokens": tokens,
        "temperature": temp
    }
    if provider == "local":
        # Cloud Run llama cold start + generation can exceed 90s.
        kwargs["request_timeout"] = 300.0
        kwargs["timeout"] = 300.0
    if eb:
        kwargs["extra_body"] = eb

    return ChatOpenAI(**kwargs)


# Initialize default dynamic singleton LLM instance
llm = create_llm_client()

# Multi-Model Registry: Gemini 2.5, 3.7, 3.8, 3.1 Pro and ONE Local Llama model
MODEL_REGISTRY: Dict[str, Dict[str, Any]] = {
    "gemini-2.5-flash": {
        "id": "gemini-2.5-flash",
        "name": "Google Gemini 2.5 Flash",
        "badge": "Gemini 2.5 Flash (Latest)",
        "tag": "Google AI · দ্রুততম",
        "family": "gemini",
        "provider": "vertex" if (resolve_vertex_project() or get_service_account_path()) else "openrouter",
        "model": "gemini-2.5-flash" if (resolve_vertex_project() or get_service_account_path()) else "google/gemini-2.5-flash",
        "supports_thinking": True,
        "is_local": False,
        "description": "সর্বাধুনিক দ্রুততম ক্লাউড মডেল ও নির্ভুল বাংলা আইনি বিশ্লেষণ (ডিফল্ট)"
    },
    "gemini-2.5-flash-lite": {
        "id": "gemini-2.5-flash-lite",
        "name": "Google Gemini 2.5 Flash-Lite",
        "badge": "Gemini 2.5 Lite",
        "tag": "Google AI · অতি দ্রুত ও সাশ্রয়ী",
        "family": "gemini",
        "provider": "vertex" if (resolve_vertex_project() or get_service_account_path()) else "openrouter",
        "model": "gemini-2.5-flash-lite" if (resolve_vertex_project() or get_service_account_path()) else "google/gemini-2.5-flash-lite",
        "supports_thinking": True,
        "is_local": False,
        "description": "অতি দ্রুত রেসপন্স ও সাশ্রয়ী বাংলা কথোপকথন"
    },
    "gemini-3.7-flash": {
        "id": "gemini-3.7-flash",
        "name": "Google Gemini 3.7 Flash",
        "badge": "Gemini 3.7 Flash (Thinking)",
        "tag": "Google AI · হাইব্রিড চিন্তা",
        "family": "gemini",
        "provider": "vertex" if (resolve_vertex_project() or get_service_account_path()) else "openrouter",
        "model": "gemini-2.5-flash" if (resolve_vertex_project() or get_service_account_path()) else "google/gemini-3.7-flash",
        "fallback_model": "gemini-2.5-flash",
        "supports_thinking": True,
        "is_local": False,
        "description": "সর্বাধুনিক হাইব্রিড যুক্তি মডেল — রিয়েল-টাইম গতি ও নিয়ন্ত্রণযোগ্য চিন্তাভাবনা"
    },
    "gemini-3.8-flash": {
        "id": "gemini-3.8-flash",
        "name": "Google Gemini 3.8 Flash",
        "badge": "Gemini 3.8 Flash (Next-Gen)",
        "tag": "Google AI · পরবর্তী প্রজন্ম",
        "family": "gemini",
        "provider": "vertex" if (resolve_vertex_project() or get_service_account_path()) else "openrouter",
        "model": "gemini-2.5-flash" if (resolve_vertex_project() or get_service_account_path()) else "google/gemini-3.8-flash",
        "fallback_model": "gemini-2.5-flash",
        "supports_thinking": True,
        "is_local": False,
        "description": "নেক্সট-জেন ফ্ল্যাশ মডেল — উন্নত চিন্তাভাবনা ও জটিল আইনি বিশ্লেষণ"
    },
    "gemini-3.1-pro": {
        "id": "gemini-3.1-pro",
        "name": "Google Gemini 3.1 Pro",
        "badge": "Gemini 3.1 Pro (Flagship Thinking)",
        "tag": "Google AI · ফ্ল্যাগশিপ চিন্তা",
        "family": "gemini",
        "provider": "vertex" if (resolve_vertex_project() or get_service_account_path()) else "openrouter",
        "model": "gemini-2.5-pro" if (resolve_vertex_project() or get_service_account_path()) else "google/gemini-3.1-pro-preview",
        "fallback_model": "gemini-2.5-pro",
        "supports_thinking": True,
        "is_local": False,
        "description": "সর্বোচ্চ স্তরের ফ্ল্যাগশিপ যুক্তি, সুক্ষ্ম আইনি ধারা ও প্রমাণের গভীরতম মূল্যায়ন"
    },
    "gemini-2.5-pro": {
        "id": "gemini-2.5-pro",
        "name": "Google Gemini 2.5 Pro",
        "badge": "Gemini 2.5 Pro",
        "tag": "Google AI · গভীর যুক্তি",
        "family": "gemini",
        "provider": "vertex" if (resolve_vertex_project() or get_service_account_path()) else "openrouter",
        "model": "gemini-2.5-pro" if (resolve_vertex_project() or get_service_account_path()) else "google/gemini-2.5-pro",
        "supports_thinking": True,
        "is_local": False,
        "description": "উচ্চতর বিশ্লেষণ, জটিল ধারা ও প্রমাণপত্র পর্যালোচনা"
    },
    "gemini-2.0-flash": {
        "id": "gemini-2.0-flash",
        "name": "Google Gemini 2.0 Flash",
        "badge": "Gemini 2.0 Flash",
        "tag": "Google AI · লো লেটেন্সি",
        "family": "gemini",
        "provider": "vertex" if (resolve_vertex_project() or get_service_account_path()) else "openrouter",
        "model": "gemini-2.0-flash" if (resolve_vertex_project() or get_service_account_path()) else "google/gemini-2.0-flash-001",
        "supports_thinking": False,
        "is_local": False,
        "description": "স্থিতিশীল ও নির্ভরযোগ্য দ্রুত বাংলা কথোপকথন"
    },
    "local-llama": {
        "id": "local-llama",
        "name": "Meta Llama (Cloud / Local GGUF)",
        "badge": "Llama GGUF",
        "tag": "Cloud Run · Ollama",
        "family": "llama",
        "provider": "local",
        "model": MODEL_NAME or "llama-3.2-1b-instruct",
        "base_url": get_ollama_v1_url(),
        "supports_thinking": False,
        "is_local": True,
        "description": "Self-hosted GGUF via OpenAI-compatible /v1 (Cloud Run llama.cpp or local Ollama)"
    }
}


def check_local_ollama_status() -> Dict[str, Any]:
    """
    Health-check the configured Llama server.
    Supports Ollama (/api/tags) and OpenAI-compatible llama.cpp (/v1/models, /health).
    Sends LLM_API_KEY when present (required for Cloud Run llama-server).
    """
    base_url = get_ollama_base_url()
    last_error: Optional[str] = None

    # 1) OpenAI-compatible /v1/models (llama.cpp Cloud Run)
    try:
        data = _http_get_json(f"{base_url}/v1/models", timeout=8.0)
        models = _extract_model_ids(data)
        has_llama = any("llama" in m.lower() for m in models) or bool(models)
        return {
            "online": True,
            "base_url": base_url,
            "models": models,
            "has_llama": has_llama,
            "protocol": "openai",
            "recommended_command": None if has_llama else "Check MODEL_NAME / LLM_BASE_URL for the Llama service.",
        }
    except Exception as e:
        last_error = str(e)

    # 2) Ollama native /api/tags
    try:
        data = _http_get_json(f"{base_url}/api/tags", timeout=3.0)
        models = _extract_model_ids(data)
        has_llama = any("llama" in m.lower() for m in models)
        return {
            "online": True,
            "base_url": base_url,
            "models": models,
            "has_llama": has_llama,
            "protocol": "ollama",
            "recommended_command": None if has_llama else "ollama run llama3.1",
        }
    except Exception as e:
        last_error = str(e)

    # 3) Plain /health (llama.cpp often exposes this without listing models)
    try:
        req = urllib.request.Request(f"{base_url}/health", headers=_llama_auth_headers())
        with urllib.request.urlopen(req, timeout=5.0) as resp:
            if 200 <= resp.status < 300:
                fallback = MODEL_NAME or "llama-3.2-1b-instruct"
                return {
                    "online": True,
                    "base_url": base_url,
                    "models": [fallback],
                    "has_llama": True,
                    "protocol": "health",
                    "recommended_command": None,
                }
    except Exception as e:
        last_error = str(e)

    return {
        "online": False,
        "base_url": base_url,
        "models": [],
        "has_llama": False,
        "error": last_error or "unreachable",
        "recommended_command": "Check LLM_BASE_URL and LLM_API_KEY for the Llama service (or run ollama locally).",
    }


def resolve_local_llama_model_name() -> str:
    """Resolve Llama model id from env or the live server's model list."""
    if MODEL_NAME and "gemini" not in MODEL_NAME.lower() and not MODEL_NAME.startswith("google/"):
        return MODEL_NAME
    status = check_local_ollama_status()
    if status.get("online") and status.get("models"):
        for m in status["models"]:
            if "llama3.1" in m.lower() or "llama-3.1" in m.lower():
                return m
        for m in status["models"]:
            if "llama" in m.lower():
                return m
        return status["models"][0]
    return "llama-3.2-1b-instruct"


def get_available_models() -> Dict[str, Any]:
    """Returns available models with real-time status and thinking levels for the frontend Model Selector."""
    ollama_info = check_local_ollama_status()
    ollama_v1 = get_ollama_v1_url()
    models_list = []
    for m_id, m_data in MODEL_REGISTRY.items():
        is_avail = True
        item = dict(m_data)
        if m_data["is_local"]:
            is_avail = ollama_info["online"]
            item["base_url"] = ollama_v1
        item["is_available"] = is_avail
        models_list.append(item)
    return {
        "models": models_list,
        "default_model": "gemini-2.5-flash",
        "thinking_levels": list(THINKING_LEVELS.values()),
        "default_thinking_level": THINKING_LEVEL_DEFAULT if THINKING_LEVEL_DEFAULT in THINKING_LEVELS else "medium",
        "ollama_status": ollama_info,
        "ollama_base_url": get_ollama_base_url(),
        "ollama_model_url": ollama_v1
    }


_client_cache: Dict[str, BaseChatModel] = {}

def get_llm_for_model(model_id: Optional[str] = None, thinking_level: Optional[str] = None) -> BaseChatModel:
    """Retrieves or dynamically instantiates a ChatModel for the requested model_id and thinking_level."""
    target_id = model_id or "gemini-2.5-flash"
    # Normalize common aliases
    if target_id in ("gemini-2.5-lite", "gemini-lite", "gemini-flash-lite"):
        target_id = "gemini-2.5-flash-lite"
    elif target_id in ("gemini-3.7", "gemini-3-7"):
        target_id = "gemini-3.7-flash"
    elif target_id in ("gemini-3.8", "gemini-3-8"):
        target_id = "gemini-3.8-flash"
    elif target_id in ("gemini-3-pro", "gemini-3.1"):
        target_id = "gemini-3.1-pro"

    reg = MODEL_REGISTRY.get(target_id)
    if not reg:
        reg = MODEL_REGISTRY["gemini-2.5-flash"]
        target_id = "gemini-2.5-flash"

    resolved_level = (thinking_level or THINKING_LEVEL_DEFAULT or "medium").lower()
    if resolved_level not in THINKING_LEVELS:
        resolved_level = "medium"

    cache_key = f"{target_id}::{resolved_level}"
    if cache_key in _client_cache:
        return _client_cache[cache_key]

    prov = reg["provider"]
    mdl = reg["model"]
    url = reg.get("base_url")

    if target_id == "local-llama":
        mdl = resolve_local_llama_model_name()
        url = get_ollama_v1_url()
        cache_key = f"{target_id}::{resolved_level}::{mdl}::{url}"
        if cache_key in _client_cache:
            return _client_cache[cache_key]
        client = create_llm_client(
            provider_override="local",
            api_key=LLM_API_KEY_RAW or "local",
            model_name=mdl,
            base_url=url,
            thinking_level=resolved_level,
        )
        _client_cache[cache_key] = client
        return client

    client = create_llm_client(
        provider_override=prov,
        model_name=mdl,
        base_url=url,
        thinking_level=resolved_level
    )
    _client_cache[cache_key] = client
    return client


def is_model_configured() -> bool:
    """
    Checks if the active model provider is properly configured.
    For local LLMs (Ollama, LM Studio), returns True without requiring an API key.
    For Vertex AI and OpenRouter, ensures an API key / token is provided and valid.
    """
    info = get_provider_info()
    if not info.get("requires_api_key", True):
        return True

    if info.get("provider") == "vertex":
        sa_path = get_service_account_path()
        if sa_path and os.path.exists(sa_path):
            return True
        key = (info.get("api_key") or "").strip()
        return bool(key and key not in ("sk-or-v1-...", "your-key-here", "dummy", "local"))

    key = (info.get("api_key") or "").strip()
    if not key:
        return False
    if key in ("sk-or-v1-...", "your-key-here", "sk-..."):
        return False
    return True


def check_llm_status(model_id: Optional[str] = None) -> Dict[str, Any]:
    """
    Checks LLM connectivity, authentication, and quota status dynamically.
    Returns a status dictionary suitable for health-check APIs and frontend indicators.
    """
    target_id = model_id or "gemini-2.5-flash"
    reg = MODEL_REGISTRY.get(target_id, MODEL_REGISTRY["gemini-2.5-flash"])
    provider_name = reg["name"]
    model_name = reg["model"]

    if reg.get("is_local"):
        ollama_status = check_local_ollama_status()
        if not ollama_status["online"]:
            return {
                "connected": False,
                "status_code": 503,
                "provider": "local",
                "provider_name": provider_name,
                "model": model_name,
                "title": "Llama সার্ভার সংযোগ বিচ্ছিন্ন",
                "message_bn": "Llama সার্ভার (Cloud Run / Ollama) সচল নেই। LLM_BASE_URL ও LLM_API_KEY যাচাই করুন, অথবা Gemini Vertex মডেল ব্যবহার করুন।",
                "message_en": f"Llama server is offline ({ollama_status.get('base_url', '')}). Check LLM_BASE_URL/LLM_API_KEY or switch to Gemini Vertex.",
                "troubleshooting_bn": [
                    "Cloud Run Llama: LLM_BASE_URL ও LLM_API_KEY সঠিক আছে কি না দেখুন।",
                    f"{ollama_status.get('base_url', '')} এ /v1/models বা /health রেসপন্স আসে কি না পরীক্ষা করুন।",
                    "লোকাল Ollama: 'ollama serve' / 'ollama run llama3.1' চালান।",
                    "অথবা ড্রপডাউন থেকে Google Gemini (Vertex AI) নির্বাচন করুন।"
                ]
            }

    info = get_provider_info(reg["provider"])
    if not reg.get("is_local") and not is_model_configured():
        err = get_error_message("missing_api_key", provider_info=info)
        err["connected"] = False
        err["provider"] = reg["provider"]
        err["model"] = model_name
        return err

    try:
        active_llm = get_llm_for_model(target_id)
        probe_prompt = ChatPromptTemplate.from_messages([("user", "hi")])
        probe_res = active_llm.invoke(probe_prompt.format_messages())
        return {
            "connected": True,
            "status_code": 200,
            "provider": reg["provider"],
            "provider_name": provider_name,
            "model": model_name,
            "selected_model": target_id,
            "title": f"{provider_name} সংযুক্ত (Connected)",
            "message_bn": f"{provider_name} সফলভাবে সংযুক্ত ও সক্রিয় আছে।",
            "message_en": f"{provider_name} is connected and active."
        }
    except Exception as exc:
        err = parse_llm_error(exc, provider_info=info)
        err["connected"] = False
        err["provider"] = reg["provider"]
        err["provider_name"] = provider_name
        err["model"] = model_name
        err["selected_model"] = target_id
        return err
