import os
import sys
import asyncio
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

# OpenRouter configuration with environment variables
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
MODEL_NAME = os.getenv("MODEL_NAME", "google/gemini-3.8-flash")
MAX_TOKENS = int(os.getenv("MAX_TOKENS", "2000"))
TEMPERATURE = float(os.getenv("TEMPERATURE", "0"))
REASONING_MAX_TOKENS = int(os.getenv("REASONING_MAX_TOKENS", "0"))

extra_body = {}
if REASONING_MAX_TOKENS > 0:
    extra_body["reasoning"] = {"max_tokens": REASONING_MAX_TOKENS}

# TOKEN THRESHOLD: If estimated tokens exceed this budget, ask user to confirm continuation
# This ensures users with low budgets or long rambling narratives stay in control
TOKEN_BUDGET_LIMIT = int(os.getenv("TOKEN_BUDGET_LIMIT", "180"))

llm = ChatOpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=OPENROUTER_API_KEY,
    model=MODEL_NAME,
    max_tokens=MAX_TOKENS,
    temperature=TEMPERATURE,
    streaming=True,
    extra_body=extra_body if extra_body else None
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
    rights_explanation: Optional[str]
    draft_complaint: Optional[str]
    referral_clinic: Optional[str]
    referral_slot: Optional[str]
    chat_history: List[Dict[str, Any]]


# Helper to estimate tokens (Bangla words average ~2.5 tokens per word)
def estimate_tokens(text: str) -> int:
    if not text:
        return 0
    words = len(text.split())
    return int(words * 2.5)

# Lazy-loaded faster-whisper instance
whisper_model = None

def get_whisper():
    global whisper_model
    if whisper_model is None:
        try:
            from faster_whisper import WhisperModel
            whisper_model = WhisperModel("tiny", device="cpu", compute_type="int8")
        except Exception as e:
            print(f"[Whisper Warning] Could not load local model: {e}")
            whisper_model = False
    return whisper_model

# ----------------- GRAPH NODES -----------------

def transcribe_node(state: IntakeState) -> Dict[str, Any]:
    """Transcribes audio using faster-whisper or preserves text input fallback."""
    audio_path = state.get("audio_path")
    if audio_path and os.path.exists(audio_path):
        model = get_whisper()
        if model:
            try:
                segments, info = model.transcribe(audio_path, language="bn")
                text = " ".join([seg.text for seg in segments]).strip()
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
        return {"safety_flag": False}

def token_budget_node(state: IntakeState) -> Dict[str, Any]:
    """
    Checks if token consumption exceeds the threshold.
    If yes and user has not confirmed continuation yet, pauses generation and asks for continuation.
    """
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
    text_to_eval = state.get("client_own_words") or state.get("transcript", "")
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", prompts.CLASSIFICATION_SYSTEM_PROMPT),
        ("user", "{text}")
    ])
    try:
        res: ClassificationOutput = classification_llm.invoke(prompt.format_messages(text=text_to_eval))
        cat = res.category
        conf = res.confidence
        disambiguation = (conf < 65) or (cat == "unclassifiable")
        
        return {
            "category": cat,
            "confidence": conf,
            "classification_reason": res.reasoning,
            "disambiguation_needed": disambiguation
        }
    except Exception as e:
        print(f"[Classification Error] {e}")
        return {
            "category": "unclassifiable",
            "confidence": 40,
            "classification_reason": "স্বয়ংক্রিয় শ্রেণিবিভাগ করা যায়নি",
            "disambiguation_needed": True
        }

def extraction_node(state: IntakeState) -> Dict[str, Any]:
    """Extracts facts from client's full narrative."""
    text_to_eval = state.get("client_own_words") or state.get("transcript", "")
    cat = state.get("category", "")
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", prompts.EXTRACTION_SYSTEM_PROMPT),
        ("user", "Category: {category}\nNarrative: {text}")
    ])
    try:
        res: ExtractedFactsOutput = extraction_llm.invoke(
            prompt.format_messages(category=cat, text=text_to_eval)
        )
        data = res.model_dump()
        return {k: v for k, v in data.items() if v is not None}
    except Exception as e:
        print(f"[Extraction Error] {e}")
        return {}

def dialogue_node(state: IntakeState) -> Dict[str, Any]:
    """Identifies missing facts and formulates a dynamic, context-aware follow-up question."""
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

        return {
            "is_complete": False,
            "follow_up_question": question
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

        return {
            "is_complete": False,
            "missing_fields": missing,
            "follow_up_question": question
        }
    
    return {
        "is_complete": True,
        "missing_fields": [],
        "follow_up_question": None
    }

def template_output_node(state: IntakeState) -> Dict[str, Any]:
    """Applies reviewed legal templates, calls nearby clinic tool, and synthesizes dynamic legal rights & solutions."""
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
    if state.get("safety_flag"):
        return "safety_breakout"
    return "token_budget"

workflow.add_conditional_edges(
    "safety_check",
    check_safety_route,
    {
        "safety_breakout": END,
        "token_budget": "token_budget"
    }
)

# Token budget routing: if exceeds threshold, pause and ask for confirmation
def check_token_route(state: IntakeState):
    if state.get("requires_continuation"):
        return "ask_continuation"
    return "classify"

workflow.add_conditional_edges(
    "token_budget",
    check_token_route,
    {
        "ask_continuation": END,
        "classify": "classify"
    }
)

# Classification routing
def check_classification_route(state: IntakeState):
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
        "extract": "extract"
    }
)

workflow.add_edge("extract", "dialogue")

# Dialogue routing
def check_dialogue_route(state: IntakeState):
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
    """Processes a single conversational turn in Bangla with token continuation support."""
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
        "rights_explanation": None,
        "draft_complaint": None,
        "referral_clinic": None,
        "referral_slot": None,
        "chat_history": list(existing_state.get("chat_history", [])) if existing_state else []
    }
    
    # Append the user's current message to chat_history if present
    if transcript and transcript.strip():
        state["chat_history"].append({
            "role": "user",
            "content": transcript.strip()
        })

    result = odhikar_graph.invoke(state)
    
    # Append assistant's response to chat_history based on outcome
    history = list(result.get("chat_history", []))
    if result.get("safety_flag"):
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


# Bengali UI labels for LangGraph node lifecycle streaming
NODE_LABELS_BN = {
    "transcribe": "কথা ও বার্তা গ্রহণ সম্পন্ন...",
    "safety_check": "জরুরি নিরাপত্তা বিশ্লেষণ সম্পন্ন...",
    "token_budget": "টোকেন বাজেট নিরীক্ষা সম্পন্ন...",
    "classify": "মামলার আইনি ধরণ নির্ধারণ সম্পন্ন...",
    "extract": "মূল তথ্যমালা বিশ্লেষণ সম্পন্ন...",
    "dialogue": "আইনি প্রতিক্রিয়া প্রস্তুত সম্পন্ন...",
    "generate_templates": "আইনি পথরেখা ও খসড়া প্রস্তুত সম্পন্ন..."
}

NODE_START_LABELS_BN = {
    "transcribe": "কথা ও বার্তা গ্রহণ করা হচ্ছে...",
    "safety_check": "জরুরি নিরাপত্তা বিশ্লেষণ চলছে...",
    "token_budget": "টোকেন বাজেট নিরীক্ষা করা হচ্ছে...",
    "classify": "মামলার আইনি ধরণ নির্ধারণ করা হচ্ছে...",
    "extract": "মূল তথ্যমালা বিশ্লেষণ করা হচ্ছে...",
    "dialogue": "আইনি ফলো-আপ প্রস্তুত করা হচ্ছে...",
    "generate_templates": "আইনি পথরেখা ও পরামর্শ প্রস্তুত করা হচ্ছে..."
}

async def run_intake_stream(
    transcript: str,
    audio_path: Optional[str] = None,
    existing_state: Optional[Dict[str, Any]] = None,
    is_continuation: bool = False
):
    """
    Native LangGraph v2 streaming generator using odhikar_graph.astream_events(state, version='v2').
    Yields live node execution lifecycle updates, real-time LLM token streams (on_chat_model_stream),
    and the final structured session state without synthetic delays or LangSmith dependency.
    """
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
        "rights_explanation": None,
        "draft_complaint": None,
        "referral_clinic": None,
        "referral_slot": None,
        "chat_history": list(existing_state.get("chat_history", [])) if existing_state else []
    }

    if transcript and transcript.strip():
        state["chat_history"].append({
            "role": "user",
            "content": transcript.strip()
        })

    current_state = dict(state)
    tokens_streamed: List[str] = []

    # Stream graph execution natively using LangGraph v2 events
    async for event in odhikar_graph.astream_events(state, version="v2"):
        kind = event.get("event")
        node = event.get("metadata", {}).get("langgraph_node")

        # 1. Native Real-Time LLM Token Streaming
        if kind == "on_chat_model_stream":
            # Stream tokens directly to user chat for conversational dialogue nodes
            if node == "dialogue":
                chunk = event.get("data", {}).get("chunk")
                if chunk and hasattr(chunk, "content") and isinstance(chunk.content, str) and chunk.content:
                    tokens_streamed.append(chunk.content)
                    yield {
                        "type": "token",
                        "content": chunk.content
                    }

        # 2. Node lifecycle start
        elif kind == "on_chain_start":
            node_name = event.get("name")
            if node_name in NODE_START_LABELS_BN:
                yield {
                    "type": "node_update",
                    "node": node_name,
                    "label": NODE_START_LABELS_BN[node_name],
                    "data": None
                }

        # 3. Node lifecycle completion
        elif kind == "on_chain_end":
            node_name = event.get("name")
            if node_name in NODE_LABELS_BN:
                node_output = event.get("data", {}).get("output")
                if isinstance(node_output, dict):
                    current_state.update(node_output)
                label = NODE_LABELS_BN.get(node_name, f"{node_name} সম্পন্ন")
                yield {
                    "type": "node_update",
                    "node": node_name,
                    "label": label,
                    "data": node_output
                }

    # Finalize chat history
    history = list(current_state.get("chat_history", []))
    final_assistant_msg = ""
    if current_state.get("safety_flag"):
        final_assistant_msg = current_state.get("safety_message") or "জরুরি নিরাপত্তা ব্রেক-আউট সক্রিয় করা হয়েছে।"
    elif current_state.get("requires_continuation"):
        final_assistant_msg = current_state.get("continuation_prompt") or "টোকেন বিশ্লেষণ অনুমতির অপেক্ষা।"
    elif current_state.get("follow_up_question"):
        final_assistant_msg = current_state.get("follow_up_question")
    elif current_state.get("is_complete"):
        cat = current_state.get("category")
        if cat == "out_of_scope":
            final_assistant_msg = "আপনার বিবরণটি পর্যালোচনা করা হয়েছে। এটি আমাদের লিগ্যাল এইডের আওতাভুক্ত না হলেও সম্ভাব্য পদক্ষেপের পরামর্শ প্রদান করা হয়েছে।"
        else:
            final_assistant_msg = (
                f"ধন্যবাদ। আপনার সম্পূর্ণ বিবরণ ও উত্তরের ভিত্তিতে ব্যক্তিগত আইনি অধিকার ও পথরেখা প্রস্তুত করা হয়েছে। "
                f"নিকটস্থ পরামর্শ কেন্দ্র: {current_state.get('referral_clinic')} ({current_state.get('referral_slot')})।"
            )

    if final_assistant_msg:
        history.append({
            "role": "assistant",
            "content": final_assistant_msg
        })
    current_state["chat_history"] = history

    # If no tokens were streamed live (e.g. is_complete reached, safety breakout, or fallback),
    # stream the final message tokens so the frontend receives the assistant's text
    if not tokens_streamed and final_assistant_msg:
        yield {"type": "token", "content": final_assistant_msg}

    yield {"type": "final_state", "data": current_state}


