"""Shared utilities for parsing relationship text fields."""

import re


def parse_text_list(text: str | None) -> list[str]:
    """Parse comma/semicolon separated text into list of names."""
    if not text:
        return []

    items = re.split(r"[,;]", text)

    result = []
    for item in items:
        item = item.strip()
        # Remove trailing citations like [16]
        item = re.sub(r"\[\d+\]$", "", item).strip()
        # Remove parenthetical notes like (Berlin), (London)
        item = re.sub(r"\s*\([^)]+\)\s*$", "", item).strip()

        if item and len(item) > 1:
            result.append(item)

    return result


def classify_partner(partner_name: str) -> str:
    """Classify partner type based on name patterns.

    Returns one of: 'research_partner', 'government', 'industrial_partner'.
    """
    name_lower = partner_name.lower()

    academic_keywords = [
        "university", "universität", "college", "institute", "institut",
        "lab", "laboratory", "research", "national", "department of energy",
        "doe", "cnrs", "max planck", "fraunhofer", "lmu", "mit",
        "princeton", "oxford", "cambridge", "stanford", "berkeley", "caltech",
    ]

    government_keywords = [
        "government", "ministry", "department", "agency", "commission",
        "u.s.", "us ", "european", "federal", "state of",
        "dod", "arpa", "darpa",
    ]

    for kw in academic_keywords:
        if kw in name_lower:
            return "research_partner"

    for kw in government_keywords:
        if kw in name_lower:
            return "government"

    return "industrial_partner"
