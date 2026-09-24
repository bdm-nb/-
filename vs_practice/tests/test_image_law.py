#!/usr/bin/env python3
"""Pure-python checks for the three image laws (no ROS required)."""

from __future__ import annotations

import os
import sys
import unittest

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src"))
sys.path.insert(0, ROOT)

from vs_practice.image_law import LAW_GAIN_SCHEDULE, LAW_P, LAW_PREDICT, image_law


class ImageLawTests(unittest.TestCase):
    def test_p_opposes_error(self):
        twist = image_law([20.0, -10.0], lam=0.5, z_hat=0.4, fx=600.0, fy=600.0, law=LAW_P)
        self.assertLess(twist[0], 0.0)
        self.assertGreater(twist[1], 0.0)
        self.assertEqual(list(twist[2:]), [0.0, 0.0, 0.0, 0.0])

    def test_gain_schedule_smaller_than_p(self):
        e = [30.0, 0.0]
        p = image_law(e, 1.0, 0.4, 500.0, 500.0, law=LAW_P)
        g = image_law(e, 1.0, 0.4, 500.0, 500.0, law=LAW_GAIN_SCHEDULE, delay_s=0.15, tau=0.1)
        self.assertLess(abs(g[0]), abs(p[0]))

    def test_predict_uses_previous_error(self):
        now = image_law([10.0, 0.0], 1.0, 0.4, 400.0, 400.0, law=LAW_PREDICT, delay_s=0.1, e_prev=[0.0, 0.0], dt=0.05)
        frozen = image_law([10.0, 0.0], 1.0, 0.4, 400.0, 400.0, law=LAW_PREDICT, delay_s=0.1, e_prev=[10.0, 0.0], dt=0.05)
        self.assertLess(now[0], frozen[0])


if __name__ == "__main__":
    unittest.main()
