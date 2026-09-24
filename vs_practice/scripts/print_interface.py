#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Step A: print planning groups, topics, and controller clues. No motion."""

from __future__ import annotations

import os
import sys


def _print_topics():
    import rospy

    print("=== published topics ===")
    try:
        topics = rospy.get_published_topics()
    except Exception as exc:
        print("  (master not reachable: %s)" % exc)
        return []
    for name, typ in sorted(topics):
        print("  %s  [%s]" % (name, typ))
    return topics


def _interesting(topics):
    keys = ("image", "camera", "joint", "traj", "velocity", "follow", "tf")
    print("=== likely vision / control topics ===")
    found = False
    for name, typ in sorted(topics):
        low = name.lower()
        if any(k in low for k in keys):
            print("  %s  [%s]" % (name, typ))
            found = True
    if not found:
        print("  (none matched; is start.sh / camera running?)")


def _params():
    import rospy

    print("=== params ===")
    for key in ("/robot_description", "/robot_description_semantic"):
        print("  %s: %s" % (key, "yes" if rospy.has_param(key) else "MISSING"))


def _services():
    import rospy

    print("=== controller-related services ===")
    try:
        names = rospy.get_published_topics()  # keep import side-effect
        del names
        import rosservice

        srvs = rosservice.get_service_list()
    except Exception as exc:
        print("  (cannot list services: %s)" % exc)
        return
    hits = [s for s in srvs if "controller" in s or "follow_joint" in s]
    if not hits:
        print("  (no controller_manager / follow_joint_trajectory service)")
        print("  ABB via abb_driver often has only a trajectory action.")
        return
    for s in sorted(hits):
        print("  %s" % s)


def _moveit():
    print("=== MoveIt 1 groups ===")
    try:
        import moveit_commander

        moveit_commander.roscpp_initialize([])
        robot = moveit_commander.RobotCommander()
        groups = robot.get_group_names()
        print("  planning_frame: %s" % robot.get_planning_frame())
        print("  groups: %s" % groups)
        for g in groups:
            mg = robot.get_group(g)
            print("  - %s  ee=%s  joints=%s" % (g, mg.get_end_effector_link(), mg.get_active_joints()))
    except Exception as exc:
        print("  moveit not ready: %s" % exc)
        print("  start the lab arm first: ./start.sh or roslaunch arm_moveit_config demo.launch")


def main():
    print("ROS_DISTRO=%s" % os.environ.get("ROS_DISTRO", "?"))
    print("ROS_MASTER_URI=%s" % os.environ.get("ROS_MASTER_URI", "?"))
    if os.environ.get("ROS_DISTRO") not in (None, "noetic"):
        print("WARNING: this package is written for ROS 1 Noetic.")

    import rospy

    rospy.init_node("vs_print_interface", anonymous=True)
    topics = _print_topics()
    print("")
    _interesting(topics or [])
    print("")
    _params()
    print("")
    _services()
    print("")
    _moveit()
    print("")
    print("Copy group / topic / ee_link names into vs_practice/config/interface.yaml")
    return 0


if __name__ == "__main__":
    sys.exit(main())
