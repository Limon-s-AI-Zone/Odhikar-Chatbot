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
    chat_history: Optional[List[Dict[str, Any]]] = []

class CaseCreate(CaseBase):
    pass

class CaseUpdate(BaseModel):
    status: Optional[str] = None
    draft_complaint: Optional[str] = None
    applicant_name: Optional[str] = None
    respondent: Optional[str] = None
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
