# 根据本机 Noetic 工作空间：必须做的调整

**依据：** 你在 WSL Ubuntu 20.04 贴出的 `ROS_DISTRO=noetic`、`ls /opt/ros`、工作空间目录和 `find … -name package.xml`。  
**结论一句话：** 练习不再按 ROS 2 / colcon / ros2_control / 课设工作空间写；只在最内层 `robot_gripper` 的 catkin 工作空间里，加一个旁路包 `vs_practice`，复用现有臂、MoveIt 1、`vi_grab` 和 RealSense。

不要另起一套仿真，不要把课设 URDF 拷进来，不要改 `abb_driver`。

---

## 1. 从 listing 能确定的事实

| 项 | 本机值 | 手册旧假设（作废） |
|---|---|---|
| 发行版 | ROS 1 **Noetic**（`/opt/ros/noetic`） | ROS 2 Humble / Jazzy |
| 构建 | **catkin_tools**（有 `.catkin_tools/`、`build/`、`devel/`） | `colcon` + `install/` |
| 工作空间根 | 最内层 `…/robot_gripper_5_29/robot_gripper` | `~/workspace_ws` 直接 colcon |
| 真源码 | 只有 `src/` 下 8 个包 | 课设夹爪包 |
| 视觉 | `vi_grab` + `99-realsense-libusb.rules` | 自己再挂一套 Gazebo 相机 |
| 启动 | `start.sh` / `start_ui.sh` / `launch_synarm_ui.sh` | `ros2 launch xxx_bringup` |
| 驱动 | `abb_driver` + `control_robot` + `robot_serial` | 课设 `ros2_control` hardware |
| IK | `bio_ik`（MoveIt 插件，调用即可） | 自写 IK |
| 其它课题 | `JEPA_POLICY_DATA_COLLECTION.md` | 与本练习无关，不要混 |

**当作源码的 8 个包（只认 `src/`，不认备份）：**

```
src/arm_description
src/arm_moveit_config
src/abb_driver
src/control_robot
src/robot_serial
src/vi_grab
src/robot_ui
src/bio_ik
```

下面这些 `package.xml` **不是** 你要改的源码：

- `backups/20260920_…` — 旧拷贝
- `.catkin_tools/profiles/default/packages/*` — 构建缓存
- `build/catkin_tools_prebuild/package.xml` — catkin_tools 脚手架

---

## 2. 目录怎么读（不要在外层 build）

```
/home/biand/workspace_ws/                          ← 只是目录容器，不是 catkin 根
  src/robot_gripper_9_91/                          ← 日期拷贝外层，不要在这里 catkin build
    robot_gripper_5_29/
      robot_gripper/                               ← ★ 唯一的 catkin 工作空间
        src/          ← 8 个实验室包；vs_practice 放这里
        build/  devel/  .catkin_tools/
        start.sh  start_ui.sh  launch_synarm_ui.sh
```

所有 `source` / `catkin build` / `roslaunch` 都在这一层做：

```bash
WS=/home/biand/workspace_ws/src/robot_gripper_9_91/robot_gripper_5_29/robot_gripper
source /opt/ros/noetic/setup.bash
cd "$WS"
# 已有 devel 时可直接：
source devel/setup.bash
```

不要对 `/home/biand/workspace_ws` 跑 `catkin build`，也不要跑 `colcon`。

---

## 3. 命令对照（手册里凡是左边的，本机都改成右边）

| 手册（ROS 2） | 本机（Noetic） |
|---|---|
| `source /opt/ros/humble/setup.bash` | `source /opt/ros/noetic/setup.bash` |
| `colcon build && source install/setup.bash` | `catkin build vs_practice && source devel/setup.bash` |
| `ros2 launch …` | `roslaunch …` |
| `ros2 run pkg node` | `rosrun pkg node` |
| `ros2 topic list` | `rostopic list` |
| `ros2 topic echo /joint_states --once` | `rostopic echo /joint_states -n 1` |
| `ros2 topic hz /camera/image_raw` | `rostopic hz /camera/color/image_raw` |
| `ros2 control list_controllers` | `rosservice call /controller_manager/list_controllers`（没有该服务就改查 `abb_driver` / `control_robot` 话题） |
| `ros2 bag record /joint_states /tf` | `rosbag record /joint_states /tf` |
| `ros2 run tf2_ros tf2_echo A B` | `rosrun tf tf_echo A B` |
| MoveIt 2 Python / pymoveit2 | **`moveit_commander`**（`MoveGroupCommander`） |
| `ros2_control` 速度控制器 | **先查有没有**；ABB 常见只有轨迹接口，见第 6 节 |

课程第八章若是 ROS 2 API，**不要把课上的节点直接拷进本机**。本仓库 `vs_practice` 已按 MoveIt 1 / rospy 写好调用骨架。

---

## 4. 现有包各自管哪一层（不要重写）

| 包 | 在闭环里的角色 | 你对它做什么 |
|---|---|---|
| `arm_description` | URDF、link 名、相机/法兰 origin | 只读；抄基座、末端、相机 frame |
| `arm_moveit_config` | SRDF 规划组、kinematics、controllers.yaml、demo launch | 只读；抄 `<arm_group>`；用它的 demo / 实验室 start 把 MoveIt 拉起来 |
| `bio_ik` | MoveIt IK 插件 | 不调 C++；kinematics.yaml 已配则会自动用 |
| `abb_driver` | 真机工业机器人客户端 | **不改**；不写第二套 driver |
| `control_robot` | 组里对臂的控制封装 | 只读；看它发轨迹还是发速度 |
| `robot_serial` | 串口 / 夹爪一类外设 | 夹爪开合跟它的现有接口；没有夹爪就省略 GRASP |
| `vi_grab` | 现有视觉 / 抓取 | **复用图像话题**；不要再开第二套 RealSense |
| `robot_ui` | 现有 UI | 可以继续用实验室启动；`vs_*` 节点旁路运行 |

`JEPA_POLICY_DATA_COLLECTION.md`、`checkpoints/`、`Data/` 属于另一条数据采集/策略线。本练习不碰它们。

---

## 5. 唯一要新增的东西

把本仓库的 `vs_practice/` 拷进实验室 `src/`，成为第 9 个包：

```bash
# 若本仓库在 Windows/WSL 某处，例如：
SRC_PKG=/path/to/this/repo/vs_practice
WS=/home/biand/workspace_ws/src/robot_gripper_9_91/robot_gripper_5_29/robot_gripper

cp -a "$SRC_PKG" "$WS/src/vs_practice"
source /opt/ros/noetic/setup.bash
cd "$WS"
catkin build vs_practice
source devel/setup.bash
```

先按实验室习惯把臂和相机拉起来（`./start.sh` 或 `./start_ui.sh`，以你们文档为准），**另开终端**再跑：

```bash
source /opt/ros/noetic/setup.bash
source /home/biand/workspace_ws/src/robot_gripper_9_91/robot_gripper_5_29/robot_gripper/devel/setup.bash
rosrun vs_practice print_interface.py
```

`print_interface.py` 会打印：规划组、末端 link、已发布话题、像不像 RealSense、有没有 `controller_manager`。把输出贴进 `vs_practice/config/interface.yaml`。

---

## 6. 步骤 E 的关键调整：ABB 往往没有速度控制器

旧手册假定：

```
切到 joint_group_velocity_controller → 每周期发关节速度
```

本机有 `abb_driver`。工业 ABB 经 `abb_driver` / `industrial_robot_client` **通常只有** `FollowJointTrajectory`（位置轨迹），没有 `ros2_control` 那种关节速度接口。因此：

1. 用 `print_interface.py` 和下面两条命令查接口，**先不要写速度切换**。

```bash
rostopic list | grep -E 'joint|controller|velocity|traj'
rosservice list | grep -E 'controller|follow'
```

2. 打开并登记（只读）：

- `src/arm_moveit_config/config/controllers.yaml`（或 `ros_controllers.yaml`）
- `src/arm_moveit_config/*.srdf` 里的 `<group name="…">`
- `src/control_robot` 里实际发布的命令话题

3. 按查到的结果选 `vs_practice/config/interface.yaml` 的 `servo_mode`：

| 查到的接口 | `servo_mode` | 含义 |
|---|---|---|
| 关节速度控制器 / 速度话题 | `joint_velocity` | 旧手册的真速度环，优先 |
| 只有 FollowJointTrajectory / ABB | `cartesian_increment` | 每周期用当前误差算一个**几毫米**的笛卡尔增量，经 Commander 走短笛卡尔段；**禁止**再 `plan()` 一条长轨迹 |
| 组里已有点动 / jog | 以后再接到该话题 | 先在 yaml 里记下话题名 |

`cartesian_increment` 频率大约 2～10 Hz，仍是“误差 → 运动 → 新图像”的闭环，不是检测一次再规划。λ 必须比真速度环更小。不要用 2 Hz 的大位移位置点冒充伺服。

---

## 7. 相机：复用，不新开

本机已有 `99-realsense-libusb.rules` 和 `vi_grab`。步骤 C 改为：

1. 臂和相机已按实验室方式启动后，`rostopic list | grep -i image`。
2. RealSense 在 Noetic 上常见是 `/camera/color/image_raw` 与 `/camera/color/camera_info`（以实际为准）。
3. 把名字写入 `interface.yaml` 的 `image_topic` / `camera_info_topic`。
4. `vs_detect` 只订阅，不 `roslaunch realsense2_camera` 第二份。
5. 手眼 TF：`rosrun tf tf_echo <ee_link> <camera_optical_frame>`，frame 名从 `arm_description` 和 RealSense 的 TF 抄，不猜。

没有现成眼在手光学系时，先把检测跑通（步骤 C），手眼不准只影响步骤 D 的一次位姿估计；步骤 E 的像素对中对标定更宽容。

---

## 8. 步骤 A～H 在本机怎么走

| 步骤 | 本机做法 | 不要做 |
|---|---|---|
| **A 清单** | 实验室 `start.sh`/`start_ui.sh` 把 MoveIt 拉起 → `rosrun vs_practice print_interface.py` → 填 `interface.yaml` → RViz MotionPlanning 拖一次 Execute | `colcon`；在外层目录 build |
| **B 开环流程** | `roslaunch vs_practice commander_only.launch`；API 是 `moveit_commander.MoveGroupCommander` | 抄 ROS 2 第八章节点；改 MoveIt / abb_driver 源码 |
| **C 检测** | 订阅 `vi_grab` / RealSense 已有图像；`roslaunch vs_practice detect_only.launch` | 再挂一套相机驱动；把像素送给 MoveIt |
| **D 开环视觉** | `/vs/tag_ok` 为真时算一次 approach，调用 B 的 `go()` | 运动中途反复 plan |
| **E 闭环** | 按第 6 节选 `servo_mode`；`vs_fsm` 在 APPROACH 成功后进 SERVO | 假定一定有 `ros2 control switch_controllers` |
| **F 对照** | `rosbag record /joint_states /tf /vs/error /vs/state` | 目视填表 |
| **G 延迟三律** | 只改 `vs_practice` 里的 `image_law()` | 换检测器、换驱动 |
| **H 真机** | 已经在实验室包上；限速、急停、短时占机 | 把课设 hardware 抄到 ABB |

规划组名以 SRDF 为准。ABB MoveIt 常见是 `manipulator`，**以 `print_interface.py` 打印值为准**，不要写死 `panda_arm`。

---

## 9. 课程怎么改（和本机对齐）

- 第一门课第八章：只保留“会调用规划”的概念。本机实现一律用 `moveit_commander`，见 `vs_practice/scripts/vs_commander_node.py`。
- 第二门 ros2_control 课：**先停**。本机不是 ros2_control。只有 `print_interface.py` 确认存在 `controller_manager` 且真有速度控制器时，才回头看“如何切控制器”。
- 不要为了课程再装 ROS 2 仿真栈来做本练习。

---

## 10. 接口清单（步骤 A 填完再写业务逻辑）

把 `print_interface.py` 的输出抄到 `vs_practice/config/interface.yaml`。至少这些键：

```yaml
ros_distro: noetic
arm_group: ""          # SRDF / print_interface
gripper_group: ""      # 没有则留空，省略 GRASP
ee_link: ""
base_frame: ""
image_topic: /camera/color/image_raw
camera_info_topic: /camera/color/camera_info
camera_optical_frame: ""
servo_mode: cartesian_increment   # 或 joint_velocity
velocity_topic: ""                # 仅 joint_velocity 时填
trajectory_controller: ""
```

清单没填满之前，不要改控制律。

---

## 11. 现在立刻做的三件事

1. 在最内层 `robot_gripper` 里按第 5 节拷入并编译 `vs_practice`。
2. 用实验室脚本启动臂（能在 RViz 里 Execute 一次即可）。
3. 跑 `rosrun vs_practice print_interface.py`，把完整终端输出发回来（或自行写入 `interface.yaml`）。有了规划组名和图像话题，步骤 B/C 才能对着真名字跑。
