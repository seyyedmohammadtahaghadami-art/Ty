# TYPO Real Professional v2 — Server Mode (No API)

این نسخه برای اجرای واقعی روی یک سرور Python/Docker آماده شده است.

## نکته
«بدون API» یعنی هیچ OpenAI/Gemini/سرویس هوش مصنوعی پولی یا API Key استفاده نمی‌شود.
سرور فقط موتور پردازش محلی خود پروژه را اجرا می‌کند:
- FastAPI
- PyMuPDF
- Tesseract OCR (فارسی + انگلیسی)
- python-docx
- Pillow

## اجرا با Docker

```bash
docker build -t typo-real .
docker run --rm -p 8000:8000 typo-real
```

سپس:
- `http://localhost:8000`
- سلامت سرور: `http://localhost:8000/api/health`
- مستندات: `http://localhost:8000/docs`

## اجرا بدون Docker

Python 3.12 پیشنهاد می‌شود:

```bash
pip install -r backend/requirements.txt
uvicorn backend.app.main:app --host 0.0.0.0 --port 8000
```

همچنین باید Tesseract و بسته زبان `fas` روی سیستم نصب باشند.

## دامنه typo.ir

فایل CNAME را می‌توان برای GitHub Pages نگه داشت، اما GitHub Pages خودش FastAPI را اجرا نمی‌کند.
برای حالت کامل باید Frontend روی Pages و Backend روی یک سرور Python/Docker باشد، یا هر دو در یک سرویس Docker اجرا شوند.

## API Key

هیچ API Key لازم نیست.
