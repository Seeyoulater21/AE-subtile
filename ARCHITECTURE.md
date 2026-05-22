# ARCHITECTURE: AE Subtitle

## System Overview

AE Subtitle is a small After Effects ScriptUI panel plus a local Python CLI helper. It does not run a server in the MVP.

```text
After Effects
  ScriptUI Panel (.jsx)
    |
    | system.callSystem("python ... transcribe ...")
    v
Python CLI
  ffmpeg audio extraction
  Whisper-compatible transcription
  sidecar JSON cache
    |
    v
Transcript JSON
    |
    v
After Effects Text Layers
```

## Components

### ScriptUI Panel

Purpose:
- Provide a dockable After Effects panel with one primary action: `Generate Subtitle`.
- Validate the active comp and source layer.
- Call the Python CLI.
- Parse transcript JSON.
- Rebuild subtitle text layers.

Responsibilities:
- Find active comp.
- Prefer comp named `Voice-over`; warn if active comp differs.
- Find one usable layer with `layer.source.file.fsName`.
- Build a shell-safe command for the Python CLI.
- Delete existing layers whose names start with `SUB `.
- Create one text layer per transcript segment.
- Apply default paragraph, position, color, and stroke/shadow settings.
- Report success or clear errors to the user.

### Python CLI

Purpose:
- Keep Whisper and ffmpeg work outside ExtendScript.
- Return stable transcript JSON to the panel.

Responsibilities:
- Accept source media path and output cache path.
- Reuse sidecar cache when source fingerprint matches.
- Extract audio with ffmpeg when needed.
- Transcribe Thai and English speech with a local Whisper-compatible engine.
- Clean segment text.
- Write transcript JSON atomically.
- Print JSON path or machine-readable status for the JSX caller.

### Transcript Cache

Sidecar file next to source media:

```text
voice-over.wav
voice-over.aesubtitle.json
```

Contract:

```json
{
  "version": "1.0",
  "source_file": "voice-over.wav",
  "source_path": "/path/to/voice-over.wav",
  "source_fingerprint": {
    "size_bytes": 123456,
    "modified_at": "2026-05-22T10:00:00Z"
  },
  "duration_seconds": 30.0,
  "language": "th",
  "model": "large-v3",
  "timebase": "source_seconds",
  "segments": [
    {
      "id": 0,
      "start": 0.0,
      "end": 2.4,
      "text": "สวัสดีครับ welcome everyone"
    }
  ]
}
```

## Timing Model

MVP uses source seconds directly as comp seconds.

This is valid when the comp contains the voice-over source starting at comp time `0`, with no time remap, speed change, or nested offset. More complex mapping is deferred.

## Text Layer Model

Each transcript segment becomes one ordinary text layer:

- Name: `SUB 001`, `SUB 002`, etc.
- `inPoint`: `segment.start`
- `outPoint`: `segment.end`
- Source text: wrapped segment text.
- Position: bottom center.
- Style: white fill, black stroke or shadow.

## Suggested Future File Structure

```text
ae/
  AE Subtitle.jsx
python/
  pyproject.toml
  aesubtitle/
    cli.py
    transcriber.py
    models.py
    cache.py
tests/
  fixtures/
docs/
  manual-qa.md
```

## Validation Strategy

- Unit-test Python cache, transcript model, and text wrapping logic.
- Smoke-test CLI against a tiny fixture audio file.
- Manually test JSX in After Effects because ExtendScript execution is hard to automate reliably.
- Keep ScriptUI behavior small enough for manual QA to be credible.

## CI Position

Do not create placeholder CI before implementation exists. Add CI in the foundation issue once Python package and smoke tests exist.

