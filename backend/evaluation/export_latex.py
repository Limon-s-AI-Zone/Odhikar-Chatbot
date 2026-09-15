"""
Generates publication-ready LaTeX tables for research papers from evaluation benchmark results.
Supports ACL, EMNLP, NeurIPS, and IEEE formatting.
"""

from typing import Dict, Any, List


def generate_intent_latex_table(results: Dict[str, Any], caption: str = "Legal Intent Classification Performance") -> str:
    """Generates LaTeX code for Intent Classification table."""
    metrics = results.get("intent_classification", {})
    per_class = metrics.get("per_class", {})

    lines = [
        r"\begin{table}[ht]",
        r"\centering",
        r"\small",
        r"\begin{tabular}{lcccc}",
        r"\toprule",
        r"\textbf{Legal Category} & \textbf{Precision} & \textbf{Recall} & \textbf{F1-Score} & \textbf{Support} \\",
        r"\midrule"
    ]

    for cat_name, stats in per_class.items():
        clean_name = cat_name.replace("_", r"\_").title()
        p = f"{stats['precision']:.3f}"
        r = f"{stats['recall']:.3f}"
        f1 = f"{stats['f1']:.3f}"
        supp = str(stats['support'])
        lines.append(f"{clean_name} & {p} & {r} & {f1} & {supp} \\\\")

    lines.append(r"\midrule")
    macro_p = f"{metrics.get('macro_precision', 0):.3f}"
    macro_r = f"{metrics.get('macro_recall', 0):.3f}"
    macro_f1 = f"{metrics.get('macro_f1', 0):.3f}"
    total = str(metrics.get("sample_count", 0))
    lines.append(rf"\textbf{{Macro Average}} & \textbf{{{macro_p}}} & \textbf{{{macro_r}}} & \textbf{{{macro_f1}}} & \textbf{{{total}}} \\\\")
    acc = f"{metrics.get('accuracy', 0)*100:.1f}\\%"
    lines.append(rf"\textbf{{Overall Accuracy}} & \multicolumn{{4}}{{c}}{{\textbf{{{acc}}}}} \\\\")
    lines.extend([
        r"\bottomrule",
        r"\end{tabular}",
        rf"\caption{{{caption}}}",
        r"\label{tab:intent_classification}",
        r"\end{table}"
    ])

    return "\n".join(lines)


def generate_safety_latex_table(safety_results: Dict[str, Any], caption: str = "Safety Escalation and Emergency Breakout Sensitivity") -> str:
    """Generates LaTeX code for Safety Evaluation table."""
    rec = f"{safety_results.get('safety_recall', 0)*100:.1f}\\%"
    fpr = f"{safety_results.get('false_positive_rate', 0)*100:.1f}\\%"
    spec = f"{safety_results.get('specificity', 0)*100:.1f}\\%"
    fn = str(safety_results.get('fn', 0))
    zero_fn = r"\checkmark \textbf{Yes}" if safety_results.get("zero_fn_guarantee") else r"\textbf{No}"

    lines = [
        r"\begin{table}[ht]",
        r"\centering",
        r"\small",
        r"\begin{tabular}{lc}",
        r"\toprule",
        r"\textbf{Safety Metric} & \textbf{Value} \\",
        r"\midrule",
        rf"Safety Detection Sensitivity (Recall) & {rec} \\\\",
        rf"False Positive Rate (FPR) & {fpr} \\\\",
        rf"Specificity & {spec} \\\\",
        rf"Critical False Negatives (Missed Danger) & {fn} \\\\",
        rf"Zero False Negative Guarantee & {zero_fn} \\\\",
        r"\bottomrule",
        r"\end{tabular}",
        rf"\caption{{{caption}}}",
        r"\label{tab:safety_breakout}",
        r"\end{table}"
    ]

    return "\n".join(lines)


def generate_full_evaluation_latex(benchmark_results: Dict[str, Any]) -> str:
    """Generates combined LaTeX tables for all benchmark tasks."""
    tables = []
    if "intent_classification" in benchmark_results:
        tables.append(generate_intent_latex_table(benchmark_results))
    if "safety_breakout" in benchmark_results:
        tables.append(generate_safety_latex_table(benchmark_results["safety_breakout"]))
    return "\n\n".join(tables)
