# 眼在手上机械臂视觉伺服闭环控制实施手册

**文件性质：** 分步实施指导书（目的—原理—实现—验收）  
**本机栈（已由 listing 锁定）：** WSL Ubuntu 20.04 · ROS 1 **Noetic** · catkin_tools  
**工作空间根：** `/home/biand/workspace_ws/src/robot_gripper_9_91/robot_gripper_5_29/robot_gripper`  
**仿真/真机模型：** 只用该工作空间里的 `arm_description` + `arm_moveit_config`，不用课设 URDF，不另起 ROS 2 仿真  
**语言约定：** 应用层 Python；调用 `moveit_commander`；不写 Commander 库、不改 `abb_driver`

对照清单见 [NOETIC_ADJUST.md](NOETIC_ADJUST.md)。  
**启动臂、RViz / Python 下发运动（先做这一章）：** [START_ARM.md](START_ARM.md)

下文每一步：**目的、原理、实现、验收**。未通过验收不得进入下一步。顺序：

**模块 S（启动 + 运动指令）→ A → B → C → D → E → F → G → H**

---

## 0. 项目在做什么（实施视角）

做出一条与现有 `vi_grab`「检测一次再规划」不同的链路：

1. 用 **MoveIt 1 Commander** 把末端送到相机能看见 ArUco 的位置（开环、粗、快）。
2. **停止规划长轨迹**，每一帧用标签中心相对图像中心的像素误差生成运动量。
3. 运动量按本机接口写入臂：若有关节速度话题则走速度；ABB/`abb_driver` 通常只有轨迹接口，则走几毫米笛卡尔增量。臂一动，下一帧误差就变，形成闭环。
4. 用表格比较开环与闭环；再给图像加延迟、让标签慢速移动，比较三种控制律。

视觉只提供误差。思考在控制：增益、限幅、延迟、停机。现有 UI / JEPA 采集线不要混进来。

新建包：`src/vs_practice`（已在本仓库写好）。规划组名以本机 SRDF / `print_interface.py` 为准。

```
vi_grab 或 RealSense 已有图像 --> vs_detect --> /vs/error, /vs/tag_ok
/joint_states, /tf            --> vs_servo  --> 速度或短笛卡尔增量
vs_fsm --APPROACH--> vs_commander --> 轨迹控制器（abb_driver / MoveIt）
vs_fsm --SERVO--> vs_servo
```

---

## 模块 S 启动本机机械臂并下发运动指令

**本机版本：** Noetic + 最内层 `robot_gripper` + `arm_description` / `arm_moveit_config` / `abb_driver` / `control_robot`。完整点击步骤、失败表、三条启动路径见 [START_ARM.md](START_ARM.md)。这里是手册里必须先过的浓缩版。

### 目的

臂要先能按你的指令动。不会启动、不会在 RViz 里 Execute、不会用 `moveit_commander` 发 2 cm 位移，后面的视觉闭环没有执行层。

### 原理

运动指令只有一层客户端：RViz MotionPlanning 或 Python `MoveGroupCommander.go()`。它们都把目标交给已经启动的 MoveIt 1；`abb_driver` / `control_robot` 跟踪轨迹。`start.sh`、`start_ui.sh`、`launch_synarm_ui.sh` 负责把这条链拉起来，不要同时开两套。

### 实现

每个新终端先：

```bash
export WS=/home/biand/workspace_ws/src/robot_gripper_9_91/robot_gripper_5_29/robot_gripper
source /opt/ros/noetic/setup.bash
source "$WS/devel/setup.bash"
cd "$WS"
```

1. `sed -n '1,80p' start.sh start_ui.sh launch_synarm_ui.sh` 和 `ls src/arm_moveit_config/launch`，判断走哪条路径（见 START_ARM 路径 1/2/3）。
2. **只开一条 bringup。** 日常优先：`./start.sh`。只练 MoveIt、不上真机：`roslaunch arm_moveit_config demo.launch`。要实验室 UI：`./start_ui.sh` 或 `./launch_synarm_ui.sh`。
3. 另开终端，确认 `rostopic echo /joint_states -n 1` 有数。
4. RViz → MotionPlanning → 选本机规划组 → 末端只拖 2～3 cm → Plan → 速度 0.1 → Execute。
5. 拷入并编译 `vs_practice` 后：

```bash
rosrun vs_practice send_small_motion.py _group:=manipulator _dz:=0.02 _dry_run:=true
rosrun vs_practice send_small_motion.py _group:=manipulator _dz:=0.02 _dry_run:=false
```

`_group` 必须改成 `print_interface.py` 打印的组名。位移 > 4 cm 脚本会拒绝。

### 验收

`/joint_states` 在刷新；RViz Execute 后关节值变化；`send_small_motion.py` 打出 `go ok=True`（或 dry-run 打出合理目标）。不通过则只排启动与组名，不写检测器。

---

## 步骤 A 环境确认与信息登记

### 目的

避免在规划组、图像话题、控制器接口都未知时写代码。本步只产生 `interface.yaml`。

### 原理

后续节点要写死：规划组、关节顺序、图像话题、`servo_mode`。这些来自 `arm_moveit_config`、`vi_grab`、`control_robot`，不是课设 panda 名。

### 实现

1. 模块 S 已经通过（臂能 Execute，Python 能发 2 cm）。
2. 把本仓库 `vs_practice/` 拷进最内层 `src/`（若 S.6 还没拷），在该层 `catkin build vs_practice`，`source devel/setup.bash`。不要对 `/home/biand/workspace_ws` 做 colcon / catkin。
3. 臂保持模块 S 的启动方式，不要另开第二套 bringup。另开终端：

```bash
source /opt/ros/noetic/setup.bash
source /home/biand/workspace_ws/src/robot_gripper_9_91/robot_gripper_5_29/robot_gripper/devel/setup.bash
rosrun vs_practice print_interface.py
rostopic echo /joint_states -n 1
```

4. 打开 `src/arm_moveit_config` 的 SRDF 与 `controllers.yaml`，把打印结果写入 `vs_practice/config/interface.yaml`。
5. 模块 S 里成功的那次末端位姿写入 `waypoints.yaml`（不要抄手册示例数字）。

### 验收

清单填满。RViz / Python 运动在模块 S 已验收。没有 `controller_manager` 不算失败——ABB 经常没有，记到 yaml 即可。

---

## 步骤 B 用 Python 调用 Commander 完成开环流程

### 目的

把「会调用」落成状态机骨架。以后视觉只替换目标从哪来。

### 原理

`moveit_commander.MoveGroupCommander` 是 MoveIt 1 客户端。`set_pose_target` + `go()` 请规划器出轨迹，由 `abb_driver` / 轨迹控制器跟踪。调用者不是驱动器。`bio_ik` 若已写在 kinematics.yaml，会在规划时自动用，不要直接调它的 C++。

状态：APPROACH → DESCEND → GRASP → LIFT → DONE。无夹爪则省略 GRASP。

### 实现

1. 在 RViz 拖出安全位姿，写入 `vs_practice/config/waypoints.yaml`（禁止沿用手册里的示例数字）。
2. 确认 `arm_group` 与 `print_interface.py` 一致后：

```bash
roslaunch vs_practice commander_only.launch arm_group:=<你的组名>
```

3. 看 `/vs/commander_state`。规划失败先改 yaml。
4. `rosbag record /joint_states /tf`。连续自动跑两遍。

### 验收

不手动拖目标，脚本能走完全流程。不要改 `abb_driver`。

---

## 步骤 C 眼在手相机与 ArUco 检测

### 目的

让图像成为系统输入。本步只做测量。

### 原理

ArUco 四角点取中心。眼在手相机固连末端。光学系与法兰系不同。

### 实现

1. **不要**再 `roslaunch realsense2_camera` 第二份。`rostopic list | grep -i image`，把 `vi_grab` / RealSense 已有话题写入 `interface.yaml`。
2. 打印或放置 ArUco（DICT_4X4_50，边长约 0.05 m）。
3. `roslaunch vs_practice detect_only.launch image_topic:=<实际话题>`。
4. 看 `/vs/tag_ok`、`/vs/error`，可用 `image_view` 看 `/vs/debug_image`。
5. `rosrun tf tf_echo <ee_link> <camera_optical_frame>`。

### 验收

看见为真，遮挡为假。禁止把像素送给 MoveIt。

---

## 步骤 D 开环视觉引导

### 目的

图像只用一次生成位姿，交给 Commander，作为开环基线。

### 原理

`T_base_tag = T_base_ee * T_ee_cam * T_cam_tag`，只在 APPROACH 入口算一次。运动中途标签再动，轨迹不变。

### 实现

`roslaunch vs_practice vs_practice.launch mode:=open`，然后 `rostopic pub /vs/start std_msgs/String "data: go"`。到位后再读像素，记开环终值误差。

### 验收

能说明图像只用了一次。本关不把误差送进伺服。

---

## 步骤 E 静态视觉闭环（核心）

### 目的

停止规划长轨迹，误差生成运动。这是与现有抓取流程的分界。

### 原理

误差 `e = (u - cx, v - cy)`。简化律 `vx = -λ Z e_u / f_x`，`vy` 同理。看丢则运动清零。伺服段禁止再 `plan()` 一条自由空间长轨迹。

**接口（本机必须先查）：**

- 有关节速度话题 → `servo_mode: joint_velocity`
- 只有 ABB 轨迹（常见）→ `servo_mode: cartesian_increment`（每周期几毫米）。λ 更小。不要用 2 Hz 大位移点冒充闭环。

### 实现

1. 填好 `interface.yaml` 的 `servo_mode`。
2. `roslaunch vs_practice vs_practice.launch mode:=closed`
3. `rostopic pub /vs/start std_msgs/String "data: go"`
4. λ 从很小加到刚振荡再回调。

### 验收

伺服段无一次长轨迹 `plan()`；遮挡后运动为 0。本步是进组演示最低完成线。

---

## 步骤 F 开环 / 闭环对照

同一初始条件，开环与闭环各 ≥5 次。`rosbag record /joint_states /tf /vs/error /vs/state`。计算准（稳态像素误差）、快（调节时间）、稳（振荡/超调）。缺表不算完成。

---

## 步骤 G 运动目标、延迟与三种律

步骤 E 稳定后：标签慢速移动；`image_delay_ms` 取 50/100/150；`law:=p|gain_schedule|predict`。只替换 `image_law()`。

---

## 步骤 H 真机

本机已经在实验室包上。先复现步骤 E。占机短、调参不在臂上盲加 λ。急停按组里规程。不改 `abb_driver`。

---

## 进度

**S 启动+运动指令** → A 清单 → B Commander 流程 → C 检测 → D 开环视觉 → E 速度/增量闭环 ★最低完成线 → F 对照 → G 延迟三律 → H 真机细则

当前：栈已锁定为 Noetic 实验室包。下一步做 **模块 S**（[START_ARM.md](START_ARM.md)），不要先写检测。
