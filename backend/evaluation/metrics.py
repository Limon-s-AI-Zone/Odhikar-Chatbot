"""
Evaluation metrics for Bengali Legal NLP tasks.
Includes classification metrics (Accuracy, Macro-F1), safety-critical metrics (Recall, FPR),
fact extraction metrics (Exact Match, Slot F1), and runtime profiling.
"""

from typing import List, Dict, Any, Optional
import math


def calculate_classification_metrics(
    predictions: List[str],
    ground_truths: List[str]
) -> Dict[str, Any]:
    """Calculates Multi-Class Accuracy, Macro-F1, Micro-F1, and per-class Precision/Recall."""
    if not ground_truths or len(predictions) != len(ground_truths):
        raise ValueError("Predictions and ground truths must be non-empty and of equal length.")

    classes = sorted(list(set(ground_truths + predictions)))
    total = len(ground_truths)
    correct = sum(1 for p, g in zip(predictions, ground_truths) if p == g)
    accuracy = correct / total

    per_class = {}
    macro_precisions = []
    macro_recalls = []
    macro_f1s = []

    for c in classes:
        tp = sum(1 for p, g in zip(predictions, ground_truths) if p == c and g == c)
        fp = sum(1 for p, g in zip(predictions, ground_truths) if p == c and g != c)
        fn = sum(1 for p, g in zip(predictions, ground_truths) if p != c and g == c)

        prec = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        rec = tp / (fn + tp) if (fn + tp) > 0 else 0.0
        f1 = (2 * prec * rec) / (prec + rec) if (prec + rec) > 0 else 0.0

        per_class[c] = {
            "precision": round(prec, 4),
            "recall": round(rec, 4),
            "f1": round(f1, 4),
            "support": sum(1 for g in ground_truths if g == c)
        }
        macro_precisions.append(prec)
        macro_recalls.append(rec)
        macro_f1s.append(f1)

    return {
        "accuracy": round(accuracy, 4),
        "macro_precision": round(sum(macro_precisions) / len(macro_precisions), 4),
        "macro_recall": round(sum(macro_recalls) / len(macro_recalls), 4),
        "macro_f1": round(sum(macro_f1s) / len(macro_f1s), 4),
        "per_class": per_class,
        "sample_count": total
    }


def calculate_safety_metrics(
    predictions: List[bool],
    ground_truths: List[bool]
) -> Dict[str, Any]:
    """
    Calculates safety sensitivity/recall and False Positive Rate (FPR).
    In legal aid safety escalation, Safety Recall MUST be 100% (0 False Negatives).
    """
    tp = sum(1 for p, g in zip(predictions, ground_truths) if p is True and g is True)
    fp = sum(1 for p, g in zip(predictions, ground_truths) if p is True and g is False)
    tn = sum(1 for p, g in zip(predictions, ground_truths) if p is False and g is False)
    fn = sum(1 for p, g in zip(predictions, ground_truths) if p is False and g is True)

    total_positives = tp + fn
    total_negatives = tn + fp

    safety_recall = (tp / total_positives) if total_positives > 0 else 1.0
    specificity = (tn / total_negatives) if total_negatives > 0 else 1.0
    fpr = (fp / total_negatives) if total_negatives > 0 else 0.0
    fnr = (fn / total_positives) if total_positives > 0 else 0.0

    return {
        "safety_recall": round(safety_recall, 4),
        "false_negative_rate": round(fnr, 4),
        "false_positive_rate": round(fpr),
        "specificity": round(specificity, 4),
        "tp": tp,
        "fp": fp,
        "tn": tn,
        "fn": fn,
        "zero_fn_guarantee": fn == 0
    }


def normalize_val(val: Any) -> Any:
    """Normalizes string/numeric values for slot exact matching."""
    if val is None:
        return None
    if isinstance(val, (int, float)):
        return float(val)
    if isinstance(val, str):
        cleaned = val.strip().replace(",", "")
        try:
            return float(cleaned)
        except ValueError:
            return cleaned.lower()
    return str(val)


def calculate_slot_metrics(
    predicted_slots_list: List[Dict[str, Any]],
    gold_slots_list: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Evaluates slot/fact extraction accuracy: Exact Match (EM), Slot Recall, Slot Precision.
    Handles numeric values and strings.
    """
    total_gold_slots = 0
    total_pred_slots = 0
    exact_matches = 0

    for pred, gold in zip(predicted_slots_list, gold_slots_list):
        total_gold_slots += len(gold)
        total_pred_slots += len(pred)
        for k, g_val in gold.items():
            p_val = pred.get(k)
            if p_val is not None and normalize_val(p_val) == normalize_val(g_val):
                exact_matches += 1

    precision = exact_matches / total_pred_slots if total_pred_slots > 0 else 0.0
    recall = exact_matches / total_gold_slots if total_gold_slots > 0 else 0.0
    f1 = (2 * precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0

    return {
        "slot_exact_match_ratio": round(recall, 4),
        "slot_precision": round(precision, 4),
        "slot_recall": round(recall, 4),
        "slot_f1": round(f1, 4),
        "matched_slots": exact_matches,
        "total_gold_slots": total_gold_slots,
        "total_predicted_slots": total_pred_slots
    }


class LatencyTracker:
    """Tracks latency statistics across benchmark evaluation runs."""
    def __init__(self):
        self.latencies: List[float] = []

    def record(self, latency_ms: float):
        self.latencies.append(latency_ms)

    def summary(self) -> Dict[str, float]:
        if not self.latencies:
            return {"mean_ms": 0.0, "min_ms": 0.0, "max_ms": 0.0, "p95_ms": 0.0}
        sorted_l = sorted(self.latencies)
        p95_idx = int(math.ceil(len(sorted_l) * 0.95)) - 1
        return {
            "mean_ms": round(sum(sorted_l) / len(sorted_l), 2),
            "min_ms": round(sorted_l[0], 2),
            "max_ms": round(sorted_l[-1], 2),
            "p95_ms": round(sorted_l[max(0, p95_idx)], 2),
            "count": len(sorted_l)
        }


def calculate_summarization_faithfulness(
    original_texts: List[str],
    summarized_texts: List[str]
) -> Dict[str, Any]:
    """
    Evaluates factual faithfulness and hallucination rate during token summarization.
    Checks:
    1. Numerical preservation: whether numbers in the original text are retained in the summary.
    2. Number hallucination: whether the summary introduced numbers NOT in the original text.
    """
    import re
    # Match both Bengali digits (০-৯) and English digits (0-9)
    num_pattern = re.compile(r'[\d০-৯]+')

    total_orig_nums = 0
    preserved_nums = 0
    hallucinated_nums = 0

    for orig, summ in zip(original_texts, summarized_texts):
        orig_set = set(num_pattern.findall(orig))
        summ_set = set(num_pattern.findall(summ))

        total_orig_nums += len(orig_set)
        preserved_nums += len(orig_set.intersection(summ_set))
        hallucinated_nums += len(summ_set.difference(orig_set))

    preservation_rate = (preserved_nums / total_orig_nums) if total_orig_nums > 0 else 1.0
    hallucination_rate = (hallucinated_nums / len(summarized_texts)) if summarized_texts else 0.0

    return {
        "numerical_preservation_rate": round(preservation_rate, 4),
        "hallucinated_numbers_per_sample": round(hallucination_rate, 4),
        "total_original_numbers": total_orig_nums,
        "preserved_numbers": preserved_nums,
        "hallucinated_numbers": hallucinated_nums,
        "faithfulness_verdict": "HIGH" if hallucinated_nums == 0 and preservation_rate >= 0.8 else "RISK_OF_HALLUCINATION"
    }


