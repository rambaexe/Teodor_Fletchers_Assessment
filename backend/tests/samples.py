"""Sample PDF / Word files built on the fly: no binary fixtures in the repo."""

import io

import docx
from PIL import Image
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas

PDF_TEXT = "This page has a real text layer with plenty of characters."


def _png() -> io.BytesIO:
    buf = io.BytesIO()
    Image.new("RGB", (200, 100), "white").save(buf, format="PNG")
    buf.seek(0)
    return buf


def make_pdf(pages: list[str], title: str | None = None) -> bytes:
    """pages: "text" = digital page, "image" = scanned page (image only), "blank"."""
    buf = io.BytesIO()
    c = canvas.Canvas(buf)
    if title:
        c.setTitle(title)
        c.setAuthor("Jane Doe")
    for kind in pages:
        if kind == "text":
            c.drawString(72, 720, PDF_TEXT)
        elif kind == "image":
            c.drawImage(ImageReader(_png()), 72, 600)
        c.showPage()
    c.save()
    return buf.getvalue()


def make_docx(content: bool = True, image: bool = False, title: str | None = None) -> bytes:
    d = docx.Document()
    if title:
        d.core_properties.title = title
        d.core_properties.author = "Jane Doe"
    if content:
        d.add_heading("Summary", level=1)
        d.add_paragraph("Revenue grew this quarter.")
        d.add_paragraph("First point", style="List Bullet")
        table = d.add_table(rows=2, cols=2)
        table.cell(0, 0).text, table.cell(0, 1).text = "Region", "Revenue"
        table.cell(1, 0).text, table.cell(1, 1).text = "EU", "1.2m"
    if image:
        d.add_picture(_png())
    buf = io.BytesIO()
    d.save(buf)
    return buf.getvalue()
