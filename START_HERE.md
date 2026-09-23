# 点这个

**更新后的 PDF（22 页，Noetic + 模块 S）：** [implementation_guide.pdf](implementation_guide.pdf)

拷到你自己的 Windows 桌面（在 **WSL 终端**里执行，不要在云端执行）。三份内容相同，只是文件名不同：

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
