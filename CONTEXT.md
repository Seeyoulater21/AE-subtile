# AE Subtitle Context

This glossary defines the project language for the After Effects subtitle workflow. It keeps future agents aligned on what the user means by comp, voice-over, transcript, cache, and generated subtitle layers.

## Language

**Subtitle Target Comp**:
The active After Effects composition that contains the voice-over source layer and receives generated subtitle text layers. The comp can use any name.
_Avoid_: timeline, sequence, Premiere sequence

**Voice-over Layer**:
A layer inside the Subtitle Target Comp whose source points to an imported audio or video file.
_Avoid_: script layer, subtitle layer

**Source Audio File**:
The filesystem media file referenced by the Voice-over Layer. It may be an audio file or a video file with audio.
_Avoid_: rendered comp audio, exported audio

**Generate Subtitle**:
The primary user action in the ScriptUI panel that transcribes the Source Audio File and rebuilds subtitle layers.
_Avoid_: auto cut, text-based edit

**Transcript**:
A JSON record of speech segments from the Source Audio File, with source-second timestamps and text.
_Avoid_: script, screenplay, caption file

**Subtitle Segment**:
One timed transcript item with `start`, `end`, and `text`. One Subtitle Segment maps to one generated After Effects text layer in MVP.
_Avoid_: word, token, paragraph

**Subtitle Text Layer**:
An ordinary After Effects text layer created from a Subtitle Segment and named with the `SUB ` prefix.
_Avoid_: caption object, subtitle file

**Transcript Cache**:
The sidecar `*.aesubtitle.json` file saved next to the Source Audio File so repeated generation can skip transcription when the source has not changed.
_Avoid_: database, project cache

**Rebuild**:
The safe repeat-generation behavior: delete only existing `SUB ` layers, then create fresh Subtitle Text Layers from the current Transcript.
_Avoid_: sync, update in place

## Flagged Ambiguities

**Script**:
The user may say "script" to mean spoken content, an After Effects `.jsx` script, or a written client script. In this project, prefer `Transcript` for recognized speech and `ScriptUI panel` for the After Effects code.

**Comp timing vs source timing**:
MVP treats source seconds as comp seconds. If the Voice-over Layer starts later than `0`, is trimmed, or is time-remapped, that is outside MVP unless a future issue adds mapping.

## Example Dialogue

Developer: "When the user clicks Generate Subtitle, should we transcribe the active comp or the Source Audio File?"

Domain expert: "Use the Source Audio File from the Voice-over Layer. Do not render the comp first."

Developer: "After transcription, should we create one text layer per word or per segment?"

Domain expert: "Use one Subtitle Text Layer per Subtitle Segment. Timing comes from the Transcript."

Developer: "What happens when Generate Subtitle is clicked again?"

Domain expert: "Rebuild. Delete only `SUB ` layers and recreate them from the Transcript Cache or regenerated Transcript."
