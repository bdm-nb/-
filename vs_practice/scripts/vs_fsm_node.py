#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""APPROACH (Commander, once) then SERVO (error → motion)."""

from __future__ import annotations

import rospy
from std_msgs.msg import Bool, String


class FsmNode(object):
    def __init__(self):
        self.mode = rospy.get_param("~mode", "closed")  # open | closed
        self.state = "IDLE"
        self.tag_ok = False
        self.pub_state = rospy.Publisher("/vs/state", String, queue_size=10, latch=True)
        self.pub_enable = rospy.Publisher("/vs/servo_enable", Bool, queue_size=1)
        self.pub_cmd = rospy.Publisher("/vs/cmd", String, queue_size=1)
        rospy.Subscriber("/vs/tag_ok", Bool, self._on_ok, queue_size=1)
        rospy.Subscriber("/vs/hold", Bool, self._on_hold, queue_size=1)
        rospy.Subscriber("/vs/start", String, self._on_start, queue_size=1)
        rospy.Subscriber("/vs/approach_done", String, self._on_approach_done, queue_size=1)
        self._set("IDLE")

    def _set(self, state):
        self.state = state
        self.pub_state.publish(String(data=state))
        rospy.loginfo("vs_fsm %s", state)

    def _on_ok(self, msg):
        self.tag_ok = bool(msg.data)

    def _on_hold(self, msg):
        if msg.data and self.state == "SERVO":
            self.pub_enable.publish(Bool(data=False))
            self._set("HOLD")

    def _on_start(self, _msg):
        if self.state not in ("IDLE", "HOLD", "DONE", "ERROR"):
            rospy.logwarn("busy in %s", self.state)
            return
        self._set("WAIT_TAG")
        deadline = rospy.Time.now() + rospy.Duration(10.0)
        rate = rospy.Rate(10)
        while not rospy.is_shutdown() and rospy.Time.now() < deadline:
            if self.tag_ok:
                break
            rate.sleep()
        if not self.tag_ok:
            self._set("ERROR")
            rospy.logerr("no tag for APPROACH")
            return
        self._set("APPROACH")
        self.pub_cmd.publish(String(data="open_loop"))
        # Commander prints DONE on /vs/commander_state; we also allow a timeout fallback.
        rospy.Timer(rospy.Duration(0.5), self._watch_commander, oneshot=False)

    def _watch_commander(self, event):
        if self.state != "APPROACH":
            event.timer.shutdown()
            return

    def _on_approach_done(self, msg):
        self._after_approach(msg.data)

    def after_commander_state(self, text):
        self._after_approach(text)

    def _after_approach(self, text):
        if self.state != "APPROACH":
            return
        if "ERROR" in text:
            self._set("ERROR")
            return
        if "DONE" not in text and "ok=True" not in text:
            return
        if self.mode == "open":
            self._set("DONE")
            return
        self._set("SERVO")
        self.pub_enable.publish(Bool(data=True))


def main():
    rospy.init_node("vs_fsm")
    node = FsmNode()

    def _on_commander(msg):
        node.after_commander_state(msg.data)

    rospy.Subscriber("/vs/commander_state", String, _on_commander, queue_size=10)
    rospy.spin()


if __name__ == "__main__":
    main()
