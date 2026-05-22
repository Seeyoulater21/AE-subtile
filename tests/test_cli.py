import json
import tempfile
import unittest
from io import StringIO
from pathlib import Path

from aesubtitle import cli


class FakeTranscriber:
    def __init__(self):
        self.calls = 0

    def transcribe(self, source_path):
        self.calls += 1
        return {
            "duration_seconds": 2.0,
            "language": "th",
            "model": "fake-whisper",
            "segments": [
                {
                    "id": 0,
                    "start": 0.0,
                    "end": 2.0,
                    "text": "สวัสดีครับ welcome everyone",
                }
            ],
        }


class CliTests(unittest.TestCase):
    def test_transcribe_command_writes_cache_for_source_path_with_spaces_and_reuses_it(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            source = Path(temp_dir) / "voice over with spaces.wav"
            source.write_bytes(b"tiny fixture media")
            stdout = StringIO()
            stderr = StringIO()
            fake = FakeTranscriber()

            first_code = cli.run(
                ["transcribe", str(source), "--model", "fake-whisper"],
                stdout=stdout,
                stderr=stderr,
                transcriber_factory=lambda args: fake,
            )

            self.assertEqual(first_code, 0, stderr.getvalue())
            first_payload = json.loads(stdout.getvalue())
            transcript_path = Path(first_payload["transcript_path"])
            self.assertEqual(first_payload["cache_status"], "generated")
            self.assertTrue(transcript_path.exists())
            self.assertEqual(fake.calls, 1)

            stdout = StringIO()
            second_code = cli.run(
                ["transcribe", str(source), "--model", "fake-whisper"],
                stdout=stdout,
                stderr=StringIO(),
                transcriber_factory=lambda args: fake,
            )

            self.assertEqual(second_code, 0)
            second_payload = json.loads(stdout.getvalue())
            self.assertEqual(second_payload["transcript_path"], str(transcript_path))
            self.assertEqual(second_payload["cache_status"], "hit")
            self.assertEqual(fake.calls, 1)

    def test_missing_source_prints_clear_json_error(self):
        stderr = StringIO()

        exit_code = cli.run(
            ["transcribe", "/tmp/no-such-source.wav"],
            stdout=StringIO(),
            stderr=stderr,
        )

        self.assertNotEqual(exit_code, 0)
        payload = json.loads(stderr.getvalue())
        self.assertIn("does not exist", payload["error"])


if __name__ == "__main__":
    unittest.main()
