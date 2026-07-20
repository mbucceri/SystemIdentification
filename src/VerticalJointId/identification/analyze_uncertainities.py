import numpy as np
import matplotlib.pyplot as plt
from scipy.signal import savgol_filter


def compute_smoothed_kinematics(t, x, window_length=101, polyorder=3):
    """
    Compute smoothed position, velocity and acceleration.

    window_length must be odd and smaller than len(x).
    """
    dt = np.mean(np.diff(t))

    if window_length >= len(x):
        window_length = len(x) - 1

    if window_length % 2 == 0:
        window_length += 1

    x_smooth = savgol_filter(x, window_length, polyorder)
    v_smooth = savgol_filter(
        x,
        window_length,
        polyorder,
        deriv=1,
        delta=dt,
    )
    a_smooth = savgol_filter(
        x,
        window_length,
        polyorder,
        deriv=2,
        delta=dt,
    )

    return x_smooth, v_smooth, a_smooth


def error_metrics(e):
    return {
        "bias": np.mean(e),
        "mae": np.mean(np.abs(e)),
        "rmse": np.sqrt(np.mean(e**2)),
        "p95_abs": np.percentile(np.abs(e), 95),
        "max_abs": np.max(np.abs(e)),
    }


def print_metrics(name, e):
    m = error_metrics(e)
    print(f"\n{name}")
    for k, v in m.items():
        print(f"  {k:10s}: {v:.6e}")


def build_operating_masks(v, a):
    abs_v = np.abs(v)
    abs_a = np.abs(a)

    low_speed = abs_v < np.percentile(abs_v, 20)
    high_speed = abs_v > np.percentile(abs_v, 80)
    high_accel = abs_a > np.percentile(abs_a, 80)

    # Reversal region: very low speed and acceleration not negligible
    reversal = low_speed & high_accel

    positive_motion = v > np.percentile(abs_v, 30)
    negative_motion = v < -np.percentile(abs_v, 30)

    return {
        "all": np.ones_like(v, dtype=bool),
        "low_speed": low_speed,
        "high_speed": high_speed,
        "high_accel": high_accel,
        "reversal": reversal,
        "positive_motion": positive_motion,
        "negative_motion": negative_motion,
    }


def diagnostic_scatter_plots(t, e, x, v, a, current):
    plots = [
        ("time [s]", t, "residual [mm]", e*1000),
        ("position [m]", x, "residual [mm]", e*1000),
        ("velocity [m/s]", v, "residual [mm]", e*1000),
        ("|velocity| [m/s]", np.abs(v), "residual [mm]", e*1000),
        ("acceleration [m/s²]", a, "residual [mm]", e*1000),
        ("motor current [A]", current, "residual [mm]", e*1000),
    ]

    for xlabel, xdata, ylabel, ydata in plots:
        plt.figure()
        plt.scatter(xdata, ydata, s=3, alpha=0.4)
        plt.xlabel(xlabel)
        plt.ylabel(ylabel)
        plt.grid(True)
        plt.title(f"Residual vs {xlabel}")
    
    plt.show()