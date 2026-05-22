from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from aesubtitle.glossary import glossary_fingerprint


def transcript_cache_path(source_path: str | Path) -> Path:
    source = Path(source_path)
    return source.with_suffix(".aesubtitle.json")


def source_fingerprint(source_path: str | Path) -> dict[str, Any]:
    source = Path(source_path)
    stat = source.stat()
    modified_at = datetime.fromtimestamp(stat.st_mtime, timezone.utc)
    return {
        "size_bytes": stat.st_size,
        "modified_at": modified_at.isoformat().replace("+00:00", "Z"),
    }


def load_transcript(cache_path: str | Path) -> dict[str, Any]:
    with Path(cache_path).open("r", encoding="utf-8") as file:
        return json.load(file)


def write_transcript_atomic(cache_path: str | Path, transcript: dict[str, Any]) -> None:
    path = Path(cache_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temp_path = path.with_suffix(".tmp")
    with temp_path.open("w", encoding="utf-8") as file:
        json.dump(transcript, file, ensure_ascii=False, indent=2)
        file.write("\n")
    os.replace(temp_path, path)


def cache_matches_source(
    transcript: dict[str, Any],
    source_path: str | Path,
    glossary_path: str | Path | None = None,
) -> bool:
    try:
        if transcript.get("source_fingerprint") != source_fingerprint(source_path):
            return False
        if glossary_path is not None:
            expected_glossary = glossary_fingerprint(glossary_path)
            return transcript.get("glossary_fingerprint") == expected_glossary
        return True
    except OSError:
        return False
