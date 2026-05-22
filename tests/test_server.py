import json
import tempfile
import threading
import unittest
import urllib.request
from pathlib import Path

from aesubtitle import server


class FakeTranscriber:
    def transcribe(self, source_path):
        return {
            "duration_seconds": 1.0,
            "language": "th",
            "model": "fake-whisper",
            "segments": [{"id": 0, "start": 0.0, "end": 1.0, "text": "hello"}],
        }


class ServerTests(unittest.TestCase):
    def test_transcribe_endpoint_returns_cache_path_json(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            source = Path(temp_dir) / "voice over.wav"
            source.write_bytes(b"fake audio bytes")
            httpd = self._create_server_or_skip(
                transcriber_factory=lambda args: FakeTranscriber(),
            )
            thread = threading.Thread(target=httpd.serve_forever, daemon=True)
            thread.start()
            try:
                url = f"http://127.0.0.1:{httpd.server_port}/transcribe"
                request = urllib.request.Request(
                    url,
                    data=json.dumps({"source_path": str(source)}).encode("utf-8"),
                    headers={"Content-Type": "application/json"},
                    method="POST",
                )

                with urllib.request.urlopen(request, timeout=5) as response:
                    payload = json.loads(response.read().decode("utf-8"))

                self.assertTrue(payload["ok"])
                self.assertEqual(payload["cache_status"], "generated")
                self.assertTrue(Path(payload["transcript_path"]).exists())
            finally:
                httpd.shutdown()
                httpd.server_close()

    def test_health_endpoint(self):
        httpd = self._create_server_or_skip()
        thread = threading.Thread(target=httpd.serve_forever, daemon=True)
        thread.start()
        try:
            with urllib.request.urlopen(f"http://127.0.0.1:{httpd.server_port}/health", timeout=5) as response:
                payload = json.loads(response.read().decode("utf-8"))

            self.assertTrue(payload["ok"])
            self.assertEqual(payload["service"], "AE Subtitle")
        finally:
            httpd.shutdown()
            httpd.server_close()

    def _create_server_or_skip(self, transcriber_factory=None):
        try:
            return server.create_server(
                ("127.0.0.1", 0),
                transcriber_factory=transcriber_factory,
            )
        except PermissionError as error:
            self.skipTest(f"Local sandbox blocked localhost bind: {error}")


if __name__ == "__main__":
    unittest.main()
