"""Render a PDF report to PNG pages for visual quality control."""

from __future__ import annotations

import argparse
from pathlib import Path

from PIL import Image, ImageDraw
import pypdfium2 as pdfium


def render_pages(pdf_path: Path, output_dir: Path, scale: float = 1.5) -> list[Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    pdf = pdfium.PdfDocument(str(pdf_path))
    paths: list[Path] = []
    for index in range(len(pdf)):
        page = pdf[index]
        bitmap = page.render(scale=scale)
        image = bitmap.to_pil()
        path = output_dir / f"page-{index + 1:02d}.png"
        image.save(path)
        paths.append(path)
    return paths


def make_contact_sheet(page_paths: list[Path], output_path: Path, thumb_width: int = 360) -> None:
    thumbs = []
    for path in page_paths:
        image = Image.open(path).convert("RGB")
        ratio = thumb_width / image.width
        thumb = image.resize((thumb_width, int(image.height * ratio)))
        thumbs.append((path.stem, thumb))

    cols = 3
    label_h = 28
    pad = 18
    rows = (len(thumbs) + cols - 1) // cols
    cell_h = max(thumb.height for _, thumb in thumbs) + label_h + pad
    width = cols * (thumb_width + pad) + pad
    height = rows * cell_h + pad
    sheet = Image.new("RGB", (width, height), "white")
    draw = ImageDraw.Draw(sheet)

    for idx, (label, thumb) in enumerate(thumbs):
        row = idx // cols
        col = idx % cols
        x = pad + col * (thumb_width + pad)
        y = pad + row * cell_h
        sheet.paste(thumb, (x, y + label_h))
        draw.text((x, y), label, fill=(20, 20, 20))
        draw.rectangle((x, y + label_h, x + thumb.width, y + label_h + thumb.height), outline=(180, 180, 180))

    sheet.save(output_path)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("pdf")
    parser.add_argument("--output-dir", default="report/rendered_pdf_pages")
    parser.add_argument("--scale", type=float, default=1.5)
    args = parser.parse_args()

    pdf_path = Path(args.pdf)
    output_dir = Path(args.output_dir)
    pages = render_pages(pdf_path, output_dir, args.scale)
    make_contact_sheet(pages, output_dir / "contact_sheet.png")
    print(f"Rendered {len(pages)} pages to {output_dir}")


if __name__ == "__main__":
    main()
