import unittest
from pathlib import Path


class JsxStaticTests(unittest.TestCase):
    def test_panel_contains_call_system_and_safe_subtitle_deletion_guard(self):
        panel_path = Path("ae/AE Subtitle.jsx")

        self.assertTrue(panel_path.exists(), "ae/AE Subtitle.jsx must exist")
        source = panel_path.read_text(encoding="utf-8")

        self.assertIn("Generate Subtitle", source)
        self.assertIn("system.callSystem", source)
        self.assertIn("SERVER_URL", source)
        self.assertIn("/transcribe", source)
        self.assertIn("curl", source)
        self.assertIn("function isSubtitleLayerName", source)
        self.assertIn("SUPPORTED_SOURCE_EXTENSIONS", source)
        self.assertIn("function isLikelyMediaSource", source)
        self.assertIn("function scanCompForSourceCandidate", source)
        self.assertIn("function describeLayerForSourceScan", source)
        self.assertIn("Scanned layers:", source)
        self.assertIn("SUBTITLE_PREFIX", source)
        self.assertIn("layer.name.indexOf(SUBTITLE_PREFIX) === 0", source)
        self.assertNotIn("VOICE_OVER_COMP_NAME", source)
        self.assertNotIn("Active comp is", source)
        self.assertNotIn('layer.name.indexOf("SUB") === 0', source)


if __name__ == "__main__":
    unittest.main()
