#!/usr/bin/env python3
"""Build the dedicated step-by-step purpose/principle/link/how-to PDF."""

from __future__ import annotations

import shutil
import sys
from pathlib import Path

from weasyprint import HTML

sys.path.insert(0, str(Path(__file__).resolve().parent))
import generate_handbook_pdf as handbook

ROOT = Path("/workspace")
MD = ROOT / "STEP_EXPLAIN.md"
HTML_OUT = ROOT / "docs" / "step_explain.html"

OUTPUTS = [
    ROOT / "step_explain.pdf",
    ROOT / "每步目的原理衔接做法.pdf",
    ROOT / "docs" / "每步目的原理衔接做法.pdf",
    Path("/opt/cursor/artifacts/step_explain.pdf"),
    Path("/opt/cursor/artifacts/每步目的原理衔接做法.pdf"),
    Path("/home/ubuntu/Desktop/step_explain.pdf"),
    Path("/home/ubuntu/Desktop/每步目的原理衔接做法.pdf"),
]

CSS = handbook.CSS.replace(
    "眼在手视觉伺服闭环实施手册 · ROS 1 Noetic / 实验室 robot_gripper",
    "每一步的目的、原理、衔接与做法 · Noetic / robot_gripper",
)


def build_html() -> str:
    md = MD.read_text(encoding="utf-8")
    body = handbook.md_to_html_body(md, first_h2=True)
    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8"/>
<title>每一步的目的、原理、衔接与做法</title>
<style>{CSS}</style>
</head>
<body>
<div class="cover">
  <p class="small">专篇讲解 · 不是总手册压缩版</p>
  <h1>每一步的目的、原理、<br/>与上一步的衔接、怎么做</h1>
  <p>模块 S → A → B → C → D → E → F → G → H<br/>每一步固定四节，做完一节再翻下一节</p>
  <div class="meta">
    <p>本机：ROS 1 Noetic · 最内层 robot_gripper</p>
    <p>/home/biand/workspace_ws/src/robot_gripper_9_91/robot_gripper_5_29/robot_gripper</p>
    <p>旁路包 vs_practice · 调用 moveit_commander · 不改 abb_driver</p>
  </div>
  <div class="ok">目的：为什么做这一层。原理：在算什么、谁在哪一层。衔接：上一步交出了什么、这一步补哪一层。怎么做：本机命令与通过标准。</div>
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
