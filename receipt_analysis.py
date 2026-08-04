"""Transparent, local receipt text extraction with optional Tesseract OCR."""

from __future__ import annotations

import importlib.util
from pathlib import Path


OCR_INSTALLATION_HINT = (
    "Local OCR is not ready. Install Tesseract OCR, add its installation folder to PATH, "
    "and install the Python package pytesseract; then restart the app. No file was sent anywhere."
)


def local_ocr_status() -> tuple[bool, str]:
    """Report whether the locally installed Tesseract executable is usable."""
    if importlib.util.find_spec("pytesseract") is None:
        return False, OCR_INSTALLATION_HINT
    try:
        import pytesseract
        pytesseract.get_tesseract_version()
    except (ImportError, OSError, RuntimeError) as error:
        return False, f"{OCR_INSTALLATION_HINT} ({error})"
    return True, "Local Tesseract OCR is available."


def _ocr_images(images) -> tuple[str, str]:
    available, status = local_ocr_status()
    if not available:
        return "", status
    try:
        import pytesseract
        text = "\n".join(pytesseract.image_to_string(image).strip() for image in images).strip()
    except (ImportError, OSError, RuntimeError, ValueError, TypeError) as error:
        return "", f"Could not run local OCR: {error}"
    return (text, "Text extracted locally with Tesseract OCR.") if text else ("", "Local Tesseract OCR found no readable text.")


def _ocr_pdf(path: Path) -> tuple[str, str]:
    available, status = local_ocr_status()
    if not available:
        return "", status
    document = None
    try:
        from pypdfium2 import PdfDocument
        document = PdfDocument(str(path))
        page_count = len(document)
        images = []
        for page_number in range(min(page_count, 5)):
            page = document.get_page(page_number)
            try:
                images.append(page.render(scale=2).to_pil())
            finally:
                page.close()
    except (ImportError, OSError, RuntimeError, ValueError, TypeError) as error:
        return "", f"Could not render this PDF for local OCR: {error}"
    finally:
        if document is not None:
            document.close()
    text, ocr_status = _ocr_images(images)
    if text and page_count > 5:
        return text, "Text extracted locally with Tesseract OCR from the first 5 PDF pages."
    return text, ocr_status


def extract_receipt_text(path: Path) -> tuple[str, str]:
    """Return locally extracted text, falling back to local OCR for scans when available."""
    path = Path(path)
    suffix = path.suffix.lower()
    if suffix == ".pdf":
        try:
            import pdfplumber
            with pdfplumber.open(path) as document:
                text = "\n".join(page.extract_text() or "" for page in document.pages).strip()
        except (ImportError, OSError, ValueError, TypeError) as error:
            return "", f"Could not read PDF text: {error}"
        if text:
            return text, "Text extracted locally from the PDF."
        return _ocr_pdf(path)

    try:
        from PIL import Image
        with Image.open(path) as image:
            return _ocr_images([image.copy()])
    except (ImportError, OSError, ValueError, TypeError) as error:
        return "", f"Could not read this image receipt: {error}"
