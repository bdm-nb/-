# 点这个

**专篇（每步目的 / 原理 / 衔接 / 怎么做，约 19 页）：** [step_explain.pdf](step_explain.pdf)  
同内容中文名：[每步目的原理衔接做法.pdf](每步目的原理衔接做法.pdf)

**总手册（22 页，Noetic + 模块 S）：** [implementation_guide.pdf](implementation_guide.pdf)

专篇拷到桌面：

```bash
D=/mnt/c/Users/biand/Desktop
B=https://github.com/bdm-nb/-/raw/cursor/visual-servo-practice-report-4530
curl -fsSL -o "$D/step_explain.pdf" "$B/step_explain.pdf"
curl -fsSL -o "$D/每步目的原理衔接做法.pdf" \
  "$B/%E6%AF%8F%E6%AD%A5%E7%9B%AE%E7%9A%84%E5%8E%9F%E7%90%86%E8%A1%94%E6%8E%A5%E5%81%9A%E6%B3%95.pdf"
```

总手册拷到桌面（三份内容相同，只是文件名不同）：

```bash
D=/mnt/c/Users/biand/Desktop
B=https://github.com/bdm-nb/-/raw/cursor/visual-servo-practice-report-4530
curl -fsSL -o "$D/implementation_guide.pdf" \
  "$B/implementation_guide.pdf"
curl -fsSL -o "$D/实施手册.pdf" \
  "$B/%E5%AE%9E%E6%96%BD%E6%89%8B%E5%86%8C.pdf"
curl -fsSL -o "$D/眼在手视觉伺服实施文档.pdf" \
  "$B/%E7%9C%BC%E5%9C%A8%E6%89%8B%E8%A7%86%E8%A7%89%E4%BC%BA%E6%9C%8D%E5%AE%9E%E6%96%BD%E6%96%87%E6%A1%A3.pdf"
```

若用户名不是 `biand`，改 `D=`。或运行 `scripts/save_pdf_to_desktop.sh`（一次存三份）。

Markdown：
1. [START_ARM.md](START_ARM.md) — 启动臂并下发运动
2. [implementation_guide.md](implementation_guide.md) — 完整手册
3. [NOETIC_ADJUST.md](NOETIC_ADJUST.md) — 相对旧 ROS 2 手册的对照
