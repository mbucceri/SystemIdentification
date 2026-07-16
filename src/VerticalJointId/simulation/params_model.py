from dataclasses import dataclass, field

# ============================================================
# Parameters
# ============================================================

@dataclass
class MotorControllerParams:
    latency_ms: float = 2.0
    kp: float = 0.1
    ki: float = 500.0
    ff_winding_resistance: float = 1    # R [Ohm]
    integral_saturation: float = 1.0
    voltage_limit: float = 48.0


@dataclass
class MotorParams:
    torque_constant: float = 0.08       # Kt [Nm/A]
    back_emf_constant: float = 0.08     # Ke [V/(rad/s)]
    rotor_inertia: float = 2.0e-4       # Jm [kg m^2]
    winding_resistance: float = 1.2     # R [ohm]
    winding_inductance: float = 1.5e-3  # L [H]


@dataclass
class GearboxParams:
    reduction_ratio: float = 25.0       # N = omega_motor / omega_screw
    inertia_motor_side: float = 1.0e-4  # [kg m^2], already motor-side
    viscous_friction: float = 1.0e-4    # [Nm s/rad], motor-side
    coulomb_friction: float = 0.02      # [Nm], motor-side


@dataclass
class LinearScrewParams:
    pitch: float = 0.02                # [m/rev]
    viscous_friction_linear: float = 30.0   # [N s/m]
    coulomb_friction_linear: float = 15.0   # [N]
    inertia_motor_side: float = 0.0         # optional [kg m^2]


@dataclass
class EndEffectorParams:
    mass: float = 30  # [kg]


@dataclass
class EncoderParams:
    motor_encoder_noise_std: float = 1e-4    # [rad]
    linear_encoder_noise_std: float = 1e-5   # [m]
    motor_encoder_quantization: float | None = None   # [rad]
    linear_encoder_quantization: float | None = None  # [m]