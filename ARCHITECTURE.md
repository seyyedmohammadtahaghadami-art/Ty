# TYPO Real v5 Architecture

## Single deployment path

```text
Browser
  │
  │ HTTPS / same origin
  ▼
Caddy
  │
  │ reverse_proxy
  ▼
FastAPI (`backend/app/main.py`)
  │
  ├── file validation / limits
  ├── `/api/health`
  ├── `/api/capabilities`
  └── `/api/convert`
          │
          ▼
   `backend/app/processor.py`
          │
          ├── PyMuPDF — PDF parsing / coordinates
          ├── Tesseract — OCR for scanned content
          └── python-docx — OOXML DOCX generation
                    │
                    ▼
                 DOCX
```

## Important design choices

- Frontend and API are served by the **same FastAPI process**, so normal deployment has no cross-origin dependency.
- CORS is disabled unless `CORS_ORIGINS` is explicitly configured.
- Heavy OCR/DOCX work is moved to a threadpool so the FastAPI event loop is not blocked by the synchronous OCR libraries.
- Conversion returns DOCX bytes directly; there is no temporary output-file race with `FileResponse`.
- Only one conversion engine exists: `processor.py`. There is no duplicate legacy converter or second Dockerfile.
- Service-worker caching explicitly excludes `/api/*`, preventing stale health/capability responses.
- Docker installs the Persian and English Tesseract language packs as part of the image build.

## Supported input

- PDF
- PNG
- JPG/JPEG

## Output

- DOCX
