from __future__ import annotations

from pathlib import Path
from typing import Any

from aesubtitle.cache import source_fingerprint
from aesubtitle.text import clean_segment_text, wrap_subtitle_text

TRANSCRIPT_VERSION = "1.0"
TIMEBASE = "source_seconds"


class TranscriptError(ValueError):
    pass


def build_transcript(source_path: str | Path, transcription: dict[str, Any]) -> dict[str, Any]:
    source = Path(source_path)
    segments = [_normalize_segment(index, segment) for index, segment in enumerate(transcription.get("segments", []))]
    segments = [segment for segment in segments if segment["text"]]
    for new_id, segment in enumerate(segments):
        segment["id"] = new_id

    return {
        "version": TRANSCRIPT_VERSION,
        "source_file": source.name,
        "source_path": str(source),
        "source_fingerprint": source_fingerprint(source),
        "duration_seconds": float(transcription.get("duration_seconds") or _segments_duration(segments)),
        "language": transcription.get("language") or "auto",
        "model": transcription.get("model") or "unknown",
        "timebase": TIMEBASE,
        "segments": segments,
    }


def _normalize_segment(index: int, segment: dict[str, Any]) -> dict[str, Any]:
    try:
        start = float(segment["start"])
        end = float(segment["end"])
    except (KeyError, TypeError, ValueError) as error:
        raise TranscriptError(f"Segment {index} must include numeric start and end") from error

    if start < 0 or end <= start:
        raise TranscriptError(f"Segment {index} has invalid timing")

    return {
        "id": index,
        "start": start,
        "end": end,
        "text": wrap_subtitle_text(clean_segment_text(segment.get("text", ""))),
    }


def _segments_duration(segments: list[dict[str, Any]]) -> float:
    if not segments:
        return 0.0
    return max(float(segment["end"]) for segment in segments)
