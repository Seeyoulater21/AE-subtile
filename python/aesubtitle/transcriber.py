from __future__ import annotations

import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Any

from aesubtitle.text import clean_segment_text


class TranscriptionError(RuntimeError):
    pass


class FfmpegWhisperTranscriber:
    def __init__(
        self,
        model: str = "small",
        language: str | None = None,
        device: str = "auto",
        compute_type: str = "default",
    ) -> None:
        self.model = model
        self.language = language
        self.device = device
        self.compute_type = compute_type

    def transcribe(self, source_path: str | Path) -> dict[str, Any]:
        source = Path(source_path)
        ffmpeg = shutil.which("ffmpeg")
        if not ffmpeg:
            raise TranscriptionError("ffmpeg not found. Install ffmpeg and make it available on PATH.")

        try:
            from faster_whisper import WhisperModel
        except ImportError as error:
            raise TranscriptionError(
                "faster-whisper is not installed. Run `python3 -m pip install -e 'python[transcribe]'`."
            ) from error

        with tempfile.TemporaryDirectory(prefix="aesubtitle-") as temp_dir:
            audio_path = Path(temp_dir) / "source.wav"
            self._extract_audio(ffmpeg, source, audio_path)
            model = WhisperModel(self.model, device=self.device, compute_type=self.compute_type)
            segments, info = model.transcribe(
                str(audio_path),
                language=self.language,
                vad_filter=True,
            )
            normalized = [
                {
                    "id": index,
                    "start": float(segment.start),
                    "end": float(segment.end),
                    "text": clean_segment_text(segment.text),
                }
                for index, segment in enumerate(segments)
            ]

        return {
            "duration_seconds": float(getattr(info, "duration", 0.0) or _segments_duration(normalized)),
            "language": getattr(info, "language", None) or self.language or "auto",
            "model": self.model,
            "segments": normalized,
        }

    @staticmethod
    def _extract_audio(ffmpeg: str, source: Path, audio_path: Path) -> None:
        command = [
            ffmpeg,
            "-y",
            "-i",
            str(source),
            "-vn",
            "-ac",
            "1",
            "-ar",
            "16000",
            "-f",
            "wav",
            str(audio_path),
        ]
        result = subprocess.run(command, capture_output=True, text=True)
        if result.returncode != 0:
            message = result.stderr.strip() or result.stdout.strip() or "ffmpeg failed to extract audio."
            raise TranscriptionError(f"ffmpeg failed to extract audio: {message}")


def _segments_duration(segments: list[dict[str, Any]]) -> float:
    if not segments:
        return 0.0
    return max(float(segment["end"]) for segment in segments)
