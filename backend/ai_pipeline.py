import os
from typing import TypedDict, Optional, List, Dict, Any
from pydantic import BaseModel, Field

from dotenv import load_dotenv

env_path = os.path.join(os.path.dirname(__file__), ".env")
if os.path.exists(env_path):
    load_dotenv(dotenv_path=env_path)
else:
    load_dotenv()

from langgraph.graph import StateGraph, END
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

# Pydantic schema for structured dynamic dialogue evaluation (Problem -> Cause -> History -> Impact -> Desired Solution)
class IntakeDialogueOutput(BaseModel):
    is_complete: bool = Field(
        description="Set to True ONLY if the client has sufficiently answered the essential dimensions of their grievance (Problem, Cause, History, Impact, Desired Solution) or cannot provide further information. Set to False if essential stages (such as why the dispute occurred) are still unanswered."
    )
    current_stage: str = Field(
        description="The stage currently being examined: 'problem', 'cause', 'history', 'impact', 'desired_solution', or 'complete'"
    )
    stages_covered: List[str] = Field(
        default_factory=list,
        description="List of stages covered so far, e.g. ['problem', 'cause']"
    )
    missing_aspect: Optional[str] = Field(
        None,
        description="Short description in Bengali of what is still missing (e.g. 'ভরণপোষণ বন্ধ হওয়ার মূল কারণ', 'কাবিননামা ও পূর্ববর্তী সালিশ')"
    )
    follow_up_question: Optional[str] = Field(
        None,
        description="If is_complete is False: an empathetic, conversational question in spoken Bengali (কথ্য বাংলা) asking for the next unaddressed stage in the Problem → Cause → History → Impact → Desired Solution flow. If is_complete is True: null."
    )
    suggested_replies: Optional[List[str]] = Field(
        None,
        description="If is_complete is False: exactly 3 to 4 natural Bengali quick-reply options directly tailored to the follow_up_question. If is_complete is True: null."
    )
    newly_identified_facts: Optional[Dict[str, Any]] = Field(
        None,
        description="Any newly extracted case facts (e.g. respondent, marriage_date, dower_amount, current_status, evidence, children, unpaid_wages_claim, address)"
    )

dialogue_llm = llm.with_structured_output(IntakeDialogueOutput)

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
    current_stage: Optional[str]
    stages_covered: Optional[List[str]]
    missing_fields: List[str]
    follow_up_question: Optional[str]
    suggested_replies: Optional[List[str]]
    extra_question_asked: Optional[bool]
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
    
    prev_safety_flag = bool(state.get("safety_flag", False))
    prev_safety_msg = state.get("safety_message")

    text_to_eval = state.get("transcript", "")
    if not text_to_eval:
        return {
            "safety_flag": prev_safety_flag,
            "safety_message": prev_safety_msg
        }

    prompt = ChatPromptTemplate.from_messages([
        ("system", prompts.SAFETY_SYSTEM_PROMPT),
        ("user", "{text}")
    ])
    try:
        res = llm.invoke(prompt.format_messages(text=text_to_eval))
        is_danger = ("DANGER" in res.content.upper()) or prev_safety_flag
        return {
            "safety_flag": is_danger,
            "safety_message": (prev_safety_msg or templates.RIGHTS_EXPLANATIONS["safety_escalation"]) if is_danger else None
        }
    except Exception as e:
        print(f"[Safety LLM Error] {e}")
        err_info = parse_llm_error(e)
        return {
            "safety_flag": prev_safety_flag,
            "llm_error": err_info["message_bn"],
            "llm_error_details": err_info
        }

def token_budget_node(state: IntakeState) -> Dict[str, Any]:
    """
    Checks if token consumption exceeds the threshold.
    If yes and user has not confirmed continuation yet, pauses generation and asks for continuation.
    Applies when the initial narrative on Turn 1 exceeds the budget, or if a single input message exceeds it.
    """
    if state.get("llm_error"):
        return {}
    tokens = state.get("estimated_tokens", 0)
    confirmed = state.get("is_continuation_confirmed", False)
    turn_count = state.get("turn_count", 1)
    current_input_tokens = estimate_tokens(state.get("transcript", ""))
    
    exceeds_budget = (turn_count == 1 and tokens > TOKEN_BUDGET_LIMIT) or (current_input_tokens > TOKEN_BUDGET_LIMIT)
    
    if exceeds_budget and not confirmed:
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
    latest_transcript = (state.get("transcript") or "").strip().lower()
    lower_eval = text_to_eval.strip().lower()

    # Fast-path keyword shortcut for land dispute selection (e.g. from disambiguation chips or direct submission)
    land_keywords = [
        "জমিজমা সংক্রান্ত", "জমিজমা", "জমির বিরোধ", "জমি নিয়ে বিরোধ", "জমি নিয়ে বিরোধ",
        "সীমানা বেদখল", "জমি দখল", "পৈতৃক জমি", "জমিজমা সংক্রান্ত বিরোধে", "জমিজমা সংক্রান্ত বিরোধ"
    ]
    if any(k in latest_transcript for k in land_keywords) or any(k in lower_eval for k in ["জমিজমা সংক্রান্ত বিরোধ", "জমিজমা সংক্রান্ত"]):
        return {
            "category": "land_dispute",
            "confidence": 95,
            "classification_reason": "ব্যবহারকারীর জমিজমা সংক্রান্ত বিষয় নির্বাচন",
            "disambiguation_needed": False
        }
    
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
    q = (question or "").strip()
    target = (missing_fields[0] if missing_fields and len(missing_fields) > 0 else "").strip()

    # 0a. Desired Solution / Legal Remedy (Court vs Salish)
    if (
        target == "desired_solution" or
        any(w in q for w in ["সালিশের মাধ্যমে", "আদালতে মামলা", "মামলা করতে চান", "আপস চান", "আইনি সমাধান", "আইনি প্রতিকার", "সালিশ চান"]) or
        (("সালিশ" in q or "আদালত" in q or "মামলা" in q) and ("চান" in q or "প্রতিকার" in q or "সমাধান" in q))
    ):
        if category in ("family_dower_maintenance", "dowry"):
            return [
                "পারিবারিক আদালতে মামলা করে দেনমোহর ও বকেয়া ভরণপোষণ আদায় করতে চাই",
                "স্থানীয় ইউনিয়ন পরিষদে চেয়ারম্যান বা মেম্বারের মাধ্যমে শান্তিপূর্ণ সালিশ চাই",
                "সন্তানের নিয়মিত মাসিক খরচ ও দেনমোহরের বকেয়া টাকা পরিশোধ করতে হবে",
                "প্রথমে আইনজীবীর মাধ্যমে আইনি নোটিশ পাঠাতে চাই"
            ]
        elif category == "land_dispute":
            return [
                "দেওয়ানি আদালতে মামলা করে জমির দখল ও স্বত্ব উদ্ধার করতে চাই",
                "ইউনিয়ন পরিষদে মেম্বার বা চেয়ারম্যানের কাছে সালিশ হয়েছিল কিন্তু সমাধান হয়নি",
                "প্রথমে স্থানীয় মুরুব্বিদের মাধ্যমে আপস-মীমাংসার চেষ্টা করতে চাই",
                "জমিতে যাতে কোনো স্থাপনা না করে সেজন্য আদালতের নিষেধাজ্ঞা চাই"
            ]
        elif category == "unpaid_wages":
            return [
                "শ্রম আদালতে বা লিগ্যাল এইডে মামলা করে পুরো বকেয়া মজুরি আদায় করতে চাই",
                "সর্দার বা স্থানীয় মেম্বারের উপস্থিতিতে দেনদরবার করে টাকা পেতে চাই",
                "মালিকের বিরুদ্ধে থানায় বা শ্রম পরিদপ্তরে লিখিত অভিযোগ দিতে চাই",
                "কোনো ঝামেলা ছাড়াই বকেয়া টাকা পরিশোধ করে দিলে মিটে যাবে"
            ]
        else:
            return [
                "আদালতে মামলা করে আইনি প্রতিকার পেতে চাই",
                "স্থানীয় সালিশে বসে আপস-মীমাংসা করতে চাই",
                "আইনি নোটিশ পাঠিয়ে সমাধানের সুযোগ দিতে চাই",
                "লিগ্যাল এইড ক্লিনিকের মাধ্যমে পরামর্শ নিতে চাই"
            ]

    # 0b. Cause of maintenance / family dispute ("ভরণপোষণ নিয়ে ঝামেলা হয়েছে কেন?")
    if (
        ("ভরণপোষণ" in q and ("ঝামেলা" in q or "কেন" in q or "কারণ" in q)) or
        ("ঝামেলা হয়েছে কেন" in q or "ঝামেলা হয়েছে কেন" in q or "বিরোধের কারণ" in q or "বিরোধের মূল কারণ" in target or target == "cause" and category in ("family_dower_maintenance", "dowry"))
    ):
        return [
            "যৌতুকের দাবিতে ঝগড়া করে খরচ দেওয়া বন্ধ করেছে",
            "স্বামী দ্বিতীয় বিয়ে করে আমাদের ছেড়ে চলে গেছে",
            "শ্বশুরবাড়ির অত্যাচার ও বনিবনা না হওয়ায় আলাদা হয়ে গেছে",
            "বিনা কারণে হঠাৎ ঝগড়া করে বাড়ি থেকে তাড়িয়ে দিয়েছে"
        ]

    # 1. Kabinnama / Marriage document evidence
    if (
        ("কাবিন" in q or "কাবিননামা" in q or "কাবিননামা" in target) or
        (("দলিল" in q or "কাগজ" in q) and category in ("family_dower_maintenance", "dowry"))
    ):
        if any(w in q for w in ["মামলা", "প্রস্তুত", "আদালত"]):
            return [
                "হ্যাঁ, কাবিননামা ও প্রয়োজনীয় সব কাগজ আমার কাছে প্রস্তুত আছে",
                "কাবিননামা স্বামীর কাছে রেখে দিয়েছে, আমাকে দেয়নি",
                "রেজিস্ট্রি হয়েছিল, কাজী অফিসে কাবিনের নকল পাওয়া যাবে",
                "আমাদের কোনো লিখিত কাবিননামা বা বিয়ের কাগজ নেই"
            ]
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
    if ("বিয়ে" in q or "বিয়ে" in q) and ("সন" in q or "কবে" in q or "সাল" in q or "বছর" in q or "তারিখ" in q or "বিয়ের সন" in target or target == "history" and category in ("family_dower_maintenance", "dowry")):
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

    # 7a. Land Possession & Nature of Dispute
    if (
        category == "land_dispute" and 
        ("দখল" in q or "দখলে" in q or "ওয়ারিশ" in q or "সীমানা" in q or "বেদখল" in q or "দখল" in target or "কারণ" in target or target == "cause")
    ):
        return [
            "জমিটি বর্তমানে আমাদের দখলেই রয়েছে",
            "প্রতিপক্ষ জোরপূর্বক জমিটি অবৈধভাবে দখল করে রেখেছে",
            "পৈতৃক ওয়ারিশ ও অংশ বণ্টন নিয়ে বিরোধ চলছে",
            "জমির সীমানা নির্ধারণ ও বেদখল নিয়ে বিরোধ তৈরি হয়েছে"
        ]

    # 7b. Land Deeds / Records / Evidence
    if (
        (category == "land_dispute" or "জমি" in q) and 
        ("দলিল" in q or "খতিয়ান" in q or "পর্চা" in q or "কাগজ" in q or "রেজিস্ট্রি" in q or "দলিল" in target or "খতিয়ান" in target or target == "history")
    ):
        return [
            "জমির মূল রেজিস্ট্রি দলিল আমাদের কাছে সংরক্ষিত আছে",
            "জমির পর্চা ও খতিয়ানের সত্যায়িত কপি আছে",
            "জমির মূল কাগজপত্র বা দলিল প্রতিপক্ষের দখলে আটকে আছে",
            "আমাদের কাছে বর্তমানে কোনো বৈধ দলিল বা পর্চা নেই"
        ]

    # 7c. Land Salish / Opponent / Chairman / Member
    if (
        (category == "land_dispute" or "জমি" in q) and 
        ("সালিশ" in q or "চেয়ারম্যান" in q or "চেয়ারম্যান" in q or "মেম্বার" in q or "প্রতিপক্ষ" in q or "শরিক" in q or "সালিশ" in target or "বিবাদী" in target or "বিরোধ" in target or target in ("impact", "desired_solution"))
    ):
        return [
            "ইউনিয়ন পরিষদে মেম্বার বা চেয়ারম্যানের কাছে সালিশ হয়েছিল কিন্তু সমাধান হয়নি",
            "পারিবারিক শরিক ও আত্মীয়দের সাথে জমি নিয়ে বিরোধ",
            "বাইরের প্রভাবশালী দখলদারদের সাথে বিরোধ",
            "স্থানীয়ভাবে এখনো কোনো সালিশ বা মীমাংসার বৈঠক হয়নি"
        ]

    # 7d. General Land Dispute fallback
    if category == "land_dispute" or "জমি" in q:
        return [
            "জমিটি বর্তমানে আমাদের দখলেই রয়েছে",
            "জমির মূল রেজিস্ট্রি দলিল আমাদের কাছে সংরক্ষিত আছে",
            "প্রতিপক্ষ জোরপূর্বক জমিটি অবৈধভাবে দখল করে রেখেছে",
            "স্থানীয়ভাবে এখনো কোনো সালিশ বা মীমাংসার বৈঠক হয়নি"
        ]

    # 8. Children / Maintenance
    if "সন্তান" in q or "বাচ্চা" in q or "ভরণপোষণ" in q:
        return [
            "হ্যাঁ, আমাদের ১টি সন্তান আছে এবং সে আমার কাছেই থাকে",
            "হ্যাঁ, আমাদের ২টি সন্তান আছে এবং তাদের দেখাশোনা আমি করছি",
            "না, আমাদের কোনো সন্তান নেই",
            "স্বামী সন্তান বা আমার কারও কোনো ভরণপোষণ বা খরচ দেয় না"
        ]


    # 10. Disambiguation
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

def check_uncertainty_or_missing_doc(text: str) -> Tuple[bool, Optional[str]]:
    """Detects if client indicates lack of documents/proof or inability to remember in response to a question."""
    if not text:
        return False, None
    t = text.strip().lower()
    
    # Do not treat long multi-sentence narrative (> 20 words) as an uncertainty chip response
    if len(t.split()) > 20:
        return False, None

    # 1. Direct document absent / lost / unknown location patterns
    doc_patterns = [
        "ডকুমেন্ট নেই", "ডকুমেন্ট নাই", "ডকুমেন্টস নেই", "ডকুমেন্টস নাই", "কোনো ডকুমেন্ট", "কোন ডকুমেন্ট",
        "কাগজ নেই", "কাগজ নাই", "কাগজপত্র নেই", "কাগজপত্র নাই", "কোনো কাগজ", "কোন কাগজ",
        "দলিল নেই", "দলিল নাই", "দলিলপত্র নেই", "কোনো দলিল", "দলিল কোথায়", "দলিল পাচ্ছি না", "দলিল হারিয়ে",
        "প্রমাণ নেই", "প্রমাণ নাই", "কোনো প্রমাণ", "লিখিত প্রমাণ নেই", "লিখিত প্রমাণ নাই",
        "লিখিত কিছু নেই", "লিখিত চুক্তি নেই", "চুক্তিপত্র নেই", "লিখিত নাই",
        "কাবিন নেই", "কাবিন নাই", "কাবিননামা নেই", "কাবিননামা নাই", "কোনো কাবিন নেই",
        "কাবিন কোথায়", "কাবিননামা কোথায়", "কাবিন পাচ্ছি না", "কাবিননামা পাচ্ছি না", "কাবিন হারিয়ে", "কাবিননামা হারিয়ে",
        "কাবিন মনে নেই", "কাবিননামা মনে নেই", "কাবিননামা মনে নাই",
        "কোথায় আছে মনে পড়ছে না", "কোথায় আছে মনে নাই", "কোথায় আছে জানি না", "কোথায় আছে মনে নেই",
        "স্লিপ নেই", "স্লিপ নাই", "খাতা নেই", "হাজিরা খাতা নেই",
        "document nei", "document nai", "no document", "no documents",
        "kagoj nei", "kagoj nai", "kono kagoj", "no proof", "no paper", "no papers", "dolil nei"
    ]
    for p in doc_patterns:
        if p in t:
            return True, "document_nei"

    # If user explicitly refers to document + uncertain/lost
    has_doc_ref = any(w in t for w in ["কাবিন", "কাবিননামা", "দলিল", "কাগজ", "খতিয়ান", "খতিয়ান", "পর্চা", "স্লিপ"])
    has_uncertain = any(w in t for w in ["কোথায়", "মনে পড়ছে না", "মনে পরছে না", "মনে নেই", "মনে নাই", "পাচ্ছি না", "খুঁজে পাচ্ছি না", "হারিয়ে", "নেই", "নাই", "জানি না"])
    if has_doc_ref and has_uncertain:
        return True, "document_nei"

    # 2. General inability to remember patterns
    memory_patterns = [
        "মনে নেই", "মনে নাই", "মনে পরছে না", "মনে পড়ছে না",
        "সঠিক মনে নেই", "সঠিক মনে নাই", "নির্দিষ্ট মনে নেই",
        "জানা নেই", "জানা নাই", "সঠিক জানা নেই", "নির্দিষ্ট জানা নেই",
        "বলতে পারছি না", "বলতে পারব না", "বলতে পারি না",
        "ভুলে গেছি", "ভুলে গেসি", "খেয়াল নেই", "খেয়াল নেই",
        "মনে করতে পারছি না", "মনে করতে পারি না",
        "mone nei", "mone nai", "sothik mone nei", "mone porche na",
        "jana nei", "jana nai", "dont know", "don't know", "dont remember", "don't remember", "not sure"
    ]
    for p in memory_patterns:
        if p in t:
            return True, "mone_nei"
            
    return False, None

def generate_extra_fallback_question(
    match_type: str,
    category: Optional[str] = None,
    previous_question: Optional[str] = None
) -> Tuple[str, List[str]]:
    """
    Generates an empathetic extra question and tailored suggested replies
    when client indicates lack of documents or inability to remember.
    """
    cat = (category or "").lower()
    prev_q = (previous_question or "").lower()

    # If question was about documents OR client indicated document uncertainty:
    is_doc_context = (
        match_type == "document_nei" or 
        any(w in prev_q for w in ["কাবিন", "কাবিননামা", "দলিল", "কাগজ", "খতিয়ান", "খতিয়ান", "পর্চা", "স্লিপ", "হাজিরা", "রেজিস্ট্রি"])
    )

    if is_doc_context:
        if cat in ("family_dower_maintenance", "dowry") or "কাবিন" in prev_q or "বিয়ে" in prev_q or "বিয়ে" in prev_q:
            question = (
                "লিখিত কাবিননামা বা কাগজ সাথে না থাকলেও কোনো অসুবিধা নেই, আইন অনুযায়ী আপনার দেনমোহর ও ভরণপোষণের অধিকার সম্পূর্ণ সংরক্ষিত। "
                "বিয়ের সময় কি কোনো কাজী উপস্থিত ছিলেন, অথবা বিয়ের কোনো প্রত্যক্ষদর্শী সাক্ষী বা কাজী অফিসের এলাকা কি জানা আছে?"
            )
            chips = [
                "কাজী অফিসের নাম ও এলাকা জানা আছে",
                "বিয়ের প্রত্যক্ষদর্শী সাক্ষী আছেন",
                "পরিবার ও আত্মীয়রা বিয়েতে ছিলেন",
                "কোনো কাজী বা সাক্ষী নেই"
            ]
            return question, chips
        elif cat == "unpaid_wages" or "মজুরি" in prev_q or "বেতন" in prev_q or "কাজ" in prev_q:
            question = (
                "কাজের লিখিত চুক্তি বা স্লিপ না থাকলেও শ্রম আইন অনুযায়ী আপনি বকেয়া পাওয়ার অধিকারী। "
                "কাজের জায়গায় কি কোনো সহকর্মী, সর্দার বা স্থানীয় কেউ আছেন যিনি আপনার কাজের সাক্ষী দিতে পারবেন?"
            )
            chips = [
                "সহকর্মী ও সর্দার সাক্ষী আছেন",
                "গ্রামের মেম্বার ও লোকজন জানেন",
                "মালিকের নাম ও ফোন নম্বর আছে",
                "সরাসরি কোনো সাক্ষী নেই"
            ]
            return question, chips
        elif cat == "land_dispute" or "জমি" in prev_q or "দলিল" in prev_q:
            question = (
                "জমির মূল দলিল আপনার কাছে সংরক্ষিত না থাকলেও সমস্যা নেই। "
                "জমিটি কি বর্তমানে আপনাদের দখলে আছে অথবা স্থানীয় ইউনিয়ন মেম্বার বা প্রতিবেশীরা কি দখলের বিষয়ে জানেন?"
            )
            chips = [
                "জমিটি আমাদের দখলে আছে",
                "খাজনার দাখিলা বা রশিদ আছে",
                "মেম্বার ও প্রতিবেশীরা জানেন",
                "কোনো দখল বা কাগজ নেই"
            ]
            return question, chips
        else:
            question = (
                "লিখিত কোনো কাগজপত্র না থাকলেও অসুবিধা নেই। "
                "এই ঘটনার বিষয়ে কি কোনো মৌখিক সাক্ষী বা স্থানীয় মেম্বার/গণ্যমান্য ব্যক্তি অবগত আছেন?"
            )
            chips = [
                "স্থানীয় লোকজন ও মেম্বার জানেন",
                "পরিবারের সদস্যরা সাক্ষী আছেন",
                "মৌখিকভাবে সিদ্ধান্ত হয়েছিল",
                "কোনো মৌখিক সাক্ষী নেই"
            ]
            return question, chips

    # Timeline / Date inquiry:
    if any(w in prev_q for w in ["কবে", "সন", "সাল", "বছর", "তারিখ", "সময়", "কতদিন"]):
        question = (
            "নির্দিষ্ট সন বা তারিখ মনে না থাকলেও কোনো সমস্যা নেই। "
            "আনুমানিক কত বছর আগে ঘটনাটি ঘটেছিল (যেমন ২-৩ বছর নাকি ৫ বছর আগে), অথবা তখনকার কোনো বিশেষ স্মৃতি মনে পড়ে?"
        )
        chips = [
            "আনুমানিক ১ থেকে ২ বছর আগে",
            "আনুমানিক ৩ থেকে ৫ বছর আগে",
            "১০ বছরের বেশি সময় আগে",
            "সঠিক সময় মনে করা যাচ্ছে না"
        ]
        return question, chips

    # Explicit money inquiry (ONLY if question specifically asked for money amount):
    if any(w in prev_q for w in ["কত টাকা", "টাকার পরিমাণ", "দেনমোহর কত", "বেতন কত", "মজুরি কত", "দাবি কত"]):
        question = (
            "সঠিক টাকার অঙ্ক নির্দিষ্ট মনে না থাকলেও কোনো চিন্তা করবেন না। "
            "আনুমানিক বা কাছাকাছি কোনো ধারণা কি আছে (যেমন ৫০ হাজার, ১ লাখ নাকি তার বেশি), অথবা পরিবারের কেউ কি জানেন?"
        )
        chips = [
            "আনুমানিক ৫০ হাজার থেকে ১ লাখ",
            "আনুমানিক ১ থেকে ২ লাখ টাকা",
            "পরিবারের মুরব্বিরা সঠিক জানেন",
            "একদম নির্দিষ্ট মনে নেই"
        ]
        return question, chips

    # General memory fallback:
    question = (
        "এই তথ্যটি নির্দিষ্টভাবে মনে না থাকলেও কোনো সমস্যা নেই। "
        "আপনার পরিবারের কেউ, আত্মীয়স্বজন বা কোনো প্রত্যক্ষদর্শী কি এ বিষয়ে প্রয়োজনীয় তথ্য দিয়ে সাহায্য করতে পারবেন?"
    )
    chips = [
        "বাবার বাড়ির লোকজন তথ্য দিতে পারবেন",
        "স্থানীয় মেম্বার বিষয়টি জানেন",
        "আত্মীয়রা খোঁজ নিয়ে জানাতে পারবেন",
        "কারও কাছেই তথ্য নেই"
    ]
    return question, chips

def get_stage_fallback_question(category: Optional[str], stage: str, missing_item: Optional[str] = None) -> str:
    cat = category or "general"
    if cat == "land_dispute":
        if stage == "cause":
            return "জমিটি নিয়ে বিরোধের সূত্রপাত কীভাবে হয়েছিল এবং জমিটি বর্তমানে কার দখলে আছে?"
        elif stage == "history":
            if missing_item == "documents_for_court" or (missing_item and any(w in missing_item for w in ["মামলা", "কাগজ", "আদালত"])):
                return "দেওয়ানি আদালতে মামলা দায়েরের জন্য জমির মূল রেজিস্ট্রি দলিল, পর্চা বা খতিয়ানের কপি কি আপনার কাছে প্রস্তুত আছে?"
            return "জমির মূল রেজিস্ট্রি দলিল বা খতিয়ান কি আপনাদের কাছে সংরক্ষিত আছে?"
        elif stage == "impact":
            return "জমিটি বেদখল বা বিরোধে থাকায় আপনাদের চাষাবাদ বা বসবাস করতে কী ধরণের সমস্যা বা ক্ষতি হচ্ছে?"
        elif stage == "desired_solution":
            return "এই জমি নিয়ে ইউনিয়ন পরিষদে মেম্বার বা চেয়ারম্যানের কাছে কোনো সালিশ হয়েছিল কি, নাকি আপনারা সরাসরি দেওয়ানি আদালতে মামলা করতে চান?"
        else:
            return "জমিটির দখল ও বিরোধ সম্পর্কে বিস্তারিত জানালে সঠিক আইনি পরামর্শ দেওয়া সহজ হবে।"
    elif cat in ("family_dower_maintenance", "dowry"):
        if stage == "cause":
            return "আপনার স্বামী যে খরচ বা ভরণপোষণ দেওয়া বন্ধ করেছেন, এই ভরণপোষণ নিয়ে ঝামেলা হয়েছে কেন বা কী কারণে উনি আলাদা থাকছেন?"
        elif stage == "history":
            if missing_item == "documents_for_court" or (missing_item and any(w in missing_item for w in ["মামলা", "কাগজ", "আদালত"])):
                return "পারিবারিক আদালতে মামলা দায়েরের জন্য বিয়ের কাবিননামা বা কাজী অফিসের নকল, এবং আপনার ও সন্তানের এনআইডি বা জন্মসনদ প্রয়োজন। এই কাগজপত্রগুলো কি বর্তমানে আপনার কাছে প্রস্তুত আছে?"
            return "আপনাদের বিয়ে আনুমানিক কত বছর আগে হয়েছিল এবং কাবিননামার কাগজটি কার কাছে আছে?"
        elif stage == "impact":
            return "বাচ্চা নিয়ে বর্তমানে বাবার বাড়িতে দিনযাপন করতে আপনার কেমন আর্থিক কষ্ট বা টানাপোড়েন হচ্ছে?"
        elif stage == "desired_solution":
            return "কাবিননামা থাকা আপনার দাবির একটি শক্ত ভিত্তি। এখন আপনি কি স্থানীয় ইউনিয়ন পরিষদে সালিশের মাধ্যমে আপস চান, নাকি সরাসরি পারিবারিক আদালতে মামলা করতে চান?"
        else:
            return "ভরণপোষণ ও পারিবারিক বিরোধের বিষয়ে বিস্তারিত জানালে সঠিক পথরেখা তৈরি করা সম্ভব হবে।"
    elif cat == "unpaid_wages":
        if stage == "cause":
            return "মালিক বা ঠিকাদার কী কারণে আপনার মজুরি বকেয়া রেখেছেন বা কোনো বিরোধ হয়েছিল কি না?"
        elif stage == "history":
            return "আপনি কতদিন সেখানে কাজ করেছেন এবং কাজের দৈনিক হাজিরা খাতা বা স্লিপের কোনো প্রমাণ আছে কি না?"
        elif stage == "impact":
            return "বকেয়া মজুরি না পাওয়ায় আপনার পরিবারে কেমন টানাপোড়েন বা সংসার চালাতে কী ধরণের সমস্যা হচ্ছে?"
        elif stage == "desired_solution":
            return "আপনি কি সর্দার বা স্থানীয় সালিশে দেনদরবার করতে চান, নাকি শ্রম আদালতে বা লিগ্যাল এইডে আইনি প্রতিকার চান?"
        else:
            return "বকেয়া মজুরির বিবরণ জানালে শ্রম অধিকার অনুযায়ী সহায়তার ব্যবস্থা করা যাবে।"
    else:
        return f"আপনার সমস্যাটির সুষ্ঠু সমাধানের জন্য একটি বিষয় জানা প্রয়োজন: {missing_item or 'বিরোধের মূল কারণ'} সম্পর্কে কি বিস্তারিত জানাবেন?"

def dialogue_node(state: IntakeState) -> Dict[str, Any]:
    """Identifies missing facts and formulates a dynamic, context-aware follow-up question."""
    if state.get("llm_error"):
        return {}
    cat = state.get("category")
    turn_count = state.get("turn_count", 1)
    extra_question_asked = state.get("extra_question_asked", False)
    text_to_eval = state.get("client_own_words") or state.get("transcript", "")
    latest_user_text = state.get("transcript", "")
    
    # 1. Structured Stages and Coverage Detection
    stages_order = ["problem", "cause", "history", "impact", "desired_solution"]
    stage_bn_map = {
        "problem": "সমস্যার মূল ধরণ",
        "cause": "বিরোধের কারণ ও সূত্রপাত (কী কারণে ঝামেলা শুরু হলো / জমি কীভাবে বেদখল হলো / ভরণপোষণ কেন বন্ধ হলো)",
        "history": "ইতিহাস, প্রমাণাদি/দলিল ও পূর্ববর্তী সালিশ (যেমন কাবিননামা, রেজিস্ট্রি দলিল/খতিয়ান, স্থানীয় সালিশ)",
        "impact": "বর্তমান প্রভাব ও পরিস্থিতি (কোথায় থাকছেন, আর্থিক অনটন, জমিতে যেতে বাধা)",
        "desired_solution": "প্রত্যাশিত আইনি প্রতিকার বা সমাধান"
    }

    existing_covered = list(state.get("stages_covered") or [])
    if not existing_covered:
        existing_covered = ["problem"]

    prev_stage = state.get("current_stage")
    if prev_stage and prev_stage in stages_order and prev_stage not in existing_covered:
        existing_covered.append(prev_stage)

    # Fact-based detection of stages from accumulated text
    lower_all = (text_to_eval + " " + latest_user_text).lower()
    
    # 1. Cause: specific trigger/reason for conflict or separation
    if any(w in lower_all for w in [
        "যৌতুক", "দ্বিতীয় বিয়ে", "দ্বিতীয় বিয়ে", "জোরপূর্বক দখল", "বেদখল", "দখল করে",
        "ঝগড়া করে আলাদা", "ঝগড়া করে আলাদা", "মেরে বের করে", "তাড়িয়ে দিয়েছে", "তাড়িয়ে দিছে",
        "বের করে দিয়েছে", "বের করে দিছে", "বাড়ি থেকে বের", "বাড়ি থেকে বের", "বাড়ি ছাড়তে বাধ্য", "বাড়ি ছাড়তে বাধ্য"
    ]):
        if "cause" not in existing_covered:
            existing_covered.append("cause")

    # 2. History & Evidence: requires knowing document possession or local salish (not merely mentioning the word 'কাবিন' or 'বিয়ে')
    has_evidence_info = any(w in lower_all for w in [
        "কাবিননামা আছে", "কাবিন আছে", "কাবিননামা বাবার", "কাবিন বাবার", "কাবিননামা স্বামীর",
        "কাবিন স্বামীর", "কাবিন হারিয়ে", "কাবিননামা হারিয়ে", "কাবিন নেই", "কাবিন নাই", "কাজী অফিসে",
        "কোথায় আছে মনে পড়ছে না", "কোথায় আছে মনে নাই", "কোথায় আছে জানি না", "মনে পড়ছে না", "মনে পরছে না", "খুঁজে পাচ্ছি না",
        "কাজী অফিসের এলাকা", "কোনো সাক্ষী নেই", "কোনো কাজী বা সাক্ষী নেই", "সাক্ষী বা কাজী নেই",
        "দলিল আছে", "দলিল সংরক্ষিত", "দলিল প্রতিপক্ষের", "দলিল নেই", "দলিল নাই", "খতিয়ান আছে",
        "হাজিরা খাতা", "সর্দার সাক্ষী", "সহকর্মী সাক্ষী", "মৌখিক চুক্তি", "সালিশ হয়েছিল", "সালিশ হয়েছে",
        "কাগজপত্র প্রস্তুত", "কাগজ প্রস্তুত", "সব কাগজ আমার কাছে", "সব কাগজপত্র আমার কাছে",
        "প্রয়োজনীয় সব কাগজ", "প্রয়োজনীয় সব কাগজ", "নকল তুলতে হবে", "কাজী অফিস থেকে তুলতে",
        "কাজী অফিস থেকে নকল", "কাগজ বাবার", "কাগজপত্র বাবার", "কাগজ স্বামীর", "কাগজপত্র স্বামীর",
        "কোনো কাগজপত্র নেই", "কোনো কাগজ নেই", "কোনো লিখিত কাবিননামা", "কোনো লিখিত কাগজ", "কাগজপত্র নেই"
    ])
    if has_evidence_info:
        if "history" not in existing_covered:
            existing_covered.append("history")

    # 3. Impact: current hardship, living condition, or residence
    if any(w in lower_all for w in ["বাবার বাড়ি", "বাবার বাড়ি", "বাচ্চা নিয়ে", "বাচ্চা নিয়ে", "কষ্টে দিন", "অনাহারে", "আশ্রয়হীন", "জমিতে যেতে বাধা"]):
        if "impact" not in existing_covered:
            existing_covered.append("impact")

    # 4. Desired Solution: specific remedy or legal route confirmed
    if any(w in lower_all for w in [
        "মামলা করতে চাই", "মামলা করে", "মামলা দায়ের", "মামলা দায়ের",
        "সালিশের মাধ্যমে", "শান্তিপূর্ণ মীমাংসা", "সালিশ চাই", "মীমাংসা চাই",
        "আইনি নোটিশ", "আদালতে যাব", "আদালতে যেতে",
        "নিয়মিত মাসিক ভরণপোষণ", "নিয়মিত ভরণপোষণ", "বকেয়া ভরণপোষণ আদায়", "বকেয়া ভরণপোষণ আদায়",
        "সালিশ হয়েছিল কিন্তু সমাধান হয়নি", "সালিশ হয়েছিল", "সমাধান হয়নি", "চেয়ারম্যানের কাছে সালিশ", "মেম্বার বা চেয়ারম্যানের কাছে সালিশ"
    ]):
        if "desired_solution" not in existing_covered:
            existing_covered.append("desired_solution")

    # 2. If an extra fallback question was ALREADY asked and client just responded to it:
    if extra_question_asked:
        if "history" not in existing_covered:
            existing_covered.append("history")
        
        remaining_stages = [s for s in stages_order if s not in existing_covered]
        if "desired_solution" in remaining_stages and turn_count < 5:
            extra_q = get_stage_fallback_question(cat, "desired_solution")
            extra_chips = generate_suggested_replies(question=extra_q, missing_fields=["desired_solution"], category=cat)
            return {
                "is_complete": False,
                "current_stage": "desired_solution",
                "stages_covered": existing_covered,
                "missing_fields": ["desired_solution"],
                "follow_up_question": extra_q,
                "suggested_replies": extra_chips,
                "extra_question_asked": False
            }
        else:
            return {
                "is_complete": True,
                "current_stage": "complete",
                "stages_covered": existing_covered,
                "missing_fields": [],
                "follow_up_question": None,
                "suggested_replies": None,
                "extra_question_asked": False
            }

    # 3. Check if client's response expresses "mone nei" or "document nei"
    is_uncertain, match_type = check_uncertainty_or_missing_doc(latest_user_text)
    if is_uncertain and match_type:
        previous_q = state.get("follow_up_question")
        if not previous_q and state.get("chat_history"):
            for m in reversed(state.get("chat_history", [])):
                if m.get("role") == "assistant" and m.get("content") and not m.get("content").startswith("⚠️"):
                    previous_q = m.get("content")
                    break

        extra_q, extra_chips = generate_extra_fallback_question(
            match_type=match_type,
            category=cat,
            previous_question=previous_q
        )

        return {
            "is_complete": False,
            "current_stage": state.get("current_stage") or "history",
            "stages_covered": existing_covered,
            "follow_up_question": extra_q,
            "suggested_replies": extra_chips,
            "extra_question_asked": True,
            "missing_fields": state.get("missing_fields", [])
        }

    # 4. Disambiguation if category is unclassifiable
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
                "extra_question_asked": False,
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
            ],
            "extra_question_asked": False
        }

    # 5. Generous safety ceiling against runaway loops (e.g. if user sends unrelated single letters/noise repeatedly)
    if turn_count >= 7:
        return {
            "is_complete": True,
            "missing_fields": [],
            "follow_up_question": None,
            "suggested_replies": None,
            "extra_question_asked": False
        }

    remaining_stages = [s for s in stages_order if s not in existing_covered]
    target_stage = remaining_stages[0] if remaining_stages else "complete"

    # Enforce thorough intake depth:
    # If the user reaches completion or selects desired_solution without clarifying essential documents/evidence,
    # route to 'history' to ask about required documentation before completing!
    if (target_stage == "complete" or "desired_solution" in existing_covered) and not has_evidence_info and turn_count < 6:
        target_stage = "history"

    # If both desired_solution AND essential documentation are covered, complete!
    if (target_stage == "complete" and turn_count >= 3 and has_evidence_info) or (turn_count >= 4 and "desired_solution" in existing_covered and has_evidence_info) or (turn_count >= 4 and len(existing_covered) >= 4 and has_evidence_info) or (turn_count >= 6):
        return {
            "is_complete": True,
            "current_stage": "complete",
            "stages_covered": existing_covered,
            "missing_fields": [],
            "follow_up_question": None,
            "suggested_replies": None,
            "extra_question_asked": False
        }

    # Assemble known facts extracted so far
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
    if state.get("current_status"):
        known.append(f"বর্তমান অবস্থা/দখল: {state.get('current_status')}")
    if state.get("children"):
        known.append(f"সন্তান: {state.get('children')}")
    if state.get("evidence"):
        known.append(f"প্রমাণ/দলিল: {state.get('evidence')}")
    if state.get("address"):
        known.append(f"ঠিকানা: {state.get('address')}")

    # Format recent conversation history for deep context
    recent_history = state.get("chat_history", [])[-6:]
    formatted_history = "\n".join([
        f"{'ক্লায়েন্ট' if m.get('role') == 'user' else 'প্যারালিগ্যাল সহকারী'}: {m.get('content', '')}"
        for m in recent_history if m.get("content")
    ])

    target_stage_bn = stage_bn_map.get(target_stage, target_stage)
    stages_covered_bn = ", ".join([f"{s} ({stage_bn_map.get(s, s)})" for s in existing_covered])

    dialogue_prompt = ChatPromptTemplate.from_messages([
        ("system", prompts.INTAKE_DIALOGUE_SYSTEM_PROMPT),
        ("user", (
            "মামলার ক্যাটাগরি: {category}\n\n"
            "ক্লায়েন্টের সম্পূর্ণ বিবরণ (Cumulative Story):\n{client_narrative}\n\n"
            "সাম্প্রতিক কথোপকথন রেকর্ড:\n{chat_history}\n\n"
            "ইতিমধ্যে প্রতিষ্ঠিত ও সংগৃহীত তথ্যসমূহ:\n{known_facts}\n\n"
            "ইতিমধ্যে সম্পন্ন হওয়া ধাপসমূহ (Covered Stages): {stages_covered_bn}\n"
            "পরবর্তী লক্ষ্য ধাপ (Target Stage): {target_stage} ({target_stage_bn})\n\n"
            "ক্লায়েন্টের সর্বশেষ উত্তর: {latest_user_text}\n"
            "বর্তমান টার্ন সংখ্যা: {turn_count}\n\n"
            "টাস্ক নির্দেশিকা:\n"
            "1. Problem → Cause → History → Impact → Desired Solution ধাপসমূহ অনুযায়ী পর্যায়ক্রমে এগোতে হবে।\n"
            "2. মানবিক সেতুবন্ধন (Empathetic Bridging): ক্লায়েন্টের সর্বশেষ বক্তব্যটি (যেমন 'আমি টাকা চেয়েছিলাম' বা 'কাবিননামা বাবার বাড়িতে আছে') প্রথমে সংক্ষিপ্ত সহানুভূতি ও উপলব্ধির সাথে স্বীকার করুন (যেমন সংসারের খরচের টাকা চাওয়ায় এমন নির্যাতন করা অন্যায়, অথবা কাবিননামা থাকা অধিকার প্রতিষ্ঠার শক্ত প্রমাণ), তারপর বুঝিয়ে বলুন পরবর্তী তথ্যটি আইনত তাদের অধিকার প্রতিষ্ঠায় কীভাবে প্রয়োজন। হুট করে সরাসরি আমলাতান্ত্রিক প্রশ্ন করবেন না।\n"
            "3. ইতিমধ্যে যে ধাপগুলো সম্পন্ন হয়েছে ({stages_covered_bn}) সে বিষয়ে পুনরাবৃত্তিমূলক প্রশ্ন করবেন না।\n"
            "4. পরবর্তী লক্ষ্য ধাপ '{target_stage}' ({target_stage_bn}) সম্পর্কে কথ্য বাংলায় একটিমাত্র আন্তরিক ও প্রাসঙ্গিক প্রশ্ন করুন:\n"
            "   - যদি target_stage='history' হয়:\n"
            "     * যদি ক্লায়েন্ট ইতিমধ্যে মামলা করার বা সালিশের কথা বলে থাকেন (যেমন 'পারিবারিক আদালতে মামলা করতে চাই' বা 'সালিশ চাই'), তবে সেই প্রতিকার পাওয়ার জন্য প্রয়োজনীয় মৌলিক কাগজপত্র (যেমন পারিবারিক আদালতের জন্য মূল কাবিননামা বা কাজী অফিসের নকল, আবেদনকারী ও সন্তানের এনআইডি/জন্মসনদ) তাঁদের কাছে বর্তমানে প্রস্তুত আছে কি না তা আন্তরিকভাবে জানতে চান।\n"
            "     * অন্যথায় দেনমোহর/ভরণপোষণের ক্ষেত্রে কাবিননামা কার কাছে আছে জানতে চান; জমির ক্ষেত্রে রেজিস্ট্রি দলিল বা খতিয়ান কার কাছে আছে তা জানতে চান।\n"
            "   - যদি target_stage='desired_solution' হয়: কাবিন বা নথির তথ্য পেয়ে থাকলে তা অধিকার প্রমাণের জন্য গুরুত্বপূর্ণ উল্লেখ করে ক্লায়েন্ট কী ধরণের আইনি সমাধান বা প্রতিকার চান (যেমন স্থানীয়ভাবে ইউনিয়ন পরিষদে সালিশ বা আপস চান, নাকি পারিবারিক/দেওয়ানি আদালতে মামলা করে দেনমোহর ও বকেয়া খোরপোষ আদায় করতে চান) তা জানতে চান।\n"
            "   - যদি target_stage='impact' হয়: বিরোধ বা বঞ্চনার ফলে বর্তমানে তিনি ও তাঁর পরিবার কী ধরনের আর্থিক টানাপোড়েন বা সংকটে দিন কাটাচ্ছেন তা জানতে চান।\n"
            "   - যদি target_stage='cause' হয়: বিরোধের সূত্রপাত বা আলাদা থাকার মূল কারণ কী ছিল তা জানতে চান।\n"
            "5. এই প্রশ্নের সাথে সরাসরি মানানসই ৩-৪টি কথ্য বাংলা দ্রুত উত্তরের অপশন (suggested_replies) প্রদান করুন।\n"
            "6. ক্লায়েন্ট যদি প্রয়োজনীয় মৌলিক উত্তরগুলো এখনো সম্পন্ন না করে থাকেন, তবে is_complete=False দিন।"
        ))
    ])

    try:
        res = dialogue_llm.invoke(dialogue_prompt.format_messages(
            category=cat or "সাধারণ বিরোধ",
            client_narrative=text_to_eval,
            chat_history=formatted_history or "কথোপকথন সবে শুরু হয়েছে।",
            known_facts="; ".join(known) if known else "নির্দিষ্ট কোনো তথ্য এখনো বিস্তারিত পাওয়া যায়নি।",
            stages_covered_bn=stages_covered_bn,
            target_stage=target_stage,
            target_stage_bn=target_stage_bn,
            latest_user_text=latest_user_text,
            turn_count=turn_count
        ))

        if res is None:
            is_comp = False
            q = None
            replies = None
            missing_item = None
            new_facts = {}
        elif isinstance(res, dict):
            is_comp = bool(res.get("is_complete", False))
            q = res.get("follow_up_question")
            replies = res.get("suggested_replies")
            missing_item = res.get("missing_aspect")
            new_facts = res.get("newly_identified_facts") or {}
        else:
            is_comp = bool(getattr(res, "is_complete", False))
            q = getattr(res, "follow_up_question", None)
            replies = getattr(res, "suggested_replies", None)
            missing_item = getattr(res, "missing_aspect", None)
            new_facts = getattr(res, "newly_identified_facts", None) or {}

        if is_comp and has_evidence_info and (target_stage == "complete" or (turn_count >= 4 and "desired_solution" in existing_covered)):
            return {
                "is_complete": True,
                "current_stage": "complete",
                "stages_covered": existing_covered,
                "missing_fields": [],
                "follow_up_question": None,
                "suggested_replies": None,
                "extra_question_asked": False
            }

        # Repetition and fallback detection:
        is_repetitive = False
        if not q or not q.strip():
            is_repetitive = True
        
        prev_assistant_questions = [
            m.get("content", "") for m in state.get("chat_history", [])
            if m.get("role") == "assistant" and m.get("content") and not m.get("content").startswith("⚠️")
        ]
        if any(q.strip() == prev_q.strip() or (len(q) > 25 and q[:35] in prev_q) for prev_q in prev_assistant_questions):
            is_repetitive = True
        elif target_stage != "cause" and any(w in (q or "") for w in ["সূত্রপাত", "ঝামেলা হয়েছে কেন", "ঝামেলা হয়েছে কেন", "কেন আপনার থেকে আলাদা", "আলাদা থাকছেন এবং", "কোনো বিশেষ কারণ"]):
            is_repetitive = True
        elif target_stage == "history" and not any(w in (q or "") for w in ["কাবিন", "কাগজ", "দলিল", "খতিয়ান", "খতিয়ান", "প্রমাণ", "নথি", "সাক্ষী", "রেজিস্ট্রি", "বিয়ে", "বিয়ে", "আদালতের জন্য"]):
            is_repetitive = True
        elif target_stage != "history" and any(w in (q or "") for w in ["কাবিননামা কি আপনাদের কাছে", "কাবিননামা কার কাছে", "বিয়ে কবে হয়েছিল", "রেজিস্ট্রি দলিল বা খতিয়ান"]):
            is_repetitive = True
        elif target_stage == "desired_solution" and not any(w in (q or "") for w in ["সালিশ", "আদালত", "মামলা", "প্রতিকার", "সমাধান", "মীমাংসা", "আইনি পদক্ষেপ", "পদক্ষেপ"]):
            is_repetitive = True

        if is_repetitive:
            fallback_missing = "documents_for_court" if "desired_solution" in existing_covered else (missing_item or "marriage_documents")
            q = get_stage_fallback_question(cat, target_stage, fallback_missing)

        if not replies or len(replies) == 0 or (target_stage != "cause" and any("দখল করে রেখেছে" in r for r in (replies or []))) or (target_stage == "desired_solution" and not any("আদালত" in r or "সালিশ" in r or "মামলা" in r for r in (replies or []))):
            replies = generate_suggested_replies(
                question=q,
                missing_fields=[target_stage],
                category=cat
            )

        ret: Dict[str, Any] = {
            "is_complete": False,
            "current_stage": target_stage,
            "stages_covered": existing_covered,
            "missing_fields": [missing_item] if missing_item else [target_stage],
            "follow_up_question": q,
            "suggested_replies": replies,
            "extra_question_asked": False
        }

        # Merge any newly discovered facts
        if isinstance(new_facts, dict):
            for k, v in new_facts.items():
                if v and str(v).strip() and str(v).lower() != "null" and not state.get(k):
                    ret[k] = v

        return ret

    except Exception as e:
        print(f"[Dialogue LLM Error] {e}")
        err_info = parse_llm_error(e)
        if err_info.get("status_code") in (401, 402, 429) or err_info.get("error_type") in ("authentication_error", "connection_error"):
            return {
                "is_complete": False,
                "missing_fields": [],
                "follow_up_question": None,
                "suggested_replies": None,
                "llm_error": err_info["message_bn"],
                "llm_error_details": err_info
            }

        # Fallback question based on Problem -> Cause -> History
        fallback_q = get_stage_fallback_question(cat, target_stage)
        fallback_replies = generate_suggested_replies(fallback_q, missing_fields=[target_stage], category=cat)
        return {
            "is_complete": False,
            "current_stage": target_stage,
            "stages_covered": existing_covered,
            "missing_fields": [target_stage],
            "follow_up_question": fallback_q,
            "suggested_replies": fallback_replies,
            "extra_question_asked": False
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

# Safety routing: No hard breakout shortcut. All clients proceed to token budget and questionnaire intake flow.
def check_safety_route(state: IntakeState):
    if state.get("llm_error"):
        return END
    return "token_budget"

workflow.add_conditional_edges(
    "safety_check",
    check_safety_route,
    {
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
            "current_stage": None,
            "stages_covered": [],
            "requires_continuation": False,
            "continuation_prompt": None,
            "follow_up_question": None,
            "suggested_replies": None,
            "extra_question_asked": False,
            "rights_explanation": None,
            "draft_complaint": None,
            "referral_clinic": None,
            "referral_slot": None,
            "chat_history": history,
            "llm_error": err_details["message_bn"],
            "llm_error_details": err_details
        }

    was_disambiguation = bool(
        existing_state and (
            existing_state.get("disambiguation_needed") or 
            existing_state.get("category") == "unclassifiable" or
            existing_state.get("missing_fields") == ["category_clarification"] or
            existing_state.get("category") is None
        )
    )
    if was_disambiguation:
        current_turn = 1
    elif existing_state:
        current_turn = existing_state.get("turn_count", 0) + 1
    else:
        current_turn = 1

    state: IntakeState = {
        "audio_path": audio_path,
        "transcript": transcript,
        "client_own_words": existing_state.get("client_own_words", "") if existing_state else "",
        "turn_count": current_turn,
        "estimated_tokens": existing_state.get("estimated_tokens", 0) if existing_state else 0,
        "requires_continuation": False,
        "continuation_prompt": None,
        "is_continuation_confirmed": is_continuation or (existing_state.get("is_continuation_confirmed", False) if existing_state else False),
        "safety_flag": existing_state.get("safety_flag", False) if existing_state else False,
        "safety_message": existing_state.get("safety_message", None) if existing_state else None,
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
        "current_stage": existing_state.get("current_stage") if existing_state else None,
        "stages_covered": list(existing_state.get("stages_covered", [])) if existing_state else [],
        "missing_fields": existing_state.get("missing_fields", []) if existing_state else [],
        "follow_up_question": None,
        "suggested_replies": existing_state.get("suggested_replies") if existing_state else None,
        "extra_question_asked": existing_state.get("extra_question_asked", False) if existing_state else False,
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
            summary_msg = "আপনার বিবরণটি পর্যালোচনা করা হয়েছে। এটি আমাদের লিগ্যাল এইডের আওতাভুক্ত না হলেও সম্ভাব্য পদক্ষেপের পরামর্শ প্রদান করা হয়েছে। পরবর্তী ধাপে গিয়ে বিস্তারিত দেখতে পারেন।"
        else:
            clinic = result.get('referral_clinic') or "ব্র্যাক মানবাধিকার ও আইনি সহায়তা কেন্দ্র"
            slot = result.get('referral_slot') or "অফিস চলাকালীন"
            summary_msg = (
                f"ধন্যবাদ। আপনার সম্পূর্ণ বিবরণ ও উত্তরের ভিত্তিতে ব্যক্তিগত আইনি অধিকার ও সমাধানের পথরেখা প্রস্তুত করা হয়েছে। "
                f"নিকটস্থ পরামর্শ কেন্দ্র: {clinic} ({slot})। "
                f"বিস্তারিত আইনি বিশ্লেষণ ও পরবর্তী পদক্ষেপ দেখতে নিচের 'পরবর্তী ধাপে যান' বাটনে ক্লিক করুন।"
            )
        history.append({
            "role": "assistant",
            "content": summary_msg
        })
    elif result.get("safety_flag"):
        history.append({
            "role": "assistant",
            "content": result.get("safety_message") or "জরুরি নিরাপত্তা সতর্কতা সক্রিয় করা হয়েছে।"
        })
    
    result["chat_history"] = history
    return result

