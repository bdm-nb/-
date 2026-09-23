#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""MoveIt 1 Commander calls only. No driver, no C++."""

from __future__ import annotations

import sys

import rospy
import moveit_commander
from geometry_msgs.msg import Pose, PoseStamped
from std_msgs.msg import String


def _pose_from_dict(data):
    pose = Pose()
    p = data["position"]
    o = data["orientation"]
    pose.position.x = float(p["x"])
    pose.position.y = float(p["y"])
    pose.position.z = float(p["z"])
    pose.orientation.x = float(o["x"])
    pose.orientation.y = float(o["y"])
    pose.orientation.z = float(o["z"])
    pose.orientation.w = float(o["w"])
    return pose


class CommanderNode(object):
    def __init__(self):
        moveit_commander.roscpp_initialize(sys.argv)
        group_name = rospy.get_param("~arm_group", "manipulator")
        self.arm = moveit_commander.MoveGroupCommander(group_name)
        self.arm.set_planning_time(5.0)
        self.state_pub = rospy.Publisher("/vs/commander_state", String, queue_size=10)
        rospy.Subscriber("/vs/approach_pose", PoseStamped, self._on_approach, queue_size=1)
        rospy.Subscriber("/vs/cmd", String, self._on_cmd, queue_size=1)
        rospy.loginfo("vs_commander group=%s ee=%s", group_name, self.arm.get_end_effector_link())

    def _log(self, text):
        rospy.loginfo("%s", text)
        self.state_pub.publish(String(data=text))

    def go_pose(self, pose):
        self.arm.set_pose_target(pose)
        ok = bool(self.arm.go(wait=True))
        self.arm.stop()
        self.arm.clear_pose_targets()
        self._log("go_pose ok=%s" % ok)
        return ok

    def descend(self, dz):
        current = self.arm.get_current_pose().pose
        lowered = Pose()
        lowered.position.x = current.position.x
        lowered.position.y = current.position.y
        lowered.position.z = current.position.z + float(dz)
        lowered.orientation = current.orientation
        waypoints = [current, lowered]
        plan, fraction = self.arm.compute_cartesian_path(waypoints, 0.01, 0.0)
        self._log("cartesian fraction=%.3f" % fraction)
        if fraction < 0.95:
            return False
        ok = bool(self.arm.execute(plan, wait=True))
        self.arm.stop()
        return ok

    def run_open_loop(self):
        wp = rospy.get_param("~waypoints")
        self._log("APPROACH")
        if not self.go_pose(_pose_from_dict(wp["approach"])):
            self._log("ERROR approach")
            return
        self._log("DESCEND")
        if not self.descend(wp.get("descend_dz", -0.05)):
            self._log("ERROR descend")
            return
        self._log("DONE")

    def _on_approach(self, msg):
        self._log("APPROACH from /vs/approach_pose")
        self.go_pose(msg.pose)

    def _on_cmd(self, msg):
        if msg.data == "open_loop":
            self.run_open_loop()
        elif msg.data == "stop":
            self.arm.stop()
            self._log("STOP")


def main():
    rospy.init_node("vs_commander")
    node = CommanderNode()
    if rospy.get_param("~run_on_start", False):
        rospy.sleep(1.0)
        node.run_open_loop()
    rospy.spin()


if __name__ == "__main__":
    main()
