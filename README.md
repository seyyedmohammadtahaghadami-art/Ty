# TYPO Real — GitHub Server

سرور جداگانه برای نسخه مرورگری TYPO Real.

## معماری

- `public/index.html` — رابط HTML
- `server/server.js` — API و پردازش سروری
- PDF متنی: ابتدا `pdftotext -layout`
- PDF اسکن‌شده: `pdftoppm` + Tesseract
- تصویر: Tesseract
- `GET /api/health` — بررسی موتورهای نصب‌شده
- `POST /api/ocr` — آپلود فایل و دریافت متن OCR

## اجرای مستقیم روی Ubuntu/Debian

```bash
sudo apt update
sudo apt install -y nodejs npm tesseract-ocr tesseract-ocr-fas tesseract-ocr-ara tesseract-ocr-eng poppler-utils
npm install
npm start
```

سپس:
`http://SERVER-IP:3000`

## اجرای Docker

```bash
docker build -t typo-real .
docker run --rm -p 3000:3000 typo-real
```

## API

`POST /api/ocr`

Form-data:
- `file`: PDF یا تصویر
- `lang`: `fas+eng` یا `ara+fas+eng` یا `eng`

نمونه پاسخ:

```json
{
  "ok": true,
  "filename": "document.pdf",
  "method": "pdftotext",
  "language": "fas+eng",
  "text": "..."
}
```

## نکته

این backend یک موتور واقعی server-side است، اما بازسازی کامل DOCX با حفظ دقیق مختصات، جدول، فونت و عناصر گرافیکی هنوز یک مرحله جداگانه است. این repository پایه‌ی درست Frontend → Backend → PDF/OCR را فراهم می‌کند.
