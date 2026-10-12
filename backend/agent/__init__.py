"""
Odhikar AI Paralegal - LangGraph Agent Package.
Contains all LangGraph workflow nodes, prompt templates, legal templates,
and dialogue managers.
"""

from .ai_pipeline import (
    run_intake,
    summarize_narrative,
    check_llm_status,
    parse_llm_error,
    is_model_configured,
    get_whisper,
    BANGLA_WHISPER_PROMPT,
    normalize_bangla_transcript,
    find_nearby_legal_aid_center,
    extract_profile_from_voice,
    IntakeState,
    LEGAL_AID_CLINIC_DIRECTORY,
    odhikar_graph,
)

from . import prompts
from . import templates
from .prompt_builder import get_prompt_builder

__all__ = [
    "run_intake",
    "summarize_narrative",
    "check_llm_status",
    "parse_llm_error",
    "is_model_configured",
    "get_whisper",
    "BANGLA_WHISPER_PROMPT",
    "normalize_bangla_transcript",
    "find_nearby_legal_aid_center",
    "extract_profile_from_voice",
    "IntakeState",
    "LEGAL_AID_CLINIC_DIRECTORY",
    "odhikar_graph",
    "prompts",
    "templates",
    "get_prompt_builder",
]
