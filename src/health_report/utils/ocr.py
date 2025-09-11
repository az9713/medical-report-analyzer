from __future__ import annotations

import logging
from pathlib import Path
from typing import Optional


DEFAULT_OCR_DPI = 200
DEFAULT_OCR_LANGS = "eng"


def ocr_page(
    pdf_path: Path,
    page_index: int,
    *,
    dpi: int = DEFAULT_OCR_DPI,
    languages: str = DEFAULT_OCR_LANGS,
) -> str:
    """Render a single PDF page to an image and run Tesseract OCR.

    Returns empty string if OCR dependencies are unavailable or an error occurs.
    - page_index is zero-based.
    """
    try:
        import pypdfium2 as pdfium  # type: ignore
        import pytesseract  # type: ignore
    except ImportError as e:
        logging.debug("OCR dependencies not available: %s", e)
        return ""

    try:
        pdf = pdfium.PdfDocument(str(pdf_path))
        if page_index < 0 or page_index >= len(pdf):
            return ""
        page = pdf.get_page(page_index)
        bitmap = page.render(scale=dpi / 72.0).to_pil()
        text = pytesseract.image_to_string(bitmap, lang=languages) or ""
        return text
    except Exception as e:
        logging.warning(f"OCR for {pdf_path.name} page {page_index} failed: {e}")
        return ""
