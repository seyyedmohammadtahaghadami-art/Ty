import express from "express";
import cors from "cors";
import helmet from "helmet";
import multer from "multer";
import fs from "node:fs/promises";
import path from "node:path";
import os from "node:os";
import { fileURLToPath } from "node:url";
import { execFile } from "node:child_process";
import { promisify } from "node:util";

const exec = promisify(execFile);
const __dirname = path.dirname(fileURLToPath(import.meta.url));
const PORT = Number(process.env.PORT || 3000);
const MAX_MB = Number(process.env.MAX_FILE_MB || 50);
const upload = multer({
  dest: path.join(os.tmpdir(), "typo-real"),
  limits: { fileSize: MAX_MB * 1024 * 1024 }
});

const app = express();
app.use(helmet({ crossOriginResourcePolicy: false }));
app.use(cors());
app.use(express.json({ limit: "2mb" }));
app.use(express.static(path.join(__dirname, "../public")));

async function cleanup(file) {
  if (file?.path) await fs.rm(file.path, { force: true }).catch(() => {});
}

async function commandExists(cmd) {
  try { await exec(cmd, ["--version"]); return true; } catch { return false; }
}

app.get("/api/health", async (_req, res) => {
  const [python, tesseract, pdftotext, libreoffice] = await Promise.all([
    commandExists(process.platform === "win32" ? "python" : "python3"),
    commandExists("tesseract"),
    commandExists("pdftotext"),
    commandExists("libreoffice")
  ]);
  res.json({
    ok: true,
    service: "TYPO Real Server",
    version: "1.0.0",
    engines: { python, tesseract, pdftotext, libreoffice }
  });
});

/*
  Real server-side OCR endpoint.
  It intentionally uses locally installed Tesseract instead of pretending
  that browser OCR is server OCR. The server returns a TXT result.
  For PDF files, pdftotext is attempted first; if that produces too little
  text, Tesseract is used on rendered pages when pdftoppm is available.
*/
app.post("/api/ocr", upload.single("file"), async (req, res) => {
  const file = req.file;
  if (!file) return res.status(400).json({ error: "No file uploaded" });

  const lang = String(req.body.lang || "fas+eng");
  const ext = path.extname(file.originalname).toLowerCase();
  const work = `${file.path}-work`;
  await fs.mkdir(work, { recursive: true });

  try {
    let text = "";
    let method = "";

    if (ext === ".pdf") {
      const txtPath = path.join(work, "native.txt");
      try {
        await exec("pdftotext", ["-layout", file.path, txtPath]);
        text = await fs.readFile(txtPath, "utf8").catch(() => "");
      } catch {}

      if (text.trim().length >= 30) {
        method = "pdftotext";
      } else {
        const ppm = await commandExists("pdftoppm");
        const tess = await commandExists("tesseract");
        if (!ppm || !tess) {
          throw new Error("برای OCR اسکن‌شده PDF، pdftoppm و tesseract باید روی سرور نصب باشند.");
        }

        const prefix = path.join(work, "page");
        await exec("pdftoppm", ["-r", "220", "-png", file.path, prefix]);
        const pages = (await fs.readdir(work))
          .filter(x => /^page-\d+\.png$/i.test(x))
          .sort((a,b) => {
            const na = Number(a.match(/\d+/)[0]), nb = Number(b.match(/\d+/)[0]);
            return na - nb;
          });

        const chunks = [];
        for (const p of pages) {
          const img = path.join(work, p);
          const outBase = path.join(work, p.replace(/\.png$/i, ""));
          await exec("tesseract", [img, outBase, "-l", lang, "--psm", "3"]);
          chunks.push(await fs.readFile(`${outBase}.txt`, "utf8").catch(() => ""));
        }
        text = chunks.join("\n\n");
        method = "tesseract";
      }
    } else {
      if (!(await commandExists("tesseract"))) {
        throw new Error("Tesseract روی سرور نصب نیست.");
      }
      const outBase = path.join(work, "image");
      await exec("tesseract", [file.path, outBase, "-l", lang, "--psm", "3"]);
      text = await fs.readFile(`${outBase}.txt`, "utf8").catch(() => "");
      method = "tesseract";
    }

    res.json({
      ok: true,
      filename: file.originalname,
      method,
      language: lang,
      text: text.trim()
    });
  } catch (err) {
    res.status(500).json({ error: err?.message || String(err) });
  } finally {
    await cleanup(file);
    await fs.rm(work, { recursive: true, force: true }).catch(() => {});
  }
});

app.get("*", (_req, res) => {
  res.sendFile(path.join(__dirname, "../public/index.html"));
});

app.listen(PORT, () => {
  console.log(`TYPO Real Server listening on http://localhost:${PORT}`);
});
