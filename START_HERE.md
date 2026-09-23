# 点这个

**更新后的 PDF（22 页，Noetic + 模块 S）：** [implementation_guide.pdf](implementation_guide.pdf)

拷到你自己的 Windows 桌面（在 **WSL 终端**里执行，不要在云端执行）：

```bash
curl -fsSL -o /mnt/c/Users/biand/Desktop/implementation_guide.pdf \
  https://github.com/bdm-nb/-/raw/cursor/visual-servo-practice-report-4530/implementation_guide.pdf
```

若用户名不是 `biand`，把路径改成你的 `C:\Users\<你的用户名>\Desktop`。或运行 `scripts/save_pdf_to_desktop.sh`。

同内容副本：
- [眼在手视觉伺服实施文档.pdf](眼在手视觉伺服实施文档.pdf)
- [实施手册.pdf](实施手册.pdf)

Markdown：
1. [START_ARM.md](START_ARM.md) — 启动臂并下发运动
2. [implementation_guide.md](implementation_guide.md) — 完整手册
3. [NOETIC_ADJUST.md](NOETIC_ADJUST.md) — 相对旧 ROS 2 手册的对照
