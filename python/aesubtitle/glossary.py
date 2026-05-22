from __future__ import annotations

import os
import re
import textwrap
from dataclasses import dataclass
from datetime import datetime, timezone
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any

TOKEN_RE = re.compile(r"[A-Za-z0-9_%\u0E00-\u0E7F]+")


class GlossaryError(ValueError):
    pass


@dataclass(frozen=True)
class GlossaryEntry:
    canonical: str
    variants: tuple[str, ...] = ()


def default_glossary_path() -> Path | None:
    env_path = os.environ.get("AESUBTITLE_GLOSSARY")
    if env_path:
        return Path(env_path).expanduser()

    path = Path(__file__).resolve().parents[2] / "glossary.md"
    return path if path.exists() else None


def resolve_glossary_path(path: str | Path | None) -> Path | None:
    if path == "":
        return None
    if path is not None:
        return Path(path).expanduser()
    return default_glossary_path()


def load_glossary(path: str | Path | None) -> list[GlossaryEntry]:
    resolved = resolve_glossary_path(path)
    if resolved is None:
        return []
    if not resolved.exists():
        raise GlossaryError(f"Glossary file does not exist: {resolved}")
    return parse_glossary_markdown(resolved.read_text(encoding="utf-8"))


def parse_glossary_markdown(markdown: str) -> list[GlossaryEntry]:
    markdown = textwrap.dedent(markdown)
    entries: list[GlossaryEntry] = []
    current: str | None = None
    variants: list[str] = []

    def flush() -> None:
        nonlocal current, variants
        if current:
            canonical = _clean_value(current)
            deduped = tuple(
                value
                for value in dict.fromkeys(_clean_value(variant) for variant in variants)
                if value and value != canonical
            )
            entries.append(GlossaryEntry(canonical=canonical, variants=deduped))
        current = None
        variants = []

    for raw_line in markdown.splitlines():
        if not raw_line.strip() or raw_line.lstrip().startswith("#"):
            continue
        indent = len(raw_line) - len(raw_line.lstrip())
        line = raw_line.strip()

        if indent <= 2 and line.startswith("- canonical:"):
            flush()
            current = line.split(":", 1)[1].strip()
            continue

        if current is not None and indent > 0 and line.startswith("- "):
            variants.append(line[2:].strip())
            continue

        if indent <= 2 and line.startswith("- "):
            flush()
            current = line[2:].strip()
            continue

    flush()
    return entries


def apply_glossary_to_transcription(
    transcription: dict[str, Any],
    entries: list[GlossaryEntry],
) -> dict[str, Any]:
    if not entries:
        return transcription

    updated = dict(transcription)
    corrected_segments = []
    for segment in transcription.get("segments", []):
        corrected = dict(segment)
        corrected["text"] = correct_text(corrected.get("text", ""), entries)
        corrected_segments.append(corrected)
    updated["segments"] = corrected_segments
    return updated


def correct_text(text: object, entries: list[GlossaryEntry]) -> str:
    if not entries:
        return str(text)
    corrected = str(text)
    corrected = _replace_exact_terms(corrected, entries)
    return _replace_fuzzy_terms(corrected, entries)


def glossary_fingerprint(path: str | Path | None) -> dict[str, Any] | None:
    resolved = resolve_glossary_path(path)
    if resolved is None:
        return None
    stat = resolved.stat()
    modified_at = datetime.fromtimestamp(stat.st_mtime, timezone.utc)
    return {
        "path": str(resolved),
        "size_bytes": stat.st_size,
        "modified_at": modified_at.isoformat().replace("+00:00", "Z"),
    }


def _replace_exact_terms(text: str, entries: list[GlossaryEntry]) -> str:
    replacements: list[tuple[str, str]] = []
    for entry in entries:
        for variant in entry.variants:
            replacements.append((variant, entry.canonical))

    replacements.sort(key=lambda item: len(item[0]), reverse=True)
    corrected = text
    for variant, canonical in replacements:
        corrected = re.sub(re.escape(variant), canonical, corrected, flags=re.IGNORECASE)
    return corrected


def _replace_fuzzy_terms(text: str, entries: list[GlossaryEntry]) -> str:
    if not entries:
        return text
    spans = [(match.start(), match.end()) for match in TOKEN_RE.finditer(text)]
    if not spans:
        return text

    canonical_norms = {_normalize_for_match(entry.canonical) for entry in entries}
    max_window = max(_term_token_count(entry.canonical) for entry in entries)
    max_window = max(1, min(4, max_window))
    pieces: list[str] = []
    cursor = 0
    index = 0

    while index < len(spans):
        best: tuple[float, int, GlossaryEntry] | None = None
        for window in range(1, max_window + 1):
            end_index = index + window - 1
            if end_index >= len(spans):
                break
            start, _ = spans[index]
            _, end = spans[end_index]
            candidate = text[start:end]
            match = _best_entry_match(candidate, entries, window, canonical_norms)
            if match is None:
                continue
            score, entry = match
            if best is None or score > best[0]:
                best = (score, end_index + 1, entry)

        if best is None:
            index += 1
            continue

        start, _ = spans[index]
        _, end = spans[best[1] - 1]
        pieces.append(text[cursor:start])
        pieces.append(best[2].canonical)
        cursor = end
        index = best[1]

    pieces.append(text[cursor:])
    return "".join(pieces)


def _best_entry_match(
    candidate: str,
    entries: list[GlossaryEntry],
    token_count: int,
    canonical_norms: set[str],
) -> tuple[float, GlossaryEntry] | None:
    candidate_norm = _normalize_for_match(candidate)
    if candidate_norm in canonical_norms:
        return None

    best: tuple[float, GlossaryEntry] | None = None
    for entry in entries:
        canonical_norm = _normalize_for_match(entry.canonical)
        if token_count != _term_token_count(entry.canonical):
            continue
        if not candidate_norm or candidate_norm == canonical_norm:
            continue
        if candidate_norm.startswith(canonical_norm) or candidate_norm.endswith(canonical_norm):
            continue
        if not _similar_length(candidate_norm, canonical_norm):
            continue
        score = SequenceMatcher(None, candidate_norm, canonical_norm).ratio()
        if score < _threshold(canonical_norm):
            continue
        if best is None or score > best[0]:
            best = (score, entry)
    return best


def _normalize_for_match(value: str) -> str:
    return re.sub(r"\s+", "", value).casefold()


def _similar_length(candidate: str, canonical: str) -> bool:
    if not candidate or not canonical:
        return False
    ratio = len(candidate) / len(canonical)
    return 0.65 <= ratio <= 1.35


def _threshold(canonical: str) -> float:
    if _contains_thai(canonical):
        return 0.70 if len(canonical) >= 5 else 0.84
    return 0.86


def _contains_thai(value: str) -> bool:
    return any("\u0E00" <= character <= "\u0E7F" for character in value)


def _term_token_count(value: str) -> int:
    return max(1, len(TOKEN_RE.findall(value)))


def _clean_value(value: str) -> str:
    return value.strip().strip("'\"`")
