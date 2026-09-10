"""
Error message definitions and error handling utilities for LLM operations.
Provides standardized, user-facing bilingual (Bengali and English) error messages
for 401 Unauthorized, disconnection/network, token/quota issues, and provider-specific errors
(Google Gemini, Local LLMs like Ollama / LM Studio, OpenAI, OpenRouter, etc.).
"""

from typing import Dict, Any, Optional, List


def get_provider_templates(provider_info: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Generates tailored error message templates based on the active provider.
    Supports Google Gemini, Ollama, LM Studio / Local LLMs, OpenAI, OpenRouter, and Custom endpoints.
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
    if provider == "ollama":
        url_display = base_url or "http://localhost:11434"
        return {
            "authentication_error": {
                "status_code": 401,
                "title": "লোকাল এলএলএম এক্সেস ত্রুটি (Ollama Access Error)",
                "message_bn": f"লোকাল Ollama সার্ভার অনুরোধটি প্রত্যাখ্যান করেছে ({url_display})।",
                "message_en": f"Local Ollama server rejected the request at {url_display}.",
                "troubleshooting_bn": [
                    f"আপনার কম্পিউটারে Ollama চালু আছে কি না পরীক্ষা করুন ({url_display})।",
                    f"টার্মিনালে 'ollama list' দিয়ে মডেলটি ইনস্টল আছে কি না দেখুন।"
                ]
            },
            "connection_error": {
                "status_code": 503,
                "title": "লোকাল এলএলএম সংযোগ বিচ্ছিন্ন (Ollama Not Connected)",
                "message_bn": f"লোকাল Ollama সার্ভারের সাথে সংযোগ স্থাপন করা যাচ্ছে না ({url_display})।",
                "message_en": f"Could not connect to local Ollama server at {url_display}. Please check if Ollama is running.",
                "troubleshooting_bn": [
                    "টার্মিনালে 'ollama serve' অথবা 'ollama run <model>' চালান।",
                    f"Ollama পোর্ট সচল আছে কি না পরীক্ষা করুন ({url_display})।",
                    "ইন্টারনেট সংযোগের প্রয়োজন নেই, শুধু লোকাল সার্ভিসটি সচল রাখুন।"
                ]
            },
            "not_found_error": {
                "status_code": 404,
                "title": "লোকাল মডেল পাওয়া যায়নি (Model Not Found)",
                "message_bn": f"মডেল '{model_name}' লোকাল Ollama-তে পাওয়া যায়নি।",
                "message_en": f"Model '{model_name}' was not found in Ollama.",
                "troubleshooting_bn": [
                    f"টার্মিনালে কমান্ডটি চালান: ollama pull {model_name}",
                    "ইনস্টল করা মডেলের তালিকা দেখতে চালান: ollama list"
                ]
            },
            "rate_limit_error": {
                "status_code": 429,
                "title": "লোকাল সিস্টেম মেমরি বা কিউ সীমাবদ্ধতা",
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
                "message_bn": f"লোকাল Ollama সার্ভার URL ({url_display}) কনফিগারেশনে সমস্যা রয়েছে।",
                "message_en": "Local server URL is misconfigured in backend/.env.",
                "troubleshooting_bn": [f"backend/.env ফাইলে LLM_BASE_URL={url_display} নিশ্চিত করুন।"]
            },
            "general_error": {
                "status_code": 500,
                "title": "লোকাল এলএলএম ত্রুটি (Local Processing Error)",
                "message_bn": "লোকাল মডেল থেকে প্রতিক্রিয়া প্রক্রিয়া করার সময় একটি অপ্রত্যাশিত ত্রুটি ঘটেছে।",
                "message_en": "An error occurred while communicating with the local LLM.",
                "troubleshooting_bn": ["Ollama টার্মিনাল লগ পরীক্ষা করুন।"]
            }
        }

    # 2. LM Studio / General Local LLM Templates
    if provider == "local":
        url_display = base_url or "http://localhost:1234/v1"
        return {
            "authentication_error": {
                "status_code": 401,
                "title": "লোকাল সার্ভার এক্সেস ত্রুটি (Local LLM Error)",
                "message_bn": f"লোকাল এলএলএম সার্ভার অনুরোধটি প্রত্যাখ্যান করেছে ({url_display})।",
                "message_en": f"Local LLM server rejected the request at {url_display}.",
                "troubleshooting_bn": [
                    f"LM Studio বা লোকাল সার্ভার চালু আছে কি না পরীক্ষা করুন ({url_display})।"
                ]
            },
            "connection_error": {
                "status_code": 503,
                "title": "লোকাল সার্ভার সংযোগ বিচ্ছিন্ন (Local Server Not Connected)",
                "message_bn": f"লোকাল এলএলএম সার্ভারের সাথে সংযোগ স্থাপন করা যাচ্ছে না ({url_display})।",
                "message_en": f"Could not connect to local LLM server at {url_display}. Ensure local server is running.",
                "troubleshooting_bn": [
                    "LM Studio বা লোকাল সার্ভারে 'Start Server' চালু আছে কি না নিশ্চিত করুন।",
                    f"সার্ভার পোর্ট ও URL ({url_display}) সঠিক কি না দেখুন।"
                ]
            },
            "not_found_error": {
                "status_code": 404,
                "title": "লোকাল মডেল লোড করা হয়নি",
                "message_bn": f"লোকাল সার্ভারে মডেল '{model_name}' লোড করা নেই।",
                "message_en": f"Model '{model_name}' is not loaded on the local server.",
                "troubleshooting_bn": ["LM Studio-তে মডেলটি লোড করে পুনরায় চেষ্টা করুন।"]
            },
            "rate_limit_error": {
                "status_code": 429,
                "title": "লোকাল সার্ভার ব্যস্ত",
                "message_bn": "লোকাল সার্ভার বর্তমানে অন্য রিকোয়েস্ট প্রক্রিয়া করছে। কিছুক্ষণ অপেক্ষা করুন।",
                "message_en": "Local server is currently busy.",
                "troubleshooting_bn": ["কিছুক্ষণ পর পুনরায় চেষ্টা করুন।"]
            },
            "token_credit_error": {
                "status_code": 402,
                "title": "রিসোর্স সীমাবদ্ধতা",
                "message_bn": "লোকাল সিস্টেমে রিসোর্স অপর্যাপ্ত।",
                "message_en": "Insufficient local resources.",
                "troubleshooting_bn": ["সিস্টেম মেমরি পরীক্ষা করুন।"]
            },
            "context_limit_error": {
                "status_code": 400,
                "title": "টোকেন কনটেক্সট সীমা অতিক্রম",
                "message_bn": "ইনপুট বিবরণটি লোকাল মডেলের কনটেক্সট উইন্ডো ছাড়িয়ে গেছে।",
                "message_en": "Input exceeds local model context window.",
                "troubleshooting_bn": ["বিবরণটি সংক্ষেপ করুন।"]
            },
            "missing_api_key": {
                "status_code": 500,
                "title": "লোকাল সার্ভার সংযোগ ত্রুটি",
                "message_bn": "লোকাল সার্ভার প্রস্তুত নয়।",
                "message_en": "Local server is not ready.",
                "troubleshooting_bn": ["LM Studio বা লোকাল সার্ভার চালু করুন।"]
            },
            "general_error": {
                "status_code": 500,
                "title": "লোকাল এলএলএম ত্রুটি",
                "message_bn": "লোকাল মডেল থেকে প্রতিক্রিয়া পেতে সমস্যা হয়েছে।",
                "message_en": "Error communicating with local server.",
                "troubleshooting_bn": ["লোকাল সার্ভার কনসোল লগ পরীক্ষা করুন।"]
            }
        }

    # 3. Google Gemini (Direct API)
    if provider == "google":
        return {
            "authentication_error": {
                "status_code": 401,
                "title": "Google Gemini এপিআই কী ত্রুটি (API Key Error)",
                "message_bn": f"Google Gemini API Key সঠিক নয় বা মেয়াদ শেষ হয়ে গেছে। backend/.env ফাইলে {key_env} যাচাই করুন।",
                "message_en": f"Google Gemini API Key is invalid, missing, or expired. Please check {key_env} in backend/.env.",
                "troubleshooting_bn": [
                    f"backend/.env ফাইলে {key_env} সঠিক কি না তা পরীক্ষা করুন।",
                    "Google AI Studio (https://aistudio.google.com) থেকে নতুন API Key সংগ্রহ করে ব্যাকএন্ড রিস্টার্ট করুন।"
                ]
            },
            "connection_error": {
                "status_code": 503,
                "title": "Google Gemini সংযোগ বিচ্ছিন্ন (Not Connected)",
                "message_bn": "Google Gemini এপিআই সার্ভারের সাথে সংযোগ স্থাপন করা যাচ্ছে না। আপনার ইন্টারনেট সংযোগ পরীক্ষা করুন।",
                "message_en": "Could not connect to Google Gemini API server. Please verify internet connection.",
                "troubleshooting_bn": [
                    "আপনার ইন্টারনেট সংযোগ সচল আছে কি না পরীক্ষা করুন।",
                    "Google AI Studio স্ট্যাটাস চালু আছে কি না দেখুন।"
                ]
            },
            "not_found_error": {
                "status_code": 404,
                "title": "Google Gemini মডেল পাওয়া যায়নি",
                "message_bn": f"মডেল '{model_name}' Google Gemini এপিআই-তে পাওয়া যায়নি।",
                "message_en": f"Model '{model_name}' was not found in Google Gemini API.",
                "troubleshooting_bn": ["backend/.env ফাইলে MODEL_NAME=gemini-1.5-flash বা gemini-2.0-flash দিয়ে চেষ্টা করুন।"]
            },
            "rate_limit_error": {
                "status_code": 429,
                "title": "Google Gemini কোটা বা রেট লিমিট অতিক্রম (Quota Exceeded)",
                "message_bn": "Google Gemini এপিআই-এর প্রতি মিনিটের রিকোয়েস্ট সীমা বা দৈনিক কোটা শেষ হয়েছে। অনুগ্রহ করে ১ মিনিট পর চেষ্টা করুন।",
                "message_en": "Google Gemini API rate limit or quota exceeded (429/RESOURCE_EXHAUSTED). Please wait a moment.",
                "troubleshooting_bn": [
                    "Google Gemini Free Tier লিমিট শেষ হতে পারে — ১-২ মিনিট পর পুনরায় চেষ্টা করুন।",
                    "অথবা Google Cloud কনসোলে বিলিং যুক্ত করুন।"
                ]
            },
            "token_credit_error": {
                "status_code": 402,
                "title": "Google Cloud বিলিং কোটা ত্রুটি",
                "message_bn": "Google Cloud / Gemini অ্যাকাউন্টে পর্যাপ্ত কোটা বা ক্রেডিট নেই।",
                "message_en": "Google Cloud / Gemini project quota or credit exhausted.",
                "troubleshooting_bn": ["Google Cloud কনসোলে কোটা ও বিলিং স্থিতি পরীক্ষা করুন।"]
            },
            "context_limit_error": {
                "status_code": 400,
                "title": "টোকেন ধারণক্ষমতা অতিক্রম",
                "message_bn": "ইনপুট বিবরণটি Gemini মডেলের অনুমোদিত কনটেক্সট সীমা ছাড়িয়ে গেছে। সংক্ষেপ করে লিখুন।",
                "message_en": "Input text exceeds Gemini model context window limit.",
                "troubleshooting_bn": ["বিবরণটি সংক্ষেপ করে পুনরায় সাবমিট করুন।"]
            },
            "missing_api_key": {
                "status_code": 401,
                "title": "Google Gemini এপিআই কী অনুপস্থিত (Missing API Key)",
                "message_bn": f"Google Gemini API কী কনফিগার করা হয়নি। backend/.env ফাইলে {key_env} প্রদান করুন।",
                "message_en": f"{key_env} is not configured in backend/.env.",
                "troubleshooting_bn": [
                    f"backend/.env ফাইলে {key_env}=AIzaSy... যোগ করুন।",
                    "https://aistudio.google.com থেকে বিনামূল্যে API কী পেতে পারেন।"
                ]
            },
            "general_error": {
                "status_code": 500,
                "title": "Google Gemini প্রসেসিং ত্রুটি",
                "message_bn": "Google Gemini মডেল থেকে প্রতিক্রিয়া পেতে সমস্যা হয়েছে।",
                "message_en": "An error occurred while communicating with Google Gemini.",
                "troubleshooting_bn": ["কিছুক্ষণ পর পুনরায় চেষ্টা করুন।"]
            }
        }

    # 4. OpenAI (Direct API)
    if provider == "openai":
        return {
            "authentication_error": {
                "status_code": 401,
                "title": "OpenAI এপিআই কী ত্রুটি (Error 401 Unauthorized)",
                "message_bn": f"OpenAI API Key সঠিক নয় বা মেয়াদ শেষ। backend/.env ফাইলে {key_env} যাচাই করুন।",
                "message_en": f"OpenAI API Key is invalid or expired. Check {key_env} in backend/.env.",
                "troubleshooting_bn": [
                    f"backend/.env ফাইলে {key_env} সঠিক আছে কি না তা যাচাই করুন।",
                    "platform.openai.com থেকে নতুন API Key সংগ্রহ করে ব্যাকএন্ড রিস্টার্ট করুন।"
                ]
            },
            "connection_error": {
                "status_code": 503,
                "title": "OpenAI সার্ভার সংযোগ বিচ্ছিন্ন",
                "message_bn": "OpenAI এপিআই সার্ভারের সাথে সংযোগ স্থাপন করা যাচ্ছে না। আপনার ইন্টারনেট সংযোগ পরীক্ষা করুন।",
                "message_en": "Could not connect to OpenAI API server.",
                "troubleshooting_bn": ["ইন্টারনেট সংযোগ এবং OpenAI সার্ভিস স্থিতি পরীক্ষা করুন।"]
            },
            "not_found_error": {
                "status_code": 404,
                "title": "OpenAI মডেল পাওয়া যায়নি",
                "message_bn": f"মডেল '{model_name}' OpenAI-তে পাওয়া যায়নি।",
                "message_en": f"Model '{model_name}' was not found in OpenAI.",
                "troubleshooting_bn": ["backend/.env ফাইলে MODEL_NAME=gpt-4o-mini ব্যবহার করুন।"]
            },
            "rate_limit_error": {
                "status_code": 429,
                "title": "OpenAI রেট লিমিট অতিক্রম (Error 429)",
                "message_bn": "OpenAI এপিআই রেট লিমিট অতিক্রম করেছে। অনুগ্রহ করে কিছুক্ষণ অপেক্ষা করুন।",
                "message_en": "OpenAI rate limit exceeded. Please retry shortly.",
                "troubleshooting_bn": ["১-২ মিনিট অপেক্ষা করে পুনরায় চেষ্টা করুন।"]
            },
            "token_credit_error": {
                "status_code": 402,
                "title": "OpenAI ক্রেডিট ব্যালেন্স শেষ (Insufficient Quota)",
                "message_bn": "আপনার OpenAI অ্যাকাউন্টে পর্যাপ্ত ক্রেডিট ব্যালেন্স নেই। platform.openai.com থেকে ক্রেডিট রিচার্জ করুন।",
                "message_en": "Insufficient quota or credit on OpenAI account.",
                "troubleshooting_bn": ["platform.openai.com/account/billing থেকে ক্রেডিট যোগ করুন।"]
            },
            "context_limit_error": {
                "status_code": 400,
                "title": "টোকেন ধারণক্ষমতা অতিক্রম",
                "message_bn": "ইনপুট বিবরণটি মডেলের টোকেন সীমা ছাড়িয়ে গেছে।",
                "message_en": "Input exceeds OpenAI model context limit.",
                "troubleshooting_bn": ["বিবরণটি সংক্ষেপ করে পুনরায় সাবমিট করুন।"]
            },
            "missing_api_key": {
                "status_code": 401,
                "title": "OpenAI এপিআই কী অনুপস্থিত",
                "message_bn": f"OpenAI API Key কনফিগার করা হয়নি। backend/.env ফাইলে {key_env} প্রদান করুন।",
                "message_en": f"{key_env} is missing in backend/.env.",
                "troubleshooting_bn": [f"backend/.env ফাইলে {key_env}=sk-... সেট করুন।"]
            },
            "general_error": {
                "status_code": 500,
                "title": "OpenAI প্রসেসিং ত্রুটি",
                "message_bn": "OpenAI মডেল থেকে প্রতিক্রিয়া পেতে সমস্যা হয়েছে।",
                "message_en": "An error occurred with OpenAI processing.",
                "troubleshooting_bn": ["কিছুক্ষণ পর পুনরায় চেষ্টা করুন।"]
            }
        }

    # 5. OpenRouter (Multi-Model Gateway)
    if provider == "openrouter":
        return {
            "authentication_error": {
                "status_code": 401,
                "title": "OpenRouter এপিআই কী ত্রুটি (Error 401 Unauthorized)",
                "message_bn": f"OpenRouter API Key বা টোকেন সঠিক নয় অথবা মেয়াদ শেষ। backend/.env ফাইলে {key_env} যাচাই করুন।",
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

    # 6. Generic / Custom OpenAI-compatible Endpoint Fallback
    return {
        "authentication_error": {
            "status_code": 401,
            "title": f"{display_name} অথেন্টিকেশন ত্রুটি (Error 401 Unauthorized)",
            "message_bn": f"এআই মডেলের API Key বা টোকেন সঠিক নয় অথবা মেয়াদ শেষ। backend/.env ফাইলে {key_env} যাচাই করুন।",
            "message_en": f"{display_name} Authentication Error (401 Unauthorized): Invalid or expired API token. Check {key_env}.",
            "troubleshooting_bn": [
                f"backend/.env ফাইলে {key_env} সঠিক আছে কি না তা যাচাই করুন।",
                "API Key পরিবর্তন করলে ব্যাকএন্ড সার্ভার রিস্টার্ট করুন।"
            ]
        },
        "connection_error": {
            "status_code": 503,
            "title": f"{display_name} সংযোগ বিচ্ছিন্ন (Not Connected)",
            "message_bn": f"{display_name} সার্ভারের সাথে সংযোগ স্থাপন করা যাচ্ছে না। ইন্টারনেট সংযোগ ও সার্ভারের স্থিতি পরীক্ষা করুন।",
            "message_en": f"Could not connect to {display_name} server. Please verify connection.",
            "troubleshooting_bn": [
                "সার্ভার ও ইন্টারনেট সংযোগ সচল আছে কি না পরীক্ষা করুন।",
                f"সার্ভার URL সঠিক কি না দেখুন: {base_url or 'default'}"
            ]
        },
        "not_found_error": {
            "status_code": 404,
            "title": f"{display_name} মডেল পাওয়া যায়নি",
            "message_bn": f"মডেল '{model_name}' পাওয়া যায়নি।",
            "message_en": f"Model '{model_name}' was not found.",
            "troubleshooting_bn": ["মডেলের নাম সঠিক কি না পরীক্ষা করুন।"]
        },
        "rate_limit_error": {
            "status_code": 429,
            "title": f"{display_name} রেট লিমিট অতিক্রম (Error 429)",
            "message_bn": "টোকেন কোটা শেষ অথবা মডেলটির সাময়িক রেট লিমিট অতিক্রম করেছে। অনুগ্রহ করে কিছুক্ষণ পর চেষ্টা করুন।",
            "message_en": f"{display_name} Rate Limit / Quota Exceeded (429). Please retry shortly.",
            "troubleshooting_bn": ["১-২ মিনিট অপেক্ষা করে পুনরায় চেষ্টা করুন।"]
        },
        "token_credit_error": {
            "status_code": 402,
            "title": f"{display_name} ব্যালেন্স ত্রুটি (Error 402 Payment Required)",
            "message_bn": f"আপনার {display_name} অ্যাকাউন্টে পর্যাপ্ত ব্যালেন্স বা ক্রেডিট নেই।",
            "message_en": f"Insufficient credit or balance on {display_name} account.",
            "troubleshooting_bn": ["অ্যাকাউন্টে ব্যালেন্স বা ক্রেডিট যোগ করুন।"]
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
            "title": f"{display_name} প্রসেসিং ত্রুটি",
            "message_bn": f"{display_name} মডেল থেকে প্রতিক্রিয়া পেতে সমস্যা হয়েছে।",
            "message_en": f"An unexpected error occurred while communicating with {display_name}.",
            "troubleshooting_bn": ["কিছুক্ষণ পর পুনরায় চেষ্টা করুন।"]
        }
    }


# Static fallback dictionary for backward compatibility
ERROR_MESSAGES = get_provider_templates()


def parse_llm_error(exc: Exception, provider_info: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Parses LLM exceptions and classifies them into standardized errors
    (401 Unauthorized, disconnection/network, 404 Model Not Found, 429 Rate Limit,
    402 Payment Required, and 400 Context Limit) with dynamic provider awareness.
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

    # 1. Check for 404 Model Not Found (common in Ollama when model isn't pulled, or deprecated cloud model)
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

        # If upstream provider recommended an alternative model, extract and display it
        if "please update your code to use" in err_lower:
            import re
            m = re.search(r"use\s+(models/)?([a-zA-Z0-9\.\-_]+)", err_str)
            if m:
                suggested_model = m.group(2)
                troubleshooting.insert(0, f"প্রস্তাবিত মডেল: backend/.env ফাইলে MODEL_NAME={suggested_model} সেট করুন।")

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

        # If upstream specifies a retry cooldown (e.g. Google's "Please retry in 11.32s")
        import re
        m = re.search(r"retry in ([0-9]+(?:\.[0-9]+)?)s?", err_str, re.IGNORECASE)
        if not m:
            m = re.search(r"retryDelay':\s*'([0-9]+)s?'", err_str)
        if m:
            try:
                sec = int(float(m.group(1)))
                message_bn += f" (অনুগ্রহ করে {sec} সেকেন্ড অপেক্ষা করুন)"
                troubleshooting.insert(0, f"গুগল এপিআই কুলডাউন: ঠিক {sec} সেকেন্ড অপেক্ষা করে আবার চেষ্টা করুন।")
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
