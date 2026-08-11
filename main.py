from __future__ import annotations

import os
import re
import time
import uuid
from pathlib import Path

import pytesseract
from fastapi import FastAPI, File, HTTPException, Query, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from fastapi.staticfiles import StaticFiles
from starlette.concurrency import run_in_threadpool

from .processor import convert_document

PROJECT_ROOT = Path(__file__).resolve().parents[2]
MAX_UPLOAD_MB = int(os.getenv("MAX_UPLOAD_MB", "75"))
MAX_UPLOAD_BYTES = MAX_UPLOAD_MB * 1024 * 1024
ALLOWED_EXTENSIONS = {".pdf", ".png", ".jpg", ".jpeg"}
VERSION = "5.0.0"

app = FastAPI(
    title="TYPO Real Document Engine",
    version=VERSION,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
)

cors_origins = [x.strip() for x in os.getenv("CORS_ORIGINS", "").split(",") if x.strip()]
if cors_origins:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=cors_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "OPTIONS"],
        allow_headers=["*"],
    )


def safe_download_name(filename: str) -> str:
    stem = Path(filename).stem or "document"
    stem = re.sub(r"[^\w\-.\u0600-\u06FF ]+", "_", stem, flags=re.UNICODE).strip(" ._")
    return f"{stem or 'document'}-TYPO-Real.docx"


def validate_options(ocr_mode: str, language: str, table_mode: str, ocr_quality: str) -> None:
    if ocr_mode not in {"auto", "always", "never"}:
        raise HTTPException(400, "ocr_mode نامعتبر است.")
    if language not in {"fas", "eng", "fas+eng"}:
        raise HTTPException(400, "language نامعتبر است.")
    if table_mode not in {"strict", "balanced", "off"}:
        raise HTTPException(400, "table_mode نامعتبر است.")
    if ocr_quality not in {"high", "balanced", "fast"}:
        raise HTTPException(400, "ocr_quality نامعتبر است.")


@app.get("/api/health")
def health() -> dict:
    try:
        languages = pytesseract.get_languages(config="")
    except Exception:
        languages = []
    return {
        "ok": True,
        "service": "TYPO Real",
        "version": VERSION,
        "ocr": "tesseract",
        "ocr_languages": {"fas": "fas" in languages, "eng": "eng" in languages},
        "max_upload_mb": MAX_UPLOAD_MB,
    }


@app.get("/api/capabilities")
def capabilities() -> dict:
    try:
        languages = pytesseract.get_languages(config="")
    except Exception:
        languages = []
    return {
        "input": ["pdf", "png", "jpg", "jpeg"],
        "output": ["docx"],
        "ocr_languages": sorted(set(languages).intersection({"fas", "eng"})),
        "tables": ["strict", "balanced", "off"],
        "ocr_modes": ["auto", "always", "never"],
        "ocr_quality": ["high", "balanced", "fast"],
    }


@app.post("/api/convert")
async def convert(
    file: UploadFile = File(...),
    ocr_mode: str = Query("auto"),
    language: str = Query("fas+eng"),
    table_mode: str = Query("balanced"),
    ocr_quality: str = Query("balanced"),
    preserve_style: bool = Query(True),
    smart_paragraphs: bool = Query(True),
    safe_tables: bool = Query(True),
):
    validate_options(ocr_mode, language, table_mode, ocr_quality)
    filename = file.filename or "document"
    suffix = Path(filename).suffix.lower()
    if suffix not in ALLOWED_EXTENSIONS:
        raise HTTPException(400, "فرمت پشتیبانی نمی‌شود. PDF، PNG و JPG/JPEG مجاز هستند.")

    request_id = uuid.uuid4().hex[:12]
    started = time.perf_counter()
    chunks: list[bytes] = []
    total = 0
    try:
        while True:
            chunk = await file.read(1024 * 1024)
            if not chunk:
                break
            total += len(chunk)
            if total > MAX_UPLOAD_BYTES:
                raise HTTPException(413, f"حجم فایل بیش از {MAX_UPLOAD_MB}MB است.")
            chunks.append(chunk)
    finally:
        await file.close()

    if not chunks:
        raise HTTPException(400, "فایل خالی است.")

    data = b"".join(chunks)
    try:
        docx_bytes, stats = await run_in_threadpool(
            convert_document,
            data,
            filename,
            ocr_mode,
            language,
            table_mode,
            ocr_quality,
            preserve_style,
            smart_paragraphs,
            safe_tables,
        )
    except RuntimeError as exc:
        raise HTTPException(503, str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc
    except Exception as exc:
        raise HTTPException(500, f"تبدیل فایل انجام نشد: {exc}") from exc

    elapsed_ms = round((time.perf_counter() - started) * 1000)
    headers = {
        "Content-Disposition": f'attachment; filename="{safe_download_name(filename)}"',
        "X-TYPO-Request-ID": request_id,
        "X-TYPO-Pages": str(stats["pages"]),
        "X-TYPO-OCR-Pages": str(stats["ocr_pages"]),
        "X-TYPO-Words": str(stats["words"]),
        "X-TYPO-Tables": str(stats["tables"]),
        "X-TYPO-Confidence": str(round(stats["confidence"])),
        "X-TYPO-Engine": f"TYPO-Real/{VERSION}",
        "X-TYPO-Processing-Ms": str(elapsed_ms),
    }
    return Response(
        content=docx_bytes,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers=headers,
    )


# One container serves both the web UI and API. API routes are registered first.
if (PROJECT_ROOT / "index.html").exists():
    app.mount("/", StaticFiles(directory=PROJECT_ROOT, html=True), name="frontend")
