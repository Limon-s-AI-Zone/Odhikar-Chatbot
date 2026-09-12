import os
from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, Depends, HTTPException, UploadFile, File, Form, Request
from fastapi.responses import StreamingResponse, Response, FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from sqlalchemy.orm import Session
import shutil
import json
import asyncio
import io
import edge_tts
import uuid
import time
import re
from pathlib import Path
from pydantic import BaseModel

import models
import schemas
from database import engine, get_db
import agent as ai_pipeline
from middleware import AIPipelineMiddleware, audit_safety_event, audit_llm_error_event, validate_narrative_input

# Production static UI (Cloud Run image copies frontend/dist here)
STATIC_DIR = Path(os.getenv("STATIC_DIR", str(Path(__file__).resolve().parent / "static")))


class StripApiPrefixMiddleware(BaseHTTPMiddleware):
    """Map /api/* -> /* so the Vite-style frontend paths work without a proxy."""

    async def dispatch(self, request: Request, call_next):
        path = request.scope.get("path", "")
        if path == "/api" or path.startswith("/api/"):
            new_path = path[4:] or "/"
            request.scope["path"] = new_path
            raw = request.scope.get("raw_path")
            if isinstance(raw, (bytes, bytearray)):
                request.scope["raw_path"] = new_path.encode("utf-8")
        return await call_next(request)

# Create database tables and ensure migrations for SQLite
models.Base.metadata.create_all(bind=engine)

def _migrate_db_columns():
    try:
        from sqlalchemy import text
        with engine.connect() as conn:
            result = conn.execute(text("PRAGMA table_info(cases)"))
            existing_cols = {row[1] for row in result.fetchall()}
            if existing_cols:
                expected_cols = {
                    "address": "TEXT",
                    "chat_history": "JSON",
                }
                for col_name, col_type in expected_cols.items():
                    if col_name not in existing_cols:
                        conn.execute(text(f"ALTER TABLE cases ADD COLUMN {col_name} {col_type}"))
                        conn.commit()
    except Exception as e:
        print(f"Warning during DB schema migration: {e}")

_migrate_db_columns()

app = FastAPI(title="Odhikar API — Legal Aid Intake")

# Register AI Pipeline Middleware
app.add_middleware(AIPipelineMiddleware)
app.add_middleware(StripApiPrefixMiddleware)

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
    index = STATIC_DIR / "index.html"
    if index.is_file():
        return FileResponse(index)
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

@app.get("/llm/models")
def get_available_models():
    """Returns available models (Gemini 2.5 / 2.0 and Local Llama) with real-time Ollama status."""
    from utils.model_connection import get_available_models as fetch_models
    return fetch_models()

@app.get("/llm/status")
def get_llm_status(model: Optional[str] = None):
    """Checks LLM connectivity, 401 authentication status, and token health for selected model."""
    return ai_pipeline.check_llm_status(model)

# Interactive Intake Endpoint with Token Continuation & LLM Error Handling
@app.post("/intake/message", response_model=schemas.IntakeResponse)
def process_intake_message(req: schemas.IntakeRequest, db: Session = Depends(get_db)):
    try:
        # Run through LangGraph pipeline with continuation support, multi-model selection, and thinking level
        result = ai_pipeline.run_intake(
            transcript=req.transcript,
            existing_state=req.existing_state,
            is_continuation=req.is_continuation,
            is_summarized=req.is_summarized,
            selected_model=req.selected_model,
            thinking_level=req.thinking_level
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
    # If complete (and not paused for continuation, and no fatal LLM error), persist to database
    if not llm_error and is_complete and not requires_continuation:
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
        extra_question_asked=result.get("extra_question_asked", False),
        is_complete=is_complete,
        action_summary=result.get("action_summary"),
        taking_action_based_on_docs=result.get("taking_action_based_on_docs"),
        doc_status=result.get("doc_status"),
        awaiting_process_confirmation=result.get("awaiting_process_confirmation", False),
        requires_continuation=requires_continuation,
        continuation_prompt=continuation_prompt,
        rights_explanation=result.get("rights_explanation"),
        draft_complaint=result.get("draft_complaint"),
        referral_clinic=result.get("referral_clinic"),
        referral_slot=result.get("referral_slot"),
        chat_history=result.get("chat_history", []),
        case_id=case_id,
        llm_error=llm_error,
        llm_error_details=llm_error_details,
        selected_model=result.get("selected_model", req.selected_model),
        thinking_level=result.get("thinking_level", req.thinking_level)
    )


# Server-Sent Events (SSE) Streaming Intake Endpoint
@app.post("/intake/stream")
async def process_intake_stream(req: schemas.IntakeRequest):
    """
    Streaming endpoint that pushes progressive status, token streams, and final response
    so that the React frontend displays smooth typewriter animations and real-time streaming feedback.
    Handles LLM connection, 401, and token errors with dedicated error SSE events.
    """
    async def event_generator():
        # Step 1: Initial status message
        yield f"data: {json.dumps({'type': 'status', 'content': 'বিবরণ বিশ্লেষণ ও আইনি তথ্য যাচাই করা হচ্ছে...'})}\n\n"
        await asyncio.sleep(0.04)
        
        try:
            # Step 2: Run pipeline asynchronously
            try:
                loop = asyncio.get_event_loop()
                result = await loop.run_in_executor(
                    None,
                    lambda: ai_pipeline.run_intake(
                        transcript=req.transcript,
                        existing_state=req.existing_state,
                        is_continuation=req.is_continuation,
                        is_summarized=req.is_summarized,
                        selected_model=req.selected_model,
                        thinking_level=req.thinking_level
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
                    "extra_question_asked": False,
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
                    "llm_error_details": err_info,
                    "selected_model": req.selected_model,
                    "thinking_level": req.thinking_level
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
            if not llm_error and is_complete and not requires_continuation:
                try:
                    from database import SessionLocal
                    with SessionLocal() as db_session:
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
                        db_session.add(db_case)
                        db_session.commit()
                        db_session.refresh(db_case)
                        case_id = db_case.id
                except Exception as db_err:
                    print(f"[Database Save Warning in Stream] {db_err}")
                
            # Step 3: Stream tokens of assistant response if no fatal LLM error
            text_to_stream = ""
            if llm_error:
                text_to_stream = f"⚠️ ত্রুটি: {llm_error}"
            elif requires_continuation:
                text_to_stream = continuation_prompt or ""
            elif result.get("follow_up_question"):
                text_to_stream = result.get("follow_up_question") or ""
            elif result.get("chat_history") and len(result.get("chat_history")) > 0:
                last_msg = result.get("chat_history")[-1]
                if last_msg.get("role") == "assistant":
                    text_to_stream = last_msg.get("content", "")
            elif safety_flag:
                text_to_stream = safety_message or ""
                    
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
                "extra_question_asked": result.get("extra_question_asked", False),
                "is_complete": is_complete,
                "action_summary": result.get("action_summary"),
                "taking_action_based_on_docs": result.get("taking_action_based_on_docs"),
                "doc_status": result.get("doc_status"),
                "awaiting_process_confirmation": result.get("awaiting_process_confirmation", False),
                "requires_continuation": requires_continuation,
                "continuation_prompt": continuation_prompt,
                "rights_explanation": result.get("rights_explanation"),
                "draft_complaint": result.get("draft_complaint"),
                "referral_clinic": result.get("referral_clinic"),
                "referral_slot": result.get("referral_slot"),
                "chat_history": result.get("chat_history", []),
                "case_id": case_id,
                "llm_error": llm_error,
                "llm_error_details": llm_error_details,
                "selected_model": result.get("selected_model", req.selected_model),
                "thinking_level": result.get("thinking_level", req.thinking_level)
            }
            yield f"data: {json.dumps(final_payload)}\n\n"
        except Exception as outer_err:
            print(f"[Streaming Generator Uncaught Error] {outer_err}")
            err_info = ai_pipeline.parse_llm_error(outer_err)
            yield f"data: {json.dumps({'type': 'error', 'llm_error': err_info['message_bn'], 'llm_error_details': err_info})}\n\n"
            yield f"data: {json.dumps({'type': 'final', 'is_complete': False, 'llm_error': err_info['message_bn']})}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache, no-transform",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )


# Extra LLM Narrative Summarization Endpoint
@app.post("/intake/summarize", response_model=schemas.SummarizeResponse)
async def summarize_intake_narrative(req: schemas.SummarizeRequest):
    """
    Summarizes a long intake narrative using an extra LLM call to fit within token limits
    while preserving all critical legal facts.
    """
    try:
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            None,
            lambda: ai_pipeline.summarize_narrative(req.transcript)
        )
        return result
    except Exception as exc:
        err_info = ai_pipeline.parse_llm_error(exc)
        raise HTTPException(
            status_code=500,
            detail=err_info.get("message_bn") or "বিবরণ সংক্ষেপণে সমস্যা হয়েছে।"
        )


# Profile & Aggressor Details Finalization Endpoint (Right Before Step 4)
@app.post("/intake/finalize_profile", response_model=schemas.FinalizeProfileResponse)
def finalize_profile(req: schemas.FinalizeProfileRequest, db: Session = Depends(get_db)):
    """
    Finalizes the client's personal info (name, division, zilla, thana, union, contact)
    and aggressor info (name, relationship, address) before moving to Step 4.
    Finds the exact regional BRAC Legal Aid Clinic based on location and regenerates the
    formal draft complaint and personalized rights advice.
    """
    # 1. Format applicant's full address
    address_parts = []
    if req.union_village:
        address_parts.append(f"গ্রাম/ইউনিয়ন: {req.union_village.strip()}")
    if req.thana:
        address_parts.append(f"থানা/উপজেলা: {req.thana.strip()}")
    if req.zilla:
        address_parts.append(f"জেলা: {req.zilla.strip()}")
    if req.division:
        address_parts.append(f"বিভাগ: {req.division.strip()}")
    if req.contact_number:
        address_parts.append(f"ফোন: {req.contact_number.strip()}")
    full_address = ", ".join(address_parts) if address_parts else "[ঠিকানা — অপ্রতিষ্ঠিত]"

    # 2. Format aggressor / respondent info
    agg_name = req.aggressor_name.strip() if req.aggressor_name and req.aggressor_name.strip() else "[বিবাদী]"
    agg_parts = [agg_name]
    if req.aggressor_relation and req.aggressor_relation.strip():
        agg_parts.append(f"সম্পর্ক: {req.aggressor_relation.strip()}")
    if req.aggressor_address and req.aggressor_address.strip():
        agg_parts.append(f"ঠিকানা: {req.aggressor_address.strip()}")
    respondent_full = " · ".join(agg_parts)

    # 3. Locate nearest BRAC Legal Aid Clinic using the client's location
    search_loc = f"{req.thana} {req.zilla} {req.division}"
    category = (req.session_state or {}).get("category") or "family_dower_maintenance"
    clinic_info = ai_pipeline.find_nearby_legal_aid_center.invoke({"location": search_loc, "issue_category": category})
    clinic_display = clinic_info.get("formatted_display") or clinic_info.get("clinic_name") or "ব্র্যাক মানবাধিকার ও আইনি সহায়তা কেন্দ্র"
    clinic_slot = clinic_info.get("referral_slot") or "বুধবার, সকাল ১০:০০ টা"
    branch_name = clinic_info.get("clinic_name") or "ব্র্যাক লিগ্যাল এইড ক্লিনিক"

    # 4. Determine applicant display name
    app_display = "[নাম সংরক্ষিত]" if req.is_anonymous else (req.applicant_name.strip() or "[নাম সংরক্ষিত]")

    # 5. Build full factual context for templates
    state_dict = dict(req.session_state or {})
    facts = {
        "applicant_name": app_display,
        "father_name": req.father_name.strip() if req.father_name and req.father_name.strip() else "[পিতার নাম]",
        "address": full_address,
        "respondent": agg_name,
        "respondent_address": req.aggressor_address.strip() if req.aggressor_address else "",
        "branch_name": branch_name,
        "marriage_date": state_dict.get("marriage_date") or "[অপ্রতিষ্ঠিত]",
        "dower_amount": state_dict.get("dower_amount") or "[অপ্রতিষ্ঠিত]",
        "dowry_paid": state_dict.get("dowry_paid") or "[অপ্রতিষ্ঠিত]",
        "unpaid_wages_claim": state_dict.get("unpaid_wages_claim") or "[অপ্রতিষ্ঠিত]",
        "work_period": state_dict.get("work_period") or "[অপ্রতিষ্ঠিত]",
        "current_status": state_dict.get("current_status") or "[চাপ প্রয়োগ করা হইতেছে]",
        "children": state_dict.get("children") or "[সন্তানের বিবরণ উল্লেখ নেই]",
        "evidence": state_dict.get("evidence") or "[অপ্রতিষ্ঠিত]"
    }

    from agent import templates
    draft = templates.generate_draft_complaint(category, facts)

    # 6. Synthesize personalized rights explanation
    rights_exp = state_dict.get("rights_explanation") or templates.RIGHTS_EXPLANATIONS.get(category, templates.RIGHTS_EXPLANATIONS["out_of_scope"])
    if app_display != "[নাম সংরক্ষিত]":
        if any(w in rights_exp for w in ["প্রিয় বোন,", "প্রিয় মহাশয়/মহাশয়া,", "প্রিয় ক্লায়েন্ট,"]):
            rights_exp = re.sub(r"^(প্রিয় বোন,|প্রিয় মহাশয়/মহাশয়া,|প্রিয় ক্লায়েন্ট,)", f"শ্রদ্ধেয় {app_display},", rights_exp)
        else:
            rights_exp = f"শ্রদ্ধেয় {app_display},\n\n" + rights_exp

    # 7. Update DB case record if case_id provided
    case_id = req.case_id or state_dict.get("case_id")
    if case_id:
        case = db.query(models.Case).filter(models.Case.id == case_id).first()
        if case:
            case.applicant_name = app_display
            case.respondent = respondent_full
            case.address = full_address
            case.referral_clinic = clinic_display
            case.referral_slot = clinic_slot
            case.draft_complaint = draft
            case.rights_explanation = rights_exp
            db.commit()
            db.refresh(case)

    # 8. Update session state
    state_dict["applicant_name"] = app_display
    state_dict["respondent"] = respondent_full
    state_dict["address"] = full_address
    state_dict["referral_clinic"] = clinic_display
    state_dict["referral_slot"] = clinic_slot
    state_dict["draft_complaint"] = draft
    state_dict["rights_explanation"] = rights_exp

    return schemas.FinalizeProfileResponse(
        case_id=case_id,
        applicant_name=app_display,
        respondent=respondent_full,
        address=full_address,
        referral_clinic=clinic_display,
        referral_slot=clinic_slot,
        rights_explanation=rights_exp,
        draft_complaint=draft,
        session_state=state_dict
    )

# Voice-to-Profile extraction endpoint for automatic form filling from speech
@app.post("/intake/extract_profile", response_model=schemas.ExtractProfileVoiceResponse)
def extract_profile_from_voice_endpoint(req: schemas.ExtractProfileVoiceRequest):
    """
    Extracts structured personal & aggressor profile info directly from spoken voice transcript or narrative.
    Enables voice-driven automatic form completion without manual typing.
    """
    extracted = ai_pipeline.extract_profile_from_voice(
        voice_transcript=req.voice_transcript,
        chat_history=req.chat_history
    )
    return schemas.ExtractProfileVoiceResponse(**extracted)



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


# --- Draft Complaint Document Export & Print Endpoints ---

def render_draft_complaint_html(case: models.Case) -> str:
    case_id_display = f"ODH-2026-{case.id:04d}" if case.id else "ODH-2026-DRAFT"
    date_display = case.received_at.strftime("%d %B, %Y") if hasattr(case, "received_at") and case.received_at else "১১ সেপ্টেম্বর, ২০২৬"
    category_label = {
        "family_dower_maintenance": "পারিবারিক — দেনমোহর ও ভরণপোষণ",
        "dowry": "যৌতুক সংক্রান্ত বিরোধ ও নির্যাতন",
        "unpaid_wages": "শ্রম ও কর্মসংস্থান — বকেয়া মজুরি আদায়",
        "land_dispute": "ভূমি ও সম্পত্তি সংক্রান্ত বিরোধ",
        "out_of_scope": "অন্যান্য / সাধারণ আইনি বিষয়"
    }.get(case.category, case.category or "পারিবারিক — দেনমোহর ও ভরণপোষণ")
    
    applicant = case.applicant_name or "[নাম সংরক্ষিত]"
    respondent = case.respondent or "[বিবাদী]"
    address = getattr(case, "address", None) or "[ঠিকানা — অপ্রতিষ্ঠিত]"
    clinic = case.referral_clinic or "ব্র্যাক মানবাধিকার ও আইনি সহায়তা কেন্দ্র"
    slot = case.referral_slot or "বুধবার, সকাল ১০:০০ টা"
    status_label = "জরুরি অগ্রাধিকার (URGENT)" if case.status == "URGENT" else "প্রাথমিক খসড়া প্রস্তুত (Draft Prepared)"
    
    draft_body = (case.draft_complaint or "খসড়া অভিযোগপত্র এখনও প্রস্তুত করা হয়নি।").replace("\n", "<br/>")
    draft_body = re.sub(
        r"(\[[^\]]+\])",
        r'<span style="background:#fef3c7;color:#92400e;border:1px dashed #d97706;padding:1px 4px;border-radius:3px;font-weight:600;">\1</span>',
        draft_body
    )

    return f"""<!DOCTYPE html>
<html lang="bn">
<head>
  <meta charset="utf-8" />
  <title>আইনি অভিযোগের খসড়া — {case_id_display}</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Hind+Siliguri:wght@400;600;700;800&display=swap" rel="stylesheet">
  <style>
    @page {{
      size: A4 portrait;
      margin: 15mm;
    }}
    body {{
      font-family: 'Hind Siliguri', -apple-system, BlinkMacSystemFont, sans-serif;
      margin: 0;
      padding: 24px;
      color: #0f172a;
      background: #f8fafc;
      line-height: 1.6;
    }}
    .document-card {{
      max-width: 800px;
      margin: 0 auto;
      background: #ffffff;
      border: 1px solid #e2e8f0;
      border-radius: 10px;
      padding: 40px 48px;
      box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05);
    }}
    @media print {{
      body {{ padding: 0; background: #ffffff; }}
      .document-card {{ border: none; box-shadow: none; padding: 0; }}
      .no-print {{ display: none !important; }}
    }}
    .action-bar {{
      max-width: 800px;
      margin: 0 auto 16px auto;
      display: flex;
      justify-content: space-between;
      align-items: center;
    }}
    .btn-print {{
      background-color: #d92d20;
      color: white;
      border: none;
      padding: 8px 18px;
      font-size: 14px;
      font-weight: 700;
      border-radius: 6px;
      cursor: pointer;
      font-family: inherit;
    }}
  </style>
</head>
<body>
  <div class="action-bar no-print">
    <div style="font-size: 14px; color: #64748b; font-weight: 600;">অধিকার (Odhikar) আইনি অভিযোগপত্র খসড়া ভিউয়ার</div>
    <button class="btn-print" onclick="window.print()">🖨️ প্রিন্ট / PDF সংরক্ষণ করুন</button>
  </div>

  <div class="document-card">
    <!-- HEADER -->
    <div style="display: flex; justify-content: space-between; align-items: flex-start; border-bottom: 2px solid #d92d20; padding-bottom: 12px; margin-bottom: 16px;">
      <div>
        <div style="font-size: 20px; font-weight: 800; color: #d92d20;">অধিকার · ODHIKAR</div>
        <div style="font-size: 15px; font-weight: 700; color: #1e293b;">ব্র্যাক মানবাধিকার ও আইনি সহায়তা কর্মসূচি (HRLS)</div>
        <div style="font-size: 12px; color: #475569;">BRAC Human Rights and Legal Aid Services</div>
      </div>
      <div style="text-align: right;">
        <div style="background: #f1f5f9; border: 1px solid #cbd5e1; border-radius: 6px; padding: 4px 10px; font-weight: 800; font-family: monospace;">
          {case_id_display}
        </div>
        <div style="font-size: 11px; color: #64748b; margin-top: 4px;">তারিখ: <strong>{date_display}</strong></div>
      </div>
    </div>

    <!-- WARNING BANNER -->
    <div style="background-color: #fef2f2; border: 1.5px solid #f87171; border-radius: 6px; padding: 10px 14px; margin-bottom: 18px; font-size: 11.5px; color: #991b1b; line-height: 1.45;">
      <strong>⚠️ খসড়া কপি — প্যারালিগ্যাল পর্যালোচনা ব্যতীত ব্যবহারযোগ্য নয়:</strong><br/>
      এই নথিটি অধিকার এআই কর্তৃক প্রস্তুতকৃত একটি প্রাথমিক অনানুষ্ঠানিক অভিযোগপত্র। ব্র্যাক লিগ্যাল এইড ক্লিনিকের প্যারালিগ্যাল কর্মকর্তা কর্তৃক যাচাই ও চূড়ান্তকরণের পূর্বে আদালতে বা কোনো সরকারি দপ্তরে দাখিলযোগ্য নয়।
    </div>

    <!-- TITLE -->
    <div style="text-align: center; margin-bottom: 16px;">
      <h2 style="margin: 0; font-size: 18px; font-weight: 800; color: #0f172a;">আইনি বিরোধ মীমাংসার অভিযোগপত্র (প্রাথমিক খসড়া)</h2>
      <div style="font-size: 12px; color: #475569; margin-top: 2px;">বিষয়শ্রেণি: <strong>{category_label}</strong> · অবস্থা: {status_label}</div>
    </div>

    <!-- METADATA -->
    <div style="background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 8px; padding: 12px 16px; margin-bottom: 20px; font-size: 12px;">
      <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 8px 16px;">
        <div><strong>অভিযোগকারী:</strong> {applicant}</div>
        <div><strong>বিবাদী:</strong> {respondent}</div>
        <div><strong>ঠিকানা:</strong> {address}</div>
        <div><strong>ক্লিনিক:</strong> {clinic} ({slot})</div>
      </div>
    </div>

    <!-- BODY -->
    <div style="border: 1px solid #cbd5e1; border-radius: 8px; padding: 20px; margin-bottom: 24px; font-size: 13.5px; line-height: 1.85; text-align: justify; background: #ffffff;">
      {draft_body}
    </div>

    <!-- SIGNATURES -->
    <div style="border-top: 1.5px dashed #94a3b8; padding-top: 16px; display: grid; grid-template-columns: 1fr 1fr; gap: 24px; margin-top: 24px;">
      <div>
        <div style="font-size: 11px; color: #475569;">উপরে উল্লেখিত বিবরণ আমার জানা মতে সত্য।</div>
        <div style="border-bottom: 1px solid #0f172a; width: 180px; margin-top: 40px;"></div>
        <div style="font-size: 11px; font-weight: 700; margin-top: 4px;">অভিযোগকারীর স্বাক্ষর / টিপসহি</div>
      </div>
      <div style="text-align: right;">
        <div style="font-size: 11px; color: #475569;">প্যারালিগ্যাল কর্মকর্তা কর্তৃক পরীক্ষিত ও সুপারিশকৃত।</div>
        <div style="border-bottom: 1px solid #0f172a; width: 220px; margin-top: 40px; margin-left: auto;"></div>
        <div style="font-size: 11px; font-weight: 700; margin-top: 4px;">প্যারালিগ্যাল কর্মকর্তার স্বাক্ষর ও সিল</div>
      </div>
    </div>

    <!-- FOOTER -->
    <div style="border-top: 1px solid #e2e8f0; padding-top: 10px; margin-top: 24px; font-size: 10px; color: #94a3b8; display: flex; justify-content: space-between;">
      <span>অধিকার (Odhikar) AI Paralegal · ব্র্যাক আইটি কোডস্প্রিন্ট ২০২৬ | হেল্পলাইন: ১৬৪৩০</span>
      <span>DRAFT ONLY</span>
    </div>
  </div>
</body>
</html>"""


@app.get("/cases/{case_id}/draft/html", response_class=HTMLResponse)
def get_case_draft_html(case_id: int, db: Session = Depends(get_db)):
    """Returns a standalone, high-fidelity printable HTML document for the case draft complaint."""
    case = db.query(models.Case).filter(models.Case.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    return HTMLResponse(content=render_draft_complaint_html(case))


@app.get("/cases/{case_id}/draft/download")
def download_case_draft_txt(case_id: int, db: Session = Depends(get_db)):
    """Downloads the draft complaint as a clean text document."""
    case = db.query(models.Case).filter(models.Case.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    
    content = case.draft_complaint or "খসড়া অভিযোগপত্র এখনও প্রস্তুত করা হয়নি।"
    filename = f"draft_complaint_case_{case.id}.txt"
    return Response(
        content=content,
        media_type="text/plain; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'}
    )


# ---- Production SPA (Cloud Run) ----
_API_PREFIXES = (
    "cases",
    "intake",
    "tts",
    "transcribe",
    "llm",
    "docs",
    "openapi.json",
    "redoc",
)

if (STATIC_DIR / "assets").is_dir():
    app.mount("/assets", StaticFiles(directory=STATIC_DIR / "assets"), name="assets")


@app.get("/{full_path:path}")
def spa_fallback(full_path: str):
    """Serve built frontend files; fall back to index.html for client routes."""
    if not STATIC_DIR.is_dir():
        raise HTTPException(status_code=404, detail="Not found")

    first = full_path.split("/", 1)[0]
    if first in _API_PREFIXES:
        raise HTTPException(status_code=404, detail="Not found")

    candidate = STATIC_DIR / full_path
    if candidate.is_file():
        return FileResponse(candidate)

    index = STATIC_DIR / "index.html"
    if index.is_file():
        return FileResponse(index)
    raise HTTPException(status_code=404, detail="Not found")
