import os
import sys
from typing import TypedDict, Optional, List, Dict, Any
from pydantic import BaseModel, Field

from dotenv import load_dotenv
load_dotenv()

from langgraph.graph import StateGraph, END
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.tools import tool

import prompts
import templates

from utils import (
    llm,
    OPENROUTER_API_KEY,
    MODEL_NAME,
    TOKEN_BUDGET_LIMIT,
    check_llm_status,
    parse_llm_error,
    is_model_configured,
    get_error_message,
)

# Directory of BRAC Legal Aid Clinics and Helplines across Bangladesh
LEGAL_AID_CLINIC_DIRECTORY = [
    {
        "keywords": ["ঢাকা", "dhaka", "মিরপুর", "mirpur", "উত্তরা", "uttara", "ধানমন্ডি", "dhanmondi", "মোহাম্মদপুর", "mohammadpur"],
        "clinic_name": "ব্র্যাক মানবাধিকার ও আইনি সহায়তা কেন্দ্র, মিরপুর শাখা",
        "address": "প্লট-২, ব্লক-বি, মিরপুর-১০, ঢাকা",
        "contact_number": "০১৭১৩-০৪৫৬৭৮",
        "referral_slot": "মঙ্গলবার, সকাল ১০:০০ টা",
        "helpline": "১৬৪৩০"
    },
    {
        "keywords": ["সাভার", "savar", "আশুলিয়া", "ashulia", "ধামরাই", "dhamrai"],
        "clinic_name": "ব্র্যাক লিগ্যাল এইড ক্লিনিক, সাভার শাখা",
        "address": "সিটি সেন্টার সংলগ্ন, ঢাকা-আরিচা রোড, সাভার",
        "contact_number": "০১৭৩০-১২৩৪৫৬",
        "referral_slot": "বুধবার, সকাল ১১:০০ টা",
        "helpline": "১৬৪৩০"
    },
    {
        "keywords": ["গাজীপুর", "gazipur", "জয়দেবপুর", "joydebpur", "টঙ্গী", "tongi"],
        "clinic_name": "ব্র্যাক লিগ্যাল এইড ক্লিনিক, জয়দেবপুর শাখা",
        "address": "শিববাড়ি মোড়, ঢাকা রোড, গাজীপুর সদর",
        "contact_number": "০১৭৩০-৭৮৯১০১",
        "referral_slot": "সোমবার, সকাল ১০:৩০ টা",
        "helpline": "১৬৪৩০"
    },
    {
        "keywords": ["নারায়ণগঞ্জ", "narayanganj", "চাষাড়া", "chasara", "সিদ্ধিরগঞ্জ", "siddhirganj"],
        "clinic_name": "ব্র্যাক লিগ্যাল এইড ক্লিনিক, নারায়ণগঞ্জ শাখা",
        "address": "চাষাড়া গোলচত্বর সংলগ্ন, বঙ্গবন্ধু সড়ক, নারায়ণগঞ্জ",
        "contact_number": "০১৭৩০-৫৫৮৮৯৯",
        "referral_slot": "বুধবার, সকাল ১০:০০ টা",
        "helpline": "১৬৪৩০"
    },
    {
        "keywords": ["রংপুর", "rangpur", "কুড়িগ্রাম", "kurigram", "গাইবান্ধা", "gaibandha", "লালমনিরহাট", "lalmonirhat", "নীলফামারী", "nilphamari"],
        "clinic_name": "ব্র্যাক লিগ্যাল এইড ক্লিনিক, রংপুর শাখা",
        "address": "মডার্ন মোড়, আরকে রোড, রংপুর সদর",
        "contact_number": "০১৭৩০-৩৩৪৫৫৬",
        "referral_slot": "বৃহস্পতিবার, সকাল ১০:০০ টা",
        "helpline": "১৬৪৩০"
    },
    {
        "keywords": ["দিনাজপুর", "dinajpur", "ঠাকুরগাঁও", "thakurgaon", "পঞ্চগড়", "panchagarh"],
        "clinic_name": "ব্র্যাক লিগ্যাল এইড ক্লিনিক, দিনাজপুর শাখা",
        "address": "মহালে রোড, বালুয়াডাঙ্গা, দিনাজপুর সদর",
        "contact_number": "০১৭৩০-৬৬৭৭৯৯",
        "referral_slot": "মঙ্গলবার, সকাল ১১:০০ টা",
        "helpline": "১৬৪৩০"
    },
    {
        "keywords": ["বগুড়া", "bogura", "bogra", "শেরপুর", "sherpur", "শিবগঞ্জ", "shibganj"],
        "clinic_name": "ব্র্যাক লিগ্যাল এইড ক্লিনিক, বগুড়া শাখা",
        "address": "সাতমাথা, শেরপুর রোড, বগুড়া সদর",
        "contact_number": "০১৭৩০-৮৮৯৯০০",
        "referral_slot": "বুধবার, সকাল ১০:০০ টা",
        "helpline": "১৬৪৩০"
    },
    {
        "keywords": ["সিলেট", "sylhet", "সুনামগঞ্জ", "sunamganj", "মৌলভীবাজার", "moulvibazar", "হবিগঞ্জ", "habiganj"],
        "clinic_name": "ব্র্যাক লিগ্যাল এইড ক্লিনিক, সিলেট সদর শাখা",
        "address": "আম্বরখানা পয়েন্ট, বিমানবন্দর রোড, সিলেট",
        "contact_number": "০১৭৩০-৫৬৭৮৯০",
        "referral_slot": "রবিবার, সকাল ১০:০০ টা",
        "helpline": "১৬৪৩০"
    },
    {
        "keywords": ["চট্টগ্রাম", "chattogram", "chittagong", "কক্সবাজার", "cox's bazar", "ফেনী", "feni"],
        "clinic_name": "ব্র্যাক লিগ্যাল এইড ক্লিনিক, চট্টগ্রাম সদর শাখা",
        "address": "জিইসি মোড়, সিডিএ এভিনিউ, নাসিরাবাদ, চট্টগ্রাম",
        "contact_number": "০১৭৩০-১১২২৩৩",
        "referral_slot": "রবিবার, সকাল ১০:৩০ টা",
        "helpline": "১৬৪৩০"
    },
    {
        "keywords": ["কুমিল্লা", "cumilla", "comilla", "ব্রাহ্মণবাড়িয়া", "brahmanbaria", "চাঁদপুর", "chandpur"],
        "clinic_name": "ব্র্যাক লিগ্যাল এইড ক্লিনিক, কুমিল্লা শাখা",
        "address": "কান্দিরপাড়, নজরুল এভিনিউ, কুমিল্লা সদর",
        "contact_number": "০১৭৩০-৭৭৮৮৯৯",
        "referral_slot": "বুধবার, সকাল ১০:০০ টা",
        "helpline": "১৬৪৩০"
    },
    {
        "keywords": ["রাজশাহী", "rajshahi", "নাটোর", "natore", "নওগাঁ", "naogaon", "পাবনা", "pabna"],
        "clinic_name": "ব্র্যাক লিগ্যাল এইড ক্লিনিক, রাজশাহী সদর শাখা",
        "address": "আলুপট্টি মোড়, বোয়ালিয়া, রাজশাহী",
        "contact_number": "০১৭৩০-৬৬৭৭৮৮",
        "referral_slot": "সোমবার, সকাল ১১:০০ টা",
        "helpline": "১৬৪৩০"
    },
    {
        "keywords": ["খুলনা", "khulna", "যশোর", "jashore", "jessore", "সাতক্ষীরা", "satkhira", "বাগেরহাট", "bagerhat"],
        "clinic_name": "ব্র্যাক লিগ্যাল এইড ক্লিনিক, খুলনা সদর শাখা",
        "address": "ডাকবাংলো মোড়, কেডিএ এভিনিউ, খুলনা",
        "contact_number": "০১৭৩০-৯৯০০১১",
        "referral_slot": "মঙ্গলবার, সকাল ১০:৩০ টা",
        "helpline": "১৬৪৩০"
    },
    {
        "keywords": ["বরিশাল", "barishal", "barisal", "পটুয়াখালী", "patuakhali", "ভোলা", "bhola", "পিরোজপুর", "pirojpur"],
        "clinic_name": "ব্র্যাক লিগ্যাল এইড ক্লিনিক, বরিশাল সদর শাখা",
        "address": "সদর রোড, কোতোয়ালি, বরিশাল",
        "contact_number": "০১৭৩০-২২৩৩৪৪",
        "referral_slot": "বুধবার, সকাল ১০:৩০ টা",
        "helpline": "১৬৪৩০"
    },
    {
        "keywords": ["ময়মনসিংহ", "mymensingh", "জামালপুর", "jamalpur", "নেত্রকোণা", "netrokona"],
        "clinic_name": "ব্র্যাক লিগ্যাল এইড ক্লিনিক, ময়মনসিংহ শাখা",
        "address": "গাঙ্গিনার পাড়, নতুন বাজার রোড, ময়মনসিংহ সদর",
        "contact_number": "০১৭৩০-৪৪৩৩২২",
        "referral_slot": "বৃহস্পতিবার, সকাল ১০:০০ টা",
        "helpline": "১৬৪৩০"
    }
]

DEFAULT_CLINIC = {
    "clinic_name": "ব্র্যাক মানবাধিকার ও আইনি সহায়তা কেন্দ্র, সদর শাখা",
    "address": "৭৫ মহাখালী, ঢাকা (বা আপনার নিকটস্থ উপজেলা কার্যালয়)",
    "contact_number": "০৯৬১২২৭২২৭২ (হেল্পলাইন: ১৬৪৩০)",
    "referral_slot": "বুধবার, সকাল ১০:০০ টা",
    "helpline": "১৬৪৩০"
}

@tool
def find_nearby_legal_aid_center(location: str, issue_category: str = "general") -> Dict[str, str]:
    """
    Search and retrieve the nearest BRAC Legal Aid Clinic and available appointment consultation slot based on the client's location and legal category.
    
    Args:
        location: The client's district, upazila, city, or area in Bangladesh (e.g. 'রংপুর', 'বগুড়া', 'সাভার', 'সিলেট', 'চট্টগ্রাম', 'খুলনা', 'রাজশাহী', 'ঢাকা', 'সদর').
        issue_category: The legal category (family_dower_maintenance, dowry, unpaid_wages, land_dispute, out_of_scope).
        
    Returns:
        A dictionary with clinic_name, address, contact_number, referral_slot, and formatted_display.
    """
    loc_lower = (location or "").strip().lower()
    matched = None
    for entry in LEGAL_AID_CLINIC_DIRECTORY:
        for kw in entry["keywords"]:
            if kw.lower() in loc_lower:
                matched = entry
                break
        if matched:
            break
            
    selected = matched if matched else DEFAULT_CLINIC
    display_name = f"{selected['clinic_name']} ({selected['address']} · ফোন: {selected['contact_number']})"
    return {
        "clinic_name": selected["clinic_name"],
        "address": selected["address"],
        "contact_number": selected["contact_number"],
        "referral_slot": selected["referral_slot"],
        "formatted_display": display_name
    }

# LLM bound with clinic finder tool
clinic_tool_llm = llm.bind_tools([find_nearby_legal_aid_center])# Pydantic schema for classification
class ClassificationOutput(BaseModel):
    category: str = Field(
        description="One of: family_dower_maintenance, dowry, unpaid_wages, land_dispute, out_of_scope, unclassifiable"
    )
    confidence: int = Field(description="Confidence percentage 0-100")
    reasoning: str = Field(description="Reasoning in Bengali explaining why this category applies")

# Pydantic schema for structured fact extraction
class ExtractedFactsOutput(BaseModel):
    applicant_name: Optional[str] = Field(None, description="Client or applicant name (default '[নাম সংরক্ষিত]' if anonymous)")
    respondent: Optional[str] = Field(None, description="Party against whom claim is made and their relationship")
    marriage_date: Optional[str] = Field(None, description="Marriage date, year, or approximate season")
    marriage_date_inferred: bool = Field(False, description="True if the marriage date is approximate or inferred from events")
    dower_amount: Optional[str] = Field(None, description="Dower amount agreed in kabinnama")
    dowry_paid: Optional[str] = Field(None, description="Dowry amount or goods (e.g. motorcycle) paid or demanded")
    unpaid_wages_claim: Optional[str] = Field(None, description="Total unpaid salary or calculated balance")
    work_period: Optional[str] = Field(None, description="Duration worked or specific months unpaid")
    current_status: Optional[str] = Field(None, description="Current situation, pressure, eviction threat, or recovery status")
    children: Optional[str] = Field(None, description="Children count, ages, or custody context")
    evidence: Optional[str] = Field(None, description="Available proof, kabinnama, ID card, witnesses, or document location")
    collective_count: Optional[str] = Field(None, description="If collective claim, number of claimants (e.g. '৪০ জন')")
    time_critical: bool = Field(False, description="True if urgent action is needed (e.g. property sale underway)")
    address: Optional[str] = Field(None, description="Client or incident location, village, upazila, district (e.g. সাভার, বগুড়া, রংপুর, সিলেট, ঢাকা)")

# Structured output invocations
classification_llm = llm.with_structured_output(ClassificationOutput)
extraction_llm = llm.with_structured_output(ExtractedFactsOutput)

# LangGraph State Schema
class IntakeState(TypedDict):
    audio_path: Optional[str]
    transcript: str
    client_own_words: str
    turn_count: int
    
    # Token budgeting & continuation
    estimated_tokens: int
    requires_continuation: bool
    continuation_prompt: Optional[str]
    is_continuation_confirmed: bool
    
    # Safety
    safety_flag: bool
    safety_message: Optional[str]
    
    # Classification
    category: Optional[str]
    confidence: Optional[int]
    classification_reason: Optional[str]
    disambiguation_needed: bool
    
    # Extraction
    applicant_name: Optional[str]
    respondent: Optional[str]
    address: Optional[str]
    marriage_date: Optional[str]
    marriage_date_inferred: Optional[bool]
    dower_amount: Optional[str]
    dowry_paid: Optional[str]
    unpaid_wages_claim: Optional[str]
    work_period: Optional[str]
    current_status: Optional[str]
    children: Optional[str]
    evidence: Optional[str]
    collective_count: Optional[str]
    time_critical: Optional[bool]
    
    # Dialogue & Templates & Chat History
    is_complete: bool
    missing_fields: List[str]
    follow_up_question: Optional[str]
    suggested_replies: Optional[List[str]]
    rights_explanation: Optional[str]
    draft_complaint: Optional[str]
    referral_clinic: Optional[str]
    referral_slot: Optional[str]
    chat_history: List[Dict[str, Any]]
    llm_error: Optional[str]
    llm_error_details: Optional[Dict[str, Any]]


# Helper to estimate tokens (Bangla words average ~2.5 tokens per word)
def estimate_tokens(text: str) -> int:
    if not text:
        return 0
    words = len(text.split())
    return int(words * 2.5)

# Lazy-loaded faster-whisper instance
whisper_model = None

BANGLA_WHISPER_PROMPT = "নিম্নলিখিত বিবরণটি সাধারণ মানুষের কথ্য বাংলা ভাষায় প্রতিলিপি: কাবিন, দেনমোহর, ভরণপোষণ, যৌতুক, বিবাহ, তালাক, বকেয়া মজুরি, জমিজমা সংক্রান্ত বিরোধ।"

def get_whisper():
    global whisper_model
    if whisper_model is None:
        try:
            from faster_whisper import WhisperModel
            whisper_model = WhisperModel("small", device="cpu", compute_type="int8")
        except Exception as e:
            print(f"[Whisper Warning] Could not load local model: {e}")
            whisper_model = False
    return whisper_model

def normalize_bangla_transcript(raw_text: str) -> str:
    """
    Cleans and restores raw/phonetic speech transcription into pure, standard Bengali script.
    Fixes Devanagari, Urdu, or phonetic distortions caused by multilingual ASR models.
    """
    if not raw_text or not raw_text.strip():
        return ""
    
    # Check if text already looks like pure Bengali without foreign scripts
    has_foreign_script = any(('\u0900' <= c <= '\u097F') or ('\u0600' <= c <= '\u06FF') for c in raw_text)
    bengali_chars = [c for c in raw_text if ('\u0980' <= c <= '\u09ff')]
    alnum_chars = [c for c in raw_text if c.isalnum()]
    
    if not has_foreign_script and len(bengali_chars) > 6 and len(bengali_chars) / max(len(alnum_chars), 1) > 0.85:
        return raw_text.strip()

    try:
        from langchain_core.messages import HumanMessage
        prompt = (
            "You are an expert Bengali audio transcriber and legal intake assistant. "
            "The following text was transcribed from a voice recording of an everyday Bengali speaker, but contains phonetic, Devanagari, or transliteration errors:\n\n"
            f"\"{raw_text}\"\n\n"
            "Restore and output ONLY the clean, natural everyday Bengali sentence in pure Bengali script (বাংলা বর্ণমালা). "
            "Output nothing else, no quotes, no explanations."
        )
        response = llm.invoke([HumanMessage(content=prompt)])
        cleaned = response.content.strip().strip('"').strip("'")
        return cleaned if cleaned else raw_text
    except Exception as ex:
        print(f"[Transcript Normalization Warning] {ex}")
        return raw_text


# ----------------- GRAPH NODES -----------------

def transcribe_node(state: IntakeState) -> Dict[str, Any]:
    """Transcribes audio using faster-whisper and restores pure Bangla script."""
    audio_path = state.get("audio_path")
    if audio_path and os.path.exists(audio_path):
        model = get_whisper()
        if model:
            try:
                segments, info = model.transcribe(
                    audio_path, 
                    language="bn", 
                    task="transcribe",
                    beam_size=5
                )
                raw_text = " ".join([seg.text for seg in segments]).strip()
                text = normalize_bangla_transcript(raw_text)
                prev_text = state.get("client_own_words", "")
                combined = f"{prev_text}\n{text}".strip() if prev_text else text
                return {
                    "transcript": text,
                    "client_own_words": combined,
                    "estimated_tokens": estimate_tokens(combined)
                }
            except Exception as ex:
                print(f"[Whisper Error] Transcription failed: {ex}")
    
    current_text = state.get("transcript", "")
    prev_text = state.get("client_own_words", "")
    combined = f"{prev_text}\n{current_text}".strip() if prev_text else current_text
    return {
        "transcript": current_text,
        "client_own_words": combined,
        "estimated_tokens": estimate_tokens(combined)
    }

def safety_check_node(state: IntakeState) -> Dict[str, Any]:
    """Safety check runs on every turn, tuned to over-trigger rather than under-trigger."""
    if state.get("llm_error"):
        return {}
    text_to_eval = state.get("transcript", "")
    if not text_to_eval:
        return {"safety_flag": False}

    prompt = ChatPromptTemplate.from_messages([
        ("system", prompts.SAFETY_SYSTEM_PROMPT),
        ("user", "{text}")
    ])
    try:
        res = llm.invoke(prompt.format_messages(text=text_to_eval))
        is_danger = "DANGER" in res.content.upper()
        return {
            "safety_flag": is_danger,
            "safety_message": templates.RIGHTS_EXPLANATIONS["safety_escalation"] if is_danger else None
        }
    except Exception as e:
        print(f"[Safety LLM Error] {e}")
        err_info = parse_llm_error(e)
        return {
            "safety_flag": False,
            "llm_error": err_info["message_bn"],
            "llm_error_details": err_info
        }

def token_budget_node(state: IntakeState) -> Dict[str, Any]:
    """
    Checks if token consumption exceeds the threshold.
    If yes and user has not confirmed continuation yet, pauses generation and asks for continuation.
    """
    if state.get("llm_error"):
        return {}
    tokens = state.get("estimated_tokens", 0)
    confirmed = state.get("is_continuation_confirmed", False)
    
    if tokens > TOKEN_BUDGET_LIMIT and not confirmed:
        prompt_msg = (
            f"আপনার বিবরণটি দীর্ঘ (আনুমানিক {tokens} টোকেন)। "
            f"পরবর্তী ধাপে বিস্তারিত আইনি তথ্য ও অভিযোগ প্রস্তুত করতে আরও টোকেন উৎপন্ন হবে। "
            f"আপনি কি পরবর্তী টোকেন বিশ্লেষণ সম্পন্ন করতে চান?"
        )
        return {
            "requires_continuation": True,
            "continuation_prompt": prompt_msg,
            "is_complete": False
        }
    
    return {
        "requires_continuation": False,
        "continuation_prompt": None
    }

def classification_node(state: IntakeState) -> Dict[str, Any]:
    """Classifies category and checks confidence."""
    if state.get("llm_error"):
        return {}
    text_to_eval = state.get("client_own_words") or state.get("transcript", "")
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", prompts.CLASSIFICATION_SYSTEM_PROMPT),
        ("user", "{text}")
    ])
    try:
        res = classification_llm.invoke(prompt.format_messages(text=text_to_eval))
        if res is None:
            cat = "unclassifiable"
            conf = 0
            reasoning = "স্বয়ংক্রিয় শ্রেণিবিভাগ করা যায়নি"
        elif isinstance(res, dict):
            cat = res.get("category", "unclassifiable")
            conf = int(res.get("confidence", 0) or 0)
            reasoning = res.get("reasoning", "")
        else:
            cat = getattr(res, "category", "unclassifiable")
            conf = int(getattr(res, "confidence", 0) or 0)
            reasoning = getattr(res, "reasoning", "")

        disambiguation = (conf < 65) or (cat == "unclassifiable")
        
        return {
            "category": cat,
            "confidence": conf,
            "classification_reason": reasoning,
            "disambiguation_needed": disambiguation
        }
    except Exception as e:
        print(f"[Classification Error] {e}")
        err_info = parse_llm_error(e)
        return {
            "category": "unclassifiable",
            "confidence": 0,
            "classification_reason": "স্বয়ংক্রিয় শ্রেণিবিভাগ করা যায়নি",
            "disambiguation_needed": False,
            "llm_error": err_info["message_bn"],
            "llm_error_details": err_info
        }

def extraction_node(state: IntakeState) -> Dict[str, Any]:
    """Extracts facts from client's full narrative."""
    if state.get("llm_error"):
        return {}
    text_to_eval = state.get("client_own_words") or state.get("transcript", "")
    cat = state.get("category", "")
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", prompts.EXTRACTION_SYSTEM_PROMPT),
        ("user", "Category: {category}\nNarrative: {text}")
    ])
    try:
        res = extraction_llm.invoke(
            prompt.format_messages(category=cat, text=text_to_eval)
        )
        if res is None:
            data = {}
        elif isinstance(res, dict):
            data = res
        elif hasattr(res, "model_dump"):
            data = res.model_dump()
        elif hasattr(res, "dict"):
            data = res.dict()
        else:
            data = {}

        return {
            k: v for k, v in data.items() 
            if v is not None and str(v).strip().lower() != "null" and str(v).strip() != ""
        }
    except Exception as e:
        print(f"[Extraction Error] {e}")
        err_info = parse_llm_error(e)
        return {
            "llm_error": err_info["message_bn"],
            "llm_error_details": err_info
        }

def generate_suggested_replies(
    question: Optional[str],
    missing_fields: Optional[List[str]] = None,
    category: Optional[str] = None
) -> List[str]:
    """Generates 3-4 natural, colloquial Bengali suggested quick-replies based on the follow-up question."""
    q = (question or "").lower()
    target = (missing_fields[0] if missing_fields else "").lower()

    # 1. Kabinnama / Marriage document evidence
    if "কাবিন" in q or "দলিল" in q or "কাগজ" in q or "কাবিননামা" in target or "দলিল" in target:
        return [
            "কাবিননামার কাগজটি বাবার বাড়িতে রাখা আছে",
            "কাবিননামা স্বামীর কাছে রেখে দিয়েছে, আমাকে দেয়নি",
            "রেজিস্ট্রি হয়েছিল, কাজী অফিসে কাবিনের নকল পাওয়া যাবে",
            "আমাদের কোনো লিখিত কাবিননামা বা বিয়ের কাগজ নেই"
        ]

    # 2. Dower / Dowry / Claim amount
    if "দেনমোহর" in q or "টাকার পরিমাণ" in target or "টাকা" in q or "দাবি" in q:
        return [
            "দেনমোহর ধার্য করা হয়েছিল ১ লাখ টাকা",
            "দেনমোহর ধার্য করা হয়েছিল ২ লাখ টাকা",
            "দেনমোহর ধার্য করা হয়েছিল ৫ লাখ টাকা",
            "কাবিননামার কাগজ দেখে সঠিক টাকার পরিমাণ বলতে পারব"
        ]

    # 3. Marriage Date / Timeline
    if ("বিয়ে" in q or "বিয়ে" in q) and ("সন" in q or "কবে" in q or "সাল" in q or "বছর" in q or "তারিখ" in q or "বিয়ের সন" in target):
        return [
            "আনুমানিক ১ থেকে ২ বছর আগে আমাদের বিয়ে হয়েছে",
            "আনুমানিক ৪ থেকে ৫ বছর আগে বিয়ে হয়েছিল",
            "১০ বছরেরও বেশি সময় আগে আমাদের বিয়ে হয়েছে",
            "সঠিক সন মনে নেই, তবে কয়েক বছর হয়ে গেছে"
        ]

    # 4. Wages / Unpaid Salary
    if "মজুরি" in q or "বেতন" in q or "বকেয়া" in target or "বকেয়া" in target or "মজুরির মোট পরিমাণ" in target:
        return [
            "১ মাসের পুরো মজুরি বা বেতন বকেয়া রয়েছে",
            "প্রায় ২ থেকে ৩ মাসের বেতন এখনও বকেয়া আছে",
            "হিসাব অনুযায়ী প্রায় ৫ থেকে ১০ হাজার টাকা পাওনা আছে",
            "কাজের চুক্তি অনুযায়ী এখনো পুরো টাকা পরিশোধ করা হয়নি"
        ]

    # 5. Work Period / Duration
    if "কতদিন" in q or "কাজের সময়" in target or "কোন সময়" in q:
        return [
            "গত ১ মাস ধরে আমি এই কাজটি করেছি",
            "টানা ৬ মাস ধরে সেখানে নিয়মিত কাজ করেছি",
            "১ বছরেরও বেশি সময় ধরে সেখানে কাজ করেছি",
            "১০ থেকে ১৫ দিনের নির্দিষ্ট চুক্তিভিত্তিক কাজ ছিল"
        ]

    # 6. Work Evidence / Witness / Sardar / Slip
    if "সাক্ষী" in q or "সর্দার" in q or "স্লিপ" in q or "হাজিরা" in q or "সাক্ষী" in target:
        return [
            "কাজের দৈনিক হাজিরা খাতা বা স্লিপের প্রমাণ রয়েছে",
            "কাজের জায়গায় সহকর্মী ও সর্দার সরাসরি সাক্ষী আছেন",
            "শুধুমাত্র মৌখিক চুক্তি হয়েছিল, লিখিত কোনো কাগজ নেই",
            "মালিক ও ঠিকাদারের পূর্ণ নাম এবং ফোন নম্বর জানা আছে"
        ]

    # 7. Land Deeds / Dispute
    if "জমি" in q or "খতিয়ান" in q or "পর্চা" in q or category == "land_dispute" or "খতিয়ান" in target:
        return [
            "জমির মূল রেজিস্ট্রি দলিল আমাদের কাছে সংরক্ষিত আছে",
            "জমির পর্চা ও খতিয়ানের সত্যায়িত কপি আছে",
            "জমির মূল কাগজপত্র বা দলিল প্রতিপক্ষের দখলে আটকে আছে",
            "কাগজপত্র জটিল হলেও জমিটি বহু বছর ধরে আমাদের দখলে আছে"
        ]

    # 8. Children / Maintenance
    if "সন্তান" in q or "বাচ্চা" in q or "ভরণপোষণ" in q:
        return [
            "হ্যাঁ, আমাদের ১টি সন্তান আছে এবং সে আমার কাছেই থাকে",
            "হ্যাঁ, আমাদের ২টি সন্তান আছে এবং তাদের দেখাশোনা আমি করছি",
            "না, আমাদের কোনো সন্তান নেই",
            "স্বামী সন্তান বা আমার কারও কোনো ভরণপোষণ বা খরচ দেয় না"
        ]

    # 9. Disambiguation
    if category == "unclassifiable" or "পারিবারিক" in q:
        return [
            "পারিবারিক দেনমোহর বা ভরণপোষণ",
            "বকেয়া মজুরি বা শ্রমিকের পাওনা",
            "জমিজমা সংক্রান্ত বিরোধ",
            "যৌতুক ও নির্যাতন সংক্রান্ত"
        ]

    # 10. Confirmation / Yes-No
    if "কি না" in q or "কিনা" in q or "আছে কি" in q or "হয়েছে কি" in q or "হয়েছে কি" in q or q.endswith("?"):
        return [
            "হ্যাঁ, এই বিষয়ে প্রমাণ ও তথ্য আছে",
            "না, এই ধরনের কোনো প্রমাণ বা তথ্য নেই",
            "হ্যাঁ, ঘটনাটি এইভাবেই হয়েছিল",
            "কিছু অংশ দেওয়া হয়েছিল, তবে পুরোটা এখনো বাকি আছে"
        ]

    # 11. General fallback
    return [
        "হ্যাঁ, এই বিষয়ে প্রয়োজনীয় সব তথ্য আমার কাছে আছে",
        "কোনো লিখিত প্রমাণ বা কাগজপত্র নেই, সবই মৌখিক",
        "সব আলোচনা ও চুক্তি মৌখিকভাবে হয়েছিল",
        "এই পরিস্থিতিতে কীভাবে অগ্রসর হব সেই আইনি পরামর্শ চাই"
    ]

def dialogue_node(state: IntakeState) -> Dict[str, Any]:
    """Identifies missing facts and formulates a dynamic, context-aware follow-up question."""
    if state.get("llm_error"):
        return {}
    cat = state.get("category")
    turn_count = state.get("turn_count", 1)
    text_to_eval = state.get("client_own_words") or state.get("transcript", "")
    
    # 1. If disambiguation is needed (vague / unclassifiable statement)
    if state.get("disambiguation_needed") or cat == "unclassifiable":
        question = "আপনার সমস্যাটি কি দেনমোহর/ভরণপোষণ, বকেয়া মজুরি, নাকি জমিজমা নিয়ে? অনুগ্রহ করে একটু বিস্তারিত বলুন।"
        try:
            prompt = ChatPromptTemplate.from_messages([
                ("system", prompts.FOLLOW_UP_SYSTEM_PROMPT),
                ("user", "Client said: {client_narrative}\n\nPlease ask a warm, colloquial Bengali question connecting to what they said to clarify whether this is about family/dower/maintenance (পারিবারিক দেনমোহর বা ভরণপোষণ), unpaid wages (বকেয়া মজুরি), or land dispute (জমিজমা).")
            ])
            res = llm.invoke(prompt.format_messages(
                client_narrative=text_to_eval,
                category="অস্পষ্ট / শ্রেণিবিহীন",
                known_facts="নির্দিষ্ট কোনো আইনি ঘটনা বা দাবি এখনো স্পষ্ট নয়",
                missing_field="সমস্যার মূল ধরণ (পারিবারিক দেনমোহর/ভরণপোষণ, বকেয়া মজুরি, নাকি জমিজমা সংক্রান্ত বিষয়)"
            ))
            if res.content and res.content.strip():
                question = res.content.strip()
        except Exception as e:
            print(f"[Dialogue LLM Error - Disambiguation] {e}")
            err_info = parse_llm_error(e)
            return {
                "is_complete": False,
                "follow_up_question": None,
                "suggested_replies": None,
                "llm_error": err_info["message_bn"],
                "llm_error_details": err_info
            }

        return {
            "is_complete": False,
            "follow_up_question": question,
            "suggested_replies": [
                "পারিবারিক দেনমোহর বা ভরণপোষণ",
                "বকেয়া মজুরি বা শ্রমিকের পাওনা",
                "জমিজমা সংক্রান্ত বিরোধ",
                "যৌতুক ও নির্যাতন সংক্রান্ত"
            ]
        }

    # 2. Conclude after 1 follow-up turn (turn_count >= 2) to avoid client fatigue
    # Remaining missing fields are safely marked with [অপ্রতিষ্ঠিত] in the draft complaint
    if turn_count >= 2:
        return {
            "is_complete": True,
            "missing_fields": [],
            "follow_up_question": None
        }

    # 3. Assemble what we already know from previous extraction
    known = []
    if state.get("applicant_name") and state.get("applicant_name") != "[নাম সংরক্ষিত]":
        known.append(f"আবেদনকারী: {state.get('applicant_name')}")
    if state.get("respondent") and state.get("respondent") != "[বিবাদী]":
        known.append(f"বিবাদী: {state.get('respondent')}")
    if state.get("marriage_date"):
        known.append(f"বিয়ের সময়: {state.get('marriage_date')}")
    if state.get("dower_amount"):
        known.append(f"দেনমোহর: {state.get('dower_amount')}")
    if state.get("dowry_paid"):
        known.append(f"যৌতুক/দাবি: {state.get('dowry_paid')}")
    if state.get("unpaid_wages_claim"):
        known.append(f"বকেয়া মজুরি: {state.get('unpaid_wages_claim')}")
    if state.get("work_period"):
        known.append(f"কাজের সময়: {state.get('work_period')}")
    if state.get("children"):
        known.append(f"সন্তান: {state.get('children')}")
    if state.get("evidence"):
        known.append(f"প্রমাণ/দলিল: {state.get('evidence')}")

    # 4. Check what critical legal fields are missing for the draft
    missing = []
    if cat in ("family_dower_maintenance", "dowry"):
        if not state.get("dower_amount") and not state.get("dowry_paid"):
            missing.append("দেনমোহর বা দাবিকৃত টাকার পরিমাণ")
        if not state.get("marriage_date"):
            missing.append("বিয়ের সন বা আনুমানিক বছর/ঋতু")
        if not state.get("evidence"):
            missing.append("কাবিননামা কার কাছে আছে বা কীভাবে সংরক্ষিত")
    elif cat == "unpaid_wages":
        if not state.get("unpaid_wages_claim"):
            missing.append("বকেয়া মজুরির মোট পরিমাণ")
        if not state.get("work_period"):
            missing.append("কতদিন বা কোন সময়ে কাজ করেছেন")
        if not state.get("evidence"):
            missing.append("কাজের কোনো মৌখিক সাক্ষী, সর্দার বা স্লিপ আছে কি না")
    elif cat == "land_dispute":
        if not state.get("evidence"):
            missing.append("জমির দলিলের বর্তমান অবস্থান বা খতিয়ান")

    # 5. Formulate dynamic question using user's narrative context and known facts
    if missing:
        target_field = missing[0]
        question = f"আপনার অভিযোগটির খসড়া প্রস্তুত করার জন্য একটি অতিরিক্ত তথ্য প্রয়োজন: {target_field} সম্পর্কে কি জানাতে পারবেন?"
        try:
            prompt = ChatPromptTemplate.from_messages([
                ("system", prompts.FOLLOW_UP_SYSTEM_PROMPT),
                ("user", "Client's Narrative:\n{client_narrative}\n\nPlease ask ONE empathetic, colloquial Bangla question connecting directly to what they mentioned, asking for: {missing_field}")
            ])
            res = llm.invoke(prompt.format_messages(
                client_narrative=text_to_eval,
                category=cat or "সাধারণ",
                known_facts="; ".join(known) if known else "কোনো তথ্য এখনো পাওয়া যায়নি",
                missing_field=target_field
            ))
            if res.content and res.content.strip():
                question = res.content.strip()
        except Exception as e:
            print(f"[Dialogue LLM Error - Follow-up] {e}")
            err_info = parse_llm_error(e)
            return {
                "is_complete": False,
                "missing_fields": missing,
                "follow_up_question": None,
                "suggested_replies": None,
                "llm_error": err_info["message_bn"],
                "llm_error_details": err_info
            }

        suggested = generate_suggested_replies(
            question=question,
            missing_fields=missing,
            category=cat
        )
        return {
            "is_complete": False,
            "missing_fields": missing,
            "follow_up_question": question,
            "suggested_replies": suggested
        }
    
    return {
        "is_complete": True,
        "missing_fields": [],
        "follow_up_question": None,
        "suggested_replies": None
    }

def template_output_node(state: IntakeState) -> Dict[str, Any]:
    """Applies reviewed legal templates, calls nearby clinic tool, and synthesizes dynamic legal rights & solutions."""
    if state.get("llm_error"):
        return {}
    cat = state.get("category", "family_dower_maintenance")
    standard_exp = templates.RIGHTS_EXPLANATIONS.get(cat, templates.RIGHTS_EXPLANATIONS["out_of_scope"])
    
    facts = {
        "applicant_name": state.get("applicant_name") or "[নাম সংরক্ষিত]",
        "respondent": state.get("respondent") or "[বিবাদী]",
        "address": state.get("address") or "[ঠিকানা — অপ্রতিষ্ঠিত]",
        "marriage_date": state.get("marriage_date") or "[অপ্রতিষ্ঠিত]",
        "dower_amount": state.get("dower_amount") or "[অপ্রতিষ্ঠিত]",
        "dowry_paid": state.get("dowry_paid") or "[অপ্রতিষ্ঠিত]",
        "unpaid_wages_claim": state.get("unpaid_wages_claim") or "[অপ্রতিষ্ঠিত]",
        "work_period": state.get("work_period") or "[অপ্রতিষ্ঠিত]",
        "current_status": state.get("current_status") or "[চাপ প্রয়োগ করা হইতেছে]",
        "children": state.get("children") or "[সন্তানের বিবরণ উল্লেখ নেই]",
        "evidence": state.get("evidence") or "[অপ্রতিষ্ঠিত]"
    }
    
    draft = templates.generate_draft_complaint(cat, facts)
    
    # 1. Tool Calling: Dynamically retrieve nearest legal aid center and consultation slot
    clinic = DEFAULT_CLINIC["clinic_name"]
    slot = DEFAULT_CLINIC["referral_slot"]
    text_to_eval = state.get("client_own_words") or state.get("transcript", "")
    user_location = state.get("address") or facts.get("address") or ""
    if user_location == "[ঠিকানা — অপ্রতিষ্ঠিত]":
        user_location = ""
        
    try:
        tool_prompt = (
            f"Client's full grievance narrative: {text_to_eval}\n"
            f"Case Category: {cat}\n"
            f"Extracted Location/Address: {user_location or 'Not explicitly provided'}\n\n"
            "Task: You MUST call the tool find_nearby_legal_aid_center with the detected or inferred location and legal issue category to locate the nearest BRAC Legal Aid Clinic and available appointment slot."
        )
        tool_res = clinic_tool_llm.invoke(tool_prompt)
        if tool_res.tool_calls:
            tool_args = tool_res.tool_calls[0].get("args", {})
            clinic_info = find_nearby_legal_aid_center.invoke(tool_args)
            clinic = clinic_info.get("formatted_display") or clinic_info.get("clinic_name") or clinic
            slot = clinic_info.get("referral_slot") or slot
        else:
            # Fallback direct tool invocation with available context
            fallback_info = find_nearby_legal_aid_center.invoke({
                "location": user_location or text_to_eval,
                "issue_category": cat
            })
            clinic = fallback_info.get("formatted_display") or fallback_info.get("clinic_name") or clinic
            slot = fallback_info.get("referral_slot") or slot
    except Exception as e:
        print(f"[Clinic Tool Calling Error] {e}")
        clinic = DEFAULT_CLINIC["clinic_name"]
        slot = DEFAULT_CLINIC["referral_slot"]
        err_info = parse_llm_error(e)
        if err_info.get("status_code") in (401, 402, 429) or err_info.get("error_type") in ("authentication_error", "connection_error"):
            return {
                "rights_explanation": standard_exp,
                "draft_complaint": draft,
                "referral_clinic": clinic,
                "referral_slot": slot,
                "is_complete": True,
                "llm_error": err_info["message_bn"],
                "llm_error_details": err_info
            }
    
    # 2. Dynamic synthesis: Generate personalized legal advice and action plan based on user's narrative & follow-up answers
    rights_exp = standard_exp
    if cat != "out_of_scope" and text_to_eval:
        try:
            prompt = ChatPromptTemplate.from_messages([
                ("system", prompts.DYNAMIC_SOLUTION_SYSTEM_PROMPT),
                ("user", "Client Full Narrative & Follow-up Answers:\n{client_narrative}\n\nExtracted Facts:\n{known_facts}\n\nStandard Legal Guidelines:\n{legal_framework}\n\nPlease generate the personalized Bengali legal explanation and actionable roadmap ('আপনার আইনি অধিকার ও পথ') for this client.")
            ])
            res = llm.invoke(prompt.format_messages(
                client_narrative=text_to_eval,
                category=cat,
                known_facts=str({k: v for k, v in facts.items() if "[অপ্রতিষ্ঠিত]" not in str(v) and "[নাম সংরক্ষিত]" not in str(v)}),
                legal_framework=standard_exp
            ))
            if res.content and len(res.content.strip()) > 60:
                rights_exp = res.content.strip()
        except Exception as e:
            print(f"[Dynamic Solution Error] Falling back to standard template: {e}")
            rights_exp = standard_exp
            err_info = parse_llm_error(e)
            if err_info.get("status_code") in (401, 402, 429) or err_info.get("error_type") in ("authentication_error", "connection_error"):
                return {
                    "rights_explanation": rights_exp,
                    "draft_complaint": draft,
                    "referral_clinic": clinic,
                    "referral_slot": slot,
                    "is_complete": True,
                    "llm_error": err_info["message_bn"],
                    "llm_error_details": err_info
                }
    
    return {
        "rights_explanation": rights_exp,
        "draft_complaint": draft,
        "referral_clinic": clinic,
        "referral_slot": slot,
        "is_complete": True
    }

# ----------------- WORKFLOW GRAPH -----------------

workflow = StateGraph(IntakeState)

workflow.add_node("transcribe", transcribe_node)
workflow.add_node("safety_check", safety_check_node)
workflow.add_node("token_budget", token_budget_node)
workflow.add_node("classify", classification_node)
workflow.add_node("extract", extraction_node)
workflow.add_node("dialogue", dialogue_node)
workflow.add_node("generate_templates", template_output_node)

workflow.set_entry_point("transcribe")
workflow.add_edge("transcribe", "safety_check")

# Safety routing
def check_safety_route(state: IntakeState):
    if state.get("llm_error"):
        return END
    if state.get("safety_flag"):
        return "safety_breakout"
    return "token_budget"

workflow.add_conditional_edges(
    "safety_check",
    check_safety_route,
    {
        "safety_breakout": END,
        "token_budget": "token_budget",
        END: END
    }
)

# Token budget routing: if exceeds threshold, pause and ask for confirmation
def check_token_route(state: IntakeState):
    if state.get("llm_error"):
        return END
    if state.get("requires_continuation"):
        return "ask_continuation"
    return "classify"

workflow.add_conditional_edges(
    "token_budget",
    check_token_route,
    {
        "ask_continuation": END,
        "classify": "classify",
        END: END
    }
)

# Classification routing
def check_classification_route(state: IntakeState):
    if state.get("llm_error"):
        return END
    if state.get("category") == "out_of_scope":
        return "generate_templates"
    if state.get("disambiguation_needed"):
        return "dialogue"
    return "extract"

workflow.add_conditional_edges(
    "classify",
    check_classification_route,
    {
        "generate_templates": "generate_templates",
        "dialogue": "dialogue",
        "extract": "extract",
        END: END
    }
)

workflow.add_edge("extract", "dialogue")

# Dialogue routing
def check_dialogue_route(state: IntakeState):
    if state.get("llm_error"):
        return END
    if state.get("is_complete"):
        return "generate_templates"
    return END

workflow.add_conditional_edges(
    "dialogue",
    check_dialogue_route,
    {
        "generate_templates": "generate_templates",
        END: END
    }
)

workflow.add_edge("generate_templates", END)

odhikar_graph = workflow.compile()

# Public runner function
def run_intake(
    transcript: str, 
    audio_path: Optional[str] = None, 
    existing_state: Optional[Dict[str, Any]] = None,
    is_continuation: bool = False
) -> Dict[str, Any]:
    """Processes a single conversational turn in Bangla with token continuation and LLM error support."""
    # Check if API Key is configured before running LangGraph
    if not is_model_configured():
        err_details = get_error_message("authentication_error", "Missing or unconfigured LLM API key in backend/.env")
        history = list(existing_state.get("chat_history", [])) if existing_state else []
        if transcript and transcript.strip():
            history.append({"role": "user", "content": transcript.strip()})
        history.append({"role": "assistant", "content": f"⚠️ {err_details['message_bn']}"})
        return {
            "transcript": transcript,
            "client_own_words": existing_state.get("client_own_words", "") if existing_state else transcript,
            "turn_count": (existing_state.get("turn_count", 0) + 1) if existing_state else 1,
            "safety_flag": False,
            "safety_message": None,
            "is_complete": False,
            "requires_continuation": False,
            "continuation_prompt": None,
            "follow_up_question": None,
            "suggested_replies": None,
            "rights_explanation": None,
            "draft_complaint": None,
            "referral_clinic": None,
            "referral_slot": None,
            "chat_history": history,
            "llm_error": err_details["message_bn"],
            "llm_error_details": err_details
        }

    state: IntakeState = {
        "audio_path": audio_path,
        "transcript": transcript,
        "client_own_words": existing_state.get("client_own_words", "") if existing_state else "",
        "turn_count": (existing_state.get("turn_count", 0) + 1) if existing_state else 1,
        "estimated_tokens": existing_state.get("estimated_tokens", 0) if existing_state else 0,
        "requires_continuation": False,
        "continuation_prompt": None,
        "is_continuation_confirmed": is_continuation or (existing_state.get("is_continuation_confirmed", False) if existing_state else False),
        "safety_flag": False,
        "safety_message": None,
        "category": existing_state.get("category") if existing_state else None,
        "confidence": existing_state.get("confidence") if existing_state else None,
        "classification_reason": None,
        "disambiguation_needed": False,
        "applicant_name": existing_state.get("applicant_name") if existing_state else None,
        "respondent": existing_state.get("respondent") if existing_state else None,
        "address": existing_state.get("address") if existing_state else None,
        "marriage_date": existing_state.get("marriage_date") if existing_state else None,
        "marriage_date_inferred": existing_state.get("marriage_date_inferred", False) if existing_state else False,
        "dower_amount": existing_state.get("dower_amount") if existing_state else None,
        "dowry_paid": existing_state.get("dowry_paid") if existing_state else None,
        "unpaid_wages_claim": existing_state.get("unpaid_wages_claim") if existing_state else None,
        "work_period": existing_state.get("work_period") if existing_state else None,
        "current_status": existing_state.get("current_status") if existing_state else None,
        "children": existing_state.get("children") if existing_state else None,
        "evidence": existing_state.get("evidence") if existing_state else None,
        "collective_count": existing_state.get("collective_count") if existing_state else None,
        "time_critical": existing_state.get("time_critical", False) if existing_state else False,
        "is_complete": False,
        "missing_fields": [],
        "follow_up_question": None,
        "suggested_replies": existing_state.get("suggested_replies") if existing_state else None,
        "rights_explanation": None,
        "draft_complaint": None,
        "referral_clinic": None,
        "referral_slot": None,
        "chat_history": list(existing_state.get("chat_history", [])) if existing_state else [],
        "llm_error": None,
        "llm_error_details": None
    }
    
    # Append the user's current message to chat_history if present
    if transcript and transcript.strip():
        state["chat_history"].append({
            "role": "user",
            "content": transcript.strip()
        })

    try:
        result = odhikar_graph.invoke(state)
    except Exception as exc:
        print(f"[Graph Invocations Error] {exc}")
        err_info = parse_llm_error(exc)
        result = dict(state)
        result["llm_error"] = err_info["message_bn"]
        result["llm_error_details"] = err_info
    
    # Append assistant's response to chat_history based on outcome
    history = list(result.get("chat_history", []))
    if result.get("llm_error"):
        history.append({
            "role": "assistant",
            "content": f"⚠️ ত্রুটি: {result.get('llm_error')}"
        })
    elif result.get("safety_flag"):
        history.append({
            "role": "assistant",
            "content": result.get("safety_message") or "জরুরি নিরাপত্তা ব্রেক-আউট সক্রিয় করা হয়েছে।"
        })
    elif result.get("requires_continuation"):
        history.append({
            "role": "assistant",
            "content": result.get("continuation_prompt") or "টোকেন বিশ্লেষণ অনুমতির অপেক্ষা।"
        })
    elif result.get("follow_up_question"):
        history.append({
            "role": "assistant",
            "content": result.get("follow_up_question")
        })
    elif result.get("is_complete"):
        cat = result.get("category")
        if cat == "out_of_scope":
            summary_msg = "আপনার বিবরণটি পর্যালোচনা করা হয়েছে। এটি আমাদের লিগ্যাল এইডের আওতাভুক্ত না হলেও সম্ভাব্য পদক্ষেপের পরামর্শ প্রদান করা হয়েছে।"
        else:
            summary_msg = (
                f"ধন্যবাদ। আপনার সম্পূর্ণ বিবরণ ও উত্তরের ভিত্তিতে ব্যক্তিগত আইনি অধিকার ও পথরেখা প্রস্তুত করা হয়েছে। "
                f"নিকটস্থ পরামর্শ কেন্দ্র: {result.get('referral_clinic')} ({result.get('referral_slot')})।"
            )
        history.append({
            "role": "assistant",
            "content": summary_msg
        })
    
    result["chat_history"] = history
    return result

