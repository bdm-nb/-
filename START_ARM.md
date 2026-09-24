# 模块 S　启动本机机械臂并下发运动指令

**这一模块先于步骤 A～H。** 臂还不能按你的指令动，后面的检测和伺服都不要做。

**本机版本（已由你贴出的 listing 锁定，不是课设 ROS 2）：**

| 项 | 值 |
|---|---|
| 系统 | WSL Ubuntu 20.04 |
| ROS | 1 **Noetic**（`/opt/ros/noetic`） |
| 工作空间根 | `/home/biand/workspace_ws/src/robot_gripper_9_91/robot_gripper_5_29/robot_gripper` |
| 构建 | catkin_tools（`devel/`，不是 `install/`） |
| 臂描述 / 规划 | `src/arm_description` + `src/arm_moveit_config` |
| 真机驱动 | `src/abb_driver`（不要改） |
| 组里封装 | `src/control_robot`、`src/robot_serial` |
| IK | `src/bio_ik`（MoveIt 插件，调用即可） |
| 视觉 / UI | `src/vi_grab`、`src/robot_ui`（本模块先不管相机） |
| 实验室启动脚本 | 工作空间根下的 `start.sh`、`start_ui.sh`、`launch_synarm_ui.sh` |

下文命令里的 `$WS` 一律等于上面那一行工作空间根。先在每个新开的终端执行一次：

```bash
export WS=/home/biand/workspace_ws/src/robot_gripper_9_91/robot_gripper_5_29/robot_gripper
source /opt/ros/noetic/setup.bash
source "$WS/devel/setup.bash"
cd "$WS"
```

也可以：`source /path/to/本仓库/vs_practice/env.sh`

---

## S.0 目的、原理、验收

### 目的

学会四件事，并且能口头复述：

1. 在哪一层目录启动（最内层 `robot_gripper`，不是 `workspace_ws`）。
2. 实验室三条脚本各自开什么，不要同时开两套 bringup。
3. 用 RViz MotionPlanning **Execute** 发出第一条轨迹。
4. 用 `moveit_commander` 发出第二条小位移（Python，不是改 driver）。

### 原理（本机这条链）

```
你（RViz 或 Python Commander）
    → MoveIt 1（arm_moveit_config / move_group，IK 可能走 bio_ik）
        → FollowJointTrajectory（controllers.yaml 里的名字）
            → abb_driver / control_robot
                → 控制器 / 仿真
                    → /joint_states、/tf 回来
```

- `start.sh` 一类脚本负责把 **驱动 + MoveIt + 必要节点** 拉起来。
- RViz 的 Execute 和 Python 的 `arm.go()` 是同一层：都是给 MoveIt 下目标，**不是**直接转电机。
- `abb_driver` 是厂家/工业接口，本练习只调用、不改。

### 验收（本模块完成线）

- `/joint_states` 有数且在刷新。
- RViz 里规划组能选中，拖一次末端，**Plan 成功且 Execute 后关节角变化**。
- `rosrun vs_practice send_small_motion.py` 再让末端动约 2 cm（或明确打印 dry-run 目标）。
- 你能一句话说明：谁规划、谁跟踪轨迹、谁是 driver。

---

## S.1 安全（真机必读，仿真也建议照做）

1. 工作空间清空，急停位置你够得到。组里有示教器/急停键，先确认谁按。
2. 第一条运动只允许 **很小**：笛卡尔 ≤ 4 cm，速度缩放 0.1。
3. 终端里随时：

```bash
rostopic pub /vs/cmd std_msgs/String "data: stop"
```

或在跑 `send_small_motion.py` 的终端 `Ctrl+C`。真机以组里急停为准。
4. 不要两个终端同时 `./start.sh` 和 `./start_ui.sh`（会抢 `roscore` / 驱动）。
5. 不要对 `/home/biand/workspace_ws` 跑 `catkin build` 或 `colcon`。

---

## S.2 先读实验室脚本（30 秒，不要猜）

在已 source 的终端：

```bash
cd "$WS"
ls -l start.sh start_ui.sh launch_synarm_ui.sh
echo "===== start.sh ====="
sed -n '1,80p' start.sh
echo "===== start_ui.sh ====="
sed -n '1,80p' start_ui.sh
echo "===== launch_synarm_ui.sh ====="
sed -n '1,80p' launch_synarm_ui.sh
echo "===== MoveIt launch ====="
ls src/arm_moveit_config/launch
```

对着脚本正文，用下表判断你走哪条路径：

| 脚本里主要在 launch 什么 | 本模块用它来 |
|---|---|
| `arm_moveit_config` 的 `demo.launch` / `fake` / `sim:=true` | **路径 1**：不上真机，只练 MoveIt + Commander |
| `abb_driver` / `robot_ip` / `control_robot` | **路径 2**：真机或实验室标准 bringup → 优先 `./start.sh` |
| `robot_ui` / `launch_synarm_ui` | **路径 3**：要实验室 UI 时用；运动仍由 MoveIt 执行 |
| `vi_grab` / RealSense / JEPA | 本模块先不管；等步骤 C 再开相机 |

把 `ls src/arm_moveit_config/launch` 里实际文件名记下来。常见会有 `demo.launch`、`moveit_planning_execution.launch`。以你磁盘上的名为准。

---

## S.3 启动（三条路径只开一条）

### 路径 1 — 只核对 MoveIt（不上真机、不抢实验室 UI）

适合：第一次练「下发运动」，控制器不在旁边。

```bash
# 终端 1（保持不关）
export WS=/home/biand/workspace_ws/src/robot_gripper_9_91/robot_gripper_5_29/robot_gripper
source /opt/ros/noetic/setup.bash
source "$WS/devel/setup.bash"
roslaunch arm_moveit_config demo.launch
```

若提示找不到 `demo.launch`，改成 S.2 里看到的那个带 `demo` / `fake` / `rviz` 的 launch。成功时一般会弹出 RViz，左侧有 **MotionPlanning**。

### 路径 2 — 实验室日常（优先）

适合：组里平时就是这样开臂。

```bash
# 终端 1
export WS=/home/biand/workspace_ws/src/robot_gripper_9_91/robot_gripper_5_29/robot_gripper
source /opt/ros/noetic/setup.bash
source "$WS/devel/setup.bash"
cd "$WS"
./start.sh
```

真机时还要满足组里规程（控制器 AUTO、电机使能、RAPID/通信程序在跑、IP 通）。这些写在你们的 `ROS_DOCUMENTATION.md` 里，本手册不替代。

若 `start.sh` 没带 RViz，再开终端 2：

```bash
export WS=/home/biand/workspace_ws/src/robot_gripper_9_91/robot_gripper_5_29/robot_gripper
source /opt/ros/noetic/setup.bash
source "$WS/devel/setup.bash"
roslaunch arm_moveit_config moveit_rviz.launch
```

`moveit_rviz.launch` 若没有，用 S.2 列出的带 `rviz` 的文件，或在已有 RViz 里手动加 MotionPlanning 插件。

### 路径 3 — 要实验室 UI（SynArm / robot_ui）

```bash
cd "$WS"
# 二选一，不要和路径 2 同时开
./start_ui.sh
# 或
./launch_synarm_ui.sh
```

UI 可以留着。本模块的运动指令仍然走 RViz / `send_small_motion.py`，不要在 UI 里乱点和大位移。

---

## S.4 确认「臂已经在听」（另开终端 2）

```bash
export WS=/home/biand/workspace_ws/src/robot_gripper_9_91/robot_gripper_5_29/robot_gripper
source /opt/ros/noetic/setup.bash
source "$WS/devel/setup.bash"

echo "ROS_DISTRO=$ROS_DISTRO"          # 必须是 noetic
rostopic echo /joint_states -n 1       # 必须有 position 数组
rostopic hz /joint_states              # Ctrl+C 停；应有稳定 Hz
rostopic list | grep -E 'joint|move_group|follow|traj|camera'
rosservice list | grep -E 'plan|execute|controller|follow' | head
```

| 现象 | 含义 | 怎么办 |
|---|---|---|
| `Unable to communicate with master` | 终端 1 没起来或没 source | 先看终端 1 有没有报错；每个终端都要 source `devel` |
| 没有 `/joint_states` | 驱动或 fake joint 没起 | 回到 S.2 看脚本少 launch 了哪一段 |
| 有 `/joint_states` 但没有 `move_group` | 只开了驱动，没开 MoveIt | 补 `roslaunch arm_moveit_config …`（S.2 里的文件） |
| `ROS_DISTRO` 不是 noetic | source 错了发行版 | 只 source `/opt/ros/noetic` |

可选（若已拷入 `vs_practice`）：

```bash
rosrun vs_practice print_interface.py
```

记下打印的 **planning groups** 和 **ee=**。后面 `--group` 必须用这个名字，不要写 `panda_arm`。

---

## S.5 用 RViz 下发第一条运动指令

这是本机「运动指令」的第一种发法：人在界面里给目标，MoveIt 规划，轨迹控制器执行。

1. RViz 左侧找到 **MotionPlanning**。没有就：Panels → Add New Panel → MotionPlanning。
2. Context / Planning 里 **Planning Group** 选 `print_interface.py` 打出来的臂组（常见 `manipulator`，以打印为准）。
3. 勾选 **Query** 的 Start 等于当前状态（或点 **Update** / **Current**）。
4. 用橙色/交互标记把末端平移 **很小一截**（目测 2～3 cm）。不要转很大关节。
5. 点 **Plan**。成功则出现一条轨迹；失败先换近一点的目标，不要改 `abb_driver`。
6. 速度缩到很低（若有 Velocity Scaling，先 0.1）。
7. 点 **Execute**。看真机或 RViz 里的臂跟着走。
8. 终端 2：再执行一次 `rostopic echo /joint_states -n 1`，确认数字相对步骤 S.4 变了。

**验收：** Execute 成功 + 关节值变化。失败只停在本步。

把这次成功的末端位姿抄下来，以后写入 `vs_practice/config/waypoints.yaml`。在终端 2 也可以等 S.6 的脚本帮你打印当前位姿。

---

## S.6 用 Python 下发第二条运动指令

这是本机「运动指令」的第二种发法：和课程第八章同一层，但是 **MoveIt 1 / rospy / `moveit_commander`**，不要拷 ROS 2 节点。

先确认 `vs_practice` 已在 `$WS/src/vs_practice` 并 `catkin build vs_practice`、重新 `source devel/setup.bash`。

**只看当前状态（臂不动）：**

```bash
rosrun vs_practice send_small_motion.py _group:=manipulator _dry_run:=true
```

把 `_group` 换成 S.4 打印的组名。屏幕会打出当前关节、当前末端位姿（可抄进 `waypoints.yaml`）。

**真的动 2 cm（沿当前末端 z，先 dry-run 看目标再执行）：**

```bash
# 先看目标，不动
rosrun vs_practice send_small_motion.py _group:=manipulator _dz:=0.02 _dry_run:=true
# 确认目标合理后再动（≤ 4 cm）
rosrun vs_practice send_small_motion.py _group:=manipulator _dz:=0.02 _dry_run:=false
```

或：

```bash
roslaunch vs_practice send_small_motion.launch group:=manipulator dz:=0.02 dry_run:=false
```

脚本内部做的事：

1. `MoveGroupCommander(group)` 接到已经在跑的 `move_group`。
2. `get_current_pose()` 取当前末端。
3. 位置加 `dx,dy,dz`（默认只加 `dz=0.02`）。
4. `set_max_velocity_scaling_factor(0.1)`。
5. `set_pose_target` → `go(wait=True)` → `stop` → `clear_pose_targets`。

位移绝对值超过 4 cm 会直接拒绝。这就是「调用 Commander」，不是写 driver。

**验收：** 日志 `go ok=True`；`/joint_states` 再变一次；你能指出代码里没有改 `abb_driver`。

---

## S.7 停机

```bash
# 停练习节点
pkill -f send_small_motion.py
# 停实验室 bringup：回到终端 1，Ctrl+C
# 真机：按组里急停 / 示教器停止，再断电规程
```

不要在臂还在动时关 WSL 窗口。

---

## S.8 运动指令失败对照

| 现象 | 先查 |
|---|---|
| `No move_group` / Commander 超时 | 终端 1 是否 launch 了 `arm_moveit_config` |
| `Invalid group name` | `--group` / `_group` 与 SRDF 不一致，跑 `print_interface.py` |
| Plan 失败 | 目标太远、碰撞、超限；先减到 2 cm |
| Plan 成功但臂不动 | 假执行 vs 真机：路径 1 只动 RViz；真机要路径 2 且控制器使能 |
| 一启动就报 robot_ip / socket | `abb_driver` 连不上控制器；查 `ROS_DOCUMENTATION.md` 和网线，不改驱动源码 |
| UI 和 RViz 抢臂 | 只留一条 bringup；UI 打开时不要再 `./start.sh` |

---

## S.9 做完之后

本模块通过 → 进入 [implementation_guide.md](implementation_guide.md) **步骤 A**（填 `interface.yaml`）。  
步骤 A 的「RViz 拖一次」若在 S.5 已做过，可以只补 `print_interface.py` 的登记。  
步骤 B 把 S.6 的单次 `go()` 扩成 APPROACH → DESCEND 流程。
