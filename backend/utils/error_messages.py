"""
Error message definitions and error handling utilities for LLM operations.
Provides standardized, user-facing bilingual (Bengali and English) error messages
for 401 Unauthorized, disconnection/network, token/quota issues, and provider-specific errors.
Supported Providers:
1. Local LLMs (Ollama, LM Studio, vLLM - requires no API key)
2. Google Cloud Vertex AI (GCP enterprise platform)
3. OpenRouter (multi-model gateway)
"""

from typing import Dict, Any, Optional, List


def get_provider_templates(provider_info: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Generates tailored error message templates based on the active provider.
    Strictly supports: Local LLMs (Ollama / LM Studio), Vertex AI, and OpenRouter.
    """
    if provider_info is None:
        try:
            from .model_connection import get_provider_info
            provider_info = get_provider_info()
        except Exception:
            provider_info = {}

    info = provider_info or {}
    provider = (info.get("provider") or "openrouter").lower()
    display_name = info.get("display_name") or "AI Model"
    key_env = info.get("api_key_env") or "LLM_API_KEY"
    base_url = info.get("base_url") or ""
    model_name = info.get("model") or "selected model"

    # 1. Local LLM / Ollama Templates
    if provider in ("local", "ollama", "lmstudio"):
        url_display = base_url or "http://localhost:11434"
        return {
            "authentication_error": {
                "status_code": 401,
                "title": "লোকাল এলএলএম এক্সেস ত্রুটি (Error 401 Unauthorized)",
                "message_bn": f"লোকাল এলএলএম (Ollama/LM Studio) সার্ভার অনুরোধটি প্রত্যাখ্যান করেছে ({url_display})।",
                "message_en": f"Local LLM server rejected the request at {url_display}.",
                "troubleshooting_bn": [
                    f"আপনার কম্পিউটারে লোকাল মডেল সার্ভার চালু আছে কি না পরীক্ষা করুন ({url_display})।",
                    "Ollama ব্যবহার করলে টার্মিনালে 'ollama list' দিয়ে মডেলটি ইনস্টল আছে কি না দেখুন।"
                ]
            },
            "connection_error": {
                "status_code": 503,
                "title": "লোকাল এলএলএম সংযোগ বিচ্ছিন্ন (Ollama / Local Not Connected)",
                "message_bn": f"লোকাল এলএলএম (Ollama/LM Studio) সার্ভারের সাথে সংযোগ স্থাপন করা যাচ্ছে না ({url_display})।",
                "message_en": f"Could not connect to local LLM server at {url_display}. Please check if server is running.",
                "troubleshooting_bn": [
                    "টার্মিনালে 'ollama serve' অথবা LM Studio Local Server চালু করুন।",
                    f"সার্ভার পোর্ট সচল আছে কি না পরীক্ষা করুন ({url_display})।",
                    "ইন্টারনেট সংযোগের প্রয়োজন নেই, শুধু লোকাল সার্ভিসটি সচল রাখুন।"
                ]
            },
            "not_found_error": {
                "status_code": 404,
                "title": "লোকাল মডেল পাওয়া যায়নি (Model Not Found)",
                "message_bn": f"মডেল '{model_name}' লোকাল সার্ভারে পাওয়া যায়নি বা লোড করা নেই।",
                "message_en": f"Model '{model_name}' was not found on local server.",
                "troubleshooting_bn": [
                    f"Ollama হলে টার্মিনালে কমান্ডটি চালান: ollama pull {model_name}",
                    "LM Studio হলে মডেলটি লোড করে 'Start Server' করুন।"
                ]
            },
            "rate_limit_error": {
                "status_code": 429,
                "title": "লোকাল সিস্টেম মেমরি বা কিউ সীমাবদ্ধতা (Error 429)",
                "message_bn": "লোকাল এলএলএম সার্ভারের প্রসেসিং ক্ষমতা সাময়িক সীমাবদ্ধতায় পৌঁছেছে। কিছুক্ষণ পর চেষ্টা করুন।",
                "message_en": "Local LLM concurrency or resource limit reached. Please retry.",
                "troubleshooting_bn": [
                    "আপনার পিসির RAM / VRAM ব্যবহার পরীক্ষা করুন।",
                    "অন্যান্য মেমরি-বহুল অ্যাপ্লিকেশন বন্ধ করে পুনরায় চেষ্টা করুন।"
                ]
            },
            "token_credit_error": {
                "status_code": 402,
                "title": "লোকাল রিসোর্স সীমাবদ্ধতা",
                "message_bn": "লোকাল সার্ভার রিসোর্স অপ্রতুল।",
                "message_en": "Local server resources exhausted.",
                "troubleshooting_bn": ["সিস্টেম রিসোর্স যাচাই করুন।"]
            },
            "context_limit_error": {
                "status_code": 400,
                "title": "টোকেন ধারণক্ষমতা অতিক্রম (Context Limit)",
                "message_bn": "ইনপুট বিবরণটি লোকাল মডেলের কনটেক্সট উইন্ডো ছাড়িয়ে গেছে। অনুগ্রহ করে সংক্ষেপ করুন।",
                "message_en": "Input exceeds local model context window limit.",
                "troubleshooting_bn": ["বিবরণটি সংক্ষেপ করে পুনরায় সাবমিট করুন।"]
            },
            "missing_api_key": {
                "status_code": 500,
                "title": "লোকাল সার্ভার কনফিগারেশন ত্রুটি",
                "message_bn": f"লোকাল সার্ভার URL ({url_display}) কনফিগারেশনে সমস্যা রয়েছে।",
                "message_en": "Local server URL is misconfigured in backend/.env.",
                "troubleshooting_bn": [f"backend/.env ফাইলে LLM_BASE_URL={url_display} নিশ্চিত করুন।"]
            },
            "general_error": {
                "status_code": 500,
                "title": "লোকাল এলএলএম ত্রুটি (Local Processing Error)",
                "message_bn": "লোকাল মডেল থেকে প্রতিক্রিয়া প্রক্রিয়া করার সময় একটি অপ্রত্যাশিত ত্রুটি ঘটেছে।",
                "message_en": "An error occurred while communicating with the local LLM.",
                "troubleshooting_bn": ["লোকাল টার্মিনাল লগ পরীক্ষা করুন।"]
            }
        }

    # 2. Google Cloud Vertex AI
    if provider in ("vertex", "vertexai"):
        region_display = info.get("region") or "us-central1"
        project_display = info.get("project") or "GOOGLE_CLOUD_PROJECT"
        return {
            "authentication_error": {
                "status_code": 401,
                "title": "Vertex AI অথেন্টিকেশন ত্রুটি (Error 401 Unauthorized)",
                "message_bn": f"Google Cloud Vertex AI এপিআই কী (API Key) বা এক্সেস টোকেন সঠিক নয়। backend/.env ফাইলে {key_env} ও GOOGLE_CLOUD_PROJECT পরীক্ষা করুন।",
                "message_en": f"Vertex AI Authentication Error: Check {key_env} and GOOGLE_CLOUD_PROJECT in backend/.env.",
                "troubleshooting_bn": [
                    f"backend/.env ফাইলে {key_env} (OAuth 2 Access Token) অথবা GOOGLE_APPLICATION_CREDENTIALS সঠিক আছে কি না পরীক্ষা করুন।",
                    f"প্রজেক্ট আইডি GOOGLE_CLOUD_PROJECT={project_display} সঠিক কি না যাচাই করুন।",
                    f"রিজিয়ন GOOGLE_CLOUD_REGION={region_display} মডেল ডেপ্লয়মেন্টের সাথে মিল আছে কি না দেখুন।"
                ]
            },
            "connection_error": {
                "status_code": 503,
                "title": "Vertex AI সংযোগ বিচ্ছিন্ন (Connection Error)",
                "message_bn": f"Google Cloud Vertex AI সার্ভারের সাথে সংযোগ স্থাপন করা যাচ্ছে না ({base_url})।",
                "message_en": f"Could not connect to Google Cloud Vertex AI endpoint at {base_url}.",
                "troubleshooting_bn": [
                    "ইন্টারনেট সংযোগ এবং Vertex AI এন্ডপয়েন্ট স্ট্যাটাস পরীক্ষা করুন।",
                    f"GOOGLE_CLOUD_REGION={region_display} সচল আছে কি না দেখুন।"
                ]
            },
            "not_found_error": {
                "status_code": 404,
                "title": "Vertex AI মডেল পাওয়া যায়নি (Model Not Found)",
                "message_bn": f"মডেল '{model_name}' Vertex AI প্রজেক্ট বা রিজিয়নে পাওয়া যায়নি।",
                "message_en": f"Model '{model_name}' not found on Vertex AI project {project_display}.",
                "troubleshooting_bn": [
                    "মডেল নামটি সঠিক কি না পরীক্ষা করুন (যেমন: google/gemini-2.0-flash বা gemini-1.5-flash)।",
                    "মডেলটি নির্বাচিত রিজিয়নে এনেবল করা আছে কি না গুগল ক্লাউড কনসোলে দেখুন।"
                ]
            },
            "rate_limit_error": {
                "status_code": 429,
                "title": "Vertex AI কোটা অতিক্রম (Error 429 Quota Exceeded)",
                "message_bn": "Google Cloud Vertex AI কোটা সীমা অতিক্রম করেছে।",
                "message_en": "Google Cloud Vertex AI rate limit or quota exceeded.",
                "troubleshooting_bn": ["গুগল ক্লাউড কনসোলে কোটা বৃদ্ধি বা রিকোয়েস্ট হার পরীক্ষা করুন।"]
            },
            "token_credit_error": {
                "status_code": 402,
                "title": "Vertex AI বিলিং ত্রুটি",
                "message_bn": "Google Cloud অ্যাকাউন্টে বিলিং বা ক্রেডিট সমস্যা দেখা দিয়েছে।",
                "message_en": "Google Cloud billing or quota problem.",
                "troubleshooting_bn": ["Google Cloud কনসোলে বিলিং স্ট্যাটাস সক্রিয় আছে কি না দেখুন।"]
            },
            "context_limit_error": {
                "status_code": 400,
                "title": "টোকেন ধারণক্ষমতা অতিক্রম",
                "message_bn": "ইনপুট বিবরণটি Vertex AI মডেলের কনটেক্সট উইন্ডো ছাড়িয়ে গেছে।",
                "message_en": "Input text exceeds Vertex AI model context limit.",
                "troubleshooting_bn": ["বিবরণটি সংক্ষেপ করে পুনরায় সাবমিট করুন।"]
            },
            "missing_api_key": {
                "status_code": 401,
                "title": "Vertex AI কনফিগারেশন ত্রুটি (API Key Missing)",
                "message_bn": f"Vertex AI এর জন্য {key_env} অথবা GOOGLE_CLOUD_PROJECT কনফিগার করা হয়নি।",
                "message_en": "Missing Vertex AI token or GOOGLE_CLOUD_PROJECT in backend/.env.",
                "troubleshooting_bn": [
                    f"backend/.env ফাইলে {key_env} এবং GOOGLE_CLOUD_PROJECT=আপনার_প্রজেক্ট যোগ করুন।"
                ]
            },
            "general_error": {
                "status_code": 500,
                "title": "Vertex AI প্রসেসিং ত্রুটি",
                "message_bn": "Google Cloud Vertex AI থেকে প্রতিক্রিয়া পেতে সমস্যা হয়েছে।",
                "message_en": "An error occurred with Vertex AI processing.",
                "troubleshooting_bn": ["গুগল ক্লাউড কনসোল লগ পরীক্ষা করুন।"]
            }
        }

    # 3. OpenRouter (Multi-Model Gateway) - Default
    return {
        "authentication_error": {
            "status_code": 401,
            "title": "OpenRouter এপিআই কী ত্রুটি (Error 401 Unauthorized)",
            "message_bn": f"এআই মডেলের OpenRouter API Key বা টোকেন সঠিক নয় অথবা মেয়াদ শেষ। backend/.env ফাইলে {key_env} যাচাই করুন।",
            "message_en": f"OpenRouter API Key is invalid, missing, or expired. Please verify {key_env} in backend/.env.",
            "troubleshooting_bn": [
                f"backend/.env ফাইলে {key_env} সঠিক আছে কি না তা যাচাই করুন।",
                "API Key পরিবর্তন করলে ব্যাকএন্ড সার্ভার রিস্টার্ট করুন।"
            ]
        },
        "connection_error": {
            "status_code": 503,
            "title": "OpenRouter সার্ভার সংযোগ বিচ্ছিন্ন (Not Connected)",
            "message_bn": "OpenRouter মডেল সার্ভারের সাথে সংযোগ স্থাপন করা যাচ্ছে না। ইন্টারনেট সংযোগ ও সার্ভারের স্থিতি পরীক্ষা করুন।",
            "message_en": "Could not connect to OpenRouter server. Please check internet connection.",
            "troubleshooting_bn": [
                "আপনার কম্পিউটার ও ব্যাকএন্ড সার্ভার সচল আছে কি না পরীক্ষা করুন।",
                "ইন্টারনেট সংযোগ চালু আছে কি না দেখুন।"
            ]
        },
        "not_found_error": {
            "status_code": 404,
            "title": "OpenRouter মডেল পাওয়া যায়নি",
            "message_bn": f"মডেল '{model_name}' OpenRouter-এ পাওয়া যায়নি।",
            "message_en": f"Model '{model_name}' was not found on OpenRouter.",
            "troubleshooting_bn": ["openrouter.ai/models থেকে সক্রিয় মডেল নাম যাচাই করে backend/.env-এ সেট করুন।"]
        },
        "rate_limit_error": {
            "status_code": 429,
            "title": "টোকেন কোটা বা রেট লিমিট অতিক্রম (Error 429 Rate Limit)",
            "message_bn": "টোকেন কোটা শেষ অথবা মডেলটির সাময়িক রেট লিমিট অতিক্রম করেছে। অনুগ্রহ করে কিছুক্ষণ পর পুনরায় চেষ্টা করুন।",
            "message_en": "OpenRouter Rate Limit / Token Quota Exceeded (429). Please retry shortly.",
            "troubleshooting_bn": [
                "মডেলের বর্তমান রিকোয়েস্ট লিমিট শেষ হয়েছে — ১-২ মিনিট অপেক্ষা করে পুনরায় চেষ্টা করুন।",
                "অথবা backend/.env ফাইলে অপর একটি সক্রিয় মডেল বা নিজস্ব API Key ব্যবহার করুন।"
            ]
        },
        "token_credit_error": {
            "status_code": 402,
            "title": "টোকেন ব্যালেন্স ত্রুটি (Error 402 Payment Required)",
            "message_bn": "আপনার OpenRouter অ্যাকাউন্টে পর্যাপ্ত টোকেন ব্যালেন্স বা ক্রেডিট নেই। অনুগ্রহ করে টোকেন রিচার্জ করুন।",
            "message_en": "OpenRouter Token Balance Error (402 Payment Required): Insufficient credit or token balance.",
            "troubleshooting_bn": [
                "আপনার OpenRouter অ্যাকাউন্টে টোকেন ব্যালেন্স বা ক্রেডিট যোগ করুন।"
            ]
        },
        "context_limit_error": {
            "status_code": 400,
            "title": "টোকেন ধারণক্ষমতা অতিক্রম (Token Context Limit)",
            "message_bn": "ইনপুট বিবরণটি মডেলের অনুমোদিত টোকেন সীমা ছাড়িয়ে গেছে। অনুগ্রহ করে সংক্ষেপ করে লিখুন।",
            "message_en": "Input text exceeds the model maximum token context window.",
            "troubleshooting_bn": ["বিবরণটি সংক্ষেপ করে পুনরায় সাবমিট করুন।"]
        },
        "missing_api_key": {
            "status_code": 401,
            "title": "LLM এপিআই কী অনুপস্থিত (API Key Missing)",
            "message_bn": f"এআই মডেলের API কী কনফিগার করা হয়নি। backend/.env ফাইলে {key_env} প্রদান করুন।",
            "message_en": f"{key_env} is missing or unconfigured in backend/.env.",
            "troubleshooting_bn": [f"backend/.env ফাইলে {key_env} সেট করুন।"]
        },
        "general_error": {
            "status_code": 500,
            "title": "এলএলএম প্রসেসিং ত্রুটি (LLM Processing Error)",
            "message_bn": "এআই মডেল থেকে প্রতিক্রিয়া পেতে সমস্যা হয়েছে।",
            "message_en": "An unexpected error occurred while communicating with the AI model.",
            "troubleshooting_bn": ["কিছুক্ষণ পর পুনরায় চেষ্টা করুন।"]
        }
    }


# Static fallback dictionary for backward compatibility
ERROR_MESSAGES = get_provider_templates()


def parse_llm_error(exc: Exception, provider_info: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Parses LLM exceptions and classifies them into standardized errors
    (401 Unauthorized, disconnection/network, 404 Model Not Found, 429 Rate Limit,
    402 Payment Required, and 400 Context Limit) for Local LLMs, Vertex AI, and OpenRouter.
    """
    if provider_info is None:
        try:
            from .model_connection import get_provider_info
            provider_info = get_provider_info()
        except Exception:
            provider_info = {}

    templates = get_provider_templates(provider_info)
    err_str = str(exc)
    err_lower = err_str.lower()
    exc_name = type(exc).__name__
    status_code = getattr(exc, "status_code", None)
    if not status_code and hasattr(exc, "response") and hasattr(exc.response, "status_code"):
        status_code = exc.response.status_code

    # 1. Check for 404 Model Not Found
    if (
        status_code == 404
        or "404" in err_str
        or "model not found" in err_lower
        or "no longer available" in err_lower
        or "try pulling it" in err_lower
        or "does not exist" in err_lower
    ):
        template = templates.get("not_found_error", templates["general_error"]).copy()
        troubleshooting = list(template.get("troubleshooting_bn", []))

        return {
            "error_type": "not_found_error",
            "status_code": 404,
            "title": template["title"],
            "message_bn": template["message_bn"],
            "message_en": template["message_en"],
            "troubleshooting_bn": troubleshooting,
            "raw_error": err_str[:300]
        }

    # 2. Check for HTTP 401 / 403 / Invalid API Key / Authentication Error
    if (
        status_code in (401, 403)
        or "401" in err_str
        or "authentication" in err_lower
        or "unauthorized" in err_lower
        or "unauthenticated" in err_lower
        or "api_key_invalid" in err_lower
        or "api key not valid" in err_lower
        or "invalid api key" in err_lower
        or "missing authentication" in err_lower
        or "incorrect api key" in err_lower
        or "user not found" in err_lower
        or "AuthenticationError" in exc_name
        or "permission_denied" in err_lower
    ):
        template = templates.get("authentication_error", templates["general_error"])
        return {
            "error_type": "authentication_error",
            "status_code": 401,
            "title": template["title"],
            "message_bn": template["message_bn"],
            "message_en": template["message_en"],
            "troubleshooting_bn": template["troubleshooting_bn"],
            "raw_error": err_str[:300]
        }

    # 3. Check for Connection / Network / Timeout / Not Connected
    if (
        "connection" in err_lower
        or "connecterror" in err_lower
        or "timeout" in err_lower
        or "refused" in err_lower
        or "name or service not known" in err_lower
        or "getaddrinfo failed" in err_lower
        or "failed to establish a new connection" in err_lower
        or "ConnectionError" in exc_name
        or "APITimeoutError" in exc_name
    ):
        template = templates.get("connection_error", templates["general_error"])
        return {
            "error_type": "connection_error",
            "status_code": 503,
            "title": template["title"],
            "message_bn": template["message_bn"],
            "message_en": template["message_en"],
            "troubleshooting_bn": template["troubleshooting_bn"],
            "raw_error": err_str[:300]
        }

    # 4. Check for 402 Payment Required / Insufficient Token Balance
    if (
        status_code == 402
        or "402" in err_str
        or "payment required" in err_lower
        or "insufficient credits" in err_lower
        or "insufficient balance" in err_lower
    ):
        template = templates.get("token_credit_error", templates["general_error"])
        return {
            "error_type": "token_credit_error",
            "status_code": 402,
            "title": template["title"],
            "message_bn": template["message_bn"],
            "message_en": template["message_en"],
            "troubleshooting_bn": template["troubleshooting_bn"],
            "raw_error": err_str[:300]
        }

    # 5. Check for 429 Rate Limit / Token Quota Exceeded / Resource Exhausted
    if (
        status_code == 429
        or "429" in err_str
        or "rate limit" in err_lower
        or "rate_limit" in err_lower
        or "quota" in err_lower
        or "too many requests" in err_lower
        or "resource_exhausted" in err_lower
        or "RateLimitError" in exc_name
    ):
        template = templates.get("rate_limit_error", templates["general_error"]).copy()
        troubleshooting = list(template.get("troubleshooting_bn", []))
        message_bn = template["message_bn"]

        import re
        m = re.search(r"retry in ([0-9]+(?:\.[0-9]+)?)s?", err_str, re.IGNORECASE)
        if not m:
            m = re.search(r"retryDelay':\s*'([0-9]+)s?'", err_str)
        if m:
            try:
                sec = int(float(m.group(1)))
                message_bn += f" (অনুগ্রহ করে {sec} সেকেন্ড অপেক্ষা করুন)"
                troubleshooting.insert(0, f"কুলডাউন: ঠিক {sec} সেকেন্ড অপেক্ষা করে আবার চেষ্টা করুন।")
            except Exception:
                pass

        return {
            "error_type": "rate_limit_error",
            "status_code": 429,
            "title": template["title"],
            "message_bn": message_bn,
            "message_en": template["message_en"],
            "troubleshooting_bn": troubleshooting,
            "raw_error": err_str[:300]
        }

    # 6. Check for Context Length / Token Budget Exceeded (Error 400)
    if (
        "context_length" in err_lower
        or "maximum context length" in err_lower
        or "token limit" in err_lower
        or "too many tokens" in err_lower
    ):
        template = templates.get("context_limit_error", templates["general_error"])
        return {
            "error_type": "context_limit_error",
            "status_code": 400,
            "title": template["title"],
            "message_bn": template["message_bn"],
            "message_en": template["message_en"],
            "troubleshooting_bn": template["troubleshooting_bn"],
            "raw_error": err_str[:300]
        }

    # Default General LLM Error
    template = templates.get("general_error", ERROR_MESSAGES["general_error"])
    return {
        "error_type": "llm_general_error",
        "status_code": getattr(exc, "status_code", 500) or 500,
        "title": template["title"],
        "message_bn": f"{template['message_bn']} ত্রুটির বিবরণ: {err_str[:150]}",
        "message_en": f"{template['message_en']} Raw: {err_str[:150]}",
        "troubleshooting_bn": template["troubleshooting_bn"],
        "raw_error": err_str[:300]
    }


def get_error_message(
    error_type: str, 
    custom_raw: Optional[str] = None,
    provider_info: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Returns predefined error details for a given error type, adapted to the active provider.
    """
    templates = get_provider_templates(provider_info)
    info = templates.get(error_type, templates["general_error"]).copy()
    info["error_type"] = error_type
    if custom_raw:
        info["raw_error"] = custom_raw
    return info
