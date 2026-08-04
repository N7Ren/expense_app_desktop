import unittest

from receipt_analysis import local_ocr_status


class TestLocalOcrAvailability(unittest.TestCase):
    def test_reports_a_clear_local_installation_hint_when_ocr_is_unavailable(self):
        available, status = local_ocr_status()
        if not available:
            self.assertIn("Install Tesseract OCR", status)
            self.assertIn("No file was sent anywhere", status)
        else:
            self.assertIn("available", status)