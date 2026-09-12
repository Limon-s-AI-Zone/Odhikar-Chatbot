from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime

class ChatMessage(BaseModel):
    role: str # 'user' or 'assistant'
    content: str
    timestamp: Optional[str] = None

class CaseBase(BaseModel):
    category: Optional[str] = None
    status: str = "New"
    applicant_name: Optional[str] = None
    respondent: Optional[str] = None
    marriage_date: Optional[str] = None
    marriage_date_inferred: Optional[bool] = False
    dower_amount: Optional[str] = None
    dowry_paid: Optional[str] = None
    unpaid_wages_claim: Optional[str] = None
    work_period: Optional[str] = None
    current_status: Optional[str] = None
    children: Optional[str] = None
    evidence: Optional[str] = None
    safety_flag: Optional[str] = "None"
    original_transcript: Optional[str] = None
    draft_complaint: Optional[str] = None
    rights_explanation: Optional[str] = None
    referral_clinic: Optional[str] = None
    referral_slot: Optional[str] = None
    address: Optional[str] = None
    chat_history: Optional[List[Dict[str, Any]]] = []

class CaseCreate(CaseBase):
    pass

class CaseUpdate(BaseModel):
    status: Optional[str] = None
    draft_complaint: Optional[str] = None
    applicant_name: Optional[str] = None
    respondent: Optional[str] = None
    address: Optional[str] = None
    marriage_date: Optional[str] = None
    dower_amount: Optional[str] = None
    dowry_paid: Optional[str] = None
    unpaid_wages_claim: Optional[str] = None
    current_status: Optional[str] = None
    evidence: Optional[str] = None

class CaseResponse(CaseBase):
    id: int
    received_at: datetime

    class Config:
        from_attributes = True

# Client intake API request/response with continuation support and chat history
class IntakeRequest(BaseModel):
    transcript: str
    existing_state: Optional[Dict[str, Any]] = None
    is_continuation: bool = False
    is_summarized: bool = False
    selected_model: Optional[str] = None
    thinking_level: Optional[str] = "medium"

class SummarizeRequest(BaseModel):
    transcript: str
    existing_state: Optional[Dict[str, Any]] = None

class SummarizeResponse(BaseModel):
    summarized_text: str
    original_tokens: int
    summarized_tokens: int


class IntakeResponse(BaseModel):
    session_state: Dict[str, Any]
    safety_flag: bool
    safety_message: Optional[str] = None
    category: Optional[str] = None
    confidence: Optional[int] = None
    follow_up_question: Optional[str] = None
    suggested_replies: Optional[List[str]] = None
    extra_question_asked: Optional[bool] = False
    is_complete: bool
    action_summary: Optional[str] = None
    taking_action_based_on_docs: Optional[str] = None
    doc_status: Optional[str] = None
    awaiting_process_confirmation: Optional[bool] = False
    requires_continuation: bool = False
    continuation_prompt: Optional[str] = None
    rights_explanation: Optional[str] = None
    draft_complaint: Optional[str] = None
    referral_clinic: Optional[str] = None
    referral_slot: Optional[str] = None
    chat_history: List[Dict[str, Any]] = []
    case_id: Optional[int] = None
    llm_error: Optional[str] = None
    llm_error_details: Optional[Dict[str, Any]] = None
    selected_model: Optional[str] = None
    thinking_level: Optional[str] = None

# Profile & Aggressor Details Finalization Request
class FinalizeProfileRequest(BaseModel):
    case_id: Optional[int] = None
    session_state: Optional[Dict[str, Any]] = None
    applicant_name: str
    father_name: Optional[str] = None
    division: str
    zilla: str
    thana: str
    union_village: str
    contact_number: Optional[str] = None
    is_anonymous: bool = False
    aggressor_name: Optional[str] = None
    aggressor_relation: Optional[str] = None
    aggressor_address: Optional[str] = None

class FinalizeProfileResponse(BaseModel):
    case_id: Optional[int] = None
    applicant_name: str
    respondent: str
    address: str
    referral_clinic: str
    referral_slot: str
    rights_explanation: str
    draft_complaint: str
    session_state: Dict[str, Any]

# Voice-to-Profile Extraction Request & Response
class ExtractProfileVoiceRequest(BaseModel):
    voice_transcript: str
    chat_history: Optional[List[Dict[str, Any]]] = None

class ExtractProfileVoiceResponse(BaseModel):
    applicant_name: Optional[str] = None
    father_name: Optional[str] = None
    division: Optional[str] = None
    zilla: Optional[str] = None
    thana: Optional[str] = None
    union_village: Optional[str] = None
    contact_number: Optional[str] = None
    aggressor_name: Optional[str] = None
    aggressor_relation: Optional[str] = None
    aggressor_address: Optional[str] = None
    summary_text: Optional[str] = None
