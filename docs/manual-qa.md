# AE Subtitle Manual QA

Run this checklist before merging user-facing subtitle generation changes.

## Prerequisites

- Adobe After Effects is installed.
- `ffmpeg` is installed and available from Terminal.
- Python 3.10 or newer is installed.
- Python dependencies are installed:

```sh
cd python
python3 -m venv .venv
. .venv/bin/activate
python3 -m pip install -e ".[transcribe]"
```

## Panel Install

1. Copy `ae/AE Subtitle.jsx` into the After Effects `Scripts/ScriptUI Panels` folder.
2. Restart After Effects.
3. Open `Window > AE Subtitle`.
4. Click `Python...` and select `python/.venv/bin/python` if `python3` from the default environment does not have the package installed.
5. Click `CLI...` and select `python/aesubtitle/cli.py` if the panel does not find it automatically.

## Test Comp

1. Create or open a comp named `Voice-over`.
2. Import one short Thai or mixed Thai-English audio/video source.
3. Put the source layer at comp time `0`.
4. Do not trim, stretch, time-remap, or nest the source layer for MVP testing.

## Checklist

1. Click `Generate Subtitle`.
2. Confirm a sidecar `*.aesubtitle.json` appears next to the source media file.
3. Confirm layers named `SUB 001`, `SUB 002`, etc. appear in the comp.
4. Confirm generated layers are ordinary editable After Effects text layers.
5. Scrub the comp and confirm each subtitle appears during the matching spoken phrase.
6. Confirm subtitles are bottom centered and readable with white fill plus black stroke.
7. Confirm long Thai/English text wraps into readable lines.
8. Add a normal non-subtitle layer, then run `Generate Subtitle` again.
9. Confirm old `SUB ` layers are replaced instead of duplicated.
10. Confirm the normal non-subtitle layer remains untouched.
11. Run `Generate Subtitle` again without changing the source media.
12. Confirm the panel reports cache reuse.
13. Replace or modify the source media and run again.
14. Confirm the cache regenerates.
15. Test error states:
    - no active comp
    - active comp with no imported source layer
    - unavailable Python executable
    - unavailable `ffmpeg`
    - missing `faster-whisper`
16. Confirm each error explains what is missing or outside MVP.

## MVP Timing Limit

MVP uses source seconds directly as comp seconds. A source layer that starts after `0`, is trimmed, stretched, or time-remapped should show a clear MVP timing error instead of generating misleading subtitle timing.
