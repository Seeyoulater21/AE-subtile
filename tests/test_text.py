import unittest

from aesubtitle.text import clean_segment_text, wrap_subtitle_text


class TextTests(unittest.TestCase):
    def test_clean_segment_text_collapses_whitespace(self):
        self.assertEqual(clean_segment_text(" hello\n\nworld\t "), "hello world")

    def test_wrap_subtitle_text_prefers_spaces_for_english(self):
        self.assertEqual(
            wrap_subtitle_text("hello world from subtitle tool", max_chars=18),
            "hello world from\nsubtitle tool",
        )

    def test_wrap_subtitle_text_splits_thai_without_losing_text(self):
        text = "สวัสดีครับยินดีต้อนรับทุกคน"
        wrapped = wrap_subtitle_text(text, max_chars=14)

        self.assertEqual(wrapped.replace("\n", ""), text)
        self.assertLessEqual(len(wrapped.splitlines()), 2)


if __name__ == "__main__":
    unittest.main()
