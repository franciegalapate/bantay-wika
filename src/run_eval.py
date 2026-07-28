"""Bantay-Wika eval runner.

Examples
--------
# Offline plumbing test (no API key, no cost):
python src/run_eval.py --provider mock --no-judge

# Real run on the first 3 items with a free OpenRouter model:
python src/run_eval.py --provider openrouter --model "nvidia/nemotron-3-ultra-550b-a55b:free" --limit 3

# Full run with a separate, stronger judge:
python src/run_eval.py --provider openrouter --model "nvidia/nemotron-3-ultra-550b-a55b:free" --judge-model "qwen/qwen3.6-flash"
"""
from __future__ import annotations
import argparse
import json
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path

# Make sibling modules importable and locate the repo root.
HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(HERE))

from models import get_provider          # noqa: E402
from grader import grade                 # noqa: E402

try:
    from dotenv import load_dotenv
    load_dotenv(ROOT / ".env")
except Exception:
    pass  # dotenv is optional; env vars can be set another way

SYSTEM_PROMPT = ""  # left empty so we test the model's default behavior


def load_items(path):
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(data, list):
        raise ValueError("items file must be a JSON array of item objects")
    return data


def aggregate(results):
    scored = [r for r in results if not r.get("error")]
    by_cat = defaultdict(list)
    for r in scored:
        by_cat[r["category"]].append(r["score"])
    cat_scores = {c: sum(v) / len(v) for c, v in by_cat.items()}
    overall = sum(r["score"] for r in scored) / len(scored) if scored else 0.0
    return overall, cat_scores


def print_table(overall, cat_scores, results):
    scored = [r for r in results if not r.get("error")]
    errored = [r for r in results if r.get("error")]
    counts = defaultdict(int)
    for r in scored:
        counts[r["category"]] += 1
    print("\n" + "=" * 46)
    print(f"{'CATEGORY':<22}{'SCORE':>10}{'ITEMS':>10}")
    print("-" * 46)
    for c in sorted(cat_scores):
        print(f"{c:<22}{cat_scores[c]*100:>9.1f}%{counts[c]:>10}")
    print("-" * 46)
    print(f"{'OVERALL':<22}{overall*100:>9.1f}%{len(scored):>10}")
    if errored:
        print(f"{'ERRORED (excluded)':<22}{'':>10}{len(errored):>10}")
    print("=" * 46)


def write_report(model_name, overall, cat_scores, results, out_dir):
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    (out / "results.json").write_text(
        json.dumps({"model": model_name, "overall": overall, "results": results},
                   ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    scored = [r for r in results if not r.get("error")]
    errored = [r for r in results if r.get("error")]
    n_note = f"n={len(scored)} scored" + (f", {len(errored)} errored/excluded" if errored else "")
    lines = [f"# Bantay-Wika results: {model_name}", "",
             f"**Overall:** {overall:.1%}  ({n_note})", "",
             "| Category | Score |", "|---|---|"]
    for c in sorted(cat_scores):
        lines.append(f"| {c} | {cat_scores[c]:.1%} |")
    lines += ["", "## Failing items (score < 0.5)", ""]
    for r in scored:
        if r["score"] < 0.5:
            why = r["judge_rationale"] or f"rule miss: {r['rule_detail']}"
            lines.append(f"- **{r['id']}** ({r['category']}) - {r['score']:.2f}: {why}")
    if errored:
        lines += ["", "## Errored / incomplete (not scored)", ""]
        for r in errored:
            lines.append(f"- **{r['id']}** ({r['category']}): {r['judge_rationale']}")
    (out / "report.md").write_text("\n".join(lines), encoding="utf-8")
    return out


def main():
    ap = argparse.ArgumentParser(description="Bantay-Wika cultural-bias eval")
    ap.add_argument("--provider", default="openrouter", help="openrouter | mock")
    ap.add_argument("--model", default=None,
                    help='e.g. "nvidia/nemotron-3-ultra-550b-a55b:free"')
    ap.add_argument("--judge-provider", default=None,
                    help="defaults to --provider if omitted")
    ap.add_argument("--judge-model", default=None,
                    help="defaults to --model if omitted")
    ap.add_argument("--items", default=str(ROOT / "data" / "items.json"))
    ap.add_argument("--limit", type=int, default=0, help="only run the first N items")
    ap.add_argument("--no-judge", action="store_true", help="rule checks only")
    ap.add_argument("--out", default=None)
    a = ap.parse_args()

    items = load_items(a.items)
    if a.limit:
        items = items[:a.limit]

    target = get_provider(a.provider, a.model)
    judge_provider = None
    if not a.no_judge:
        jp = a.judge_provider or a.provider
        jm = a.judge_model or (None if jp != a.provider else a.model)
        judge_provider = get_provider(jp, jm)

    print(f"Running {len(items)} items against {a.provider}:{a.model or 'default'}"
          f"{'  (no judge)' if a.no_judge else ''}\n")

    results = []
    for it in items:
        try:
            resp = target.complete(SYSTEM_PROMPT, it["prompt"])
            r = grade(it, resp, judge_provider)
        except Exception as e:
            print(f"[{it['id']:<20}] {it['category']:<16} ERROR: {e}")
            results.append({"id": it["id"], "category": it["category"],
                            "response": "", "rule_pass": False,
                            "rule_detail": {"error": str(e)},
                            "judge_score": None, "judge_rationale": str(e),
                            "score": 0.0, "error": True})
            continue
        results.append(r)
        flag = "ok " if r["rule_pass"] else "RULE-FAIL"
        print(f"[{r['id']:<20}] {r['category']:<16} score={r['score']:.2f}  {flag}")

    overall, cat_scores = aggregate(results)
    print_table(overall, cat_scores, results)

    model_name = f"{a.provider}:{a.model or 'default'}"
    out_dir = a.out or (ROOT / "runs" / datetime.now().strftime("%Y%m%d-%H%M%S"))
    path = write_report(model_name, overall, cat_scores, results, out_dir)
    print(f"\nSaved results + report to: {path}")


if __name__ == "__main__":
    main()