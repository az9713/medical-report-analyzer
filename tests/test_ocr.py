import pdfplumber
import sys
import pathlib

sys.path.append(str(pathlib.Path(__file__).resolve().parents[1] / "src"))
import health_report.extract.pdf_parser as pdf_parser

def make_fake_pdf(texts):
    class FakePage:
        def __init__(self, text):
            self._text = text
        def extract_text(self):
            return self._text
        def extract_tables(self):
            return []
    class FakePDF:
        def __init__(self, texts):
            self.pages = [FakePage(t) for t in texts]
        def __enter__(self):
            return self
        def __exit__(self, exc_type, exc, tb):
            pass
    def opener(_):
        return FakePDF(texts)
    return opener

def test_ocr_auto_triggers_when_no_text(monkeypatch, tmp_path):
    monkeypatch.setattr(pdfplumber, "open", make_fake_pdf([""]))
    called = {}
    def fake_ocr_page(path, idx, **kwargs):
        called["called"] = True
        return "GLUCOSE 81 Reference Range: 65-99 mg/dL"
    monkeypatch.setattr(pdf_parser, "ocr_page", fake_ocr_page)
    dummy = tmp_path / "file.pdf"
    dummy.write_bytes(b"%")
    rows = pdf_parser.extract_from_pdf(dummy, ocr={"enabled": True, "dpi": 150, "languages": "eng"})
    assert called.get("called")
    assert any(r["test_name"] == "GLUCOSE" for r in rows)

def test_ocr_always_runs_even_with_text(monkeypatch, tmp_path):
    monkeypatch.setattr(pdfplumber, "open", make_fake_pdf(["CHOLESTEROL 200 Reference Range: 0-199 mg/dL"]))
    calls = []
    def fake_ocr_page(path, idx, **kwargs):
        calls.append(1)
        return "GLUCOSE 81 Reference Range: 65-99 mg/dL"
    monkeypatch.setattr(pdf_parser, "ocr_page", fake_ocr_page)
    dummy = tmp_path / "file.pdf"
    dummy.write_bytes(b"%")
    rows = pdf_parser.extract_from_pdf(dummy, ocr={"enabled": True, "mode": "always"})
    # OCR called even though page had text, yielding two measurements
    assert calls
    names = {r["test_name"] for r in rows}
    assert {"CHOLESTEROL", "GLUCOSE"} <= names

def test_ocr_skipped_when_disabled(monkeypatch, tmp_path):
    monkeypatch.setattr(pdfplumber, "open", make_fake_pdf([""]))
    called = {}
    def fake_ocr_page(path, idx, **kwargs):
        called["called"] = True
        return ""  # would return text if invoked
    monkeypatch.setattr(pdf_parser, "ocr_page", fake_ocr_page)
    dummy = tmp_path / "file.pdf"
    dummy.write_bytes(b"%")
    rows = pdf_parser.extract_from_pdf(dummy, ocr={"enabled": False})
    assert not called
    assert rows == []
