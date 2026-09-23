"""Three interchangeable image-space laws. Only this module changes in step G."""

from __future__ import annotations

import numpy as np

LAW_P = "p"
LAW_GAIN_SCHEDULE = "gain_schedule"
LAW_PREDICT = "predict"


def _p_velocity(e, lam, z_hat, fx, fy):
    e = np.asarray(e, dtype=float).reshape(2)
    fx = max(float(fx), 1.0)
    fy = max(float(fy), 1.0)
    vx = -float(lam) * float(z_hat) * e[0] / fx
    vy = -float(lam) * float(z_hat) * e[1] / fy
    return np.array([vx, vy, 0.0, 0.0, 0.0, 0.0], dtype=float)


def image_law(e, lam, z_hat, fx, fy, law=LAW_P, delay_s=0.0, tau=0.1, e_prev=None, dt=0.02):
    """Return a 6-vector camera twist [vx, vy, vz, wx, wy, wz].

    Step E uses law='p'. Step G switches law only; measurement and limits stay shared.
    """
    e = np.asarray(e, dtype=float).reshape(2)
    if law == LAW_GAIN_SCHEDULE:
        lam_d = float(lam) / (1.0 + float(delay_s) / max(float(tau), 1e-6))
        return _p_velocity(e, lam_d, z_hat, fx, fy)
    if law == LAW_PREDICT:
        prev = np.zeros(2) if e_prev is None else np.asarray(e_prev, dtype=float).reshape(2)
        de = (e - prev) / max(float(dt), 1e-3)
        e_hat = e + de * float(delay_s)
        return _p_velocity(e_hat, lam, z_hat, fx, fy)
    return _p_velocity(e, lam, z_hat, fx, fy)
