import time
import logging
from typing import Callable, Dict, Any, Optional
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

# Configure logger for AI pipeline requests and safety auditing
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] [AI Middleware] %(message)s"
)
logger = logging.getLogger("ai_pipeline_middleware")

class AIPipelineMiddleware(BaseHTTPMiddleware):
    """
    Middleware dedicated to monitoring, logging, and guarding AI pipeline requests.
    - Measures end-to-end execution latency for LLM inference (ensuring ~5s latency SLA).
    - Logs safety breakouts and token budgets.
    - Handles exceptions gracefully and adds custom X-AI-Response-Time headers.
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Check if the request is destined for the AI intake pipeline
        is_ai_route = request.url.path.startswith("/intake")

        if not is_ai_route:
            return await call_next(request)

        start_time = time.perf_counter()
        logger.info(f"Incoming AI request: {request.method} {request.url.path} from {request.client.host if request.client else 'unknown'}")

        try:
            response = await call_next(request)
            process_time = time.perf_counter() - start_time
            response.headers["X-AI-Execution-Time"] = f"{process_time:.3f}s"
            
            logger.info(f"AI request completed: {request.url.path} in {process_time:.3f}s (Status: {response.status_code})")
            return response

        except Exception as exc:
            process_time = time.perf_counter() - start_time
            logger.error(f"AI Pipeline failed after {process_time:.3f}s: {str(exc)}", exc_info=True)
            raise exc

def audit_safety_event(user_text: str, safety_flag: bool, category: Optional[str] = None):
    """
    Audits safety check results for paralegal compliance and emergency records.
    """
    if safety_flag:
        logger.warning(f"🚨 [SAFETY EMERGENCY TRIGGERED] Client narrative contained violence/threat: '{user_text[:80]}...'")
    else:
        logger.info(f"✅ [SAFE INTAKE] Category: {category or 'General'} | Text: '{user_text[:50]}...'")

def validate_narrative_input(text: str) -> bool:
    """
    Pre-checks narrative string before feeding into LangGraph.
    """
    if not text or not text.strip():
        return False
    # Max reasonable narrative character limit (e.g. 50,000 characters)
    if len(text) > 50000:
        logger.warning("Narrative exceeds max characters limit.")
        return False
    return True
