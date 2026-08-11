# Architecture

Frontend: GitHub Pages + PWA. PDF.js extracts text and coordinates first; Tesseract.js is a fallback for scanned pages/images; layout code groups words into lines and paragraphs; conservative table detection is used to avoid false tables; the `docx` UMD library produces an actual OOXML DOCX.

Backend: FastAPI + PyMuPDF + Tesseract + python-docx. It is included as a deployable server component, but GitHub Pages cannot execute it.
