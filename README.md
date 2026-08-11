# TYPO Real v5 — Unified Server Architecture

موتور واقعی بازسازی PDF/PNG/JPG به DOCX با یک معماری واحد:

**Browser UI → FastAPI → PyMuPDF/Tesseract → python-docx → DOCX**

## قابلیت‌ها

- PDF متنی: استخراج مستقیم متن و مختصات قبل از OCR
- PDF اسکن‌شده و تصویر: OCR واقعی با Tesseract
- زبان‌های فارسی و English
- حالت‌های OCR: خودکار، اجباری، خاموش
- کیفیت OCR: Fast / Balanced / High
- بازسازی RTL/LTR
- حفظ تقریبی فونت، اندازه، Bold و Italic در PDFهای متنی
- بازسازی فاصله و پاراگراف
- تشخیص محافظه‌کارانه جدول
- حفظ اندازه صفحه PDF در Word
- خروجی واقعی و قابل ویرایش DOCX
- API واقعی `/api/convert`
- `/api/health` و `/api/capabilities`
- محدودیت حجم 75MB به‌صورت پیش‌فرض
- Frontend و Backend در **یک سرویس واحد**
- بدون CDN و بدون API Key خارجی
- Docker + Docker Compose
- Caddy برای HTTPS خودکار
- CI برای compile، OCR و تست API

## اجرای production

روی سروری که Docker و Docker Compose دارد:

```bash
docker compose up -d --build
```

سپس رکورد DNS دامنه را به IP عمومی سرور وصل کنید. Caddy گواهی HTTPS را برای دامنه موجود در `Caddyfile` دریافت و تمدید می‌کند.

## تست محلی Backend

```bash
python -m compileall -q backend
python -m pytest -q backend/tests
```

## معماری فایل‌ها

- `index.html` — رابط کاربری
- `js/app.js` — کلاینت API و UI
- `js/config.js` — آدرس Backend
- `backend/app/main.py` — API و سرو فایل‌های Frontend
- `backend/app/processor.py` — موتور استخراج/OCR/بازسازی DOCX
- `Dockerfile` — تنها ایمیج Backend + Frontend
- `docker-compose.yml` — سرویس برنامه + Caddy
- `Caddyfile` — HTTPS و reverse proxy

## نکته مهم درباره دقت

بازسازی دقیق تمام PDFهای پیچیده، به‌خصوص PDFهایی با طراحی گرافیکی، ستون‌های پیچیده یا جدول‌های غیر استاندارد، بدون داشتن ساختار اصلی سند قابل تضمین نیست. این نسخه فایل جعلی تولید نمی‌کند؛ واقعاً PDF/تصویر را پردازش و DOCX قابل ویرایش می‌سازد.
