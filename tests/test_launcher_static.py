import unittest
from pathlib import Path


class LauncherStaticTests(unittest.TestCase):
    def test_command_launcher_follows_dependency_and_server_flow(self):
        launcher = Path("AE Subtitle.command")

        self.assertTrue(launcher.exists(), "AE Subtitle.command must exist")
        source = launcher.read_text(encoding="utf-8")

        self.assertIn("ensure_dependencies", source)
        self.assertIn("python[transcribe]", source)
        self.assertIn("faster_whisper", source)
        self.assertIn("ffmpeg", source)
        self.assertIn("aesubtitle.server", source)
        self.assertIn("port_is_free", source)
        self.assertIn("\\033[?1049h", source)
        self.assertIn("\\033[?2026h", source)
        self.assertNotIn("echo -e", source)
        self.assertNotIn("tput", source)


if __name__ == "__main__":
    unittest.main()
