#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Measure only: ArUco center and pixel error. No MoveIt, no velocity."""

from __future__ import annotations

import collections
import time

import cv2
import numpy as np
import rospy
from cv_bridge import CvBridge
from geometry_msgs.msg import Point, Vector3
from sensor_msgs.msg import CameraInfo, Image
from std_msgs.msg import Bool


def _dictionary(name):
    table = {
        "DICT_4X4_50": cv2.aruco.DICT_4X4_50,
        "DICT_4X4_100": cv2.aruco.DICT_4X4_100,
        "DICT_5X5_50": cv2.aruco.DICT_5X5_50,
        "DICT_6X6_50": cv2.aruco.DICT_6X6_50,
    }
    key = table.get(name, cv2.aruco.DICT_4X4_50)
    return cv2.aruco.getPredefinedDictionary(key)


def _detect(gray, dictionary):
    if hasattr(cv2.aruco, "DetectorParameters_create"):
        params = cv2.aruco.DetectorParameters_create()
        corners, ids, _ = cv2.aruco.detectMarkers(gray, dictionary, parameters=params)
        return corners, ids
    detector = cv2.aruco.ArucoDetector(dictionary, cv2.aruco.DetectorParameters())
    return detector.detectMarkers(gray)


class DetectNode(object):
    def __init__(self):
        self.bridge = CvBridge()
        self.cx = None
        self.cy = None
        self.want_id = int(rospy.get_param("~aruco_id", 0))
        self.dictionary = _dictionary(rospy.get_param("~aruco_dictionary", "DICT_4X4_50"))
        delay_ms = float(rospy.get_param("~image_delay_ms", 0.0))
        self.delay_s = max(delay_ms, 0.0) / 1000.0
        self.queue = collections.deque()

        self.pub_ok = rospy.Publisher("/vs/tag_ok", Bool, queue_size=1)
        self.pub_pixel = rospy.Publisher("/vs/pixel", Point, queue_size=1)
        self.pub_error = rospy.Publisher("/vs/error", Vector3, queue_size=1)
        self.pub_debug = rospy.Publisher("/vs/debug_image", Image, queue_size=1)

        image_topic = rospy.get_param("~image_topic", "/camera/color/image_raw")
        info_topic = rospy.get_param("~camera_info_topic", "/camera/color/camera_info")
        rospy.Subscriber(info_topic, CameraInfo, self._on_info, queue_size=1)
        rospy.Subscriber(image_topic, Image, self._on_image, queue_size=1)
        rospy.loginfo("vs_detect image=%s info=%s delay_ms=%.0f", image_topic, info_topic, delay_ms)

    def _on_info(self, msg):
        if msg.k[0] > 0:
            self.cx = float(msg.k[2])
            self.cy = float(msg.k[5])

    def _measure(self, msg):
        cv_img = self.bridge.imgmsg_to_cv2(msg, desired_encoding="bgr8")
        gray = cv2.cvtColor(cv_img, cv2.COLOR_BGR2GRAY)
        corners, ids = _detect(gray, self.dictionary)
        ok = False
        u = v = 0.0
        if ids is not None:
            for i, marker_id in enumerate(ids.flatten()):
                if int(marker_id) != self.want_id:
                    continue
                pts = corners[i].reshape(-1, 2)
                u, v = pts.mean(axis=0)
                ok = True
                cv2.polylines(cv_img, [pts.astype(np.int32)], True, (0, 255, 0), 2)
                cv2.circle(cv_img, (int(u), int(v)), 4, (0, 0, 255), -1)
                break
        h, w = gray.shape[:2]
        cx = self.cx if self.cx is not None else 0.5 * w
        cy = self.cy if self.cy is not None else 0.5 * h
        cv2.drawMarker(cv_img, (int(cx), int(cy)), (255, 255, 0), cv2.MARKER_CROSS, 24, 1)
        debug = self.bridge.cv2_to_imgmsg(cv_img, encoding="bgr8")
        debug.header = msg.header
        return ok, u, v, cx, cy, debug

    def _on_image(self, msg):
        measured = self._measure(msg)
        now = time.time()
        self.queue.append((now, measured))
        ready = None
        while self.queue and (now - self.queue[0][0]) >= self.delay_s:
            ready = self.queue.popleft()[1]
        if ready is None:
            return
        ok, u, v, cx, cy, debug = ready
        self.pub_ok.publish(Bool(data=bool(ok)))
        self.pub_pixel.publish(Point(x=float(u), y=float(v), z=0.0))
        self.pub_error.publish(Vector3(x=float(u - cx), y=float(v - cy), z=0.0))
        self.pub_debug.publish(debug)


def main():
    rospy.init_node("vs_detect")
    DetectNode()
    rospy.spin()


if __name__ == "__main__":
    main()
