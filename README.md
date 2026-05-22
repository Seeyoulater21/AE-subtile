# AE Subtitle

Lightweight After Effects ScriptUI panel for one-click subtitle generation from the active comp.

## Product Goal

AE Subtitle creates ordinary After Effects text layers from speech in the active composition. The MVP is intentionally small: keep the local server launcher open, click `Generate Subtitle`, transcribe the source audio file with local Whisper-compatible Python, then create timed subtitle text layers in the current composition.

## MVP Workflow

1. Double-click `AE Subtitle.command` and keep the Terminal launcher open.
2. Open any After Effects comp that contains one imported voice-over audio/video layer.
3. Click `Generate Subtitle` in the dockable ScriptUI panel.
4. The panel calls the local Python server through `system.callSystem` and `curl`.
5. The Python server transcribes the layer source file and writes a sidecar cache named `*.aesubtitle.json`.
6. The JSX panel deletes existing layers whose names start with `SUB `.
7. The JSX panel creates ordinary text layers, one per transcript segment, with matching `inPoint` and `outPoint`.

## MVP Defaults

- After Effects UI: dockable `.jsx` ScriptUI panel.
- Transcription: local Python server/CLI using ffmpeg plus a Whisper-compatible engine.
- Source: first usable audio/video layer source file in the active comp. The comp name can be anything.
- Cache: `*.aesubtitle.json` next to the source audio/video file.
- Subtitle layers: `SUB 001`, `SUB 002`, etc.
- Subtitle style: bottom centered, white fill, black stroke or shadow, size scaled from comp height.
- Text wrapping: up to two readable lines per segment, without changing Whisper segment timing.
- Repeat generation: remove only `SUB ` layers, then rebuild.

## Install

1. Double-click `AE Subtitle.command`.
2. The launcher checks Python, `aesubtitle`, `faster-whisper`, and `ffmpeg` before installing anything missing.
3. Keep the launcher Terminal window open. It starts or adopts the local server at `http://127.0.0.1:8765`.
4. Copy `ae/AE Subtitle.jsx` into the After Effects `Scripts/ScriptUI Panels` folder.
5. Restart After Effects and open `Window > AE Subtitle`.

## CLI Usage

```sh
PYTHONPATH=python python3 -m aesubtitle transcribe "/path/to/voice over.wav"
```

Server usage:

```sh
PYTHONPATH=python python3 -m aesubtitle.server
```

The CLI prints machine-readable JSON:

```json
{"ok": true, "transcript_path": "/path/to/voice over.aesubtitle.json", "cache_status": "generated"}
```

Repeated runs reuse the sidecar transcript cache when source file size and modified time still match.

## Manual QA

See `docs/manual-qa.md`.

## Non-Goals

- No cloud transcription.
- No cloud or remote server process.
- No automatic comp audio render for MVP.
- No word-level karaoke highlighting.
- No manual subtitle editor.
- No translation.
- No Premiere Pro panel work in this repository.

## Related Reference

This project borrows the local Whisper and transcript JSON ideas from the sibling project `Thai-Text-Based-Editing-tool`, but the integration target is After Effects and the UI is much smaller.
