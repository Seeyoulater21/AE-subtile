import json
import tempfile
import unittest
from pathlib import Path

from aesubtitle.cache import (
    cache_matches_source,
    load_transcript,
    source_fingerprint,
    transcript_cache_path,
    write_transcript_atomic,
)
from aesubtitle.glossary import glossary_fingerprint


class CacheTests(unittest.TestCase):
    def test_transcript_cache_path_uses_aesubtitle_sidecar_suffix(self):
        source = Path("/tmp/voice over.final.mp4")

        self.assertEqual(
            transcript_cache_path(source),
            Path("/tmp/voice over.final.aesubtitle.json"),
        )

    def test_cache_matches_source_until_size_or_mtime_changes(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            source = Path(temp_dir) / "voice over.wav"
            source.write_bytes(b"first")
            transcript = {
                "version": "1.0",
                "source_file": source.name,
                "source_path": str(source),
                "source_fingerprint": source_fingerprint(source),
                "duration_seconds": 1.0,
                "language": "th",
                "model": "fake",
                "timebase": "source_seconds",
                "segments": [{"id": 0, "start": 0.0, "end": 1.0, "text": "hello"}],
            }
            cache_path = transcript_cache_path(source)

            write_transcript_atomic(cache_path, transcript)

            self.assertEqual(load_transcript(cache_path), transcript)
            self.assertTrue(cache_matches_source(load_transcript(cache_path), source))

            source.write_bytes(b"changed bytes")

            self.assertFalse(cache_matches_source(load_transcript(cache_path), source))
            self.assertFalse(cache_path.with_suffix(".tmp").exists())

    def test_cache_matches_glossary_fingerprint_when_glossary_is_used(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            source = Path(temp_dir) / "voice over.wav"
            glossary = Path(temp_dir) / "campaign.md"
            source.write_bytes(b"first")
            glossary.write_text("- canonical: ทั่วไทย\n", encoding="utf-8")
            transcript = {
                "version": "1.0",
                "source_file": source.name,
                "source_path": str(source),
                "source_fingerprint": source_fingerprint(source),
                "glossary_fingerprint": glossary_fingerprint(glossary),
                "duration_seconds": 1.0,
                "language": "th",
                "model": "fake",
                "timebase": "source_seconds",
                "segments": [{"id": 0, "start": 0.0, "end": 1.0, "text": "hello"}],
            }
            cache_path = transcript_cache_path(source)

            write_transcript_atomic(cache_path, transcript)

            self.assertTrue(cache_matches_source(load_transcript(cache_path), source, glossary))

            glossary.write_text("- canonical: ทั่วไทย\n- canonical: Shopee Payday\n", encoding="utf-8")

            self.assertFalse(cache_matches_source(load_transcript(cache_path), source, glossary))


if __name__ == "__main__":
    unittest.main()
