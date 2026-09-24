#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Send one small Cartesian motion on the already-running lab arm (MoveIt 1).

Does not start the driver. Run after start.sh / demo.launch / start_ui.sh.
Rejects steps larger than 4 cm. This is a Commander call, not a driver.
"""

from __future__ import annotations

import math
import sys

import rospy
import moveit_commander
from geometry_msgs.msg import Pose


MAX_STEP_M = 0.04


def _print_state(arm):
    joints = arm.get_current_joint_values()
    pose = arm.get_current_pose().pose
    rospy.loginfo("group=%s ee=%s", arm.get_name(), arm.get_end_effector_link())
    rospy.loginfo("joints=%s", ["%.4f" % j for j in joints])
    rospy.loginfo(
        "pose xyz=(%.4f, %.4f, %.4f) quat=(%.4f, %.4f, %.4f, %.4f)",
        pose.position.x,
        pose.position.y,
        pose.position.z,
        pose.orientation.x,
        pose.orientation.y,
        pose.orientation.z,
        pose.orientation.w,
    )
    return pose


def _offset(pose, dx, dy, dz):
    out = Pose()
    out.position.x = pose.position.x + dx
    out.position.y = pose.position.y + dy
    out.position.z = pose.position.z + dz
    out.orientation = pose.orientation
    return out


def main():
    moveit_commander.roscpp_initialize(sys.argv)
    rospy.init_node("vs_send_small_motion", anonymous=True)

    group = rospy.get_param("~group", "manipulator")
    dx = float(rospy.get_param("~dx", 0.0))
    dy = float(rospy.get_param("~dy", 0.0))
    dz = float(rospy.get_param("~dz", 0.02))
    dry_run = bool(rospy.get_param("~dry_run", True))
    vel = float(rospy.get_param("~vel_scale", 0.1))
    step = math.sqrt(dx * dx + dy * dy + dz * dz)
    if step > MAX_STEP_M + 1e-9:
        rospy.logerr("refusing step %.3f m > %.3f m; use a smaller dx/dy/dz", step, MAX_STEP_M)
        return 2

    arm = moveit_commander.MoveGroupCommander(group)
    arm.set_max_velocity_scaling_factor(max(0.05, min(vel, 0.3)))
    arm.set_max_acceleration_scaling_factor(0.1)
    arm.set_planning_time(5.0)

    current = _print_state(arm)
    target = _offset(current, dx, dy, dz)
    rospy.loginfo(
        "target xyz=(%.4f, %.4f, %.4f)  delta=(%.4f, %.4f, %.4f) dry_run=%s",
        target.position.x,
        target.position.y,
        target.position.z,
        dx,
        dy,
        dz,
        dry_run,
    )
    if dry_run:
        rospy.logwarn("dry_run=true: no motion. rerun with _dry_run:=false to execute.")
        return 0

    arm.set_pose_target(target)
    ok = bool(arm.go(wait=True))
    arm.stop()
    arm.clear_pose_targets()
    rospy.loginfo("go ok=%s", ok)
    _print_state(arm)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main() or 0)
