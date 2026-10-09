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
    ts_start = unit.get("ts_start")
    ts_end = unit.get("ts_end")
    cit_type = "page"

    if ts_start is not None and ts_end is not None:
        start_min = int(ts_start // 60)
        start_sec = int(ts_start % 60)
        end_min = int(ts_end // 60)
        end_sec = int(ts_end % 60)
        loc_str = f"⏱️ {start_min:02d}:{start_sec:02d}–{end_min:02d}:{end_sec:02d}"
        cit_type = "timestamp"
    elif unit.get("page") is not None:
        loc_str = f"Page {unit['page']}"
        cit_type = "page"
    elif unit.get("slide_no") is not None:
        loc_str = f"Slide {unit['slide_no']}"
        cit_type = "slide"
    else:
        loc_str = f"Section {unit_id}"

    label = f"[{source_title}, {loc_str}]"

    # Compute video_url with timestamp if video source
    video_url = unit.get("video_url") or unit.get("file_path") or ""
    video_jump_url = ""
    if video_url and ("youtube" in video_url or "youtu.be" in video_url) and ts_start is not None:
        from app.modules.ingestion.parsers.youtube import extract_youtube_id
        vid = extract_youtube_id(video_url)
        if vid:
            video_jump_url = f"https://www.youtube.com/watch?v={vid}&t={int(ts_start)}s"

    return {
        "unit_id": unit_id,
        "source_id": unit.get("source_id", 1),
        "source_title": source_title,
        "type": cit_type,
        "location": loc_str,
        "locator": loc_str,
        "citation_label": label,
        "snippet": (unit.get("text") or "")[:250],
        "excerpt": (unit.get("text") or "")[:250],
        "ts_start": ts_start,
        "ts_end": ts_end,
        "video_url": video_jump_url or video_url,
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
