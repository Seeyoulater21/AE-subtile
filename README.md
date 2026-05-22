# AE Subtitle

Lightweight After Effects ScriptUI panel for one-click subtitle generation from the active voice-over comp.

## Product Goal

AE Subtitle creates ordinary After Effects text layers from speech in a `Voice-over` composition. The MVP is intentionally small: click `Generate Subtitle`, transcribe the source audio file with a local Whisper-compatible Python CLI, then create timed subtitle text layers in the current composition.

## MVP Workflow

1. Open the After Effects composition named `Voice-over`.
2. Select or keep active the comp that contains one imported voice-over audio/video layer.
3. Click `Generate Subtitle` in the dockable ScriptUI panel.
4. The panel calls a local Python CLI through `system.callSystem`.
5. The Python CLI transcribes the layer source file and writes a sidecar cache named `*.aesubtitle.json`.
6. The JSX panel deletes existing layers whose names start with `SUB `.
7. The JSX panel creates ordinary text layers, one per transcript segment, with matching `inPoint` and `outPoint`.

## MVP Defaults

- After Effects UI: dockable `.jsx` ScriptUI panel.
- Transcription: local Python CLI using ffmpeg plus a Whisper-compatible engine.
- Source: first usable audio/video layer source file in the active `Voice-over` comp.
- Cache: `*.aesubtitle.json` next to the source audio/video file.
- Subtitle layers: `SUB 001`, `SUB 002`, etc.
- Subtitle style: bottom centered, white fill, black stroke or shadow, size scaled from comp height.
- Text wrapping: up to two readable lines per segment, without changing Whisper segment timing.
- Repeat generation: remove only `SUB ` layers, then rebuild.

## Install

1. Install `ffmpeg`.
2. Create the local Python environment:

```sh
cd python
python3 -m venv .venv
. .venv/bin/activate
python3 -m pip install -e ".[transcribe]"
```

3. Copy `ae/AE Subtitle.jsx` into the After Effects `Scripts/ScriptUI Panels` folder.
4. Restart After Effects and open `Window > AE Subtitle`.
5. If needed, click `Python...` and select `python/.venv/bin/python`.
6. If needed, click `CLI...` and select `python/aesubtitle/cli.py`.

## CLI Usage

```sh
PYTHONPATH=python python3 -m aesubtitle transcribe "/path/to/voice over.wav"
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
- No server process for MVP.
- No automatic comp audio render for MVP.
- No word-level karaoke highlighting.
- No manual subtitle editor.
- No translation.
- No Premiere Pro panel work in this repository.

## Related Reference

This project borrows the local Whisper and transcript JSON ideas from the sibling project `Thai-Text-Based-Editing-tool`, but the integration target is After Effects and the UI is much smaller.
