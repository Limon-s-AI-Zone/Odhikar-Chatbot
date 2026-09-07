from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, JSON
from database import Base
import datetime

class Case(Base):
    __tablename__ = "cases"

    id = Column(Integer, primary_key=True, index=True)
    category = Column(String, index=True)
    status = Column(String, default="New") # URGENT, New, Assigned, Booked, Approved
    received_at = Column(DateTime, default=datetime.datetime.utcnow)
    
    # Extracted fields
    applicant_name = Column(String, default="[নাম সংরক্ষিত]")
    respondent = Column(String, default="[বিবাদী]")
    marriage_date = Column(String, nullable=True)
    marriage_date_inferred = Column(Boolean, default=False)
    dower_amount = Column(String, nullable=True)
    dowry_paid = Column(String, nullable=True)
    unpaid_wages_claim = Column(String, nullable=True)
    work_period = Column(String, nullable=True)
    current_status = Column(Text, nullable=True)
    children = Column(String, nullable=True)
    evidence = Column(Text, nullable=True)
    
    # Flags and original text
    safety_flag = Column(String, default="None")
    original_transcript = Column(Text, nullable=True)
    rights_explanation = Column(Text, nullable=True)
    draft_complaint = Column(Text, nullable=True)
    referral_clinic = Column(String, default="ব্র্যাক লিগ্যাল এইড ক্লিনিক, সদর শাখা")
    referral_slot = Column(String, default="বুধবার, সকাল ১০:০০ টা")

    # Complete multi-turn conversational chat history
    chat_history = Column(JSON, default=list)
