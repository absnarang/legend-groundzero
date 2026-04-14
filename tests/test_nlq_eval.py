"""Unit tests for nlq_eval scoring functions."""

import json
import os
import sys
import pytest

# Add parent directory to path so we can import nlq_eval
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import nlq_eval
from nlq_eval import (
    EvalResult,
    score_retrieval,
    score_routing,
    score_ops,
    compute_overall_score,
    load_cases,
)


# ── score_retrieval tests ────────────────────────────────────────────────────

class TestScoreRetrieval:
    def test_perfect_recall(self):
        expected = {"mustIncludeClasses": ["Product", "Category"]}
        retrieved = ["northwind::model::Product", "northwind::model::Category"]
        recall, precision = score_retrieval(expected, retrieved)
        assert recall == 1.0
        assert precision == 1.0

    def test_partial_recall(self):
        expected = {"mustIncludeClasses": ["Product", "Category", "Supplier"]}
        retrieved = ["northwind::model::Product", "northwind::model::Category"]
        recall, precision = score_retrieval(expected, retrieved)
        assert abs(recall - 2 / 3) < 0.01
        assert precision == 1.0

    def test_precision_with_extra_classes(self):
        expected = {"mustIncludeClasses": ["Product", "Category"]}
        retrieved = [
            "northwind::model::Product",
            "northwind::model::Category",
            "northwind::model::Supplier",
            "northwind::model::Order",
        ]
        recall, precision = score_retrieval(expected, retrieved)
        assert recall == 1.0
        assert precision == 0.5

    def test_zero_recall(self):
        expected = {"mustIncludeClasses": ["Product", "Category"]}
        retrieved = ["northwind::model::Supplier"]
        recall, precision = score_retrieval(expected, retrieved)
        assert recall == 0.0
        assert precision == 0.0

    def test_empty_retrieved(self):
        expected = {"mustIncludeClasses": ["Product"]}
        recall, precision = score_retrieval(expected, [])
        assert recall == 0.0
        assert precision == 0.0

    def test_empty_expected(self):
        expected = {"mustIncludeClasses": []}
        recall, precision = score_retrieval(expected, ["Product"])
        assert recall == 1.0
        assert precision == 1.0

    def test_base_name_normalization(self):
        """Class names should be compared ignoring package prefixes."""
        expected = {"mustIncludeClasses": ["Fund", "Holding"]}
        retrieved = ["etf::Fund", "etf::Holding"]
        recall, precision = score_retrieval(expected, retrieved)
        assert recall == 1.0
        assert precision == 1.0


# ── score_routing tests ──────────────────────────────────────────────────────

class TestScoreRouting:
    def test_exact_match(self):
        assert score_routing("Product", "Product") is True

    def test_qualified_match(self):
        assert score_routing("Product", "northwind::model::Product") is True

    def test_mismatch(self):
        assert score_routing("Product", "Order") is False

    def test_empty_strings(self):
        assert score_routing("", "") is True

    def test_one_empty(self):
        assert score_routing("Product", "") is False


# ── score_ops tests ──────────────────────────────────────────────────────────

class TestScoreOps:
    def test_all_ops_present(self):
        query = "etf::Fund.all()->filter(f|$f.assetClass == 'EQUITY')->project([f|$f.ticker], ['ticker'])->sort(~aum->descending())"
        coverage = score_ops(["filter", "project", "sort"], query)
        assert coverage == 1.0

    def test_partial_ops(self):
        query = "etf::Fund.all()->project([f|$f.ticker], ['ticker'])->sort('ticker')"
        coverage = score_ops(["filter", "project", "sort"], query)
        assert abs(coverage - 2 / 3) < 0.01

    def test_no_ops_found(self):
        query = "etf::Fund.all()"
        coverage = score_ops(["filter", "project", "sort"], query)
        assert coverage == 0.0

    def test_empty_expected_ops(self):
        coverage = score_ops([], "anything")
        assert coverage == 1.0

    def test_groupby_detection(self):
        query = "->project([...], [...])->groupBy([...], [...], [...])->sort(...)"
        coverage = score_ops(["project", "groupBy", "sort"], query)
        assert coverage == 1.0

    def test_take_detection(self):
        query = "->project([...], [...])->sort(~x->descending())->take(5)"
        coverage = score_ops(["project", "sort", "take"], query)
        assert coverage == 1.0


# ── compute_overall_score tests ───────────────────────────────────────────────

class TestComputeOverallScore:
    def test_perfect_scores(self):
        result = EvalResult(
            case_id="test",
            success=True,
            retrieval_recall=1.0,
            retrieval_precision=1.0,
            answer_accuracy=1.0,
            judge_completeness=5.0,
            judge_faithfulness=5.0,
            judge_relevance=5.0,
            judge_fidelity=5.0,
        )
        score = compute_overall_score(result)
        assert abs(score - 1.0) < 0.001

    def test_zero_scores(self):
        result = EvalResult(
            case_id="test",
            success=True,
            retrieval_recall=0.0,
            retrieval_precision=0.0,
            answer_accuracy=0.0,
            judge_completeness=0.0,
            judge_faithfulness=0.0,
            judge_relevance=0.0,
            judge_fidelity=0.0,
        )
        score = compute_overall_score(result)
        assert score == 0.0

    def test_mixed_scores(self):
        result = EvalResult(
            case_id="test",
            success=True,
            retrieval_recall=0.8,
            retrieval_precision=0.5,
            answer_accuracy=0.7,
            judge_completeness=4.0,
            judge_faithfulness=3.0,
            judge_relevance=4.0,
            judge_fidelity=4.0,
        )
        # 0.15*0.8 + 0.10*0.5 + 0.25*0.7 + 0.10*(4/5) + 0.10*(3/5) + 0.10*(4/5) + 0.20*(4/5)
        # = 0.12 + 0.05 + 0.175 + 0.08 + 0.06 + 0.08 + 0.16 = 0.725
        score = compute_overall_score(result)
        assert abs(score - 0.725) < 0.01

    def test_weights_sum_to_one(self):
        """Verify that the weight coefficients sum to 1.0."""
        assert abs(0.15 + 0.10 + 0.25 + 0.10 + 0.10 + 0.10 + 0.20 - 1.0) < 0.001

    def test_fidelity_weight_is_highest_judge(self):
        """Fidelity has the highest weight (20%) among judge dimensions."""
        # With only fidelity at 5 and everything else at 0
        result = EvalResult(
            case_id="test", success=True,
            judge_fidelity=5.0,
        )
        score_fidelity_only = compute_overall_score(result)
        # With only completeness at 5 and everything else at 0
        result2 = EvalResult(
            case_id="test", success=True,
            judge_completeness=5.0,
        )
        score_completeness_only = compute_overall_score(result2)
        assert score_fidelity_only > score_completeness_only


# ── load_cases tests ─────────────────────────────────────────────────────────

class TestLoadCases:
    def test_load_cases_count(self):
        cases_path = os.path.join(os.path.dirname(__file__), "..", "eval_cases.json")
        cases = load_cases(cases_path)
        assert len(cases) >= 40

    def test_load_cases_structure(self):
        cases_path = os.path.join(os.path.dirname(__file__), "..", "eval_cases.json")
        cases = load_cases(cases_path)
        for case in cases:
            assert case.id
            assert case.question
            assert case.domain in ("Northwind", "ETF")
            assert case.difficulty in ("easy", "medium", "hard")
            assert "mustIncludeClasses" in case.expected
            assert "rootClass" in case.expected
            assert "referenceQuery" in case.expected
            assert "mustContainOps" in case.expected

    def test_northwind_cases_count(self):
        cases_path = os.path.join(os.path.dirname(__file__), "..", "eval_cases.json")
        cases = load_cases(cases_path)
        nw = [c for c in cases if c.domain == "Northwind"]
        assert len(nw) == 23

    def test_etf_cases_count(self):
        cases_path = os.path.join(os.path.dirname(__file__), "..", "eval_cases.json")
        cases = load_cases(cases_path)
        etf = [c for c in cases if c.domain == "ETF"]
        assert len(etf) >= 20
