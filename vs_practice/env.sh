# Source this in every new WSL terminal before roslaunch / rosrun.
#   source /path/to/vs_practice/env.sh
export WS="${LAB_WS:-/home/biand/workspace_ws/src/robot_gripper_9_91/robot_gripper_5_29/robot_gripper}"
# shellcheck disable=SC1091
source /opt/ros/noetic/setup.bash
if [[ -f "$WS/devel/setup.bash" ]]; then
  # shellcheck disable=SC1091
  source "$WS/devel/setup.bash"
else
  echo "missing $WS/devel/setup.bash — catkin build in the innermost robot_gripper first" >&2
fi
cd "$WS" || exit 1
echo "WS=$WS  ROS_DISTRO=${ROS_DISTRO:-?}  pwd=$(pwd)"
