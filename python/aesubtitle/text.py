from __future__ import annotations

import re


def clean_segment_text(text: object) -> str:
    return re.sub(r"\s+", " ", str(text)).strip()


def wrap_subtitle_text(text: object, max_chars: int = 42, max_lines: int = 2) -> str:
    cleaned = clean_segment_text(text)
    if not cleaned or len(cleaned) <= max_chars:
        return cleaned

    if " " not in cleaned:
        return _limit_lines([cleaned[i : i + max_chars] for i in range(0, len(cleaned), max_chars)], max_lines)

    lines: list[str] = []
    current = ""
    for word in cleaned.split(" "):
        candidate = word if not current else f"{current} {word}"
        if len(candidate) <= max_chars:
            current = candidate
            continue
        if current:
            lines.append(current)
        current = word
    if current:
        lines.append(current)

    return _limit_lines(lines, max_lines)


def _limit_lines(lines: list[str], max_lines: int) -> str:
    if len(lines) <= max_lines:
        return "\n".join(lines)
    kept = lines[: max_lines - 1]
    kept.append(" ".join(lines[max_lines - 1 :]))
    return "\n".join(kept)
