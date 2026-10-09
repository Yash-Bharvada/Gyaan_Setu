"""Citations formatting and extraction module.

Formats explicit source citations matching:
- Page numbers: [Source: Biology 101, Page 42]
- Slide numbers: [Source: Lecture 3, Slide 14]
- Timestamps: [Source: Quantum Physics Video, 04:25–06:10]
"""
from __future__ import annotations

import re
from typing import Any, Dict, List, Optional


def format_unit_citation(unit: Dict[str, Any]) -> Dict[str, Any]:
    """Generate structured citation object and human-readable label for a unit."""
    source_title = unit.get("source_title", "Course Material")
    unit_type = unit.get("type", "text")
    unit_id = unit.get("unit_id") or unit.get("id")

    loc_str = ""
    if unit.get("page") is not None:
        loc_str = f"Page {unit['page']}"
    elif unit.get("slide_no") is not None:
        loc_str = f"Slide {unit['slide_no']}"
    elif unit.get("ts_start") is not None and unit.get("ts_end") is not None:
        start_min = int(unit["ts_start"] // 60)
        start_sec = int(unit["ts_start"] % 60)
        end_min = int(unit["ts_end"] // 60)
        end_sec = int(unit["ts_end"] % 60)
        loc_str = f"{start_min:02d}:{start_sec:02d}–{end_min:02d}:{end_sec:02d}"
    else:
        loc_str = f"Section {unit_id}"

    label = f"[{source_title}, {loc_str}]"

    return {
        "unit_id": unit_id,
        "source_title": source_title,
        "location": loc_str,
        "citation_label": label,
        "snippet": (unit.get("text") or "")[:200],
    }


def extract_citations_from_text(
    response_text: str,
    available_citations: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """Match citations mentioned in the answer text to available citation objects."""
    used_citations = []
    for cit in available_citations:
        label = cit["citation_label"]
        # Check if the citation or key terms appear in the text
        if label in response_text or cit["source_title"] in response_text or str(cit["location"]) in response_text:
            used_citations.append(cit)

    # If none explicitly matched, return all top sources that supported the response
    if not used_citations and available_citations:
        used_citations = available_citations[:2]

    return used_citations
