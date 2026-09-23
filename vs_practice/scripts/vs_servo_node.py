#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Closed-loop servo. No plan() of a long trajectory."""

from __future__ import annotations

import sys

import numpy as np
import rospy
from geometry_msgs.msg import Vector3, TwistStamped
from std_msgs.msg import Bool, Float64MultiArray

from vs_practice.image_law import image_law


class ServoNode(object):
    def __init__(self):
        self.enabled = False
        self.tag_ok = False
        self.error = np.zeros(2)
        self.e_prev = np.zeros(2)
        self.lost = 0
        self.hold = 0
        self.fx = float(rospy.get_param("~fx", 600.0))
        self.fy = float(rospy.get_param("~fy", 600.0))
        self.lam = float(rospy.get_param("~lambda", 0.4))
        self.z_hat = float(rospy.get_param("~z_hat", 0.35))
        self.law = rospy.get_param("~law", "p")
        self.delay_s = float(rospy.get_param("~image_delay_ms", 0.0)) / 1000.0
        self.tau = float(rospy.get_param("~tau", 0.1))
        self.eps = float(rospy.get_param("~epsilon_px", 8.0))
        self.hold_need = int(rospy.get_param("~hold_cycles", 15))
        self.lost_abort = int(rospy.get_param("~lost_frames_abort", 20))
        self.step_m = float(rospy.get_param("~cart_step_m", 0.004))
        self.qdot_max = float(rospy.get_param("~qdot_max", 0.15))
        self.mode = rospy.get_param("~servo_mode", "cartesian_increment")
        self.vel_topic = rospy.get_param("~velocity_topic", "")
        rate_hz = float(rospy.get_param("~rate_hz", 20.0))

        self.pub_twist = rospy.Publisher("/vs/ee_twist", TwistStamped, queue_size=1)
        self.pub_qdot = rospy.Publisher("/vs/joint_velocity", Float64MultiArray, queue_size=1)
        self.pub_hold = rospy.Publisher("/vs/hold", Bool, queue_size=1)
        self.hw_vel = None
        if self.mode == "joint_velocity" and self.vel_topic:
            self.hw_vel = rospy.Publisher(self.vel_topic, Float64MultiArray, queue_size=1)

        self.arm = None
        if self.mode == "cartesian_increment":
            import moveit_commander

            moveit_commander.roscpp_initialize(sys.argv)
            group = rospy.get_param("~arm_group", "manipulator")
            self.arm = moveit_commander.MoveGroupCommander(group)
            rospy.loginfo("servo cartesian_increment group=%s step=%.4f m", group, self.step_m)

        rospy.Subscriber("/vs/error", Vector3, self._on_error, queue_size=1)
        rospy.Subscriber("/vs/tag_ok", Bool, self._on_ok, queue_size=1)
        rospy.Subscriber("/vs/servo_enable", Bool, self._on_enable, queue_size=1)
        self.timer = rospy.Timer(rospy.Duration(1.0 / max(rate_hz, 1.0)), self._tick)
        rospy.loginfo("vs_servo mode=%s law=%s lambda=%.3f", self.mode, self.law, self.lam)

    def _on_error(self, msg):
        self.error = np.array([msg.x, msg.y], dtype=float)

    def _on_ok(self, msg):
        self.tag_ok = bool(msg.data)

    def _on_enable(self, msg):
        self.enabled = bool(msg.data)
        self.lost = 0
        self.hold = 0
        if not self.enabled:
            self._publish_twist(np.zeros(6))
            rospy.loginfo("servo disabled")

    def _publish_twist(self, twist6):
        out = TwistStamped()
        out.header.stamp = rospy.Time.now()
        out.twist.linear.x = float(twist6[0])
        out.twist.linear.y = float(twist6[1])
        out.twist.linear.z = float(twist6[2])
        self.pub_twist.publish(out)

    def _apply_cartesian(self, twist6):
        if self.arm is None:
            return
        pose = self.arm.get_current_pose().pose
        # Optical X/Y mapped as base X/Y increment; sign is verified on the real arm.
        pose.position.x += float(np.clip(twist6[0], -1.0, 1.0)) * self.step_m
        pose.position.y += float(np.clip(twist6[1], -1.0, 1.0)) * self.step_m
        self.arm.set_pose_target(pose)
        # Short goal only — do not plan a long free-space path.
        self.arm.set_planning_time(0.2)
        self.arm.go(wait=True)
        self.arm.stop()
        self.arm.clear_pose_targets()

    def _tick(self, _event):
        if not self.enabled:
            return
        if not self.tag_ok:
            self.lost += 1
            self._publish_twist(np.zeros(6))
            if self.lost >= self.lost_abort:
                rospy.logerr("servo ABORT: tag lost")
                self.enabled = False
            return
        self.lost = 0
        twist6 = image_law(
            self.error,
            self.lam,
            self.z_hat,
            self.fx,
            self.fy,
            law=self.law,
            delay_s=self.delay_s,
            tau=self.tau,
            e_prev=self.e_prev,
            dt=1.0 / max(float(self.timer._period.to_sec()), 1e-3) if self.timer._period else 0.05,
        )
        self.e_prev = self.error.copy()
        self._publish_twist(twist6)

        if np.linalg.norm(self.error) < self.eps:
            self.hold += 1
            if self.hold >= self.hold_need:
                self._publish_twist(np.zeros(6))
                self.pub_hold.publish(Bool(data=True))
                self.enabled = False
                rospy.loginfo("servo HOLD")
                return
        else:
            self.hold = 0

        if self.mode == "joint_velocity" and self.hw_vel is not None:
            # Placeholder: publish the two image-space speeds; fill joints after Jacobian is wired.
            msg = Float64MultiArray(data=[float(np.clip(twist6[0], -self.qdot_max, self.qdot_max)),
                                          float(np.clip(twist6[1], -self.qdot_max, self.qdot_max))])
            self.hw_vel.publish(msg)
            self.pub_qdot.publish(msg)
        elif self.mode == "cartesian_increment":
            self._apply_cartesian(twist6)


def main():
    rospy.init_node("vs_servo")
    ServoNode()
    rospy.spin()


if __name__ == "__main__":
    main()
