"""
Odhikar Legal Aid NLP Benchmark and Evaluation Suite.
"""

from .metrics import (
    calculate_classification_metrics,
    calculate_safety_metrics,
    calculate_slot_metrics,
    calculate_summarization_faithfulness,
    LatencyTracker
)
from .export_latex import (
    generate_intent_latex_table,
    generate_safety_latex_table,
    generate_full_evaluation_latex
)

__all__ = [
    "calculate_classification_metrics",
    "calculate_safety_metrics",
    "calculate_slot_metrics",
    "calculate_summarization_faithfulness",
    "LatencyTracker",
    "generate_intent_latex_table",
    "generate_safety_latex_table",
    "generate_full_evaluation_latex",
]

