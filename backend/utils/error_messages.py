"""
Error message definitions and error handling utilities for LLM operations.
Provides standardized, user-facing bilingual (Bengali and English) error messages
for 401 Unauthorized, disconnection/network, and token/quota issues.
"""

from typing import Dict, Any, Optional

# Standard user-facing error message dictionaries
ERROR_MESSAGES = {
    "authentication_error": {
        "status_code": 401,
        "title": "LLM অথেন্টিকেশন ত্রুটি (Error 401 Unauthorized)",
        "message_bn": "এআই মডেলের API Key বা টোকেন সঠিক নয় অথবা মেয়াদ শেষ হয়ে গেছে। backend/.env ফাইলে OPENROUTER_API_KEY যাচাই করুন।",
        "message_en": "LLM Authentication Error (401 Unauthorized): Invalid, missing, or expired API token. Please verify OPENROUTER_API_KEY.",
        "troubleshooting_bn": [
            "প্রকল্পের backend/.env ফাইলে OPENROUTER_API_KEY সঠিক আছে কি না তা যাচাই করুন।",
            "API Key পরিবর্তন করলে ব্যাকএন্ড সার্ভার রিস্টার্ট করুন।"
        ]
    },
    "connection_error": {
        "status_code": 503,
        "title": "LLM সার্ভার সংযোগ বিচ্ছিন্ন (Not Connected)",
        "message_bn": "এআই মডেল সার্ভারের (LLM) সাথে সংযোগ স্থাপন করা যাচ্ছে না। আপনার ইন্টারনেট সংযোগ এবং মডেল সার্ভারের স্থিতি পরীক্ষা করুন।",
        "message_en": "LLM Connection Error: Could not connect to AI server. Please check internet connection and provider status.",
        "troubleshooting_bn": [
            "আপনার কম্পিউটার ও ব্যাকএন্ড সার্ভার (Port 8000) সচল আছে কি না পরীক্ষা করুন।",
            "ইন্টারনেট সংযোগ চালু আছে কি না দেখুন।"
        ]
    },
    "rate_limit_error": {
        "status_code": 429,
        "title": "টোকেন কোটা বা রেট লিমিট অতিক্রম (Error 429 Rate Limit)",
        "message_bn": "টোকেন কোটা শেষ অথবা মডেলটির সাময়িক রেট লিমিট অতিক্রম করেছে। অনুগ্রহ করে কিছুক্ষণ পর পুনরায় চেষ্টা করুন।",
        "message_en": "LLM Rate Limit / Token Quota Exceeded (429): Token limit reached or upstream rate-limited. Please retry shortly.",
        "troubleshooting_bn": [
            "মডেলের বর্তমান রিকোয়েস্ট লিমিট শেষ হয়েছে — ১-২ মিনিট অপেক্ষা করে পুনরায় চেষ্টা করুন।",
            "অথবা backend/.env ফাইলে অপর একটি সক্রিয় মডেল বা নিজস্ব API Key ব্যবহার করুন।"
        ]
    },
    "token_credit_error": {
        "status_code": 402,
        "title": "টোকেন ব্যালেন্স ত্রুটি (Error 402 Payment Required)",
        "message_bn": "আপনার একাউন্টে পর্যাপ্ত টোকেন ব্যালেন্স বা ক্রেডিট নেই। অনুগ্রহ করে টোকেন রিচার্জ বা ক্রেডিট যুক্ত করুন।",
        "message_en": "LLM Token Balance Error (402 Payment Required): Insufficient credit or token balance.",
        "troubleshooting_bn": [
            "আপনার OpenRouter একাউন্টে টোকেন ব্যালেন্স বা ক্রেডিট যোগ করুন।"
        ]
    },
    "context_limit_error": {
        "status_code": 400,
        "title": "টোকেন ধারণক্ষমতা অতিক্রম (Token Context Limit)",
        "message_bn": "ইনপুট বিবরণটি মডেলের অনুমোদিত টোকেন সীমা ছাড়িয়ে গেছে। অনুগ্রহ করে সংক্ষেপ করে লিখুন।",
        "message_en": "LLM Token Limit Exceeded: Input text exceeds the model maximum token context window.",
        "troubleshooting_bn": [
            "বিবরণটি সংক্ষেপ করে পুনরায় সাবমিট করুন।"
        ]
    },
    "missing_api_key": {
        "status_code": 401,
        "title": "LLM এপিআই কী অনুপস্থিত (API Key Missing)",
        "message_bn": "এআই মডেলের API কী (API Key) কনফিগার করা হয়নি। backend/.env ফাইলে OPENROUTER_API_KEY প্রদান করুন।",
        "message_en": "OPENROUTER_API_KEY is missing or unconfigured in backend/.env.",
        "troubleshooting_bn": [
            "backend/.env ফাইলে OPENROUTER_API_KEY সেট করুন।"
        ]
    },
    "general_error": {
        "status_code": 500,
        "title": "এলএলএম প্রসেসিং ত্রুটি (LLM Processing Error)",
        "message_bn": "এআই মডেল থেকে প্রতিক্রিয়া পেতে সমস্যা হয়েছে।",
        "message_en": "LLM Processing Error: An unexpected error occurred while communicating with the AI model.",
        "troubleshooting_bn": [
            "কিছুক্ষণ পর পুনরায় চেষ্টা করুন।"
        ]
    }
}


def parse_llm_error(exc: Exception) -> Dict[str, Any]:
    """
    Parses LLM exceptions and identifies 401 Unauthorized, disconnection/network,
    or token/quota issues with user-friendly Bengali and English explanations.
    """
    err_str = str(exc)
    err_lower = err_str.lower()
    exc_name = type(exc).__name__
    status_code = getattr(exc, "status_code", None)
    if not status_code and hasattr(exc, "response") and hasattr(exc.response, "status_code"):
        status_code = exc.response.status_code

    # 1. Check for HTTP 401 Unauthorized / Invalid Token / Authentication Error
    if (
        status_code == 401
        or "401" in err_str
        or "authentication" in err_lower
        or "unauthorized" in err_lower
        or "invalid api key" in err_lower
        or "missing authentication" in err_lower
        or "incorrect api key" in err_lower
        or "user not found" in err_lower
        or "AuthenticationError" in exc_name
    ):
        template = ERROR_MESSAGES["authentication_error"]
        return {
            "error_type": "authentication_error",
            "status_code": 401,
            "title": template["title"],
            "message_bn": template["message_bn"],
            "message_en": template["message_en"],
            "troubleshooting_bn": template["troubleshooting_bn"],
            "raw_error": err_str[:300]
        }

    # 2. Check for Connection / Network / Timeout / Not Connected
    if (
        "connection" in err_lower
        or "connecterror" in err_lower
        or "timeout" in err_lower
        or "name or service not known" in err_lower
        or "getaddrinfo failed" in err_lower
        or "failed to establish a new connection" in err_lower
        or "ConnectionError" in exc_name
        or "APITimeoutError" in exc_name
    ):
        template = ERROR_MESSAGES["connection_error"]
        return {
            "error_type": "connection_error",
            "status_code": 503,
            "title": template["title"],
            "message_bn": template["message_bn"],
            "message_en": template["message_en"],
            "troubleshooting_bn": template["troubleshooting_bn"],
            "raw_error": err_str[:300]
        }

    # 3. Check for 402 Payment Required / Insufficient Token Balance
    if (
        status_code == 402
        or "402" in err_str
        or "payment required" in err_lower
        or "insufficient credits" in err_lower
        or "insufficient balance" in err_lower
    ):
        template = ERROR_MESSAGES["token_credit_error"]
        return {
            "error_type": "token_credit_error",
            "status_code": 402,
            "title": template["title"],
            "message_bn": template["message_bn"],
            "message_en": template["message_en"],
            "troubleshooting_bn": template["troubleshooting_bn"],
            "raw_error": err_str[:300]
        }

    # 4. Check for 429 Rate Limit / Token Quota Exceeded
    if (
        status_code == 429
        or "429" in err_str
        or "rate limit" in err_lower
        or "rate_limit" in err_lower
        or "quota" in err_lower
        or "too many requests" in err_lower
        or "RateLimitError" in exc_name
    ):
        template = ERROR_MESSAGES["rate_limit_error"]
        return {
            "error_type": "rate_limit_error",
            "status_code": 429,
            "title": template["title"],
            "message_bn": template["message_bn"],
            "message_en": template["message_en"],
            "troubleshooting_bn": template["troubleshooting_bn"],
            "raw_error": err_str[:300]
        }

    # 5. Check for Context Length / Token Budget Exceeded (Error 400)
    if (
        "context_length" in err_lower
        or "maximum context length" in err_lower
        or "token limit" in err_lower
        or "too many tokens" in err_lower
    ):
        template = ERROR_MESSAGES["context_limit_error"]
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
    template = ERROR_MESSAGES["general_error"]
    return {
        "error_type": "llm_general_error",
        "status_code": getattr(exc, "status_code", 500) or 500,
        "title": template["title"],
        "message_bn": f"{template['message_bn']} ত্রুটির বিবরণ: {err_str[:150]}",
        "message_en": f"{template['message_en']} Raw: {err_str[:150]}",
        "troubleshooting_bn": template["troubleshooting_bn"],
        "raw_error": err_str[:300]
    }


def get_error_message(error_type: str, custom_raw: Optional[str] = None) -> Dict[str, Any]:
    """
    Returns predefined error details for a given error type.
    """
    info = ERROR_MESSAGES.get(error_type, ERROR_MESSAGES["general_error"]).copy()
    info["error_type"] = error_type
    if custom_raw:
        info["raw_error"] = custom_raw
    return info
