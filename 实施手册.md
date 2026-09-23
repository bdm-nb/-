# 眼在手上机械臂视觉伺服闭环控制实施手册

**文件性质：** 分步实施指导书（目的—原理—实现—验收）  
**适用对象：** 控制专业本科；Python 调用 MoveIt Commander；已进组、尚未承担正式课题  
**仿真模型：** 使用课设工作空间中的臂与夹爪，不使用实验室内部 URDF  
**语言约定：** 应用层用 Python；不要求编写 Commander 库或厂家 driver  

下文每一步均按同一结构书写：**目的（为什么做）、原理（在算什么）、实现（具体写什么、调什么）、验收（怎样才算完成）。** 未通过验收不得进入下一步。

---

## 0. 项目在做什么（实施视角）

本项目要做出一条与课设“检测一次再规划”不同的链路：

1. 用 Commander **调用** MoveIt，把末端送到相机能看见 ArUco 的位置（开环、粗、快）。
2. **停止规划**，每一帧用标签中心相对图像中心的像素误差生成速度。
3. 速度经雅可比变成关节速度，写入 `ros2_control`，臂一动，下一帧误差就变，形成闭环。
4. 用表格比较开环与闭环；再给图像加延迟、让标签慢速移动，比较三种控制律。

视觉只提供误差。思考全部在控制：增益、限幅、延迟、停机。Commander 只需会调用，不必研读其源码。

建议新建包：`vs_practice`。规划组名以本机 SRDF 为准，写作 `<arm_group>`、`<gripper_group>`。

节点关系：

```
/camera/image_raw --> vs_detect --> /vs/error, /vs/tag_ok
/joint_states, /tf --> vs_servo --> 关节速度 --> ros2_control 速度控制器
vs_fsm --APPROACH--> vs_commander --> 轨迹控制器
vs_fsm --SERVO--> vs_servo
```

---

## 步骤 A 环境确认与信息登记

### 目的

避免在包名、规划组、控制器名都未知时写代码。本步只产生一张接口清单。

### 原理

后续每个节点都要写死：规划组、关节顺序、图像话题、控制器名。这些来自已有 description / moveit_config / bringup。

### 实现

1. `source /opt/ros/$ROS_DISTRO/setup.bash`，进入 `~/workspace_ws`，执行 `colcon build && source install/setup.bash`。
2. 启动课设 bringup 或 demo。
3. 另开终端执行并抄结果：

```bash
ros2 topic list
ros2 topic echo /joint_states --once
ros2 control list_controllers
```

4. 打开 SRDF / `moveit_controllers.yaml`，登记：ROS 发行版、臂规划组、夹爪规划组、末端 link、基座 frame、轨迹控制器名、关节顺序。
5. 在 RViz 里用 MotionPlanning 拖一次末端并 Execute，确认仿真在动。

### 验收

清单填满；轨迹控制器为 `active`；RViz 执行一次成功。不通过则只排启动问题。

---

## 步骤 B 用 Python 调用 Commander 完成开环流程

### 目的

把第八章的“会调用”落成状态机骨架。以后视觉只替换目标从哪来。

### 原理

Commander 是 MoveIt 客户端。`set_pose_target` 表示希望末端到哪；`plan()` 搜索路径；`execute()` 把轨迹交给轨迹控制器。调用者不是驱动器。状态：APPROACH → DESCEND → GRASP → LIFT → DONE。

### 实现

1. 在 RViz 拖出安全位姿，写入 `vs_practice/config/waypoints.yaml`（数字必须本机试过）。
2. 新建 `vs_commander_node.py`，按第八章 Python API 调用 `set_pose_target`、`go`、`compute_cartesian_path`、夹爪开合。
3. 每步打印状态与返回码。
4. `ros2 bag record /joint_states /tf`。
5. 连续自动运行两遍。

### 验收

不手动拖目标，脚本能走完全流程。规划失败先改 yaml，不要改 MoveIt 源码。

---

## 步骤 C 眼在手相机与 ArUco 检测

### 目的

让图像成为系统输入。本步只做测量，不做控制。

### 原理

ArUco 四角点取中心为特征。眼在手相机固连末端。光学系与法兰系不同，TF 必须与 URDF 一致。

### 实现

1. 末端增加相机 link，Gazebo 发布 `/camera/image_raw` 与 `/camera/camera_info`。
2. 场景放置 ArUco（如 DICT_4X4_50，边长 0.05 m）。
3. 节点 `vs_detect` 发布 `/vs/tag_ok`、`/vs/pixel`、`/vs/error`。
4. `tf2_echo` 核对手眼。

### 验收

看见标签为真，遮挡为假。禁止把像素送给 MoveIt。

---

## 步骤 D 开环视觉引导

### 目的

图像只用一次生成位姿，交给 Commander，作为开环基线。

### 原理

`T_base_tag = T_base_ee * T_ee_cam * T_cam_tag`，只在 APPROACH 入口算一次。运动中途标签再动，轨迹不变。

### 实现

等待 `/vs/tag_ok`，算一次 approach_pose，调用步骤 B 的 `go()`。到位后再读像素，记开环终值误差。

### 验收

能说明图像只用了一次。本关不把误差送进速度环。

---

## 步骤 E 静态视觉速度闭环（核心）

### 目的

停止规划，误差生成速度，写入 ros2_control。这是与课设抓取的分界。

### 原理

误差 `e = (u - cx, v - cy)`。简化律 `vx = -λ eu`，`vy = -λ ev`。`qdot = J+ V`，限幅。看丢则速度清零。伺服段禁止 `plan()`。

### 实现

1. 切到速度控制器。
2. `vs_servo` 以约 50 Hz 计算误差、速度、关节速度并发布。
3. 状态机 APPROACH 成功后进入 SERVO。
4. λ 从很小加到刚振荡再回调。

### 验收

伺服段零次 plan；遮挡后速度为 0。本步是进组演示最低完成线。

---

## 步骤 F 开环 / 闭环对照

同一初始条件，开环与闭环各重复不少于 5 次。用 bag 计算准（稳态像素误差）、快（调节时间）、稳（振荡/超调）。缺表不算完成。

---

## 步骤 G 运动目标、延迟与三种律

在步骤 E 稳定后：标签慢速移动；软件加入 50/100/150 ms 延迟；比较固定比例、按延迟降增益、一拍预测。只替换 `image_law()`。

---

## 步骤 H 真机（可选）

用实验室官方 ROS 包，不抄课设 driver。先复现步骤 E。占机短、调参回仿真。

---

## 进度

A → B → C → D → E（最低完成线）→ F → G（含金量）→ H

当前全部未开始。第八章 Python 调用跑通后做 A、B。
