#!/usr/bin/env python3
"""Build the current Noetic handbook PDF (Module S + steps A–H) with WeasyPrint."""

from __future__ import annotations

import html
import re
import shutil
from pathlib import Path

from weasyprint import HTML

ROOT = Path("/workspace")
START_ARM = ROOT / "START_ARM.md"
GUIDE = ROOT / "implementation_guide.md"
HTML_OUT = ROOT / "docs" / "handbook_noetic.html"

OUTPUTS = [
    ROOT / "implementation_guide.pdf",
    ROOT / "实施手册.pdf",
    ROOT / "眼在手视觉伺服实施文档.pdf",
    ROOT / "docs" / "眼在手视觉伺服实施文档.pdf",
    ROOT / "docs" / "眼在手视觉伺服闭环实施手册.pdf",
    Path("/opt/cursor/artifacts/implementation_guide.pdf"),
    Path("/opt/cursor/artifacts/眼在手视觉伺服实施文档.pdf"),
]


CSS = """
@page { size: A4; margin: 2.0cm 1.8cm 2.1cm 1.8cm;
  @top-center { content: "眼在手视觉伺服闭环实施手册 · ROS 1 Noetic / 实验室 robot_gripper";
                font-family: "WenQuanYi Micro Hei"; font-size: 8.5pt; color: #555; }
  @bottom-center { content: counter(page); font-family: "WenQuanYi Micro Hei"; font-size: 9pt; color: #555; }
}
html { font-size: 10.5pt; }
body {
  font-family: "WenQuanYi Micro Hei", "Droid Sans Fallback", sans-serif;
  color: #222; line-height: 1.75; text-align: justify;
}
h1 { font-size: 18pt; text-align: center; line-height: 1.45; margin: 0 0 14pt 0; }
h2 { font-size: 14pt; color: #1b3a4b; page-break-before: always; margin-top: 0;
     border-bottom: 1.4px solid #1b3a4b; padding-bottom: 5pt; }
h2.first { page-break-before: avoid; }
h3 { font-size: 12pt; color: #245071; margin-top: 13pt; }
h4 { font-size: 11pt; color: #333; margin-top: 10pt; }
p { margin: 0 0 7pt 0; }
.cover { text-align: center; margin-top: 2.1cm; }
.cover p { text-align: center; }
.meta { margin-top: 22pt; color: #333; }
.box { background: #f4f7fa; border-left: 4px solid #1b3a4b; padding: 7pt 9pt; margin: 9pt 0; }
.warn { background: #fff6e8; border-left: 4px solid #c47b12; padding: 7pt 9pt; margin: 9pt 0; }
.ok { background: #eef7ef; border-left: 4px solid #2e7d32; padding: 7pt 9pt; margin: 9pt 0; }
table { width: 100%; border-collapse: collapse; margin: 8pt 0 12pt 0; font-size: 9pt; }
th { background: #1b3a4b; color: #fff; padding: 4pt 5pt; text-align: left; }
td { border: 0.4pt solid #b0bec5; padding: 4pt 5pt; vertical-align: top; }
tr:nth-child(even) td { background: #f7f9fb; }
code, pre { font-family: "WenQuanYi Micro Hei", monospace; }
pre { background: #f4f6f8; padding: 7pt 9pt; font-size: 8.6pt; line-height: 1.5;
      white-space: pre-wrap; page-break-inside: avoid; }
ol, ul { margin: 5pt 0 9pt 0; padding-left: 1.3em; }
li { margin-bottom: 3pt; }
.small { font-size: 9pt; color: #555; }
"""


def inline(text: str) -> str:
    text = html.escape(text)
    text = re.sub(r"`([^`]+)`", r"<code>\1</code>", text)
    text = re.sub(r"\*\*([^*]+)\*\*", r"<b>\1</b>", text)
    text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)
    return text


def skip_condensed_module_s(md: str) -> str:
    """Drop the short Module S already expanded in START_ARM.md."""
    lines = md.splitlines()
    out: list[str] = []
    skipping = False
    for line in lines:
        if line.startswith("## 模块 S"):
            skipping = True
            continue
        if skipping and line.startswith("## "):
            skipping = False
        if not skipping:
            out.append(line)
    return "\n".join(out)


def md_to_html_body(md: str, first_h2: bool = False) -> str:
    parts: list[str] = []
    lines = md.splitlines()
    i = 0
    in_code = False
    code: list[str] = []
    table: list[str] = []
    saw_h2 = False

    def flush_table() -> None:
        nonlocal table
        if not table:
            return
        rows = []
        for row in table:
            cols = [c.strip() for c in row.strip().strip("|").split("|")]
            if all(re.match(r"^:?-+:?$", c) for c in cols):
                continue
            rows.append(cols)
        if not rows:
            table = []
            return
        html_rows = []
        for idx, cols in enumerate(rows):
            tag = "th" if idx == 0 else "td"
            html_rows.append("<tr>" + "".join(f"<{tag}>{inline(c)}</{tag}>" for c in cols) + "</tr>")
        parts.append("<table>" + "".join(html_rows) + "</table>")
        table = []

    while i < len(lines):
        raw = lines[i]
        line = raw.rstrip()
        if line.startswith("```"):
            flush_table()
            if not in_code:
                in_code = True
                code = []
            else:
                parts.append("<pre>" + html.escape("\n".join(code) or " ") + "</pre>")
                in_code = False
            i += 1
            continue
        if in_code:
            code.append(raw)
            i += 1
            continue
        if line.startswith("|"):
            table.append(line)
            i += 1
            continue
        flush_table()
        if not line or line == "---":
            i += 1
            continue
        if line.startswith("# "):
            # Document title already on the cover.
            i += 1
            continue
        if line.startswith("## "):
            cls = ' class="first"' if first_h2 and not saw_h2 else ""
            saw_h2 = True
            parts.append(f"<h2{cls}>{inline(line[3:].strip())}</h2>")
        elif line.startswith("### "):
            parts.append(f"<h3>{inline(line[4:].strip())}</h3>")
        elif line.startswith("#### "):
            parts.append(f"<h4>{inline(line[5:].strip())}</h4>")
        elif line.startswith("- ") or line.startswith("* "):
            items = []
            while i < len(lines) and re.match(r"^[-*] ", lines[i].rstrip()):
                items.append("<li>" + inline(lines[i].rstrip()[2:]) + "</li>")
                i += 1
            parts.append("<ul>" + "".join(items) + "</ul>")
            continue
        elif re.match(r"^\d+\.\s", line):
            items = []
            while i < len(lines) and re.match(r"^\d+\.\s", lines[i].rstrip()):
                items.append("<li>" + inline(re.sub(r"^\d+\.\s", "", lines[i].rstrip())) + "</li>")
                i += 1
            parts.append("<ol>" + "".join(items) + "</ol>")
            continue
        elif line.startswith(">"):
            parts.append('<div class="box">' + inline(line.lstrip("> ").strip()) + "</div>")
        else:
            parts.append("<p>" + inline(line) + "</p>")
        i += 1
    flush_table()
    return "\n".join(parts)


def build_html() -> str:
    start = START_ARM.read_text(encoding="utf-8")
    guide = skip_condensed_module_s(GUIDE.read_text(encoding="utf-8"))
    body = md_to_html_body(start, first_h2=True) + "\n" + md_to_html_body(guide)
    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8"/>
<title>眼在手视觉伺服闭环实施手册（Noetic）</title>
<style>{CSS}</style>
</head>
<body>
<div class="cover">
  <p class="small">本科科研预备 · 实施手册（已按本机更新）</p>
  <h1>眼在手上机械臂<br/>视觉伺服闭环控制<br/>实施手册</h1>
  <p>ROS 1 Noetic · 实验室 catkin 工作空间 robot_gripper<br/>含模块 S：启动机械臂并下发运动指令</p>
  <div class="meta">
    <p>工作空间：/home/biand/workspace_ws/src/robot_gripper_9_91/robot_gripper_5_29/robot_gripper</p>
    <p>包：arm_description · arm_moveit_config · abb_driver · control_robot · vi_grab · bio_ik</p>
    <p>启动脚本：start.sh · start_ui.sh · launch_synarm_ui.sh</p>
    <p>应用层：Python / moveit_commander · 不改 abb_driver · 不做 ROS 2 课设仿真</p>
  </div>
  <div class="ok">顺序：模块 S（启动 + RViz / Python 运动）→ A → B → C → D → E → F → G → H</div>
</div>
{body}
</body>
</html>
"""


def main() -> None:
    html_text = build_html()
    HTML_OUT.parent.mkdir(parents=True, exist_ok=True)
    HTML_OUT.write_text(html_text, encoding="utf-8")
    pdf_bytes = HTML(string=html_text, base_url=str(ROOT)).write_pdf()
    first = OUTPUTS[0]
    first.write_bytes(pdf_bytes)
    print(f"wrote {first} ({len(pdf_bytes)} bytes)")
    for dest in OUTPUTS[1:]:
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(first, dest)
        print(f"wrote {dest}")


if __name__ == "__main__":
    main()
