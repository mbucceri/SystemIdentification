import numpy as np

def generate_sin_trajectory(t, amplitude, frequency, phase):
    """
    Generate a sinusoidal trajectory.

    Parameters:
    - t: Time array
    - amplitude: Amplitude of the sine wave
    - frequency: Frequency of the sine wave (in Hz)
    - phase: Phase shift of the sine wave (in radians)

    Returns:
    - trajectory: Sinusoidal trajectory array
    """
    trajectory = amplitude * np.sin(2 * np.pi * frequency * t + phase)
    return trajectory

