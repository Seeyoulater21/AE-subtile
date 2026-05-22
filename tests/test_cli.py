import json
import tempfile
import unittest
from io import StringIO
from pathlib import Path

from aesubtitle import cli
from aesubtitle.transcriber import DEFAULT_COMPUTE_TYPE, DEFAULT_MODEL


class FakeTranscriber:
    def __init__(self, text="สวัสดีครับ welcome everyone"):
        self.text = text
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
                    "text": self.text,
                }
            ],
        }


class CliTests(unittest.TestCase):
    def test_transcribe_defaults_use_smarter_local_model_settings(self):
        args = cli.build_parser().parse_args(["transcribe", "voice.wav"])

        self.assertEqual(args.model, DEFAULT_MODEL)
        self.assertEqual(args.compute_type, DEFAULT_COMPUTE_TYPE)
        self.assertFalse(args.condition_on_previous_text)

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

    def test_transcribe_applies_glossary_before_writing_cache(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            source = Path(temp_dir) / "voice over.wav"
            source.write_bytes(b"tiny fixture media")
            glossary = Path(temp_dir) / "campaign.md"
            glossary.write_text(
                """
                - canonical: ช็อปของ
                  variants:
                    - Shop ของ
                - canonical: เล็งไว้
                  variants:
                    - เล็งไว
                - canonical: ทั่วไทย
                """,
                encoding="utf-8",
            )
            fake = FakeTranscriber("Shop ของที่เล็งไว ส่งไว ทั่วชัย")
            stdout = StringIO()

            exit_code = cli.run(
                ["transcribe", str(source), "--glossary", str(glossary)],
                stdout=stdout,
                stderr=StringIO(),
                transcriber_factory=lambda args: fake,
            )

            self.assertEqual(exit_code, 0)
            payload = json.loads(stdout.getvalue())
            transcript = json.loads(Path(payload["transcript_path"]).read_text(encoding="utf-8"))
            text = transcript["segments"][0]["text"].replace("\n", "")
            self.assertEqual(text, "ช็อปของที่เล็งไว้ ส่งไว ทั่วไทย")
            self.assertIn("glossary_fingerprint", transcript)

    def test_empty_glossary_argument_disables_default_glossary(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            source = Path(temp_dir) / "voice over.wav"
            source.write_bytes(b"tiny fixture media")
            fake = FakeTranscriber("Shop ของที่เล็งไว ส่งไว ทั่วชัย")
            stdout = StringIO()

            exit_code = cli.run(
                ["transcribe", str(source), "--glossary", ""],
                stdout=stdout,
                stderr=StringIO(),
                transcriber_factory=lambda args: fake,
            )

            self.assertEqual(exit_code, 0)
            payload = json.loads(stdout.getvalue())
            transcript = json.loads(Path(payload["transcript_path"]).read_text(encoding="utf-8"))
            text = transcript["segments"][0]["text"].replace("\n", "")
            self.assertEqual(text, "Shop ของที่เล็งไว ส่งไว ทั่วชัย")
            self.assertNotIn("glossary_fingerprint", transcript)

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
