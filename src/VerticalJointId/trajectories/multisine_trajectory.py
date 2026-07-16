
import numpy as np

def smooth_start_envelope(t: np.ndarray, ramp_time: float) -> np.ndarray:
    """
    Smooth envelope from 0 to 1 to avoid exciting the system
    with an artificial discontinuity at t = 0.
    """
    envelope = np.ones_like(t)

    ramp_mask = t < ramp_time
    tau = t[ramp_mask] / ramp_time

    envelope[ramp_mask] = 0.5 * (1.0 - np.cos(np.pi * tau))

    return envelope

def generate_current_excitation(
    t: np.ndarray,
    freqs_and_phases: np.ndarray,  # [(frequency Hz, phase), ...]
    bias_current: float,
    amplitude: float,
    ramp_time: float,
    current_min: float,
    current_max: float,
) -> np.ndarray:
    """
    Multisine signal around a bias value and a ramp-up envelope. The signal is a sum of
    sinusoids with specified frequencies and phases.

    Output:
        desired array of the sine series evaluated at times t.
    """

    signal = np.zeros_like(t)

    for f, phi in freqs_and_phases:
        signal += np.sin(2.0 * np.pi * f * t + phi)

    # Normalize to approximately [-1, 1]
    signal /= np.max(np.abs(signal))

    envelope = smooth_start_envelope(t, ramp_time)

    current = envelope * (bias_current + amplitude * signal) 

    current = np.clip(current, current_min, current_max)

    return current