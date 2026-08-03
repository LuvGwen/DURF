"""Source quality and domain coverage helpers for R7."""

from __future__ import annotations

from collections import Counter

from literature_stage_r7_data import DOMAINS, SOURCES


MINIMUM_DOMAIN_COUNTS = {
    "social_deduction": 5,
    "asymmetric_information": 6,
    "herding_trust": 5,
    "deception_misinformation": 5,
    "behavioral_finance": 8,
    "bow_domain_shift": 5,
    "offline_policy": 6,
    "simulation_validation": 5,
    "risk_metrics": 5,
}


def source_quality_rows(sources=None) -> list[dict[str, str]]:
    rows = []
    for source in sources or SOURCES:
        rows.append(
            {
                "source_id": source["source_id"],
                "peer_reviewed": source["peer_reviewed"],
                "primary_or_secondary": "primary"
                if source["source_type"] in {"journal article", "conference paper", "book chapter", "workshop paper"}
                else "secondary_or_reference",
                "venue_quality": "high" if source["quality_grade"] in {"A", "B"} else "background",
                "methodological_relevance": "high" if source["quality_grade"] == "A" else "moderate",
                "directness_to_project": "high"
                if source["domain"] in {"social_deduction", "offline_policy", "simulation_validation"}
                else "moderate",
                "citation_reliability": "high" if source["metadata_status"].startswith("verified") else "needs_review",
                "recency": "recent" if int(source["year"]) >= 2018 else "classic_or_foundational",
                "limitations": source["limitations"],
                "quality_grade": source["quality_grade"],
            }
        )
    return rows


def domain_counts(sources=None) -> Counter:
    counts = Counter()
    for source in sources or SOURCES:
        counts[source["domain"]] += 1
        for domain in source.get("secondary_domains", "").split(";"):
            if domain in DOMAINS:
                counts[domain] += 1
    return counts


def domain_coverage_rows(sources=None) -> list[dict[str, str]]:
    counts = domain_counts(sources)
    rows = []
    for domain, label in DOMAINS.items():
        count = counts[domain]
        required = MINIMUM_DOMAIN_COUNTS[domain]
        rows.append(
            {
                "domain": domain,
                "domain_label": label,
                "source_count": str(count),
                "minimum_required": str(required),
                "meets_minimum": str(count >= required),
                "notes": "minimum met" if count >= required else "coverage gap remains",
            }
        )
    return rows


def source_quality_counts(sources=None) -> Counter:
    return Counter(source["quality_grade"] for source in sources or SOURCES)


if __name__ == "__main__":
    for row in domain_coverage_rows():
        print(row)
