from __future__ import annotations

import re
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, Preformatted, SimpleDocTemplate, Spacer


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "docs" / "api-documentation.md"
OUTPUT = ROOT / "docs" / "api-documentation.pdf"


def build_styles():
    styles = getSampleStyleSheet()
    styles.add(
        ParagraphStyle(
            name="DocTitle",
            parent=styles["Title"],
            alignment=TA_CENTER,
            fontSize=20,
            leading=24,
            spaceAfter=12,
        )
    )
    styles.add(
        ParagraphStyle(
            name="H1",
            parent=styles["Heading1"],
            fontSize=16,
            leading=20,
            textColor=colors.HexColor("#1f2937"),
            spaceBefore=10,
            spaceAfter=8,
        )
    )
    styles.add(
        ParagraphStyle(
            name="H2",
            parent=styles["Heading2"],
            fontSize=13,
            leading=16,
            textColor=colors.HexColor("#111827"),
            spaceBefore=8,
            spaceAfter=6,
        )
    )
    styles.add(
        ParagraphStyle(
            name="Body",
            parent=styles["BodyText"],
            fontSize=10,
            leading=14,
            spaceAfter=6,
        )
    )
    styles.add(
        ParagraphStyle(
            name="BulletDoc",
            parent=styles["BodyText"],
            fontSize=10,
            leading=14,
            leftIndent=12,
            firstLineIndent=-8,
            spaceAfter=4,
        )
    )
    styles.add(
        ParagraphStyle(
            name="CodeLabel",
            parent=styles["BodyText"],
            fontName="Helvetica-Bold",
            fontSize=10,
            textColor=colors.HexColor("#374151"),
            spaceBefore=4,
            spaceAfter=2,
        )
    )
    return styles


def flush_paragraph(buffer: list[str], story: list, styles) -> None:
    if not buffer:
        return
    text = " ".join(line.strip() for line in buffer).strip()
    if text:
        story.append(Paragraph(escape_inline(text), styles["Body"]))
    buffer.clear()


def escape_inline(text: str) -> str:
    text = (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )
    return re.sub(
        r"`([^`]+)`",
        lambda match: f"<font name='Courier'>{match.group(1)}</font>",
        text,
    )


def build_story(markdown: str):
    styles = build_styles()
    story = []
    paragraph_buffer: list[str] = []
    in_code = False
    code_lines: list[str] = []

    for raw_line in markdown.splitlines():
        line = raw_line.rstrip("\n")

        if line.startswith("```"):
            flush_paragraph(paragraph_buffer, story, styles)
            if in_code:
                story.append(Preformatted("\n".join(code_lines), styles["Code"]))
                story.append(Spacer(1, 4))
                code_lines.clear()
                in_code = False
            else:
                in_code = True
                story.append(Paragraph("Code example", styles["CodeLabel"]))
            continue

        if in_code:
            code_lines.append(line)
            continue

        if not line.strip():
            flush_paragraph(paragraph_buffer, story, styles)
            story.append(Spacer(1, 4))
            continue

        if line.startswith("# "):
            flush_paragraph(paragraph_buffer, story, styles)
            story.append(Paragraph(escape_inline(line[2:].strip()), styles["DocTitle"]))
            continue

        if line.startswith("## "):
            flush_paragraph(paragraph_buffer, story, styles)
            story.append(Paragraph(escape_inline(line[3:].strip()), styles["H1"]))
            continue

        if line.startswith("### "):
            flush_paragraph(paragraph_buffer, story, styles)
            story.append(Paragraph(escape_inline(line[4:].strip()), styles["H2"]))
            continue

        if line.startswith("- "):
            flush_paragraph(paragraph_buffer, story, styles)
            story.append(Paragraph(f"• {escape_inline(line[2:].strip())}", styles["BulletDoc"]))
            continue

        if line.startswith(("1. ", "2. ", "3. ", "4. ", "5. ")):
            flush_paragraph(paragraph_buffer, story, styles)
            story.append(Paragraph(escape_inline(line.strip()), styles["Body"]))
            continue

        paragraph_buffer.append(line)

    flush_paragraph(paragraph_buffer, story, styles)
    return story


def main() -> None:
    markdown = SOURCE.read_text(encoding="utf-8")
    doc = SimpleDocTemplate(
        str(OUTPUT),
        pagesize=A4,
        leftMargin=18 * mm,
        rightMargin=18 * mm,
        topMargin=16 * mm,
        bottomMargin=16 * mm,
        title="Fitness Planner API Documentation",
        author="Tom Chen",
    )
    doc.build(build_story(markdown))
    print(f"Wrote {OUTPUT}")


if __name__ == "__main__":
    main()
