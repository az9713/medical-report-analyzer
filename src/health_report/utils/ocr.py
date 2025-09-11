from __future__ import annotations

from pathlib import Path
from typing import Optional


def ocr_page(pdf_path: Path, page_index: int, *, dpi: int = 200, languages: str = "eng") -> str:
    """Render a single PDF page to an image and run Tesseract OCR.

    Returns empty string if OCR dependencies are unavailable.
    - page_index is zero-based.
    """
    try:
        import pypdfium2 as pdfium  # type: ignore
    except Exception:
        return ""
    try:
        import pytesseract  # type: ignore
    except Exception:
        return ""

    try:
        pdf = pdfium.PdfDocument(str(pdf_path))
        if page_index < 0 or page_index >= len(pdf):
            return ""
        page = pdf.get_page(page_index)
        bitmap = page.render(scale=dpi / 72.0).to_pil()
        text = pytesseract.image_to_string(bitmap, lang=languages) or ""
        return text
    except Exception:
        return ""

