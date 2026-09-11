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
from prompt_builder import get_prompt_builder

# Dynamic prompt builder singleton (loads from prompt_config.yaml)
_pb = get_prompt_builder()

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
    },
    {
        "keywords": ["ফরিদপুর", "faridpur", "মাদারীপুর", "madaripur", "শরীয়তপুর", "shariatpur", "গোপালগঞ্জ", "gopalganj", "রাজবাড়ী", "rajbari"],
        "clinic_name": "ব্র্যাক লিগ্যাল এইড ক্লিনিক, ফরিদপুর শাখা",
        "address": "ঝিলটুলী, মুজিব সড়ক, ফরিদপুর সদর",
        "contact_number": "০১৭৩০-৫৫৬৬৭৭",
        "referral_slot": "মঙ্গলবার, সকাল ১০:০০ টা",
        "helpline": "১৬৪৩০"
    },
    {
        "keywords": ["টাঙ্গাইল", "tangail", "কিশোরগঞ্জ", "kishoreganj", "মানিকগঞ্জ", "manikganj", "মুন্সীগঞ্জ", "munshiganj", "নরসিংদী", "narsingdi"],
        "clinic_name": "ব্র্যাক লিগ্যাল এইড ক্লিনিক, টাঙ্গাইল শাখা",
        "address": "ভিক্টোরিয়া রোড, টাঙ্গাইল সদর",
        "contact_number": "০১৭৩০-৭৭৮৮১১",
        "referral_slot": "সোমবার, সকাল ১০:০০ টা",
        "helpline": "১৬৪৩০"
    },
    {
        "keywords": ["নোয়াখালী", "noakhali", "লক্ষ্মীপুর", "lakshmipur", "ফেনী", "feni", "চাঁদপুর", "chandpur"],
        "clinic_name": "ব্র্যাক লিগ্যাল এইড ক্লিনিক, নোয়াখালী শাখা",
        "address": "মাইজদী কোর্ট, প্রধান সড়ক, নোয়াখালী সদর",
        "contact_number": "০১৭৩০-৯৯৮৮৭৭",
        "referral_slot": "বৃহস্পতিবার, সকাল ১০:৩০ টা",
        "helpline": "১৬৪৩০"
    },
    {
        "keywords": ["কুষ্টিয়া", "kushtia", "চুয়াডাঙ্গা", "chuadanga", "মেহেরপুর", "meherpur", "ঝিনাইদহ", "jhenaidah", "মাগুরা", "magura"],
        "clinic_name": "ব্র্যাক লিগ্যাল এইড ক্লিনিক, কুষ্টিয়া শাখা",
        "address": "এনএস রোড, মজমপুর গেট, কুষ্টিয়া সদর",
        "contact_number": "০১৭৩০-১২৯৯১১",
        "referral_slot": "বুধবার, সকাল ১১:০০ টা",
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
    best_pos = 999999
    for entry in LEGAL_AID_CLINIC_DIRECTORY:
        for kw in entry["keywords"]:
            pos = loc_lower.find(kw.lower())
            if pos != -1 and pos < best_pos:
                best_pos = pos
                matched = entry
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
    action_summary: Optional[str]
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
    """Generates 3-4 natural, colloquial Bengali suggested quick-replies based on the follow-up question.
    Now delegates to PromptBuilder which loads replies from prompt_config.yaml."""
    return _pb.get_suggested_replies(question, missing_fields, category)

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
    Now delegates to PromptBuilder which loads from prompt_config.yaml.
    """
    return _pb.get_fallback_question(
        match_type=match_type,
        category=category,
        previous_question=previous_question
    )

def get_stage_fallback_question(category: Optional[str], stage: str, missing_item: Optional[str] = None) -> str:
    """Gets the fallback follow-up question for a given category and stage.
    Now delegates to PromptBuilder which loads from prompt_config.yaml."""
    return _pb.get_stage_fallback_question(category, stage, missing_item)

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

# ----------------- ACTION SUMMARY GENERATION (STEP 3 COMPLETION) -----------------
ACTION_SUMMARY_SYSTEM_PROMPT = """You are an expert Bengali legal aid paralegal at BRAC Human Rights and Legal Aid Services.
The client has just completed answering all questions in their intake consultation.
Generate a concise, professional, empathetic, and legally precise summary of the immediate legal actions to be taken (আপনার করণীয় আইনি পদক্ষেপের সারসংক্ষেপ) tailored specifically to the client's answers and circumstances.

Structure:
📋 আপনার করণীয় আইনি পদক্ষেপের সারসংক্ষেপ:

১. **আইনি প্রতিকার ও মামলার ভিত্তি:** (Specify the exact statutory rights and court, e.g. পারিবারিক আদালত অধ্যাদেশ ১৯৮৫ for dower/maintenance suit, or বাংলাদেশ শ্রম আইন ২০০৬ for unpaid wages, or দেওয়ানি আদালত/সুনির্দিষ্ট প্রতিকার আইন for land dispute. Accurately reflect whether the client chose court lawsuit or ADR/arbitration if stated).
২. **প্রয়োজনীয় প্রস্তুতি ও প্রমাণাদি:** (List the exact documents they confirmed they have ready, e.g. Kabinnama, NID, salary slips, land khatians/deeds).
৩. **পরবর্তী প্রত্যক্ষ পদক্ষেপ:** (Actionable next step with legal aid clinic, e.g. ব্র্যাক লিগ্যাল এইড ক্লিনিকের প্যানেল আইনজীবীর মাধ্যমে আনুষ্ঠানিক অভিযোগপত্র ও আরজি চূড়ান্তকরণ এবং আদালতে মামলা দাখিল বা নোটিশ প্রেরণ).

আপনার এলাকার নিকটস্থ আইনি সহায়তা কেন্দ্র চিহ্নিত করতে এবং আনুষ্ঠানিক অভিযোগপত্র প্রস্তুত করতে নিচের ব্যক্তিগত ও বিবাদীর তথ্য প্রদান করুন।

Guidelines:
- Clear, empathetic, numbered bullet points, in spoken Bengali (কথ্য ও প্রাঞ্জল বাংলা).
- Total length under 130 words.
- Do NOT output generic filler phrases. Focus directly on the 3 actionable steps."""

def generate_action_summary(state: Dict[str, Any]) -> str:
    """
    Generates a personalized summary of actionable legal steps (করণীয় আইনি পদক্ষেপের সারসংক্ষেপ)
    tailored to the client's answers, legal category, and verified evidence.
    Falls back to a category-specific deterministic legal template on error or timeout.
    """
    cat = state.get("category") or "family_dower_maintenance"
    dower = state.get("dower_amount")
    evidence = state.get("evidence")
    wages = state.get("unpaid_wages_claim")
    clinic = state.get("referral_clinic") or "ব্র্যাক মানবাধিকার ও আইনি সহায়তা কেন্দ্র"

    # 1. Attempt dynamic LLM generation for maximum personalization
    try:
        dialogue_snippets = []
        for msg in state.get("chat_history", [])[-6:]:
            if msg.get("content"):
                dialogue_snippets.append(f"{msg.get('role')}: {msg.get('content')}")
        chat_context = "\n".join(dialogue_snippets)

        facts_list = [f"Category: {cat}"]
        if dower: facts_list.append(f"Dower: {dower}")
        if wages: facts_list.append(f"Unpaid wages claim: {wages}")
        if evidence: facts_list.append(f"Evidence: {evidence}")
        if state.get("current_status"): facts_list.append(f"Current situation: {state.get('current_status')}")
        if state.get("children"): facts_list.append(f"Children: {state.get('children')}")
        facts_summary = "\n".join(facts_list)

        prompt = ChatPromptTemplate.from_messages([
            ("system", ACTION_SUMMARY_SYSTEM_PROMPT),
            ("user", f"Client Facts:\n{facts_summary}\n\nRecent Dialogue:\n{chat_context}\n\nPlease generate the '📋 আপনার করণীয় আইনি পদক্ষেপের সারসংক্ষেপ':")
        ])
        res = llm.invoke(prompt.format_messages())
        if res.content and len(res.content.strip()) > 50:
            return res.content.strip()
    except Exception as exc:
        print(f"[Action Summary LLM Warning] Falling back to template: {exc}")

    # 2. Deterministic high-quality fallback templates by category
    if cat == "family_dower_maintenance":
        dower_str = f"আপনার {dower} টাকার দেনমোহর" if dower and dower != "[অপ্রতিষ্ঠিত]" else "আপনার দেনমোহর"
        return (
            "📋 আপনার করণীয় আইনি পদক্ষেপের সারসংক্ষেপ:\n\n"
            f"১. **আইনি প্রতিকার ও মামলার ভিত্তি:** পারিবারিক আদালত অধ্যাদেশ, ১৯৮৫ এর অধীনে {dower_str} ও বিগত দিনগুলোর বকেয়া খোরপোষ/ভরণপোষণ আদায়ের জন্য পারিবারিক আদালতে নিয়মিত মামলা দায়ের করা।\n"
            "২. **প্রয়োজনীয় প্রস্তুতি ও প্রমাণাদি:** আপনার নিকাহনামা/কাবিননামা, দেনমোহরের দাবিপত্র, জাতীয় পরিচয়পত্র (NID) এবং অন্যান্য প্রাসঙ্গিক সকল প্রমাণাদি প্রস্তুত রাখুন।\n"
            f"৩. **পরবর্তী প্রত্যক্ষ পদক্ষেপ:** {clinic}-এর বিজ্ঞ আইনজীবীর সহায়তায় আনুষ্ঠানিকভাবে নালিশ ও আরজি চূড়ান্ত করে পারিবারিক আদালতে মামলা দাখিল সম্পন্ন করা।\n\n"
            "আপনার এলাকার নিকটস্থ আইনি সহায়তা কেন্দ্র চিহ্নিত করতে এবং আনুষ্ঠানিক অভিযোগপত্র প্রস্তুত করতে নিচের ব্যক্তিগত ও বিবাদীর তথ্য প্রদান করুন।"
        )
    elif cat == "unpaid_wages":
        wage_str = f"আপনার {wages} টাকার বকেয়া মজুরি" if wages and wages != "[অপ্রতিষ্ঠিত]" else "আপনার বকেয়া মজুরি"
        return (
            "📋 আপনার করণীয় আইনি পদক্ষেপের সারসংক্ষেপ:\n\n"
            f"১. **আইনি প্রতিকার ও মামলার ভিত্তি:** বাংলাদেশ শ্রম আইন, ২০০৬ এর ৩৩ ধারা অনুযায়ী {wage_str} ও ক্ষতিপূরণ আদায়ের জন্য মালিকপক্ষ বরাবর আনুষ্ঠানিক আইনি নোটিশ প্রেরণ ও শ্রম আদালতে নালিশ দায়ের।\n"
            "২. **প্রয়োজনীয় প্রস্তুতি ও প্রমাণাদি:** আপনার কাজের পরিচয়পত্র (ID Card), দৈনিক হাজিরা খাতা বা স্লিপ, কাজের চুক্তিনামা এবং বকেয়া বেতনের হিসাব প্রস্তুত রাখুন।\n"
            f"৩. **পরবর্তী প্রত্যক্ষ পদক্ষেপ:** {clinic}-এর মাধ্যমে মালিকপক্ষকে লিখিত দাবি নোটিশ প্রেরণ এবং শ্রম আদালতের জন্য অভিযোগপত্র প্রস্তুত করা।\n\n"
            "আপনার এলাকার নিকটস্থ আইনি সহায়তা কেন্দ্র চিহ্নিত করতে এবং আনুষ্ঠানিক অভিযোগপত্র প্রস্তুত করতে নিচের ব্যক্তিগত ও বিবাদীর তথ্য প্রদান করুন।"
        )
    elif cat == "land_dispute":
        return (
            "📋 আপনার করণীয় আইনি পদক্ষেপের সারসংক্ষেপ:\n\n"
            "১. **আইনি প্রতিকার ও মামলার ভিত্তি:** সুনির্দিষ্ট প্রতিকার আইন, ১৮৭৭ অনুযায়ী স্বত্ব সাব্যস্তপূর্বক খাস দখল বা চিরস্থায়ী নিষেধাজ্ঞার দেওয়ানি মোকদ্দমা এবং শান্তিভঙ্গ রোধে ফৌজদারি কার্যবিধির ১৪৫ ধারায় প্রতিকার চাওয়া।\n"
            "২. **প্রয়োজনীয় প্রস্তুতি ও প্রমাণাদি:** আপনার জমির মূল রেজিস্ট্রি দলিল, হালনাগাদ পরচা/খতিয়ান (CS/SA/RS), দাখিলা ও দখলের প্রমাণপত্র প্রস্তুত রাখুন।\n"
            f"৩. **পরবর্তী প্রত্যক্ষ পদক্ষেপ:** {clinic}-এর লিগ্যাল এইড প্যানেল আইনজীবীর মাধ্যমে নালিশি জমির স্বত্ব যাচাইপূর্বক দেওয়ানি আদালতে মামলা বা সালিশি মীমাংসার উদ্যোগ গ্রহণ।\n\n"
            "আপনার এলাকার নিকটস্থ আইনি সহায়তা কেন্দ্র চিহ্নিত করতে এবং আনুষ্ঠানিক অভিযোগপত্র প্রস্তুত করতে নিচের ব্যক্তিগত ও বিবাদীর তথ্য প্রদান করুন।"
        )
    else:
        return (
            "📋 আপনার করণীয় আইনি পদক্ষেপের সারসংক্ষেপ:\n\n"
            "১. **আইনি প্রতিকার ও ভিত্তি:** আপনার বর্ণিত বিষয়টি আমাদের প্রাথমিক তালিকার বাইরে হলেও প্রচলিত দেওয়ানি বা ফৌজদারি আইনের অধীনে আদালতে আইনি প্রতিকার লাভের সুযোগ রয়েছে।\n"
            "২. **প্রয়োজনীয় প্রস্তুতি ও প্রমাণাদি:** ঘটনার প্রত্যক্ষদর্শী সাক্ষী, লিখিত চুক্তি বা অভিযোগ সংক্রান্ত সকল নথিপত্র প্রস্তুত রাখুন।\n"
            f"৩. **পরবর্তী প্রত্যক্ষ পদক্ষেপ:** উপযুক্ত আদালত, সংশ্লিষ্ট থানা বা সরকারি জেলা লিগ্যাল এইড কর্মকর্তার কার্যালয়ে যোগাযোগ করে আনুষ্ঠানিক পদক্ষেপ গ্রহণ করা।\n\n"
            "আপনার এলাকার নিকটস্থ সহায়তা কেন্দ্র চিহ্নিত করতে নিচের ব্যক্তিগত তথ্য প্রদান করুন।"
        )

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
            "action_summary": None,
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
        "action_summary": existing_state.get("action_summary") if existing_state else None,
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
        action_summary = generate_action_summary(result)
        result["action_summary"] = action_summary
        history.append({
            "role": "assistant",
            "content": action_summary
        })
    elif result.get("safety_flag"):
        history.append({
            "role": "assistant",
            "content": result.get("safety_message") or "জরুরি নিরাপত্তা সতর্কতা সক্রিয় করা হয়েছে।"
        })
    
    result["chat_history"] = history
    return result


# Pydantic schema for voice-to-profile extraction
class ProfileVoiceExtractOutput(BaseModel):
    applicant_name: Optional[str] = Field(None, description="Client or applicant's full name")
    father_name: Optional[str] = Field(None, description="Father's or guardian's name")
    division: Optional[str] = Field(None, description="Division in Bangladesh: ঢাকা, চট্টগ্রাম, রাজশাহী, খুলনা, বরিশাল, সিলেট, রংপুর, or ময়মনসিংহ")
    zilla: Optional[str] = Field(None, description="District / Zilla in Bangladesh, e.g. কুমিল্লা, ঢাকা, ফরিদপুর, বগুড়া, নারায়ণগঞ্জ, নোয়াখালী")
    thana: Optional[str] = Field(None, description="Upazila or Thana, e.g. চান্দিনা, ভাঙ্গা, সাভার, মিরপুর")
    union_village: Optional[str] = Field(None, description="Union or Village name, e.g. বাতাঘাসী, ঘারুয়া")
    contact_number: Optional[str] = Field(None, description="Mobile / phone number")
    aggressor_name: Optional[str] = Field(None, description="Opponent or aggressor's full name")
    aggressor_relation: Optional[str] = Field(None, description="Relationship with applicant, e.g. স্বামী, ভাই, শ্বশুর, প্রতিবেশী, মালিক")
    aggressor_address: Optional[str] = Field(None, description="Opponent's address or workplace location")
    summary_text: Optional[str] = Field(None, description="Concise 1-sentence summary in Bengali of the extracted profile")

profile_voice_extractor_llm = llm.with_structured_output(ProfileVoiceExtractOutput)

VOICE_PROFILE_PROMPT = """You are an expert Bengali legal paralegal information extractor.
Given the user's spoken statement and recent intake transcript, extract personal identity and location details for legal aid registration:
- applicant_name: Client or applicant's full name (e.g. মোসাম্মৎ রহিমা খাতুন, মোতালেব)
- father_name: Father's or guardian's name if mentioned (e.g. আবদুল করিম)
- division: Administrative division in Bangladesh (ঢাকা, চট্টগ্রাম, রাজশাহী, খুলনা, বরিশাল, সিলেট, রংপুর, ময়মনসিংহ). If not mentioned explicitly, infer it from the district/zilla (e.g. কুমিল্লা -> চট্টগ্রাম, ফরিদপুর -> ঢাকা, বগুড়া -> রাজশাহী).
- zilla: District / Zilla (e.g. কুমিল্লা, ফরিদপুর, ঢাকা, নারায়ণগঞ্জ, বগুড়া)
- thana: Upazila or Thana (e.g. চান্দিনা, ভাঙ্গা, সাভার, মিরপুর)
- union_village: Union or Village name (e.g. বাতাঘাসী, ঘারুয়া)
- contact_number: Phone / mobile number (e.g. ০১৭১২৩৪৫৬৭৮)
- aggressor_name: Opponent or aggressor's full name (e.g. রফিকুল ইসলাম, কাশেম)
- aggressor_relation: Relationship with applicant (e.g. স্বামী, ভাই, শ্বশুর, প্রতিবেশী, মালিক)
- aggressor_address: Opponent's address or workplace location (e.g. চান্দিনা বাজার, ভাঙ্গা বাজার)
- summary_text: 1-sentence Bengali summary of extracted info

If a field is not mentioned, leave it null. Always respond in valid structured output."""

def extract_profile_from_voice(voice_transcript: str, chat_history: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
    """
    Extracts applicant and aggressor information automatically from a spoken Bengali audio transcript
    or text narrative using LLM with structured entity output.
    """
    context_snippets = []
    if chat_history:
        for msg in chat_history[-6:]:
            if msg.get("role") == "user":
                context_snippets.append(f"আগের কথা: {msg.get('content', '')}")
    
    combined_input = voice_transcript
    if context_snippets:
        combined_input = f"{voice_transcript}\n\nপূর্ববর্তী কথোপকথন:\n" + "\n".join(context_snippets)
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", VOICE_PROFILE_PROMPT),
        ("user", "Spoken input: {spoken_input}")
    ])
    
    try:
        res = profile_voice_extractor_llm.invoke(prompt.format_messages(spoken_input=combined_input))
        if res is not None and hasattr(res, "model_dump"):
            data = res.model_dump()
            return data
        elif isinstance(res, dict):
            return res
    except Exception as e:
        print(f"[Profile Voice Extraction Warning] {e}")

    # Fallback basic extraction if LLM is unavailable
    fallback_data = {
        "applicant_name": None,
        "father_name": None,
        "division": None,
        "zilla": None,
        "thana": None,
        "union_village": None,
        "contact_number": None,
        "aggressor_name": None,
        "aggressor_relation": None,
        "aggressor_address": None,
        "summary_text": None
    }
    
    import re
    # Simple regex for mobile number
    phone_match = re.search(r'(01[3-9]\d{8}|০১[৩-৯][০-৯]{8})', voice_transcript)
    if phone_match:
        fallback_data["contact_number"] = phone_match.group(1)
        
    return fallback_data
