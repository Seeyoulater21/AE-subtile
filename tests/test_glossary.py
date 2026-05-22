import tempfile
import unittest
from pathlib import Path

from aesubtitle.glossary import (
    apply_glossary_to_transcription,
    correct_text,
    glossary_fingerprint,
    load_glossary,
    parse_glossary_markdown,
)


class GlossaryTests(unittest.TestCase):
    def test_parse_markdown_canonical_entries_and_variants(self):
        entries = parse_glossary_markdown(
            """
            # Campaign words
            - canonical: Shopee Payday
              variants:
                - shopee payday
                - ชอบพี่เพเด

            - canonical: ทั่วไทย
            """
        )

        self.assertEqual(entries[0].canonical, "Shopee Payday")
        self.assertEqual(entries[0].variants, ("shopee payday", "ชอบพี่เพเด"))
        self.assertEqual(entries[1].canonical, "ทั่วไทย")

    def test_correct_text_uses_exact_variants_then_fuzzy_campaign_terms(self):
        entries = parse_glossary_markdown(
            """
            - canonical: ช็อปของ
              variants:
                - Shop ของ
            - canonical: เล็งไว้
              variants:
                - เล็งไว
            - canonical: Shopee Payday
              variants:
                - shopee payday
            - canonical: เงินออกช็อปเลย
              variants:
                - เงินออก ชอปเลย
            - canonical: ทั่วไทย
            """
        )

        corrected = correct_text(
            "Shop ของที่เล็งไว ที่ shopee payday เงินออก ชอปเลย ส่งฟรี ส่งไว ทั่วชัย",
            entries,
        )

        self.assertEqual(
            corrected,
            "ช็อปของที่เล็งไว้ ที่ Shopee Payday เงินออกช็อปเลย ส่งฟรี ส่งไว ทั่วไทย",
        )

    def test_apply_glossary_to_transcription_preserves_timing(self):
        entries = parse_glossary_markdown(
            """
            - canonical: เที่ยงคืน
              variants:
                - เชียงคืน
            """
        )
        transcription = {
            "duration_seconds": 1.0,
            "language": "th",
            "model": "fake",
            "segments": [{"id": 0, "start": 0.1, "end": 0.9, "text": "เชียงคืน"}],
        }

        corrected = apply_glossary_to_transcription(transcription, entries)

        self.assertEqual(corrected["segments"][0]["text"], "เที่ยงคืน")
        self.assertEqual(corrected["segments"][0]["start"], 0.1)
        self.assertEqual(corrected["segments"][0]["end"], 0.9)

    def test_fuzzy_correction_preserves_numbers_and_existing_canonical_terms(self):
        entries = parse_glossary_markdown(
            """
            - canonical: ดิวลดครึ่งราคา
              variants:
                - ดีลลดครึ่งราคา
            - canonical: เที่ยงคืน
              variants:
                - เชียงคืน
            - canonical: เที่ยงวัน
              variants:
                - เชียงวัน
            - canonical: พฤษภาคม
              variants:
                - พฤษภาคมมี
            """
        )

        self.assertEqual(correct_text("ดีลลดครึ่งราคา 50%", entries), "ดิวลดครึ่งราคา 50%")
        self.assertEqual(correct_text("เที่ยงคืน เที่ยงวัน", entries), "เที่ยงคืน เที่ยงวัน")
        self.assertEqual(correct_text("25 พฤษภาคมนี้", entries), "25 พฤษภาคมนี้")

    def test_load_glossary_from_file_and_fingerprint(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            glossary = Path(temp_dir) / "campaign.md"
            glossary.write_text("- canonical: ทั่วไทย\n", encoding="utf-8")

            self.assertEqual(load_glossary(glossary)[0].canonical, "ทั่วไทย")
            self.assertEqual(glossary_fingerprint(glossary)["path"], str(glossary))


if __name__ == "__main__":
    unittest.main()
