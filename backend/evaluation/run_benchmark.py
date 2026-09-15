"""
CLI Benchmark Runner for Odhikar Legal Aid NLP.
Executes standardized evaluation suites for:
1. Legal Intent & Category Classification
2. Safety Breakout & Emergency Hotlines Sensitivity
3. Fact Extraction & Legal Arithmetic
4. Latency & Token Efficiency Profiling

Usage:
    python -m evaluation.run_benchmark --task all
    python -m evaluation.run_benchmark --task intent
    python -m evaluation.run_benchmark --task safety
    python -m evaluation.run_benchmark --task facts --export-latex paper_tables.tex
"""

import sys
import os
import json
import time
import argparse
from typing import Dict, Any, List

# Ensure backend root is on sys.path
backend_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if backend_root not in sys.path:
    sys.path.insert(0, backend_root)

# Set UTF-8 encoding
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from evaluation.metrics import (
    calculate_classification_metrics,
    calculate_safety_metrics,
    calculate_slot_metrics,
    LatencyTracker,
)
from evaluation.export_latex import (
    generate_intent_latex_table,
    generate_safety_latex_table,
    generate_full_evaluation_latex,
)

ai_pipeline = None

def get_pipeline():
    global ai_pipeline
    if ai_pipeline is None:
        try:
            from agent import ai_pipeline as pipeline_mod
            ai_pipeline = pipeline_mod
        except Exception as e:
            raise RuntimeError(f"Could not import agent.ai_pipeline: {e}. Check your virtualenv and requirements.")
    return ai_pipeline



BENCHMARK_PATH = os.path.join(
    os.path.dirname(__file__), "datasets", "benchmark_cases.json"
)


def load_benchmark_dataset() -> Dict[str, Any]:
    if not os.path.exists(BENCHMARK_PATH):
        raise FileNotFoundError(f"Benchmark file not found at: {BENCHMARK_PATH}")
    with open(BENCHMARK_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def evaluate_intent_classification(cases: List[Dict[str, Any]], latency_tracker: LatencyTracker, mock: bool = False) -> Dict[str, Any]:
    print("\n" + "=" * 65)
    print("▶ Evaluating Task 1: Legal Intent & Category Classification")
    print("=" * 65)

    preds = []
    golds = []
    pipeline = None if mock else get_pipeline()

    for item in cases:
        narrative = item["narrative"]
        gold = item["gold_category"]

        start_t = time.perf_counter()
        if mock:
            # Deterministic mock simulation for testing/CI
            time.sleep(0.02)
            elapsed_ms = (time.perf_counter() - start_t) * 1000.0
            latency_tracker.record(elapsed_ms)
            pred = gold
        else:
            try:
                res = pipeline.run_intake(transcript=narrative)
                elapsed_ms = (time.perf_counter() - start_t) * 1000.0
                latency_tracker.record(elapsed_ms)

                # Check for disambiguation vs category
                if item.get("disambiguation_needed") and res.get("disambiguation_needed"):
                    pred = "ambiguous"
                else:
                    pred = res.get("category") or "unknown"
            except Exception as e:
                print(f"  [ERROR] {item['id']}: {e}")
                pred = "error"

        preds.append(pred)
        golds.append(gold)

        status_mark = "✓" if pred == gold else "✗"
        print(f"  [{status_mark}] {item['id']}: Gold='{gold}' | Pred='{pred}' ({item['description']})")

    metrics = calculate_classification_metrics(preds, golds)
    print("\n--- Intent Classification Summary ---")
    print(f"  Accuracy:        {metrics['accuracy'] * 100:.2f}%")
    print(f"  Macro Precision: {metrics['macro_precision']:.4f}")
    print(f"  Macro Recall:    {metrics['macro_recall']:.4f}")
    print(f"  Macro F1-Score:  {metrics['macro_f1']:.4f}")
    return metrics


def evaluate_safety_breakout(cases: List[Dict[str, Any]], latency_tracker: LatencyTracker, mock: bool = False) -> Dict[str, Any]:
    print("\n" + "=" * 65)
    print("▶ Evaluating Task 2: Safety Breakout Sensitivity (0 FN Target)")
    print("=" * 65)

    preds = []
    golds = []
    pipeline = None if mock else get_pipeline()

    for item in cases:
        narrative = item["narrative"]
        gold_flag = item["gold_safety_flag"]

        start_t = time.perf_counter()
        if mock:
            time.sleep(0.015)
            elapsed_ms = (time.perf_counter() - start_t) * 1000.0
            latency_tracker.record(elapsed_ms)
            pred_flag = gold_flag
        else:
            try:
                res = pipeline.run_intake(transcript=narrative)
                elapsed_ms = (time.perf_counter() - start_t) * 1000.0
                latency_tracker.record(elapsed_ms)
                pred_flag = bool(res.get("safety_flag"))
            except Exception as e:
                print(f"  [ERROR] {item['id']}: {e}")
                pred_flag = False

        preds.append(pred_flag)
        golds.append(gold_flag)

        status_mark = "✓" if pred_flag == gold_flag else "✗"
        print(f"  [{status_mark}] {item['id']}: Gold={gold_flag} | Pred={pred_flag} ({item['description']})")

    metrics = calculate_safety_metrics(preds, golds)
    print("\n--- Safety Breakout Summary ---")
    print(f"  Safety Sensitivity (Recall): {metrics['safety_recall'] * 100:.2f}%")
    print(f"  Specificity:                 {metrics['specificity'] * 100:.2f}%")
    print(f"  False Positive Rate (FPR):   {metrics['false_positive_rate'] * 100:.2f}%")
    print(f"  Missed Emergencies (FN):     {metrics['fn']} (Target: 0)")
    print(f"  Zero FN Safety Guarantee:    {'PASSED ✓' if metrics['zero_fn_guarantee'] else 'FAILED ✗'}")
    return metrics


def evaluate_fact_extraction(cases: List[Dict[str, Any]], latency_tracker: LatencyTracker, mock: bool = False) -> Dict[str, Any]:
    print("\n" + "=" * 65)
    print("▶ Evaluating Task 3: Fact & Numerical Arithmetic Extraction")
    print("=" * 65)

    pred_facts_list = []
    gold_facts_list = []
    pipeline = None if mock else get_pipeline()

    for item in cases:
        narrative = item["narrative"]
        gold_facts = item["gold_facts"]

        start_t = time.perf_counter()
        if mock:
            time.sleep(0.025)
            elapsed_ms = (time.perf_counter() - start_t) * 1000.0
            latency_tracker.record(elapsed_ms)
            extracted_facts = dict(gold_facts)
        else:
            try:
                res = pipeline.run_intake(transcript=narrative)
                elapsed_ms = (time.perf_counter() - start_t) * 1000.0
                latency_tracker.record(elapsed_ms)
                extracted_facts = res.get("facts") or {}
            except Exception as e:
                print(f"  [ERROR] {item['id']}: {e}")
                extracted_facts = {}

        pred_facts_list.append(extracted_facts)
        gold_facts_list.append(gold_facts)

        print(f"  [*] {item['id']} ({item['category']}):")
        print(f"      Gold: {gold_facts}")
        print(f"      Pred: {extracted_facts}")

    metrics = calculate_slot_metrics(pred_facts_list, gold_facts_list)
    print("\n--- Fact Extraction Summary ---")
    print(f"  Slot Exact Match Ratio: {metrics['slot_exact_match_ratio'] * 100:.2f}%")
    print(f"  Slot Precision:         {metrics['slot_precision']:.4f}")
    print(f"  Slot Recall:            {metrics['slot_recall']:.4f}")
    print(f"  Slot F1-Score:          {metrics['slot_f1']:.4f}")
    return metrics


def main():
    parser = argparse.ArgumentParser(description="Odhikar Legal Aid NLP Benchmark Suite")
    parser.add_argument(
        "--task",
        choices=["all", "intent", "safety", "facts"],
        default="all",
        help="Task benchmark to run (default: all)"
    )
    parser.add_argument(
        "--output-json",
        type=str,
        default=None,
        help="Path to save evaluation output as JSON"
    )
    parser.add_argument(
        "--export-latex",
        type=str,
        default=None,
        help="Path to export evaluation tables in LaTeX"
    )
    parser.add_argument(
        "--model",
        type=str,
        default=None,
        help="Override MODEL_NAME for this evaluation run"
    )
    parser.add_argument(
        "--mock",
        action="store_true",
        help="Run benchmark in simulated deterministic mock mode (for fast testing/CI)"
    )

    args = parser.parse_args()

    if args.model:
        os.environ["MODEL_NAME"] = args.model
        print(f"[Config] Evaluated Model Override: {args.model}")
    if args.mock:
        print("[Config] Running in MOCK evaluation mode.")

    dataset = load_benchmark_dataset()
    latency_tracker = LatencyTracker()
    results: Dict[str, Any] = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "model": os.getenv("MODEL_NAME", "mock" if args.mock else "default"),
        "tasks_evaluated": args.task,
        "is_mock": args.mock,
    }

    print("\n" + "#" * 65)
    print("   ODHIKAR LEGAL AID NLP RESEARCH BENCHMARK EVALUATOR")
    print("#" * 65)

    tasks_data = dataset.get("tasks", {})

    if args.task in ("all", "intent"):
        results["intent_classification"] = evaluate_intent_classification(
            tasks_data.get("intent_classification", []), latency_tracker, mock=args.mock
        )

    if args.task in ("all", "safety"):
        results["safety_breakout"] = evaluate_safety_breakout(
            tasks_data.get("safety_breakout", []), latency_tracker, mock=args.mock
        )

    if args.task in ("all", "facts"):
        results["fact_extraction"] = evaluate_fact_extraction(
            tasks_data.get("fact_extraction", []), latency_tracker, mock=args.mock
        )

    # Latency Summary
    lat_summary = latency_tracker.summary()
    results["latency_ms"] = lat_summary
    print("\n" + "=" * 65)
    print("▶ Runtime Latency Profile")
    print("=" * 65)
    print(f"  Mean Latency: {lat_summary['mean_ms']} ms")
    print(f"  P95 Latency:  {lat_summary['p95_ms']} ms")
    print(f"  Min / Max:    {lat_summary['min_ms']} ms / {lat_summary['max_ms']} ms")

    # Export results
    if args.output_json:
        with open(args.output_json, "w", encoding="utf-8") as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        print(f"\n[✓] Results saved to JSON: {args.output_json}")

    if args.export_latex:
        latex_str = generate_full_evaluation_latex(results)
        with open(args.export_latex, "w", encoding="utf-8") as f:
            f.write(latex_str)
        print(f"[✓] LaTeX tables exported to: {args.export_latex}")

    print("\n[✓] Benchmark execution complete.\n")


if __name__ == "__main__":
    main()
