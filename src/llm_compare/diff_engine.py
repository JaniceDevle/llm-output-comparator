from __future__ import annotations

from dataclasses import dataclass
from difflib import SequenceMatcher
import html
import re


@dataclass
class Segment:
    text: str
    status: str
    matched_with: str = ""
    score: float = 0.0


@dataclass
class ComparisonResult:
    left_segments: list[Segment]
    right_segments: list[Segment]
    agreement_score: float
    details: list[dict]


def split_into_chunks(text: str) -> list[str]:
    """
    Split model output into readable comparison chunks.

    Handles normal sentences and common Markdown bullet/numbered lists.
    """
    cleaned = text.strip()

    if not cleaned:
        return []

    # Keep markdown list items as separate chunks.
    lines = [line.strip() for line in cleaned.splitlines() if line.strip()]

    chunks: list[str] = []

    for line in lines:
        # Remove common markdown emphasis to improve matching.
        line = re.sub(r"\*\*(.*?)\*\*", r"\1", line)
        line = re.sub(r"__(.*?)__", r"\1", line)

        # Headings are useful as chunks.
        if re.match(r"^#{1,6}\s+", line):
            chunks.append(re.sub(r"^#{1,6}\s+", "", line).strip())
            continue

        # Bullet or numbered list item.
        if re.match(r"^(\-|\*|•|\d+\.)\s+", line):
            chunks.append(line)
            continue

        # Otherwise split paragraph into sentences.
        sentence_parts = re.split(r"(?<=[.!?。！？])\s+", line)
        chunks.extend(part.strip() for part in sentence_parts if part.strip())

    # Filter tiny chunks like "1." or "2."
    chunks = [chunk for chunk in chunks if len(chunk.strip()) > 3]

    return chunks


def similarity(a: str, b: str) -> float:
    """
    Return approximate string similarity between 0 and 1.
    """
    return SequenceMatcher(None, a.lower(), b.lower()).ratio()


def classify_score(score: float) -> str:
    if score >= 0.72:
        return "agree"
    if score >= 0.45:
        return "partial"
    return "disagree"


def compare_texts(left_text: str, right_text: str) -> ComparisonResult:
    left_chunks = split_into_chunks(left_text)
    right_chunks = split_into_chunks(right_text)

    used_right_indexes: set[int] = set()
    left_segments: list[Segment] = []
    right_segments: list[Segment] = [
        Segment(text=chunk, status="disagree") for chunk in right_chunks
    ]
    details: list[dict] = []

    total_score = 0.0

    for left_chunk in left_chunks:
        best_index = -1
        best_score = 0.0

        for index, right_chunk in enumerate(right_chunks):
            if index in used_right_indexes:
                continue

            score = similarity(left_chunk, right_chunk)

            if score > best_score:
                best_score = score
                best_index = index

        status = classify_score(best_score)

        if best_index >= 0:
            used_right_indexes.add(best_index)
            matched_right = right_chunks[best_index]
            right_segments[best_index].status = status
            right_segments[best_index].matched_with = left_chunk
            right_segments[best_index].score = best_score
        else:
            matched_right = ""

        left_segments.append(
            Segment(
                text=left_chunk,
                status=status,
                matched_with=matched_right,
                score=best_score,
            )
        )

        details.append(
            {
                "left": left_chunk,
                "best_right_match": matched_right,
                "score": round(best_score, 3),
                "status": status,
            }
        )

        total_score += best_score

    denominator = max(len(left_chunks), len(right_chunks), 1)
    agreement_score = total_score / denominator

    return ComparisonResult(
        left_segments=left_segments,
        right_segments=right_segments,
        agreement_score=agreement_score,
        details=details,
    )


def segment_to_html(segment: Segment) -> str:
    safe_text = html.escape(segment.text)

    css_class = {
        "agree": "agree",
        "partial": "partial",
        "disagree": "disagree",
    }.get(segment.status, "disagree")

    return f'<span class="segment {css_class}">{safe_text}</span>'


def segments_to_html(segments: list[Segment]) -> str:
    return " ".join(segment_to_html(segment) for segment in segments)