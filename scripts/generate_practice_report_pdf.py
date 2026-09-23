#!/usr/bin/env python3
"""Generate a formal A4 PDF from the visual-servo practice report (Chinese)."""

from __future__ import annotations

import re
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import cm, mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    ListFlowable,
    ListItem,
    PageBreak,
    Paragraph,
    Preformatted,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

FONT_PATH = "/usr/share/fonts/truetype/wqy/wqy-microhei.ttc"
MD_PATH = Path("/workspace/docs/眼在手视觉伺服闭环练习报告.md")
OUTPUTS = [
    Path("/home/ubuntu/Desktop/眼在手视觉伺服闭环练习报告.pdf"),
    Path("/workspace/docs/眼在手视觉伺服闭环练习报告.pdf"),
    Path("/opt/cursor/artifacts/眼在手视觉伺服闭环练习报告.pdf"),
]


def register_font() -> str:
    pdfmetrics.registerFont(TTFont("WQY", FONT_PATH, subfontIndex=0))
    return "WQY"


def styles(font: str) -> dict[str, ParagraphStyle]:
    return {
        "cover_title": ParagraphStyle(
            "cover_title",
            fontName=font,
            fontSize=18,
            leading=28,
            alignment=TA_CENTER,
            spaceAfter=16,
            textColor=colors.HexColor("#1a1a1a"),
        ),
        "cover_sub": ParagraphStyle(
            "cover_sub",
            fontName=font,
            fontSize=12,
            leading=20,
            alignment=TA_CENTER,
            spaceAfter=8,
        ),
        "h1": ParagraphStyle(
            "h1",
            fontName=font,
            fontSize=14,
            leading=22,
            spaceBefore=16,
            spaceAfter=10,
            textColor=colors.HexColor("#1b3a4b"),
        ),
        "h2": ParagraphStyle(
            "h2",
            fontName=font,
            fontSize=12,
            leading=20,
            spaceBefore=12,
            spaceAfter=6,
            textColor=colors.HexColor("#245071"),
        ),
        "h3": ParagraphStyle(
            "h3",
            fontName=font,
            fontSize=11,
            leading=18,
            spaceBefore=10,
            spaceAfter=4,
            textColor=colors.HexColor("#2c3e50"),
        ),
        "body": ParagraphStyle(
            "body",
            fontName=font,
            fontSize=10,
            leading=17,
            alignment=TA_JUSTIFY,
            spaceAfter=6,
            firstLineIndent=22,
        ),
        "body_left": ParagraphStyle(
            "body_left",
            fontName=font,
            fontSize=10,
            leading=17,
            alignment=TA_LEFT,
            spaceAfter=6,
        ),
        "bullet": ParagraphStyle(
            "bullet",
            fontName=font,
            fontSize=10,
            leading=16,
            leftIndent=8,
            spaceAfter=3,
        ),
        "code": ParagraphStyle(
            "code",
            fontName=font,
            fontSize=8.5,
            leading=13,
            backColor=colors.HexColor("#f4f6f8"),
            borderPadding=6,
            spaceBefore=4,
            spaceAfter=8,
        ),
        "caption": ParagraphStyle(
            "caption",
            fontName=font,
            fontSize=9,
            leading=14,
            alignment=TA_CENTER,
            textColor=colors.HexColor("#555555"),
            spaceAfter=8,
        ),
        "footer": ParagraphStyle(
            "footer",
            fontName=font,
            fontSize=8,
            alignment=TA_CENTER,
            textColor=colors.HexColor("#666666"),
        ),
    }


def escape(text: str) -> str:
    text = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    text = re.sub(r"`([^`]+)`", r"<font face='Courier' size='8.5'>\1</font>", text)
    text = re.sub(r"\*\*([^*]+)\*\*", r"<b>\1</b>", text)
    return text


def parse_table(lines: list[str], font: str) -> Table:
    rows = []
    for line in lines:
        cols = [c.strip() for c in line.strip().strip("|").split("|")]
        if all(re.match(r"^:?-+:?$", c) for c in cols):
            continue
        rows.append([Paragraph(escape(c), ParagraphStyle("td", fontName=font, fontSize=8, leading=12)) for c in cols])
    col_n = max(len(r) for r in rows)
    for r in rows:
        while len(r) < col_n:
            r.append(Paragraph("", ParagraphStyle("td", fontName=font, fontSize=8)))
    width = 17.0 * cm
    col_w = [width / col_n] * col_n
    table = Table(rows, colWidths=col_w, repeatRows=1)
    table.setStyle(
        TableStyle(
            [
                ("FONTNAME", (0, 0), (-1, -1), font),
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1b3a4b")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("BACKGROUND", (0, 1), (-1, -1), colors.HexColor("#f7f9fb")),
                ("GRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#b0bec5")),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 4),
                ("RIGHTPADDING", (0, 0), (-1, -1), 4),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ]
        )
    )
    return table


def add_header_footer(canvas, doc):
    canvas.saveState()
    canvas.setStrokeColor(colors.HexColor("#1b3a4b"))
    canvas.setLineWidth(0.6)
    canvas.line(2 * cm, A4[1] - 1.4 * cm, A4[0] - 2 * cm, A4[1] - 1.4 * cm)
    canvas.setFont("WQY", 8)
    canvas.setFillColor(colors.HexColor("#555555"))
    canvas.drawString(2 * cm, A4[1] - 1.2 * cm, "眼在手上机械臂视觉伺服闭环控制练习报告")
    canvas.drawRightString(A4[0] - 2 * cm, A4[1] - 1.2 * cm, "科研预备 · 非正式投稿")
    canvas.line(2 * cm, 1.5 * cm, A4[0] - 2 * cm, 1.5 * cm)
    canvas.drawCentredString(A4[0] / 2, 1.1 * cm, f"— {doc.page} —")
    canvas.restoreState()


def build_story(md_text: str, s: dict[str, ParagraphStyle], font: str):
    story = []
    lines = md_text.splitlines()
    i = 0
    cover_done = False
    in_code = False
    code_buf: list[str] = []
    table_buf: list[str] = []

    def flush_table():
        nonlocal table_buf
        if table_buf:
            story.append(Spacer(1, 4))
            story.append(parse_table(table_buf, font))
            story.append(Spacer(1, 8))
            table_buf = []

    while i < len(lines):
        raw = lines[i]
        line = raw.rstrip()

        if line.startswith("```"):
            flush_table()
            if not in_code:
                in_code = True
                code_buf = []
            else:
                story.append(Preformatted("\n".join(code_buf) or " ", s["code"]))
                in_code = False
            i += 1
            continue
        if in_code:
            code_buf.append(raw)
            i += 1
            continue

        if line.startswith("|"):
            table_buf.append(line)
            i += 1
            continue
        flush_table()

        if not line:
            i += 1
            continue

        if line.startswith("# "):
            title = line[2:].strip()
            if not cover_done:
                story.append(Spacer(1, 3.2 * cm))
                story.append(Paragraph("本科科研预备练习指导书", s["cover_sub"]))
                story.append(Spacer(1, 8))
                story.append(Paragraph(escape(title), s["cover_title"]))
                story.append(Spacer(1, 12))
                story.append(
                    Paragraph(
                        "视觉提供误差，控制完成闭环。练习覆盖静态对准、开环对照，以及运动目标与图像延迟下的三种控制律。",
                        s["cover_sub"],
                    )
                )
                story.append(Spacer(1, 24))
                meta = [
                    "文件性质：科研预备练习指导书（非正式投稿论文）",
                    "适用对象：控制专业本科生；已进入课题组、尚未承担正式课题",
                    "工作空间：以本机已有机械臂与夹爪功能包为基础",
                    "方向：视觉—控制闭环，偏重控制（稳、准、快）",
                ]
                for m in meta:
                    story.append(Paragraph(escape(m), s["cover_sub"]))
                story.append(PageBreak())
                cover_done = True
            else:
                story.append(Paragraph(escape(title), s["h1"]))
        elif line.startswith("## "):
            story.append(Paragraph(escape(line[3:].strip()), s["h1"]))
        elif line.startswith("### "):
            story.append(Paragraph(escape(line[4:].strip()), s["h2"]))
        elif line.startswith("---"):
            i += 1
            continue
        elif line.startswith("- "):
            items = []
            while i < len(lines) and lines[i].rstrip().startswith("- "):
                items.append(ListItem(Paragraph(escape(lines[i].rstrip()[2:]), s["bullet"]), leftIndent=12))
                i += 1
            story.append(ListFlowable(items, bulletType="bullet", start="•", leftIndent=18))
            story.append(Spacer(1, 4))
            continue
        elif re.match(r"^\d+\.\s", line):
            items = []
            while i < len(lines) and re.match(r"^\d+\.\s", lines[i].rstrip()):
                text = re.sub(r"^\d+\.\s", "", lines[i].rstrip())
                items.append(ListItem(Paragraph(escape(text), s["bullet"]), leftIndent=12))
                i += 1
            story.append(ListFlowable(items, bulletType="1", leftIndent=18))
            story.append(Spacer(1, 4))
            continue
        else:
            style = s["body_left"] if line.startswith("**") else s["body"]
            story.append(Paragraph(escape(line), style))
        i += 1

    flush_table()
    return story


def main() -> None:
    font = register_font()
    s = styles(font)
    md = MD_PATH.read_text(encoding="utf-8")
    # Skip duplicate YAML-like header lines already in markdown after title
    primary = OUTPUTS[0]
    primary.parent.mkdir(parents=True, exist_ok=True)
    doc = SimpleDocTemplate(
        str(primary),
        pagesize=A4,
        leftMargin=2 * cm,
        rightMargin=2 * cm,
        topMargin=2 * cm,
        bottomMargin=2 * cm,
        title="眼在手上机械臂视觉伺服闭环控制练习报告",
        author="课题组科研预备练习",
    )
    story = build_story(md, s, font)
    doc.build(story, onFirstPage=add_header_footer, onLaterPages=add_header_footer)

    data = primary.read_bytes()
    for dest in OUTPUTS[1:]:
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(data)
        print(f"wrote {dest}")
    print(f"wrote {primary} ({len(data)} bytes)")


if __name__ == "__main__":
    main()
