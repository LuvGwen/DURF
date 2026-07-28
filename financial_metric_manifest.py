"""R5 financial-analogy metric manifest.

The R5 metrics are analysis-only game-payoff analogues. They do not alter the
R4 payoff manifest, game mechanics, or strategy policies.
"""

from __future__ import annotations

import hashlib
import json
from copy import deepcopy
from pathlib import Path


RESULTS_DIR = Path("results/financial_risk_stage_r5")
R4_MANIFEST_HASH = (
    "eee8007693ec6a484632f61444a53f6f8b1b9feb64b18c865f0edf704a15c7cd"
)
METRIC_MANIFEST_VERSION = "r5_financial_metric_manifest_v1"


METRIC_DEFINITIONS = [
    {
        "metric_id": "expected_payoff",
        "label": "Expected payoff",
        "formula": "arithmetic mean of player-game total_payoff",
        "primary_unit": "player-game",
        "financial_analogy": "expected return analogue",
    },
    {
        "metric_id": "payoff_variance",
        "label": "Payoff variance",
        "formula": "sample variance of player-game payoff",
        "primary_unit": "player-game",
        "financial_analogy": "return variance analogue",
    },
    {
        "metric_id": "payoff_volatility",
        "label": "Payoff volatility",
        "formula": "sample standard deviation of player-game payoff",
        "primary_unit": "player-game",
        "financial_analogy": "return volatility analogue",
    },
    {
        "metric_id": "downside_deviation",
        "label": "Downside deviation",
        "formula": "sqrt(mean((target - payoff)^2 for payoff < target))",
        "primary_unit": "player-game",
        "financial_analogy": "downside-risk analogue",
    },
    {
        "metric_id": "negative_payoff_probability",
        "label": "Negative-payoff probability",
        "formula": "count(payoff < 0) / count(payoff)",
        "primary_unit": "player-game",
        "financial_analogy": "loss-frequency analogue",
    },
    {
        "metric_id": "var_like_payoff_threshold",
        "label": "VaR-like payoff threshold",
        "formula": "empirical lower-tail payoff quantile at 1 - confidence",
        "primary_unit": "player-game",
        "financial_analogy": "VaR-like threshold analogue",
    },
    {
        "metric_id": "cvar_like_loss",
        "label": "CVaR-like downside loss",
        "formula": "mean(-payoff for payoff at or below VaR-like threshold)",
        "primary_unit": "player-game",
        "financial_analogy": "CVaR-like tail-loss analogue",
    },
    {
        "metric_id": "sharpe_like_ratio",
        "label": "Sharpe-like payoff ratio",
        "formula": "(mean payoff - benchmark payoff) / payoff standard deviation",
        "primary_unit": "player-game",
        "financial_analogy": "Sharpe-ratio analogue without risk-free rate",
    },
    {
        "metric_id": "sortino_like_ratio",
        "label": "Sortino-like payoff ratio",
        "formula": "(mean payoff - target payoff) / downside deviation",
        "primary_unit": "player-game",
        "financial_analogy": "Sortino-ratio analogue",
    },
    {
        "metric_id": "opportunity_cost_adjusted_payoff",
        "label": "Opportunity-cost-adjusted payoff",
        "formula": "payoff excluding opportunity cost plus opportunity cost",
        "primary_unit": "player-game",
        "financial_analogy": "opportunity-cost-adjusted return analogue",
    },
    {
        "metric_id": "information_premium",
        "label": "Information premium",
        "formula": "mean payoff with useful information event minus without",
        "primary_unit": "player-game",
        "financial_analogy": "informed-trader premium analogue",
    },
    {
        "metric_id": "manipulation_premium",
        "label": "Manipulation premium",
        "formula": "mean wolf payoff with manipulation event minus without",
        "primary_unit": "player-game",
        "financial_analogy": "adversarial-manipulation premium analogue",
    },
    {
        "metric_id": "risk_return_frontier",
        "label": "Risk-return frontier",
        "formula": "non-dominated expected-payoff/risk points by role",
        "primary_unit": "strategy-role",
        "financial_analogy": "efficient-frontier analogue",
    },
]


BENCHMARKS = [
    {
        "benchmark_id": "zero_payoff",
        "label": "Zero payoff",
        "definition": "Break-even game payoff; primary Sharpe-like benchmark.",
    },
    {
        "benchmark_id": "role_specific_random_strategy",
        "label": "Role-specific random strategy mean",
        "definition": (
            "Village roles use villager_random_vote; werewolves use "
            "wolf_random_kill when available."
        ),
    },
    {
        "benchmark_id": "reference_strategy_mix",
        "label": "Existing default strategy mix",
        "definition": "R4 reference_strategy_mix condition mean by role.",
    },
]


def _hash_payload(payload):
    stable = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(stable.encode("utf-8")).hexdigest()


def build_metric_manifest():
    manifest = {
        "metric_manifest_version": METRIC_MANIFEST_VERSION,
        "r4_manifest_hash": R4_MANIFEST_HASH,
        "financial_analogy_boundary": (
            "Metrics are empirical game-payoff analogues, not literal market "
            "returns, investment performance, regulatory VaR, or portfolio "
            "Sharpe ratios."
        ),
        "primary_analysis_unit": "player-game for role payoff; game for game outcomes",
        "bootstrap_unit": "game clusters for player-level metrics",
        "metric_definitions": deepcopy(METRIC_DEFINITIONS),
        "benchmarks": deepcopy(BENCHMARKS),
        "confidence_levels": [0.90, 0.95],
        "coefficient_sensitivity_factors": [0.75, 1.00, 1.25],
    }
    payload = deepcopy(manifest)
    manifest["metric_manifest_hash"] = _hash_payload(payload)
    return manifest


def write_metric_manifest(path=RESULTS_DIR / "r5_metric_definition_manifest.json"):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    manifest = build_metric_manifest()
    path.write_text(json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8")
    return manifest
