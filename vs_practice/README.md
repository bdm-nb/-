# vs_practice（ROS 1 Noetic）

旁路练习包：眼在手 ArUco 视觉伺服。放到实验室 catkin 工作空间的 `src/` 下，**不替换** `vi_grab` / `abb_driver` / `robot_ui`。

工作空间根必须是：

```
/home/biand/workspace_ws/src/robot_gripper_9_91/robot_gripper_5_29/robot_gripper
```

## 安装

```bash
WS=/home/biand/workspace_ws/src/robot_gripper_9_91/robot_gripper_5_29/robot_gripper
cp -a vs_practice "$WS/src/vs_practice"
source /opt/ros/noetic/setup.bash
cd "$WS"
catkin build vs_practice
source devel/setup.bash
```

或在本仓库执行 `scripts/install_vs_practice_into_lab_ws.sh`。

每个终端先 `source vs_practice/env.sh`（或按手册手动 source Noetic + `devel`）。

## 先启动实验室臂

完整步骤见仓库根目录 [START_ARM.md](../START_ARM.md)。用现有的 `start.sh` / `start_ui.sh` / `launch_synarm_ui.sh` / `arm_moveit_config`。能在 RViz 里 Execute 一次后再开检测。

## 节点

| 命令 | 作用 |
|---|---|
| `rosrun vs_practice print_interface.py` | 步骤 A：打印规划组、话题、控制器线索 |
| `rosrun vs_practice send_small_motion.py` | 模块 S：下发一次 ≤4 cm 的 Commander 运动 |
| `roslaunch vs_practice send_small_motion.launch` | 同上，launch 版 |
| `roslaunch vs_practice detect_only.launch` | 步骤 C：只检测 |
| `roslaunch vs_practice commander_only.launch` | 步骤 B：只调用 Commander |
| `roslaunch vs_practice vs_practice.launch` | 检测 + 规划 + 伺服 + 状态机 |

启动闭环后：

```bash
rostopic pub /vs/start std_msgs/String "data: go"
```

改 `interface.yaml` 里的 `arm_group`、图像话题、`servo_mode`。路点必须从本机 RViz 抄到 `waypoints.yaml`。
