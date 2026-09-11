"""
Prompt templates for Odhikar AI Paralegal.
Tailored for Bengali colloquial speech, regional accents, and BRAC Legal Aid case types.

Now powered by PromptBuilder — loads prompts dynamically from prompt_config.yaml.
The module-level constants below are backward-compatible aliases so existing code
(e.g. `prompts.CLASSIFICATION_SYSTEM_PROMPT`) continues to work without changes.
"""

from prompt_builder import get_prompt_builder

_pb = get_prompt_builder()

# Backward-compatible aliases — these read from prompt_config.yaml at import time.
# To hot-reload, call: prompts._pb.reload(); prompts._refresh()
CLASSIFICATION_SYSTEM_PROMPT = _pb.get_system_prompt("classification")
SAFETY_SYSTEM_PROMPT = _pb.get_system_prompt("safety")
EXTRACTION_SYSTEM_PROMPT = _pb.get_system_prompt("extraction")
INTAKE_DIALOGUE_SYSTEM_PROMPT = _pb.get_system_prompt("intake_dialogue")
FOLLOW_UP_SYSTEM_PROMPT = _pb.get_system_prompt("follow_up")
DYNAMIC_SOLUTION_SYSTEM_PROMPT = _pb.get_system_prompt("dynamic_solution")


def _refresh():
    """Refresh all module-level prompt constants from the config.
    Call after _pb.reload() to update the aliases."""
    global CLASSIFICATION_SYSTEM_PROMPT, SAFETY_SYSTEM_PROMPT, EXTRACTION_SYSTEM_PROMPT
    global INTAKE_DIALOGUE_SYSTEM_PROMPT, FOLLOW_UP_SYSTEM_PROMPT, DYNAMIC_SOLUTION_SYSTEM_PROMPT
    CLASSIFICATION_SYSTEM_PROMPT = _pb.get_system_prompt("classification")
    SAFETY_SYSTEM_PROMPT = _pb.get_system_prompt("safety")
    EXTRACTION_SYSTEM_PROMPT = _pb.get_system_prompt("extraction")
    INTAKE_DIALOGUE_SYSTEM_PROMPT = _pb.get_system_prompt("intake_dialogue")
    FOLLOW_UP_SYSTEM_PROMPT = _pb.get_system_prompt("follow_up")
    DYNAMIC_SOLUTION_SYSTEM_PROMPT = _pb.get_system_prompt("dynamic_solution")
