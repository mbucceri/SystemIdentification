from dataclasses import dataclass, field

@dataclass
class SystemParams:
    dt: float = 1e-3          # fixed simulation timestep [s]
    gravity: float = 9.80665  # [m/s^2]