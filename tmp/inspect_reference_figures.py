from __future__ import annotations

import json
import re
import sys
import zipfile
from pathlib import Path

from docx import Document
from PIL import Image
from PIL import ImageDraw
import pdfplumber


def inspect_docx(path: Path, out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    doc = Document(path)
    paragraphs = [p.text.strip() for p in doc.paragraphs]
    hits = []
    pattern = re.compile(r"(多智能体|协作|框架|机制|流程|架构|图\s*\d+)")
    for index, text in enumerate(paragraphs):
        if text and pattern.search(text):
            hits.append({
                "index": index,
                "previous": paragraphs[index - 1] if index else "",
                "text": text,
                "next": paragraphs[index + 1] if index + 1 < len(paragraphs) else "",
            })
    (out_dir / "text_hits.json").write_text(
        json.dumps(hits, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    media_dir = out_dir / "media"
    media_dir.mkdir(exist_ok=True)
    media = []
    with zipfile.ZipFile(path) as archive:
        for name in archive.namelist():
            if not name.startswith("word/media/"):
                continue
            destination = media_dir / Path(name).name
            destination.write_bytes(archive.read(name))
            try:
                with Image.open(destination) as image:
                    width, height = image.size
                    media.append({"name": destination.name, "width": width, "height": height})
            except Exception:
                media.append({"name": destination.name, "width": None, "height": None})
    media.sort(key=lambda item: ((item["width"] or 0) * (item["height"] or 0)), reverse=True)
    (out_dir / "media.json").write_text(
        json.dumps(media, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"paragraphs={len(paragraphs)} hits={len(hits)} media={len(media)}")
    for hit in hits[:80]:
        print(f"[{hit['index']}] {hit['text']}")
    print("largest media:")
    for item in media[:30]:
        print(item)


def make_contact_sheet(input_dir: Path, pattern: str, output: Path, columns: int = 4) -> None:
    files = sorted(input_dir.glob(pattern))
    if not files:
        raise SystemExit(f"No files matched {pattern}")
    width, height = 360, 510
    label_height = 28
    rows = (len(files) + columns - 1) // columns
    sheet = Image.new("RGB", (columns * width, rows * (height + label_height)), "white")
    draw = ImageDraw.Draw(sheet)
    for index, file in enumerate(files):
        image = Image.open(file).convert("RGB")
        image.thumbnail((width - 12, height - 12))
        x = (index % columns) * width + (width - image.width) // 2
        y = (index // columns) * (height + label_height) + label_height
        sheet.paste(image, (x, y))
        draw.text(((index % columns) * width + 8, (index // columns) * (height + label_height) + 6), file.stem, fill="#172033")
    sheet.save(output)
    print(f"contact_sheet={output} items={len(files)} size={sheet.size}")


if __name__ == "__main__":
    if sys.argv[1] == "--contact":
        make_contact_sheet(Path(sys.argv[2]), sys.argv[3], Path(sys.argv[4]), int(sys.argv[5]))
    elif Path(sys.argv[1]).suffix.lower() == ".pdf":
        pdf_path = Path(sys.argv[1])
        output = Path(sys.argv[2])
        output.mkdir(parents=True, exist_ok=True)
        rows = []
        pattern = re.compile(r"(多智能体|协作|框架|机制|流程|架构|图\s*\d+)")
        with pdfplumber.open(pdf_path) as pdf:
            for page_number, page in enumerate(pdf.pages, start=1):
                page_text = page.extract_text() or ""
                rows.append({"page": page_number, "text": page_text})
                matched = [line for line in page_text.splitlines() if pattern.search(line)]
                if matched:
                    print(f"--- page {page_number} ---")
                    for line in matched[:30]:
                        print(line)
        (output / "pages.json").write_text(
            json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        print(f"pages={len(rows)}")
    else:
        inspect_docx(Path(sys.argv[1]), Path(sys.argv[2]))
