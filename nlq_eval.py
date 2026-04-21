"""
NLQ Evaluation Framework — scoring module, LLM judge, and eval runner.

Measures quality of the NLQ pipeline (POST /engine/nlq) across dimensions:
  - Retrieval recall & precision (class-level)
  - Root class routing accuracy
  - Operation coverage (filter, project, sort, etc.)
  - Answer accuracy (column overlap + row count comparison)
  - LLM-as-judge (completeness, faithfulness, relevance)
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import time
import urllib.request
import urllib.error
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Optional, Union


# ── Data structures ──────────────────────────────────────────────────────────

@dataclass
class EvalCase:
    id: str
    question: str
    domain: str
    difficulty: str
    expected: dict  # mustIncludeClasses, rootClass, referenceQuery, mustContainOps, properties
    expect_decline: bool = False
    decline_category: str = ""


@dataclass
class EvalResult:
    case_id: str
    success: bool
    retrieval_recall: float = 0.0
    retrieval_precision: float = 0.0
    root_class_match: bool = False
    ops_coverage: float = 0.0
    answer_accuracy: float = 0.0
    judge_completeness: float = 0.0
    judge_faithfulness: float = 0.0
    judge_relevance: float = 0.0
    query_precision: float = 0.0
    judge_fidelity: float = 0.0  # Reserved for future use
    overall_score: float = 0.0
    generated_query: str = ""
    latency_ms: int = 0
    error: Optional[str] = None
    judge_rationale: str = ""
    follow_up_triggered: bool = False
    follow_up_usefulness: float = 0.0


# ── Scoring functions ────────────────────────────────────────────────────────

def score_retrieval(expected: dict, retrieved_classes: list[str]) -> tuple[float, float]:
    """
    Compute retrieval recall and precision.
    Returns (recall, precision).
    """
    must_include = set(expected.get("mustIncludeClasses", []))
    if not must_include:
        return 1.0, 1.0

    # Normalize: strip package prefixes, compare base class names
    def base_name(cls: str) -> str:
        return cls.rsplit("::", 1)[-1].rsplit(".", 1)[-1]

    must_base = {base_name(c) for c in must_include}
    retrieved_base = {base_name(c) for c in retrieved_classes} if retrieved_classes else set()

    intersection = must_base & retrieved_base
    recall = len(intersection) / len(must_base) if must_base else 1.0
    precision = (2 * len(intersection)) / (len(intersection) + len(retrieved_base)) if retrieved_base else 0.0

    return recall, precision


def score_query_precision(expected: dict, generated_query: str, actual_root: str) -> float:
    """
    Measure how targeted the generated Pure query is: what fraction of classes
    referenced in the query are actually needed (per mustIncludeClasses)?

    Formula: |classes_in_query ∩ expected| / |classes_in_query|

    Classes are detected by:
      - actual_root (the rootClass from the NLQ response)
      - Scanning the query string for mustIncludeClasses names (case-insensitive),
        which appear in association navigation like $d.product.productName
    """
    must_include = set(expected.get("mustIncludeClasses", []))
    if not must_include:
        return 1.0

    def base_name(cls: str) -> str:
        return cls.rsplit("::", 1)[-1].rsplit(".", 1)[-1]

    expected_bases = {base_name(c).lower() for c in must_include}

    # Collect classes referenced in the query
    classes_in_query: set[str] = set()

    # 1. The root class is always referenced
    if actual_root:
        classes_in_query.add(base_name(actual_root).lower())

    # 2. Scan query for class names from mustIncludeClasses
    query_lower = generated_query.lower()
    for cls in must_include:
        bn = base_name(cls).lower()
        if bn in query_lower:
            classes_in_query.add(bn)

    if not classes_in_query:
        return 0.0

    intersection = classes_in_query & expected_bases
    return len(intersection) / len(classes_in_query)


def score_routing(expected_root: str, actual_root: str) -> bool:
    """Check if the root class matches (ignoring package prefix)."""
    def base_name(cls: str) -> str:
        return cls.rsplit("::", 1)[-1].rsplit(".", 1)[-1] if cls else ""

    return base_name(expected_root) == base_name(actual_root)


def score_ops(must_contain_ops: list[str], generated_query: str) -> float:
    """
    Scan the generated Pure query for expected operation names.
    Returns coverage ratio: |found ops| / |expected ops|.
    """
    if not must_contain_ops:
        return 1.0

    found = 0
    query_lower = generated_query.lower()
    for op in must_contain_ops:
        # Match operation names like ->filter(, ->project(, ->sort(, ->groupBy(
        pattern = rf'->\s*{re.escape(op.lower())}\s*\('
        if re.search(pattern, query_lower):
            found += 1
        elif op.lower() in query_lower:
            # Fallback: bare mention
            found += 1

    return found / len(must_contain_ops)


def _normalize_col(name: str) -> str:
    """Lowercase and strip non-alphanumeric chars for fuzzy column comparison."""
    return re.sub(r'[^a-z0-9]', '', name.lower())


def score_answer_accuracy(
    model_src: str,
    ref_query: str,
    gen_query: str,
    engine_url: str,
) -> float:
    """
    Compile Pure→SQL via /engine/plan, then execute via /engine/sql
    (which shares the seeded in-memory DB connection).
    Compare: (a) column name overlap, (b) row count ratio.
    Returns 0.0-1.0.
    """
    def _extract_runtime(src: str) -> Optional[str]:
        m = re.search(r'Runtime\s+([\w:]+)', src)
        return m.group(1) if m else None

    def compile_and_execute(query: str) -> Optional[dict]:
        # Step 1: Compile Pure → SQL via /engine/plan
        full_code = model_src.strip() + "\n\n" + query.strip()
        plan_payload = json.dumps({"code": full_code}).encode("utf-8")
        plan_req = urllib.request.Request(
            f"{engine_url}/engine/plan",
            data=plan_payload,
            headers={"Content-Type": "application/json"},
        )
        try:
            with urllib.request.urlopen(plan_req, timeout=30) as resp:
                plan_result = json.loads(resp.read())
        except Exception:
            return None

        if not plan_result.get("success"):
            return None

        sql = plan_result.get("sql", "")
        if not sql:
            return None

        # Step 2: Execute SQL via /engine/sql (shares seeded connection)
        runtime_name = _extract_runtime(model_src)
        if not runtime_name:
            return None

        sql_payload = json.dumps({
            "code": model_src,
            "sql": sql,
            "runtime": runtime_name,
        }).encode("utf-8")
        sql_req = urllib.request.Request(
            f"{engine_url}/engine/sql",
            data=sql_payload,
            headers={"Content-Type": "application/json"},
        )
        try:
            with urllib.request.urlopen(sql_req, timeout=30) as resp:
                result = json.loads(resp.read())
        except Exception:
            return None

        if not result.get("success"):
            return None

        # Normalize to common format
        columns = result.get("columns", [])
        data = json.loads(result.get("data", "[]")) if result.get("data") else []
        return {"success": True, "columns": columns, "rowCount": len(data)}

    ref_result = compile_and_execute(ref_query)
    gen_result = compile_and_execute(gen_query)

    if not ref_result or not ref_result.get("success"):
        return 0.0
    if not gen_result or not gen_result.get("success"):
        return 0.0

    # Column overlap (normalized + fuzzy)
    ref_cols_raw = ref_result.get("columns", [])
    gen_cols_raw = gen_result.get("columns", [])
    ref_normed = [_normalize_col(c) for c in ref_cols_raw]
    gen_normed = [_normalize_col(c) for c in gen_cols_raw]
    if ref_normed:
        matched = 0
        for rc in ref_normed:
            if rc in gen_normed:
                matched += 1
            elif any(rc in gc or gc in rc for gc in gen_normed):
                matched += 1
        col_overlap = matched / len(ref_normed)
    else:
        col_overlap = 1.0

    # Row count ratio
    ref_rows = ref_result.get("rowCount", 0)
    gen_rows = gen_result.get("rowCount", 0)
    if ref_rows > 0 and gen_rows > 0:
        row_ratio = min(ref_rows, gen_rows) / max(ref_rows, gen_rows)
    elif ref_rows == 0 and gen_rows == 0:
        row_ratio = 1.0
    else:
        row_ratio = 0.0

    return 0.6 * col_overlap + 0.4 * row_ratio


def _call_claude_cli(prompt: str, model: str = "sonnet") -> str:
    """
    Invoke the local Claude Code CLI (`claude -p`) as a subprocess and
    return its stdout. Used as the non-API-key transport for the judge;
    mirrors legend-intelligence's AnthropicCliClient pattern.

    Raises FileNotFoundError if `claude` is not on PATH, or
    subprocess.CalledProcessError if the CLI exits non-zero.
    """
    result = subprocess.run(
        ["claude", "-p", prompt, "--model", model],
        capture_output=True,
        text=True,
        check=True,
        timeout=120,
    )
    return result.stdout


def _parse_judge_json(text: str) -> dict:
    """Strip markdown fences and parse the JSON body from a judge response."""
    text = text.strip()
    text = re.sub(r'^```\w*\n?', '', text).rstrip('`').strip()
    return json.loads(text)


def llm_judge(
    question: str,
    ref_query: str,
    gen_query: str,
    api_key: str,
    model: str = "claude-sonnet-4-6",
    provider: str = "api",
) -> tuple[float, float, float, str]:
    """
    Use Claude as a judge to score the generated query vs reference.
    Returns (completeness, faithfulness, relevance, rationale).
    Scores are 1-5. `provider` is "api" (Anthropic SDK + api_key) or
    "cli" (local `claude -p` subprocess, uses the user's Claude
    subscription).
    """
    judge_prompt = f"""You are evaluating the quality of a generated Pure query against a reference query for a natural language question.

Question: {question}

Reference Query:
{ref_query}

Generated Query:
{gen_query}

Score the generated query on three dimensions (1-5 scale each):

1. **Completeness** (1-5): Does the generated query capture all the data elements and operations requested in the question? 5 = perfectly complete, 1 = missing most elements.

2. **Faithfulness** (1-5): Does the generated query accurately represent what was asked, without introducing incorrect filters, wrong classes, or hallucinated operations? 5 = fully faithful, 1 = significantly wrong.

3. **Relevance** (1-5): Does the generated query return data that would actually answer the user's question? 5 = perfectly relevant results, 1 = irrelevant results.

Return your response as JSON only, no markdown:
{{"completeness": <int>, "faithfulness": <int>, "relevance": <int>, "rationale": "<brief explanation>"}}"""

    try:
        if provider == "cli":
            text = _call_claude_cli(judge_prompt, model="sonnet")
        else:
            import anthropic
            client = anthropic.Anthropic(api_key=api_key)
            response = client.messages.create(
                model=model,
                max_tokens=512,
                messages=[{"role": "user", "content": judge_prompt}],
            )
            text = response.content[0].text
        result = _parse_judge_json(text)
        return (
            float(result.get("completeness", 3)),
            float(result.get("faithfulness", 3)),
            float(result.get("relevance", 3)),
            result.get("rationale", ""),
        )
    except FileNotFoundError:
        return 3.0, 3.0, 3.0, "Judge error: `claude` CLI not found on PATH"
    except subprocess.CalledProcessError as e:
        return 3.0, 3.0, 3.0, f"Judge error: claude CLI exited {e.returncode}: {(e.stderr or '')[:200]}"
    except Exception as e:
        return 3.0, 3.0, 3.0, f"Judge error: {e}"


def score_follow_up_usefulness(
    question: str,
    follow_up_question: str,
    api_key: str,
    model: str = "claude-sonnet-4-6",
    provider: str = "api",
) -> float:
    """
    Use Claude as a judge to score how useful a follow-up question is.
    Returns a score from 1-5. `provider` is "api" or "cli" (see llm_judge).
    """
    judge_prompt = f"""You are evaluating the quality of a follow-up question that an NLQ system asked when it could not answer a user's question.

User's original question: {question}

System's follow-up question: {follow_up_question}

Score the follow-up question on usefulness (1-5 scale):

1 = Completely unhelpful — generic, vague, or doesn't help clarify the issue
2 = Slightly helpful — acknowledges the problem but the follow-up is too broad
3 = Moderately helpful — points in the right direction but could be more specific
4 = Very helpful — specific, actionable, and helps the user understand what's needed
5 = Excellent — precisely identifies the gap and guides the user to a successful query

Return your response as JSON only, no markdown:
{{"usefulness": <int>, "rationale": "<brief explanation>"}}"""

    try:
        if provider == "cli":
            text = _call_claude_cli(judge_prompt, model="sonnet")
        else:
            import anthropic
            client = anthropic.Anthropic(api_key=api_key)
            response = client.messages.create(
                model=model,
                max_tokens=256,
                messages=[{"role": "user", "content": judge_prompt}],
            )
            text = response.content[0].text
        result = _parse_judge_json(text)
        return float(result.get("usefulness", 3))
    except Exception:
        return 3.0


def compute_overall_score(result: EvalResult, expect_decline: bool = False) -> float:
    """
    Weighted composite overall score.

    For decline cases (expectDecline=true):
      0.60 * follow_up_triggered + 0.40 * (follow_up_usefulness / 5)

    For normal cases:
      0.20 * recall + 0.10 * query_precision + 0.20 * answer_accuracy
    + 0.10 * ops_coverage + 0.15 * (completeness/5) + 0.10 * (faithfulness/5)
    + 0.15 * (relevance/5)
    """
    if expect_decline:
        triggered = 1.0 if result.follow_up_triggered else 0.0
        return 0.60 * triggered + 0.40 * (result.follow_up_usefulness / 5.0)

    return (
        0.20 * result.retrieval_recall
        + 0.10 * result.query_precision
        + 0.20 * result.answer_accuracy
        + 0.10 * result.ops_coverage
        + 0.15 * (result.judge_completeness / 5.0)
        + 0.10 * (result.judge_faithfulness / 5.0)
        + 0.15 * (result.judge_relevance / 5.0)
    )


# ── Case loading ─────────────────────────────────────────────────────────────

def load_cases(path: str | Path) -> list[EvalCase]:
    """Load eval cases from a JSON file."""
    with open(path, "r") as f:
        raw = json.load(f)

    cases = []
    for item in raw:
        cases.append(EvalCase(
            id=item["id"],
            question=item["question"],
            domain=item["domain"],
            difficulty=item["difficulty"],
            expected=item["expected"],
            expect_decline=item.get("expectDecline", False),
            decline_category=item.get("declineCategory", ""),
        ))
    return cases


# ── NLQ endpoint call ────────────────────────────────────────────────────────

def _call_nlq(model_src: str, question: str, engine_url: str, llm_model: str = "") -> dict:
    """Call POST /engine/nlq and return the response dict."""
    payload = {"code": model_src, "question": question}
    if llm_model:
        payload["model"] = llm_model
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        f"{engine_url}/engine/nlq",
        data=data,
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=180) as resp:
            return json.loads(resp.read())
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        return {"success": False, "error": f"HTTP {e.code}: {body[:500]}"}
    except Exception as e:
        return {"success": False, "error": str(e)}


# ── Eval runner ──────────────────────────────────────────────────────────────

def run_eval(
    cases: list[EvalCase],
    model_src: str,
    engine_url: str,
    llm_model: str = "",
    api_key: str = "",
    domain_filter: str = "",
    progress_callback=None,
    judge_provider: str = "api",
) -> list[EvalResult]:
    """
    Run evaluation across all cases.
    Calls NLQ endpoint, scores each case, returns list of EvalResult.
    progress_callback(i, total, case_id) is called after each case if provided.

    `domain_filter` is polymorphic:
      - "" or "All" → no filter
      - a domain name ("Northwind", "ETF") → filter by case.domain
      - an exact case ID ("etf-024", "nw-d05")     → filter to that single case
    `judge_provider` selects the LLM judge transport: "api" or "cli".
    """
    filtered = cases
    if domain_filter and domain_filter != "All":
        case_ids = {c.id for c in cases}
        if domain_filter in case_ids:
            filtered = [c for c in cases if c.id == domain_filter]
        else:
            filtered = [c for c in cases if c.domain == domain_filter]

    results = []
    for i, case in enumerate(filtered):
        t0 = time.time()
        nlq_resp = _call_nlq(model_src, case.question, engine_url, llm_model)
        latency = int((time.time() - t0) * 1000)

        result = EvalResult(case_id=case.id, success=False, latency_ms=latency)

        if not nlq_resp.get("success"):
            result.error = nlq_resp.get("error", "NLQ call failed")
            results.append(result)
            if progress_callback:
                progress_callback(i + 1, len(filtered), case.id)
            continue

        result.success = True

        # Handle decline cases
        if case.expect_decline:
            result.follow_up_triggered = bool(nlq_resp.get("cannotAnswer", False))
            follow_up_q = nlq_resp.get("followUpQuestion", "")
            judge_available = judge_provider == "cli" or bool(api_key)
            if result.follow_up_triggered and follow_up_q and judge_available:
                result.follow_up_usefulness = score_follow_up_usefulness(
                    case.question, follow_up_q, api_key, provider=judge_provider
                )
            elif result.follow_up_triggered:
                result.follow_up_usefulness = 3.0  # default when no judge
            result.overall_score = compute_overall_score(result, expect_decline=True)
            result.generated_query = follow_up_q if result.follow_up_triggered else nlq_resp.get("pureQuery", "")
            results.append(result)
            if progress_callback:
                progress_callback(i + 1, len(filtered), case.id)
            continue

        gen_query = nlq_resp.get("pureQuery") or ""
        result.generated_query = gen_query

        # Retrieval scoring
        retrieved = nlq_resp.get("retrievedClasses", [])
        result.retrieval_recall, result.retrieval_precision = score_retrieval(
            case.expected, retrieved
        )

        # Root class routing
        actual_root = nlq_resp.get("rootClass", "")
        result.root_class_match = score_routing(
            case.expected.get("rootClass", ""), actual_root
        )

        # Query precision
        result.query_precision = score_query_precision(
            case.expected, gen_query, actual_root
        )

        # Ops coverage
        result.ops_coverage = score_ops(
            case.expected.get("mustContainOps", []), gen_query
        )

        # Answer accuracy (only if we have a reference query)
        ref_query = case.expected.get("referenceQuery", "")
        if ref_query and gen_query:
            result.answer_accuracy = score_answer_accuracy(
                model_src, ref_query, gen_query, engine_url
            )

        # LLM judge (API key for "api" provider, or always available for "cli")
        judge_available = judge_provider == "cli" or bool(api_key)
        if judge_available and ref_query and gen_query:
            comp, faith, rel, rationale = llm_judge(
                case.question, ref_query, gen_query, api_key,
                provider=judge_provider,
            )
            result.judge_completeness = comp
            result.judge_faithfulness = faith
            result.judge_relevance = rel
            result.judge_rationale = rationale
        else:
            # Default to neutral scores when no judge can run
            result.judge_completeness = 3.0
            result.judge_faithfulness = 3.0
            result.judge_relevance = 3.0
            if not judge_available:
                reason = "No API key provided"
            elif not gen_query:
                reason = "Engine returned no query (likely declined); nothing to judge"
            elif not ref_query:
                reason = "Eval case has no referenceQuery; nothing to compare against"
            else:
                reason = "Judge skipped"
            result.judge_rationale = f"{reason}; using default scores"

        # Overall score
        result.overall_score = compute_overall_score(result)

        results.append(result)
        if progress_callback:
            progress_callback(i + 1, len(filtered), case.id)

    return results


# ── Summary stats ────────────────────────────────────────────────────────────

def summary_stats(results: list[EvalResult], cases: list[EvalCase] | None = None) -> dict:
    """Compute aggregate statistics from eval results."""
    if not results:
        return {
            "count": 0,
            "avg_overall_score": 0.0,
            "avg_recall": 0.0,
            "avg_precision": 0.0,
            "avg_query_precision": 0.0,
            "avg_answer_accuracy": 0.0,
            "avg_completeness": 0.0,
            "avg_faithfulness": 0.0,
            "avg_relevance": 0.0,
            "pass_rate": 0.0,
            "success_rate": 0.0,
            "by_difficulty": {},
            "follow_up_rate": 0.0,
            "follow_up_usefulness": 0.0,
        }

    n = len(results)
    successful = [r for r in results if r.success]

    stats = {
        "count": n,
        "avg_overall_score": sum(r.overall_score for r in results) / n,
        "avg_recall": sum(r.retrieval_recall for r in results) / n,
        "avg_precision": sum(r.retrieval_precision for r in results) / n,
        "avg_query_precision": sum(r.query_precision for r in results) / n,
        "avg_answer_accuracy": sum(r.answer_accuracy for r in results) / n,
        "avg_completeness": sum(r.judge_completeness for r in results) / n,
        "avg_faithfulness": sum(r.judge_faithfulness for r in results) / n,
        "avg_relevance": sum(r.judge_relevance for r in results) / n,
        "pass_rate": sum(1 for r in results if r.overall_score > 0.6) / n,
        "success_rate": len(successful) / n,
    }

    # Follow-up metrics (decline cases)
    # Build a lookup of case_id -> EvalCase for decline detection
    decline_case_ids = set()
    if cases:
        decline_case_ids = {c.id for c in cases if c.expect_decline}
    else:
        # Fallback: detect by follow_up_triggered flag
        decline_case_ids = {r.case_id for r in results if r.follow_up_triggered}

    decline_results = [r for r in results if r.case_id in decline_case_ids]
    if decline_results:
        n_decline = len(decline_results)
        stats["follow_up_rate"] = sum(1 for r in decline_results if r.follow_up_triggered) / n_decline
        triggered = [r for r in decline_results if r.follow_up_triggered]
        stats["follow_up_usefulness"] = (
            sum(r.follow_up_usefulness for r in triggered) / len(triggered) if triggered else 0.0
        )
    else:
        stats["follow_up_rate"] = 0.0
        stats["follow_up_usefulness"] = 0.0

    # Per-domain breakdown
    by_difficulty: dict[str, dict] = {}
    for prefix_label, prefix in [("Northwind", "nw"), ("ETF", "etf")]:
        group = [r for r in results if r.case_id.startswith(prefix)]
        if group:
            ng = len(group)
            by_difficulty[prefix_label] = {
                "count": ng,
                "avg_overall_score": sum(r.overall_score for r in group) / ng,
                "avg_recall": sum(r.retrieval_recall for r in group) / ng,
                "pass_rate": sum(1 for r in group if r.overall_score > 0.6) / ng,
            }

    stats["by_difficulty"] = by_difficulty
    return stats
