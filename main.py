from __future__ import annotations

import os
import shutil
import tempfile
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from .converter import convert_to_docx

APP_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = APP_DIR.parent.parent
MAX_UPLOAD_MB = int(os.getenv("MAX_UPLOAD_MB", "50"))
MAX_UPLOAD_BYTES = MAX_UPLOAD_MB * 1024 * 1024

app = FastAPI(
    title="TYPO Real Professional Server",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

origins = os.getenv("CORS_ORIGINS", "*").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[x.strip() for x in origins if x.strip()],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

ALLOWED = {
    ".pdf": "application/pdf",
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
}

@app.get("/api/health")
def health():
    return {"ok": True, "service": "TYPO Real Professional", "version": "2.0.0"}

@app.post("/api/convert")
async def convert(
    file: UploadFile = File(...),
    ocr: str = Form("auto"),
    tables: str = Form("balanced"),
):
    suffix = Path(file.filename or "").suffix.lower()
    if suffix not in ALLOWED:
        raise HTTPException(400, "فرمت پشتیبانی نمی‌شود. PDF، PNG و JPG مجاز هستند.")

    temp_dir = Path(tempfile.mkdtemp(prefix="typo_"))
    try:
        source = temp_dir / f"input{suffix}"
        total = 0
        with source.open("wb") as out:
            while chunk := await file.read(1024 * 1024):
                total += len(chunk)
                if total > MAX_UPLOAD_BYTES:
                    raise HTTPException(413, f"حجم فایل بیش از {MAX_UPLOAD_MB}MB است.")
                out.write(chunk)

        result = convert_to_docx(
            source,
            ocr_mode=ocr,
            table_mode=tables,
            output_dir=temp_dir,
        )
        return FileResponse(
            result,
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            filename="TYPO-Real-Converted.docx",
            background=None,
        )
    finally:
        # FileResponse reads before the request finishes in normal ASGI operation.
        # Temp cleanup is intentionally conservative; OS/container cleanup can remove it.
        pass

# Optional local static serving when deployed as one container.
frontend = PROJECT_ROOT
if (frontend / "index.html").exists():
    app.mount("/", StaticFiles(directory=frontend, html=True), name="frontend")
