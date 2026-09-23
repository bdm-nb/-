#!/usr/bin/env bash
# Copy vs_practice into the innermost lab catkin workspace and build it.
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
WS="${LAB_WS:-/home/biand/workspace_ws/src/robot_gripper_9_91/robot_gripper_5_29/robot_gripper}"

if [[ ! -d "$WS/src" ]]; then
  echo "Lab workspace not found: $WS/src" >&2
  echo "Set LAB_WS if your path differs." >&2
  exit 1
fi

rm -rf "$WS/src/vs_practice"
cp -a "$REPO_ROOT/vs_practice" "$WS/src/vs_practice"
# shellcheck disable=SC1091
source /opt/ros/noetic/setup.bash
cd "$WS"
catkin build vs_practice
# shellcheck disable=SC1091
source "$WS/devel/setup.bash"
echo "Installed. Next: start the lab arm, then rosrun vs_practice print_interface.py"
