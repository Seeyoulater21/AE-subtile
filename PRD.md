# PRD: AE Subtitle

## Problem

Creating Thai and English subtitles in After Effects is repetitive. The user already has a `Voice-over` composition with an imported voice-over audio or video layer, but turning speech into timed text layers still requires manual transcription, timing, layer creation, and styling.

## Target User

Primary user: Pakdaesed / Aboutmotion motion designer working in After Effects on Thai and mixed Thai-English voice-over videos.

## Product Goal

Provide a very lightweight After Effects tool that generates normal subtitle text layers in the current comp with one click.

## Core Workflow

1. User opens the `Voice-over` comp in After Effects.
2. User clicks `Generate Subtitle` in a dockable ScriptUI panel.
3. The panel finds the source audio/video file from the comp layer.
4. The panel calls a local Python CLI through `system.callSystem`.
5. The CLI extracts/transcribes audio with a local Whisper-compatible engine.
6. The CLI writes or reuses a sidecar `*.aesubtitle.json` transcript cache.
7. The panel deletes old `SUB ` layers and creates one ordinary text layer per segment.

## MVP Scope

### In Scope

- Dockable After Effects ScriptUI panel with a `Generate Subtitle` button.
- Active comp validation for the `Voice-over` workflow.
- Source file detection from an imported audio/video layer.
- Python CLI transcription helper using local ffmpeg and Whisper-compatible transcription.
- Thai and English transcript support.
- Sidecar transcript cache next to the source file.
- Transcript JSON contract with source fingerprint and timed segments.
- Ordinary After Effects text layers with `inPoint` and `outPoint` matching transcript segment timing.
- Bottom-centered subtitle style with readable defaults.
- Safe rebuild behavior that deletes only layers named `SUB *`.
- Focused manual QA instructions for After Effects.

### Out of Scope

- Cloud transcription.
- Always-running local HTTP server.
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
- The panel works from the active `Voice-over` comp.
- The panel finds an imported source file from a comp layer.
- The user receives a clear error if no usable source file exists.
- A successful run creates `SUB 001`, `SUB 002`, etc.

### US-2: Reuse Transcript Cache

As a user, I want repeated generation to be faster when the audio file has not changed.

Acceptance criteria:
- The Python CLI writes `*.aesubtitle.json` next to the source media.
- The CLI reuses the cache when source fingerprint still matches.
- The CLI regenerates the cache when source size or modified time changes.

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
- The source layer is not time-remapped, speed-changed, or nested in a way that requires offset mapping in MVP.
- The user is on macOS with After Effects and local Python available.
- ffmpeg and the selected Whisper-compatible engine can be installed locally.
- The first implementation can borrow concepts from ThaiCut but should not depend on running the ThaiCut server.

## Risks

| Risk | Impact | Mitigation |
| --- | --- | --- |
| After Effects `system.callSystem` path quoting is fragile | Python CLI fails for paths with spaces | Add technical validation spike with real paths containing spaces |
| AE cannot read source files from some layer types | No transcription source | Validate imported audio/video layer only; show clear error |
| Whisper setup is heavy for a "lightweight" script | Install friction | Keep AE side tiny; isolate transcription in Python helper |
| Thai segmentation creates awkward long lines | Poor readability | Add conservative line wrapping without changing timing |
| Cache becomes stale | Wrong subtitles | Store source size and modified time in JSON |
| Rebuild deletes wrong layers | User data loss | Delete only names matching `SUB ` prefix |

