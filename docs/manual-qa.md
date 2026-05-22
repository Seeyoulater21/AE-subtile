# AE Subtitle Manual QA

Run this checklist before merging user-facing subtitle generation changes.

## Prerequisites

- Adobe After Effects is installed.
- Python 3.10 or newer is installed.
- `AE Subtitle.command` is available in the repo root. It checks Python dependencies and `ffmpeg` before installing missing dependencies.
- `glossary.md` contains the current campaign terms and common recognition mistakes.

## Panel Install

1. Copy `ae/AE Subtitle.jsx` into the After Effects `Scripts/ScriptUI Panels` folder.
2. Restart After Effects.
3. Double-click `AE Subtitle.command` and keep the Terminal launcher open.
4. Open `Window > AE Subtitle`.

## Test Comp

1. Create or open any comp name.
2. Import one short Thai or mixed Thai-English audio/video source.
3. Put the source layer at comp time `0`.
4. Do not trim, stretch, or time-remap the source layer for MVP testing. A simple nested precomp is okay only when each timing layer starts at `0`.

## Checklist

1. Click `Generate Subtitle`.
2. Confirm a sidecar `*.aesubtitle.json` appears next to the source media file.
3. Confirm campaign words in `glossary.md`, such as brand and promotion terms, appear with canonical spelling.
4. Confirm layers named `SUB 001`, `SUB 002`, etc. appear in the comp.
5. Confirm generated layers are ordinary editable After Effects text layers.
6. Scrub the comp and confirm each subtitle appears during the matching spoken phrase.
7. Confirm subtitles are bottom centered and readable with white fill plus black stroke.
8. Confirm long Thai/English text wraps into readable lines.
9. Add a normal non-subtitle layer, then run `Generate Subtitle` again.
10. Confirm old `SUB ` layers are replaced instead of duplicated.
11. Confirm the normal non-subtitle layer remains untouched.
12. Run `Generate Subtitle` again without changing the source media.
13. Confirm the panel reports cache reuse.
14. Edit `glossary.md`, then run again.
15. Confirm the cache regenerates and glossary corrections update the subtitle text.
16. Replace or modify the source media and run again.
17. Confirm the cache regenerates.
18. Test error states:
    - no active comp
    - active comp with no imported source layer
    - unavailable Python executable
    - unavailable `ffmpeg`
    - missing `faster-whisper`
19. Confirm each error explains what is missing or outside MVP.

## MVP Timing Limit

MVP uses source seconds directly as comp seconds. A source layer or nested precomp layer that starts after `0`, is trimmed, stretched, or time-remapped should show a clear MVP timing error instead of generating misleading subtitle timing.
