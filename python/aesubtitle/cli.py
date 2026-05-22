from __future__ import annotations

if __package__ in (None, ""):
    import sys
    from pathlib import Path

    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import argparse
import json
import os
import sys
from argparse import Namespace
from pathlib import Path
from typing import Callable, TextIO

from aesubtitle.cache import cache_matches_source, load_transcript, transcript_cache_path, write_transcript_atomic
from aesubtitle.glossary import (
    apply_glossary_to_transcription,
    glossary_fingerprint,
    load_glossary,
    resolve_glossary_path,
)
from aesubtitle.models import TranscriptError, build_transcript
from aesubtitle.transcriber import DEFAULT_COMPUTE_TYPE, DEFAULT_MODEL, FfmpegWhisperTranscriber, TranscriptionError


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="ae-subtitle")
    subparsers = parser.add_subparsers(dest="command", required=True)
    transcribe = subparsers.add_parser("transcribe", help="Transcribe source media and write sidecar JSON")
    transcribe.add_argument("source", help="Source audio/video media path")
    transcribe.add_argument("--output", "-o", help="Transcript JSON output path")
    transcribe.add_argument("--model", default=os.environ.get("AESUBTITLE_MODEL", DEFAULT_MODEL))
    transcribe.add_argument("--language", default=os.environ.get("AESUBTITLE_LANGUAGE"))
    transcribe.add_argument("--device", default=os.environ.get("AESUBTITLE_DEVICE", "auto"))
    transcribe.add_argument("--compute-type", default=os.environ.get("AESUBTITLE_COMPUTE_TYPE", DEFAULT_COMPUTE_TYPE))
    transcribe.add_argument("--glossary", default=os.environ.get("AESUBTITLE_GLOSSARY"))
    transcribe.add_argument("--condition-on-previous-text", action="store_true")
    transcribe.add_argument("--force", action="store_true", help="Regenerate even when cache fingerprint matches")
    return parser


def run(
    argv: list[str] | None = None,
    stdout: TextIO = sys.stdout,
    stderr: TextIO = sys.stderr,
    transcriber_factory: Callable[[argparse.Namespace], object] | None = None,
) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        if args.command == "transcribe":
            payload = _handle_transcribe(args, transcriber_factory)
        else:
            raise ValueError(f"Unsupported command: {args.command}")
    except (OSError, TranscriptionError, TranscriptError, ValueError) as error:
        _write_json(stderr, {"ok": False, "error": str(error)})
        return 1

    _write_json(stdout, payload)
    return 0


def main(argv: list[str] | None = None) -> int:
    return run(argv)


def _handle_transcribe(
    args: argparse.Namespace,
    transcriber_factory: Callable[[argparse.Namespace], object] | None,
) -> dict[str, object]:
    source = Path(args.source).expanduser()
    return transcribe_source(
        source=source,
        output=args.output,
        model=args.model,
        language=args.language,
        device=args.device,
        compute_type=args.compute_type,
        glossary=args.glossary,
        condition_on_previous_text=args.condition_on_previous_text,
        force=args.force,
        transcriber_factory=transcriber_factory,
    )


def transcribe_source(
    source: str | Path,
    output: str | Path | None = None,
    model: str = DEFAULT_MODEL,
    language: str | None = None,
    device: str = "auto",
    compute_type: str = DEFAULT_COMPUTE_TYPE,
    glossary: str | Path | None = None,
    condition_on_previous_text: bool = False,
    force: bool = False,
    transcriber_factory: Callable[[argparse.Namespace], object] | None = None,
) -> dict[str, object]:
    source = Path(source).expanduser()
    if not source.exists():
        raise ValueError(f"Source media does not exist: {source}")
    if not source.is_file():
        raise ValueError(f"Source media is not a file: {source}")

    cache_path = Path(output).expanduser() if output else transcript_cache_path(source)
    glossary_path = resolve_glossary_path(glossary)
    if not force and cache_path.exists():
        cached = load_transcript(cache_path)
        if cache_matches_source(cached, source, glossary_path):
            return {"ok": True, "transcript_path": str(cache_path), "cache_status": "hit"}

    factory = transcriber_factory or _default_transcriber_factory
    args = Namespace(
        model=model,
        language=language,
        device=device,
        compute_type=compute_type,
        condition_on_previous_text=condition_on_previous_text,
    )
    transcriber = factory(args)
    transcription = transcriber.transcribe(source)  # type: ignore[attr-defined]
    entries = load_glossary(glossary_path) if glossary_path is not None else []
    transcription = apply_glossary_to_transcription(transcription, entries)
    transcription["glossary_fingerprint"] = glossary_fingerprint(glossary_path) if glossary_path is not None else None
    transcript = build_transcript(source, transcription)
    write_transcript_atomic(cache_path, transcript)
    return {"ok": True, "transcript_path": str(cache_path), "cache_status": "generated"}


def _default_transcriber_factory(args: argparse.Namespace) -> FfmpegWhisperTranscriber:
    return FfmpegWhisperTranscriber(
        model=args.model,
        language=args.language,
        device=args.device,
        compute_type=args.compute_type,
        condition_on_previous_text=args.condition_on_previous_text,
    )


def _write_json(stream: TextIO, payload: dict[str, object]) -> None:
    json.dump(payload, stream, ensure_ascii=False)
    stream.write("\n")


if __name__ == "__main__":
    raise SystemExit(main())
