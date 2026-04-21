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
SOURCE = ROOT / "docs" / "technical-report.md"
OUTPUT = ROOT / "docs" / "technical-report.pdf"


def build_styles():
    styles = getSampleStyleSheet()
    styles.add(
        ParagraphStyle(
            name="DocTitle",
            parent=styles["Title"],
            alignment=TA_CENTER,
            fontSize=19,
            leading=22,
            spaceAfter=10,
        )
    )
    styles.add(
        ParagraphStyle(
            name="H1",
            parent=styles["Heading1"],
            fontSize=14,
            leading=18,
            textColor=colors.HexColor("#1f2937"),
            spaceBefore=8,
            spaceAfter=6,
        )
    )
    styles.add(
        ParagraphStyle(
            name="Body",
            parent=styles["BodyText"],
            fontSize=9,
            leading=11,
            spaceAfter=4,
        )
    )
    styles.add(
        ParagraphStyle(
            name="BulletDoc",
            parent=styles["BodyText"],
            fontSize=9,
            leading=11,
            leftIndent=10,
            firstLineIndent=-7,
            spaceAfter=3,
        )
    )
    styles.add(
        ParagraphStyle(
            name="CodeLabel",
            parent=styles["BodyText"],
            fontName="Helvetica-Bold",
            fontSize=9,
            textColor=colors.HexColor("#374151"),
            spaceBefore=3,
            spaceAfter=2,
        )
    )
    return styles


def escape_inline(text: str) -> str:
    text = (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )
    text = re.sub(
        r"\[([^\]]+)\]\(([^)]+)\)",
        lambda match: f"<link href='{match.group(2)}' color='blue'>{match.group(1)}</link>",
        text,
    )
    return re.sub(
        r"`([^`]+)`",
        lambda match: f"<font name='Courier'>{match.group(1)}</font>",
        text,
    )


def flush_paragraph(buffer: list[str], story: list, styles) -> None:
    if not buffer:
        return
    text = " ".join(line.strip() for line in buffer).strip()
    if text:
        story.append(Paragraph(escape_inline(text), styles["Body"]))
    buffer.clear()


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
                story.append(Spacer(1, 3))
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
            story.append(Spacer(1, 3))
            continue

        if line.startswith("# "):
            flush_paragraph(paragraph_buffer, story, styles)
            story.append(Paragraph(escape_inline(line[2:].strip()), styles["DocTitle"]))
            continue

        if line.startswith("## "):
            flush_paragraph(paragraph_buffer, story, styles)
            story.append(Paragraph(escape_inline(line[3:].strip()), styles["H1"]))
            continue

        if line.startswith("- "):
            flush_paragraph(paragraph_buffer, story, styles)
            story.append(Paragraph(f"• {escape_inline(line[2:].strip())}", styles["BulletDoc"]))
            continue

        if re.match(r"^\d+\.\s", line):
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
        leftMargin=16 * mm,
        rightMargin=16 * mm,
        topMargin=14 * mm,
        bottomMargin=14 * mm,
        title="Technical Report: Constraint-Aware Fitness Planning API",
        author="Tom Chen",
    )
    doc.build(build_story(markdown))
    print(f"Wrote {OUTPUT}")


if __name__ == "__main__":
    main()
