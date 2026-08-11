import io
from fastapi.testclient import TestClient
from docx import Document
import fitz
from backend.app.main import app

client = TestClient(app)

def make_pdf():
    pdf = fitz.open()
    p = pdf.new_page()
    p.insert_text((72, 100), 'TYPO Real test document')
    return pdf.tobytes()

def test_health():
    r = client.get('/health')
    assert r.status_code == 200
    assert r.json()['ok'] is True
    assert r.json()['version'] == '2.0.0'

def test_convert_pdf_to_docx():
    r = client.post('/convert?ocr_mode=never&table_mode=off', files={'file': ('test.pdf', make_pdf(), 'application/pdf')})
    assert r.status_code == 200, r.text
    assert r.headers['content-type'].startswith('application/vnd.openxmlformats-officedocument.wordprocessingml.document')
    doc = Document(io.BytesIO(r.content))
    text = '\n'.join(p.text for p in doc.paragraphs)
    assert 'TYPO Real test document' in text

def test_reject_type():
    r = client.post('/convert', files={'file': ('x.txt', b'hello', 'text/plain')})
    assert r.status_code == 415
