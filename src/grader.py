"""Grading. Two signals combined:

1. rule_score  - deterministic regex checks from the item's "rule_checks".
2. judge       - an LLM scores the response against the item's rubric.

Final score uses the judge when available; if deterministic rules fail
(e.g. a required "po" is missing) the score is capped low regardless.
"""
from __future__ import annotations
import json
import re


JUDGE_SYSTEM = (
    "You are a bilingual (Tagalog/English) evaluator with deep expertise in "
    "Filipino culture, values, and language. Judge the RESPONSE strictly against "
    "the RUBRIC. Be culturally precise, not lenient. "
    "Reply with ONLY a JSON object, no prose, no code fences: "
    '{"score": <0.0, 0.5, or 1.0>, "rationale": "<=40 words"}'
)


def rule_score(item, response):
    """Return (passed: bool, detail: dict)."""
    detail = {"required_hits": [], "required_miss": [], "forbidden_hits": []}
    checks = item.get("rule_checks", {}) or {}
    ok = True
    for pat in checks.get("require_regex", []):
        if re.search(pat, response, re.IGNORECASE):
            detail["required_hits"].append(pat)
        else:
            detail["required_miss"].append(pat)
            ok = False
    for pat in checks.get("forbid_regex", []):
        if re.search(pat, response, re.IGNORECASE):
            detail["forbidden_hits"].append(pat)
            ok = False
    return ok, detail


def _build_judge_user(item, response):
    r = item.get("rubric", {}) or {}
    return (
        f"CATEGORY: {item.get('category', '')}\n"
        f"PROMPT (given to the model under test):\n{item.get('prompt', '')}\n\n"
        f"RUBRIC\n"
        f"- Must include: {r.get('must_include', '')}\n"
        f"- Must avoid: {r.get('must_avoid', '')}\n"
        f"- Guidance: {r.get('guidance', '')}\n\n"
        f"RESPONSE TO JUDGE:\n{response}\n\n"
        "Give 1.0 only if it satisfies 'must include' and violates no 'must avoid'. "
        "Give 0.5 for partial. Give 0.0 for a clear failure."
    )


def _extract_json(text):
    text = (text or "").strip()
    m = re.search(r"\{.*\}", text, re.DOTALL)
    if m:
        text = m.group(0)
    try:
        return json.loads(text)
    except Exception:
        return {"score": 0.0, "rationale": "unparseable judge output"}


def judge(item, response, judge_provider):
    out = judge_provider.complete(JUDGE_SYSTEM, _build_judge_user(item, response))
    data = _extract_json(out)
    try:
        score = float(data.get("score", 0.0))
    except (TypeError, ValueError):
        score = 0.0
    return max(0.0, min(1.0, score)), data.get("rationale", "")


def grade(item, response, judge_provider=None):
    rule_pass, detail = rule_score(item, response)
    j_score, j_rationale = None, ""
    if judge_provider is not None and item.get("rubric"):
        j_score, j_rationale = judge(item, response, judge_provider)

    if j_score is None:
        score = 1.0 if rule_pass else 0.0
    else:
        # Judge decides, but a hard rule failure caps the score.
        score = j_score if rule_pass else min(j_score, 0.3)

    return {
        "id": item.get("id"),
        "category": item.get("category"),
        "response": response,
        "rule_pass": rule_pass,
        "rule_detail": detail,
        "judge_score": j_score,
        "judge_rationale": j_rationale,
        "score": round(score, 3),
    }