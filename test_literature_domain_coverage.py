from literature_source_quality import MINIMUM_DOMAIN_COUNTS, domain_counts


def test_literature_domain_coverage():
    counts = domain_counts()
    for domain, minimum in MINIMUM_DOMAIN_COUNTS.items():
        assert counts[domain] >= minimum, (domain, counts[domain], minimum)


if __name__ == "__main__":
    test_literature_domain_coverage()
    print("test_literature_domain_coverage.py passed")
