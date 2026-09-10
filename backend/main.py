import os
from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, Depends, HTTPException, UploadFile, File, Form
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
import shutil
import json
import asyncio

import models
import schemas
from database import engine, get_db
import ai_pipeline
from middleware import AIPipelineMiddleware, audit_safety_event, validate_narrative_input

# Create database tables
models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="Odhikar API — Legal Aid Intake")

# Register AI Pipeline Middleware
app.add_middleware(AIPipelineMiddleware)

# Enable CORS for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def read_root():
    return {"message": "Welcome to Odhikar Legal Aid AI API"}

# List all cases for Paralegal Dashboard
@app.get("/cases/", response_model=list[schemas.CaseResponse])
def get_cases(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    cases = db.query(models.Case).order_by(
        models.Case.status == "URGENT",
        models.Case.received_at.desc()
    ).offset(skip).limit(limit).all()
    return cases

# Get single case detail
@app.get("/cases/{case_id}", response_model=schemas.CaseResponse)
def get_case(case_id: int, db: Session = Depends(get_db)):
    case = db.query(models.Case).filter(models.Case.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    return case

# Update case (Paralegal review / approval)
@app.put("/cases/{case_id}", response_model=schemas.CaseResponse)
def update_case(case_id: int, update_data: schemas.CaseUpdate, db: Session = Depends(get_db)):
    case = db.query(models.Case).filter(models.Case.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    
    for key, value in update_data.model_dump(exclude_unset=True).items():
        setattr(case, key, value)
    
    db.commit()
    db.refresh(case)
    return case

# Interactive Intake Endpoint with Token Continuation Handling
@app.post("/intake/message", response_model=schemas.IntakeResponse)
def process_intake_message(req: schemas.IntakeRequest, db: Session = Depends(get_db)):
    # Run through LangGraph pipeline with continuation support
    result = ai_pipeline.run_intake(
        transcript=req.transcript,
        existing_state=req.existing_state,
        is_continuation=req.is_continuation
    )

    safety_flag = result.get("safety_flag", False)
    safety_message = result.get("safety_message")
    is_complete = result.get("is_complete", False)
    requires_continuation = result.get("requires_continuation", False)
    continuation_prompt = result.get("continuation_prompt")
    
    # Audit safety and narrative via middleware logger
    audit_safety_event(
        user_text=req.transcript,
        safety_flag=safety_flag,
        category=result.get("category")
    )
    
    case_id = None
    # If complete or safety breakout (and not paused for continuation), persist to database
    if (is_complete or safety_flag) and not requires_continuation:
        status = "URGENT" if safety_flag else "New"
        db_case = models.Case(
            category=result.get("category") or ("Family — Violence Disclosed" if safety_flag else "General"),
            status=status,
            applicant_name=result.get("applicant_name") or "[নাম সংরক্ষিত]",
            respondent=result.get("respondent") or "[বিবাদী]",
            marriage_date=result.get("marriage_date"),
            marriage_date_inferred=result.get("marriage_date_inferred", False),
            dower_amount=result.get("dower_amount"),
            dowry_paid=result.get("dowry_paid"),
            unpaid_wages_claim=result.get("unpaid_wages_claim"),
            work_period=result.get("work_period"),
            current_status=result.get("current_status"),
            children=result.get("children"),
            evidence=result.get("evidence"),
            safety_flag="URGENT — VIOLENCE DETECTED" if safety_flag else "None",
            original_transcript=result.get("client_own_words") or req.transcript,
            rights_explanation=result.get("rights_explanation"),
            draft_complaint=result.get("draft_complaint"),
            referral_clinic=result.get("referral_clinic") or "ব্র্যাক লিগ্যাল এইড ক্লিনিক, সদর শাখা",
            referral_slot=result.get("referral_slot") or "বুধবার, সকাল ১০:০০ টা",
            chat_history=result.get("chat_history", [])
        )
        db.add(db_case)
        db.commit()
        db.refresh(db_case)
        case_id = db_case.id

    return schemas.IntakeResponse(
        session_state=result,
        safety_flag=safety_flag,
        safety_message=safety_message,
        category=result.get("category"),
        confidence=result.get("confidence"),
        follow_up_question=result.get("follow_up_question"),
        is_complete=is_complete,
        requires_continuation=requires_continuation,
        continuation_prompt=continuation_prompt,
        rights_explanation=result.get("rights_explanation"),
        draft_complaint=result.get("draft_complaint"),
        referral_clinic=result.get("referral_clinic"),
        referral_slot=result.get("referral_slot"),
        chat_history=result.get("chat_history", []),
        case_id=case_id
    )


# Server-Sent Events (SSE) Streaming Intake Endpoint powered by Native LangGraph Streaming
@app.post("/intake/stream")
async def process_intake_stream(req: schemas.IntakeRequest, db: Session = Depends(get_db)):
    """
    Native LangGraph streaming endpoint using graph.astream(stream_mode='updates').
    Emits live node execution events, token streams, and final structured state.
    """
    async def event_generator():
        yield f"data: {json.dumps({'type': 'status', 'content': 'ল্যাংগ্রাফ পাইপলাইন সক্রিয় করা হচ্ছে...'})}\n\n"
        
        final_state = None
        
        # Stream directly from native LangGraph astream generator
        async for event in ai_pipeline.run_intake_stream(
            transcript=req.transcript,
            existing_state=req.existing_state,
            is_continuation=req.is_continuation
        ):
            if event["type"] == "node_update":
                yield f"data: {json.dumps({'type': 'status', 'node': event['node'], 'content': event['label']})}\n\n"
            elif event["type"] == "token":
                yield f"data: {json.dumps({'type': 'token', 'content': event['content']})}\n\n"
            elif event["type"] == "final_state":
                final_state = event["data"]
                
        if not final_state:
            final_state = ai_pipeline.run_intake(
                transcript=req.transcript,
                existing_state=req.existing_state,
                is_continuation=req.is_continuation
            )
            
        safety_flag = final_state.get("safety_flag", False)
        safety_message = final_state.get("safety_message")
        is_complete = final_state.get("is_complete", False)
        requires_continuation = final_state.get("requires_continuation", False)
        continuation_prompt = final_state.get("continuation_prompt")
        
        audit_safety_event(
            user_text=req.transcript,
            safety_flag=safety_flag,
            category=final_state.get("category")
        )
        
        case_id = None
        if (is_complete or safety_flag) and not requires_continuation:
            status = "URGENT" if safety_flag else "New"
            db_case = models.Case(
                category=final_state.get("category") or ("Family — Violence Disclosed" if safety_flag else "General"),
                status=status,
                applicant_name=final_state.get("applicant_name") or "[নাম সংরক্ষিত]",
                respondent=final_state.get("respondent") or "[বিবাদী]",
                marriage_date=final_state.get("marriage_date"),
                marriage_date_inferred=final_state.get("marriage_date_inferred", False),
                dower_amount=final_state.get("dower_amount"),
                dowry_paid=final_state.get("dowry_paid"),
                unpaid_wages_claim=final_state.get("unpaid_wages_claim"),
                work_period=final_state.get("work_period"),
                current_status=final_state.get("current_status"),
                children=final_state.get("children"),
                evidence=final_state.get("evidence"),
                safety_flag="URGENT — VIOLENCE DETECTED" if safety_flag else "None",
                original_transcript=final_state.get("client_own_words") or req.transcript,
                rights_explanation=final_state.get("rights_explanation"),
                draft_complaint=final_state.get("draft_complaint"),
                referral_clinic=final_state.get("referral_clinic") or "ব্র্যাক লিগ্যাল এইড ক্লিনিক, সদর শাখা",
                referral_slot=final_state.get("referral_slot") or "বুধবার, সকাল ১০:০০ টা",
                chat_history=final_state.get("chat_history", [])
            )
            db.add(db_case)
            db.commit()
            db.refresh(db_case)
            case_id = db_case.id
            
        final_payload = {
            "type": "final",
            "session_state": final_state,
            "safety_flag": safety_flag,
            "safety_message": safety_message,
            "category": final_state.get("category"),
            "confidence": final_state.get("confidence"),
            "follow_up_question": final_state.get("follow_up_question"),
            "is_complete": is_complete,
            "requires_continuation": requires_continuation,
            "continuation_prompt": continuation_prompt,
            "rights_explanation": final_state.get("rights_explanation"),
            "draft_complaint": final_state.get("draft_complaint"),
            "referral_clinic": final_state.get("referral_clinic"),
            "referral_slot": final_state.get("referral_slot"),
            "chat_history": final_state.get("chat_history", []),
            "case_id": case_id
        }
        yield f"data: {json.dumps(final_payload)}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")


# Audio upload endpoint
@app.post("/intake/audio")
async def upload_audio(file: UploadFile = File(...), db: Session = Depends(get_db)):
    os.makedirs("uploads", exist_ok=True)
    file_location = f"uploads/{file.filename}"
    with open(file_location, "wb+") as file_object:
        shutil.copyfileobj(file.file, file_object)
    
    result = ai_pipeline.run_intake(transcript="", audio_path=file_location)
    return result
