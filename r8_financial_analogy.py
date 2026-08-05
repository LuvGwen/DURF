"""R8 financial analogy wrapper."""

from __future__ import annotations

from r8_payoff_risk_synthesis import build_financial_analogy_final_table


def build_financial_analogy_report_notes() -> list[str]:
    return [
        "The financial analogy is quantitatively useful inside the frozen game payoff ledger.",
        "p_wolf behaves like a dynamic risk score, not a real-world probability of default.",
        "Deception and trust memory are best framed as adversarial manipulation and reputation controls.",
        "No claim is made that simulated payoffs are externally priced financial returns.",
    ]
