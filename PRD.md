# PRD: AE Subtitle

## Problem

Creating Thai and English subtitles in After Effects is repetitive. The user already has a `Voice-over` composition with an imported voice-over audio or video layer, but turning speech into timed text layers still requires manual transcription, timing, layer creation, and styling.

## Target User

Primary user: Pakdaesed / Aboutmotion motion designer working in After Effects on Thai and mixed Thai-English voice-over videos.

## Product Goal

Provide a very lightweight After Effects tool that generates normal subtitle text layers in the current comp with one click.

## Core Workflow

1. User opens `AE Subtitle.command` and keeps the Terminal launcher running.
2. User opens any comp containing the voice-over source in After Effects.
3. User clicks `Generate Subtitle` in a dockable ScriptUI panel.
4. The panel finds the source audio/video file from the comp layer, including a simple nested precomp source when timing is still at `0`.
5. The panel calls a local Python server through `system.callSystem` and `curl`.
6. The server extracts/transcribes audio with a local Whisper-compatible engine.
7. The server writes or reuses a sidecar `*.aesubtitle.json` transcript cache.
8. The panel deletes old `SUB ` layers and creates one ordinary text layer per segment.

## MVP Scope

### In Scope

- Dockable After Effects ScriptUI panel with a `Generate Subtitle` button.
- Active comp validation for the subtitle workflow. The comp can use any name.
- Source file detection from an imported audio/video layer.
- Python local server and CLI transcription helper using local ffmpeg and Whisper-compatible transcription.
- macOS `.command` launcher that checks dependencies before installing, starts/adopts the local server, and shows status/logs.
- Thai and English transcript support.
- Sidecar transcript cache next to the source file.
- Transcript JSON contract with source fingerprint and timed segments.
- Ordinary After Effects text layers with `inPoint` and `outPoint` matching transcript segment timing.
- Bottom-centered subtitle style with readable defaults.
- Safe rebuild behavior that deletes only layers named `SUB *`.
- Focused manual QA instructions for After Effects.

### Out of Scope

- Cloud transcription.
- Cloud or remote HTTP server.
- Rendering the whole comp to audio before transcription.
- Retimed, nested, or multi-layer audio alignment.
- Manual subtitle editing UI.
- Translation.
- Karaoke or word-by-word animation.
- Subtitle export formats such as SRT or VTT.
- Packaging as a full Adobe UXP plugin.

## User Stories

### US-1: Generate Subtitles

As a motion designer, I want to click one button in After Effects so that subtitle text layers are created from the voice-over audio.

Acceptance criteria:
- The panel works from any active comp name.
- The panel finds an imported source file from a comp layer.
- The user receives a clear error if no usable source file exists.
- A successful run creates `SUB 001`, `SUB 002`, etc.

### US-2: Reuse Transcript Cache

As a user, I want repeated generation to be faster when the audio file has not changed.

Acceptance criteria:
- The Python server/CLI writes `*.aesubtitle.json` next to the source media.
- The server/CLI reuses the cache when source fingerprint still matches.
- The server/CLI regenerates the cache when source size or modified time changes.

### US-3: Safe Rebuild

As a user, I want to regenerate subtitles without damaging my comp.

Acceptance criteria:
- The panel deletes only layers with names starting `SUB `.
- Non-subtitle layers remain untouched.
- New subtitle layers use segment start/end timing.

### US-4: Readable Default Styling

As a user, I want generated subtitles to be readable without manual styling.

Acceptance criteria:
- Text appears bottom centered.
- Text uses white fill with black stroke or shadow.
- Text size scales from comp height.
- Long text is wrapped into up to two readable lines when possible.

## Success Criteria

- A 30-second Thai/English voice-over comp can generate subtitles end-to-end.
- Re-running generation does not duplicate subtitle layers.
- Existing non-subtitle layers remain unchanged.
- Cached transcript reuse avoids re-transcribing unchanged source media.
- Generated layers are normal After Effects text layers that the user can edit manually.

## Assumptions

- The active comp contains one usable imported voice-over audio/video source file.
- The source layer and any simple nested precomp source start at comp time `0` and are not time-remapped, speed-changed, or trimmed.
- The user is on macOS with After Effects and local Python available.
- ffmpeg and the selected Whisper-compatible engine can be installed locally.
- The first implementation can borrow concepts from ThaiCut but should not depend on running the ThaiCut server.

## Risks

| Risk | Impact | Mitigation |
| --- | --- | --- |
| After Effects `system.callSystem` path quoting is fragile | Server request fails for paths with spaces | Add technical validation spike with real paths containing spaces |
| AE cannot read source files from some layer types | No transcription source | Validate imported audio/video layer only; show clear error |
| Whisper setup is heavy for a "lightweight" script | Install friction | Keep AE side tiny; isolate transcription in Python helper |
| Thai segmentation creates awkward long lines | Poor readability | Add conservative line wrapping without changing timing |
| Cache becomes stale | Wrong subtitles | Store source size and modified time in JSON |
| Rebuild deletes wrong layers | User data loss | Delete only names matching `SUB ` prefix |
