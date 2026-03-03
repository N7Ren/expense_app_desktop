import os
import tempfile
import unittest
from categorizer import Categorizer

class TestCategorizer(unittest.TestCase):
    def setUp(self):
        self._tmp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp_dir.cleanup)
        rules_path = os.path.join(self._tmp_dir.name, "rules.json")
        self.categorizer = Categorizer(rules_path=rules_path)

    def test_extract_keyword_normal(self):
        self.assertEqual(self.categorizer.extract_keyword("REWE SAGT DANKE"), "rewe sagt")

    def test_extract_keyword_single_word(self):
        self.assertEqual(self.categorizer.extract_keyword("AMAZON"), "amazon")

    def test_extract_keyword_empty(self):
        self.assertEqual(self.categorizer.extract_keyword(""), "")

    def test_extract_keyword_extra_spaces(self):
        self.assertEqual(self.categorizer.extract_keyword("  APPLE   STORE  "), "apple store")

    def test_extract_keyword_more_than_two_words(self):
        self.assertEqual(self.categorizer.extract_keyword("NETTO MARKEN-DISCOUNT NUERNBERG"), "netto marken-discount")

if __name__ == "__main__":
    unittest.main()
