import io
import fitz
from docx import Document
from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)

def make_pdf():
    pdf = fitz.open()
    p = pdf.new_page()
    p.insert_text((72, 100), 'TYPO Real test document')
    return pdf.tobytes()

def test_convert_pdf_to_docx():
    r = client.post('/api/convert?ocr_mode=never&table_mode=off&language=eng', files={'file': ('test.pdf', make_pdf(), 'application/pdf')})
    assert r.status_code == 200, r.text
    doc = Document(io.BytesIO(r.content))
    text = '\n'.join(p.text for p in doc.paragraphs)
    assert 'TYPO Real test document' in text
