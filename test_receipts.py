import tempfile
import unittest
from pathlib import Path

from receipts import ReceiptStore


class TestReceiptStore(unittest.TestCase):
    def test_imports_valid_receipts_lists_metadata_and_skips_duplicates(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "receipt.pdf"
            source.write_bytes(b"%PDF-1.7\nreceipt text")
            store = ReceiptStore(Path(directory) / "stored")

            result = store.import_files([source])

            self.assertEqual(result["imported"], ["receipt.pdf"])
            rows = store.list_receipts()
            self.assertEqual(len(rows), 1)
            self.assertEqual(rows[0]["File name"], "receipt.pdf")
            self.assertEqual(rows[0]["Type"], "PDF")
            self.assertEqual(rows[0]["Size"], "21 B")
            self.assertTrue((store.root / "receipts.json").is_file())
            self.assertEqual(store.import_files([source])["skipped"], ["receipt.pdf: already uploaded"])

    def test_rejects_invalid_extension_and_mismatched_content(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            text_file = root / "note.txt"
            text_file.write_text("not a receipt", encoding="utf-8")
            fake_pdf = root / "fake.pdf"
            fake_pdf.write_text("not actually a PDF", encoding="utf-8")
            store = ReceiptStore(root / "stored")

            result = store.import_files([text_file, fake_pdf])

            self.assertEqual(result["imported"], [])
            self.assertEqual(len(result["failed"]), 2)
            self.assertEqual(store.list_receipts(), [])
