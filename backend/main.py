import os
from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, Depends, HTTPException, UploadFile, File, Form
from fastapi.responses import StreamingResponse, Response
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
import shutil
import json
import asyncio
import io
import edge_tts
import uuid
import time
import re
from pydantic import BaseModel

import models
import schemas
from database import engine, get_db
import ai_pipeline
from middleware import AIPipelineMiddleware, audit_safety_event, audit_llm_error_event, validate_narrative_input

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

@app.get("/llm/status")
def get_llm_status():
    """Checks LLM connectivity, 401 authentication status, and token health."""
    return ai_pipeline.check_llm_status()

# Interactive Intake Endpoint with Token Continuation & LLM Error Handling
@app.post("/intake/message", response_model=schemas.IntakeResponse)
def process_intake_message(req: schemas.IntakeRequest, db: Session = Depends(get_db)):
    try:
        # Run through LangGraph pipeline with continuation support
        result = ai_pipeline.run_intake(
            transcript=req.transcript,
            existing_state=req.existing_state,
            is_continuation=req.is_continuation
        )
    except Exception as exc:
        err_info = ai_pipeline.parse_llm_error(exc)
        result = {
            "transcript": req.transcript,
            "safety_flag": False,
            "is_complete": False,
            "requires_continuation": False,
            "llm_error": err_info["message_bn"],
            "llm_error_details": err_info,
            "chat_history": (req.existing_state.get("chat_history", []) if req.existing_state else []) + [
                {"role": "assistant", "content": f"⚠️ ত্রুটি: {err_info['message_bn']}"}
            ]
        }

    safety_flag = result.get("safety_flag", False)
    safety_message = result.get("safety_message")
    is_complete = result.get("is_complete", False)
    requires_continuation = result.get("requires_continuation", False)
    continuation_prompt = result.get("continuation_prompt")
    llm_error = result.get("llm_error")
    llm_error_details = result.get("llm_error_details")
    
    # Audit safety and narrative via middleware logger
    audit_safety_event(
        user_text=req.transcript,
        safety_flag=safety_flag,
        category=result.get("category")
    )
    if llm_error:
        audit_llm_error_event(
            error_info=llm_error_details or {"message_bn": llm_error},
            user_text=req.transcript
        )
    
    case_id = None
    # If complete or safety breakout (and not paused for continuation, and no fatal LLM error), persist to database
    if not llm_error and (is_complete or safety_flag) and not requires_continuation:
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
        suggested_replies=result.get("suggested_replies"),
        is_complete=is_complete,
        requires_continuation=requires_continuation,
        continuation_prompt=continuation_prompt,
        rights_explanation=result.get("rights_explanation"),
        draft_complaint=result.get("draft_complaint"),
        referral_clinic=result.get("referral_clinic"),
        referral_slot=result.get("referral_slot"),
        chat_history=result.get("chat_history", []),
        case_id=case_id,
        llm_error=llm_error,
        llm_error_details=llm_error_details
    )


# Server-Sent Events (SSE) Streaming Intake Endpoint
@app.post("/intake/stream")
async def process_intake_stream(req: schemas.IntakeRequest, db: Session = Depends(get_db)):
    """
    Streaming endpoint that pushes progressive status, token streams, and final response
    so that the React frontend displays smooth typewriter animations and real-time streaming feedback.
    Handles LLM connection, 401, and token errors with dedicated error SSE events.
    """
    async def event_generator():
        # Step 1: Initial status message
        yield f"data: {json.dumps({'type': 'status', 'content': 'বিবরণ বিশ্লেষণ ও আইনি তথ্য যাচাই করা হচ্ছে...'})}\n\n"
        await asyncio.sleep(0.04)
        
        # Step 2: Run pipeline asynchronously
        try:
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None,
                lambda: ai_pipeline.run_intake(
                    transcript=req.transcript,
                    existing_state=req.existing_state,
                    is_continuation=req.is_continuation
                )
            )
        except Exception as exc:
            err_info = ai_pipeline.parse_llm_error(exc)
            yield f"data: {json.dumps({'type': 'error', 'llm_error': err_info['message_bn'], 'llm_error_details': err_info})}\n\n"
            err_payload = {
                "type": "final",
                "session_state": {"llm_error": err_info["message_bn"], "llm_error_details": err_info},
                "safety_flag": False,
                "safety_message": None,
                "category": None,
                "confidence": None,
                "follow_up_question": None,
                "suggested_replies": None,
                "is_complete": False,
                "requires_continuation": False,
                "continuation_prompt": None,
                "rights_explanation": None,
                "draft_complaint": None,
                "referral_clinic": None,
                "referral_slot": None,
                "chat_history": (req.existing_state.get("chat_history", []) if req.existing_state else []) + [
                    {"role": "assistant", "content": f"⚠️ ত্রুটি: {err_info['message_bn']}"}
                ],
                "case_id": None,
                "llm_error": err_info["message_bn"],
                "llm_error_details": err_info
            }
            yield f"data: {json.dumps(err_payload)}\n\n"
            return
        
        safety_flag = result.get("safety_flag", False)
        safety_message = result.get("safety_message")
        is_complete = result.get("is_complete", False)
        requires_continuation = result.get("requires_continuation", False)
        continuation_prompt = result.get("continuation_prompt")
        llm_error = result.get("llm_error")
        llm_error_details = result.get("llm_error_details")

        # If LLM returned an error (e.g. 401, not connected, token issue)
        if llm_error:
            yield f"data: {json.dumps({'type': 'error', 'llm_error': llm_error, 'llm_error_details': llm_error_details})}\n\n"
        
        audit_safety_event(
            user_text=req.transcript,
            safety_flag=safety_flag,
            category=result.get("category")
        )
        if llm_error:
            audit_llm_error_event(
                error_info=llm_error_details or {"message_bn": llm_error},
                user_text=req.transcript
            )
        
        case_id = None
        if not llm_error and (is_complete or safety_flag) and not requires_continuation:
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
            
        # Step 3: Stream tokens of assistant response if no fatal LLM error
        text_to_stream = ""
        if llm_error:
            text_to_stream = f"⚠️ ত্রুটি: {llm_error}"
        elif safety_flag:
            text_to_stream = safety_message or ""
        elif requires_continuation:
            text_to_stream = continuation_prompt or ""
        elif result.get("follow_up_question"):
            text_to_stream = result.get("follow_up_question") or ""
        elif result.get("chat_history") and len(result.get("chat_history")) > 0:
            last_msg = result.get("chat_history")[-1]
            if last_msg.get("role") == "assistant":
                text_to_stream = last_msg.get("content", "")
                
        if text_to_stream:
            words = text_to_stream.split(" ")
            chunk_size = 2
            for i in range(0, len(words), chunk_size):
                chunk = " ".join(words[i:i+chunk_size])
                if i + chunk_size < len(words):
                    chunk += " "
                yield f"data: {json.dumps({'type': 'token', 'content': chunk})}\n\n"
                await asyncio.sleep(0.03)

        # Step 4: Final event with complete state
        final_payload = {
            "type": "final",
            "session_state": result,
            "safety_flag": safety_flag,
            "safety_message": safety_message,
            "category": result.get("category"),
            "confidence": result.get("confidence"),
            "follow_up_question": result.get("follow_up_question"),
            "suggested_replies": result.get("suggested_replies", []),
            "is_complete": is_complete,
            "requires_continuation": requires_continuation,
            "continuation_prompt": continuation_prompt,
            "rights_explanation": result.get("rights_explanation"),
            "draft_complaint": result.get("draft_complaint"),
            "referral_clinic": result.get("referral_clinic"),
            "referral_slot": result.get("referral_slot"),
            "chat_history": result.get("chat_history", []),
            "case_id": case_id,
            "llm_error": llm_error,
            "llm_error_details": llm_error_details
        }
        yield f"data: {json.dumps(final_payload)}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")


# Audio upload endpoint (Speech-to-Text & Intake)
@app.post("/intake/audio")
async def upload_audio(file: UploadFile = File(...), db: Session = Depends(get_db)):
    os.makedirs("uploads", exist_ok=True)
    file_location = f"uploads/{file.filename}"
    with open(file_location, "wb+") as file_object:
        shutil.copyfileobj(file.file, file_object)
    
    result = ai_pipeline.run_intake(transcript="", audio_path=file_location)
    return result


# Audio transcription endpoint (Speech-to-Text directly returning text for client verification)
@app.post("/transcribe")
async def transcribe_audio_file(file: UploadFile = File(...)):
    """Transcribes an uploaded voice audio clip into clean Bengali text."""
    os.makedirs("uploads", exist_ok=True)
    temp_filename = f"rec_{uuid.uuid4().hex[:8]}_{file.filename or 'audio.webm'}"
    file_location = os.path.join("uploads", temp_filename)
    try:
        with open(file_location, "wb+") as file_object:
            shutil.copyfileobj(file.file, file_object)
        
        whisper = ai_pipeline.get_whisper()
        if whisper:
            segments, info = whisper.transcribe(
                file_location,
                language="bn",
                task="transcribe",
                initial_prompt=ai_pipeline.BANGLA_WHISPER_PROMPT,
                beam_size=5
            )
            raw_text = " ".join([seg.text for seg in segments]).strip()
            cleaned_text = ai_pipeline.normalize_bangla_transcript(raw_text)
            return {"text": cleaned_text, "raw": raw_text}
        else:
            return {"text": "", "error": "Whisper ASR model unavailable"}
    except Exception as e:
        print(f"[Transcribe Error] {e}")
        return {"text": "", "error": str(e)}
    finally:
        if os.path.exists(file_location):
            try:
                os.remove(file_location)
            except Exception:
                pass


# In-memory TTS store for audio streaming tokens
tts_store: dict = {}

def clean_markdown_for_tts(text: str) -> str:
    if not text:
        return ""
    # Strip markdown bold, italics, headers, code, bullet marks
    t = re.sub(r'\*\*([^*]+)\*\*', r'\1', text)
    t = re.sub(r'\*([^*]+)\*', r'\1', t)
    t = re.sub(r'__([^_]+)__', r'\1', t)
    t = re.sub(r'_([^_]+)_', r'\1', t)
    t = re.sub(r'#+\s*', '', t)
    t = re.sub(r'^\s*[-*•]\s+', '', t, flags=re.MULTILINE)
    t = re.sub(r'[`~]', '', t)
    # Replace newlines with Bengali danda pause for smooth reading
    t = re.sub(r'[\r\n]+', '। ', t)
    t = re.sub(r'\s*।\s*।+', '।', t)
    t = re.sub(r'[\t]+', ' ', t)
    t = re.sub(r'\s+', ' ', t)
    return t.strip()

class TTSPrepareRequest(BaseModel):
    text: str

@app.post("/tts/prepare")
async def prepare_tts(req: TTSPrepareRequest):
    """
    Stores text in-memory and returns a streaming URL with a temporary token.
    This completely avoids HTTP 431 'Request Header Fields Too Large' errors
    when passing long Bengali legal text through browser requests and proxies.
    """
    raw_text = req.text.strip() if req.text else ""
    if not raw_text:
        raise HTTPException(status_code=400, detail="Text cannot be empty")
    
    clean_text = clean_markdown_for_tts(raw_text)
    token = str(uuid.uuid4())
    
    # Cleanup tokens older than 15 minutes
    now = time.time()
    for k in list(tts_store.keys()):
        if now - tts_store[k].get("created_at", 0) > 900:
            tts_store.pop(k, None)
            
    tts_store[token] = {"text": clean_text, "created_at": now}
    return {"token": token, "audio_url": f"/api/tts/stream/{token}"}

@app.get("/tts/stream/{token}")
async def stream_tts_by_token(token: str):
    """
    Streams neural audio chunk-by-chunk using edge-tts.
    HTML5 Audio starts playing immediately (< 1s) as chunks arrive,
    without waiting for the full multi-minute audio file to generate.
    """
    entry = tts_store.get(token)
    if not entry:
        raise HTTPException(status_code=404, detail="Audio session not found or expired")
    
    clean_text = entry["text"]

    async def audio_generator():
        try:
            communicate = edge_tts.Communicate(clean_text, voice="bn-BD-NabanitaNeural")
            async for chunk in communicate.stream():
                if chunk["type"] == "audio":
                    yield chunk["data"]
        except Exception as e:
            print(f"[TTS Stream Error] {e}")

    return StreamingResponse(
        audio_generator(),
        media_type="audio/mpeg",
        headers={
            "Content-Disposition": "inline; filename=speech.mp3",
            "Cache-Control": "no-cache"
        }
    )

# Text-to-Speech (TTS) endpoint (Direct GET fallback)
@app.get("/tts")
async def get_tts_audio(text: str):
    """
    Direct GET endpoint for short texts or fallback callers. Uses StreamingResponse.
    """
    if not text or not text.strip():
        raise HTTPException(status_code=400, detail="Text cannot be empty")
    
    cleaned_text = clean_markdown_for_tts(text)
    
    async def audio_generator():
        try:
            communicate = edge_tts.Communicate(cleaned_text, voice="bn-BD-NabanitaNeural")
            async for chunk in communicate.stream():
                if chunk["type"] == "audio":
                    yield chunk["data"]
        except Exception as e:
            print(f"[TTS Error] {e}")

    return StreamingResponse(
        audio_generator(),
        media_type="audio/mpeg",
        headers={
            "Content-Disposition": "inline; filename=speech.mp3",
            "Cache-Control": "no-cache"
        }
    )
