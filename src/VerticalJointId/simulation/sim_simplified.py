from __future__ import annotations

from dataclasses import dataclass, field
import numpy as np
import VerticalJointId.simulation.params_model as ModelParams

# ============================================================
# Parameters
# ============================================================

@dataclass
class SimplifiedSystemParams:
    dt: float = 1e-3
    gravity: float = 9.80665


@dataclass
class SimplifiedKinematicParams:
    """
    These parameters are used only to convert between motor-side
    and linear-side quantities.

    The dynamic model itself is linear-side.
    """

    # The following params are set by using the ground-truth model's parameters, to keep consistency
    # and because they are not subjected to system identification. For these, using plate data is safe...
    gearbox_reduction_ratio: float = ModelParams.GearboxParams.reduction_ratio
    screw_pitch: float = ModelParams.LinearScrewParams.pitch  # [m/rev]


@dataclass
class SimplifiedDynamicParams:
    """
    Parameters of the simplified model.

    This is the parameter set you may later identify.
    """
    load_mass: float = 30.0             # M_load [kg], for gravity
    equivalent_mass: float = 100*load_mass       # M_eq [kg]
    current_force_gain: float = (
        ModelParams.MotorParams.torque_constant *
        SimplifiedKinematicParams.gearbox_reduction_ratio *
        2 * np.pi / SimplifiedKinematicParams.screw_pitch)
    
    viscous_friction: float = 30.0     # b_eq [N s/m]
    coulomb_friction: float = 15.0     # F_c [N]
    friction_smoothing_velocity: float = 1e-4  # v_eps [m/s]


@dataclass
class SimplifiedEncoderParams:
    linear_encoder_noise_std: float = 0.0
    motor_encoder_noise_std: float = 0.0

    linear_encoder_quantization: float | None = None
    motor_encoder_quantization: float | None = None

    linear_encoder_bias: float = 0.0
    motor_encoder_bias: float = 0.0


@dataclass
class SimplifiedVerticalJointParams:
    system: SimplifiedSystemParams = field(default_factory=SimplifiedSystemParams)
    kinematics: SimplifiedKinematicParams = field(default_factory=SimplifiedKinematicParams)
    dynamics: SimplifiedDynamicParams = field(default_factory=SimplifiedDynamicParams)
    encoders: SimplifiedEncoderParams = field(default_factory=SimplifiedEncoderParams)


# ============================================================
# State
# ============================================================

@dataclass
class SimplifiedVerticalJointState:
    linear_position: float = 0.0  # x [m]
    linear_speed: float = 0.0     # v [m/s]


# ============================================================
# Utility functions
# ============================================================

def motor_to_linear_gain(params: SimplifiedVerticalJointParams) -> float:
    """
    Returns kx such that:

        x = kx * theta_motor

    where:
        x           = linear position [m]
        theta_motor = motor angle [rad]
    """
    pitch = params.kinematics.screw_pitch
    reduction = params.kinematics.gearbox_reduction_ratio

    return pitch / (2.0 * np.pi * reduction)


def linear_to_motor_angle(
    linear_position: float,
    params: SimplifiedVerticalJointParams,
) -> float:
    """
    Converts linear position to equivalent motor angle.
    """
    kx = motor_to_linear_gain(params)
    return linear_position / kx


def linear_to_motor_speed(
    linear_speed: float,
    params: SimplifiedVerticalJointParams,
) -> float:
    """
    Converts linear velocity to equivalent motor angular speed.
    """
    kx = motor_to_linear_gain(params)
    return linear_speed / kx


def smooth_coulomb_friction(
    velocity: float,
    coulomb_friction: float,
    smoothing_velocity: float,
) -> float:
    """
    Smooth Coulomb friction model:

        F_c * tanh(v / v_eps)

    This avoids a discontinuous sign(v), making the model more suitable
    for numerical simulation and optimization.
    """
    return coulomb_friction * np.tanh(velocity / smoothing_velocity)


def quantize(value: float, quantum: float | None) -> float:
    if quantum is None or quantum <= 0.0:
        return value

    return quantum * np.round(value / quantum)


# ============================================================
# Component-level simplified model functions
# ============================================================

def current_to_linear_force(
    motor_current: float,
    params: SimplifiedVerticalJointParams,
) -> float:
    """
    Simplified current-to-linear-force model:

        F_motor = K_f * i_m

    K_f may be known from motor/gear/screw data or identified directly.
    """
    return params.dynamics.current_force_gain * motor_current


def gravity_force(
    params: SimplifiedVerticalJointParams,
) -> float:
    """
    Gravity force on vertical axis.

    Positive x is upward, so gravity opposes positive motion.
    """
    return params.dynamics.load_mass * params.system.gravity


def equivalent_linear_friction(
    linear_speed: float,
    params: SimplifiedVerticalJointParams,
) -> float:
    """
    Single equivalent linear-side friction model.

    F_friction =
        b_eq * v
        + F_c * tanh(v / v_eps)
    """
    dyn = params.dynamics

    viscous = dyn.viscous_friction * linear_speed

    coulomb = smooth_coulomb_friction(
        velocity=linear_speed,
        coulomb_friction=dyn.coulomb_friction,
        smoothing_velocity=dyn.friction_smoothing_velocity,
    )

    return viscous + coulomb


def mechanical_step(
    motor_current: float,
    state: SimplifiedVerticalJointState,
    params: SimplifiedVerticalJointParams,
) -> dict:
    """
    Simplified vertical linear-axis dynamics:

        M_eq * x_ddot =
            K_f * i_m
            - M_load * g
            - b_eq * x_dot
            - F_c * tanh(x_dot / v_eps)

    Integration:
        semi-implicit Euler
    """
    dt = params.system.dt
    dyn = params.dynamics

    x = state.linear_position
    v = state.linear_speed

    force_motor = current_to_linear_force(
        motor_current=motor_current,
        params=params,
    )

    force_gravity = gravity_force(params)

    force_friction = equivalent_linear_friction(
        linear_speed=v,
        params=params,
    )

    net_force = force_motor - force_gravity - force_friction

    acceleration = net_force / dyn.equivalent_mass

    # Semi-implicit Euler
    v = v + dt * acceleration
    x = x + dt * v

    state.linear_speed = v
    state.linear_position = x

    return {
        "force_motor": force_motor,
        "force_gravity": force_gravity,
        "force_friction": force_friction,
        "net_force": net_force,
        "linear_acceleration": acceleration,
    }


def encoder_measurements(
    state: SimplifiedVerticalJointState,
    params: SimplifiedVerticalJointParams,
    rng: np.random.Generator,
) -> dict:
    """
    Simplified encoder measurements.

    In identification mode, you may disable noise and compare directly
    against measured ground-truth outputs.
    """
    enc = params.encoders

    linear_position = state.linear_position
    motor_angle = linear_to_motor_angle(
        linear_position=linear_position,
        params=params,
    )

    linear_meas = linear_position + enc.linear_encoder_bias
    motor_meas = motor_angle + enc.motor_encoder_bias

    if enc.linear_encoder_noise_std > 0.0:
        linear_meas += rng.normal(0.0, enc.linear_encoder_noise_std)

    if enc.motor_encoder_noise_std > 0.0:
        motor_meas += rng.normal(0.0, enc.motor_encoder_noise_std)

    linear_meas = quantize(
        linear_meas,
        enc.linear_encoder_quantization,
    )

    motor_meas = quantize(
        motor_meas,
        enc.motor_encoder_quantization,
    )

    return {
        "linear_encoder": linear_meas,
        "motor_encoder": motor_meas,
    }


# ============================================================
# Full simplified simulator
# ============================================================

class SimplifiedVerticalPrismaticJointSimulator:
    """
    Simplified model used for parameter identification.

    Compared to the ground-truth model, this model intentionally does NOT include:

    - motor controller latency
    - PI current control
    - motor electrical dynamics
    - separate motor, gearbox and screw friction
    - gearbox-side inertia split
    - screw-side inertia split

    Instead, it uses:

    - measured motor current as direct input
    - one equivalent current-to-force gain
    - one equivalent mass
    - one equivalent viscous friction
    - one equivalent Coulomb friction at the linear joint
    """

    def __init__(
        self,
        params: SimplifiedVerticalJointParams,
        initial_state: SimplifiedVerticalJointState | None = None,
        seed: int = 1,
    ) -> None:
        self.params = params
        self.state = initial_state or SimplifiedVerticalJointState()
        self.rng = np.random.default_rng(seed)
        self.time = 0.0

    def step(self, motor_current: float) -> dict:
        """
        Advance simulation by one fixed timestep.

        Input:
            motor_current [A]

        Returns:
            dictionary of model states and outputs
        """
        p = self.params
        s = self.state

        force_terms = mechanical_step(
            motor_current=motor_current,
            state=s,
            params=p,
        )

        motor_angle = linear_to_motor_angle(
            linear_position=s.linear_position,
            params=p,
        )

        motor_speed = linear_to_motor_speed(
            linear_speed=s.linear_speed,
            params=p,
        )

        enc = encoder_measurements(
            state=s,
            params=p,
            rng=self.rng,
        )

        output = {
            "time": self.time,
            "motor_current": motor_current,

            "linear_position": s.linear_position,
            "linear_speed": s.linear_speed,

            "motor_angle": motor_angle,
            "motor_speed": motor_speed,

            "linear_encoder": enc["linear_encoder"],
            "motor_encoder": enc["motor_encoder"],

            **force_terms,
        }

        self.time += p.system.dt

        return output

    def simulate(self, motor_current_profile: np.ndarray) -> dict:
        """
        Simulate a complete measured-current profile.

        motor_current_profile:
            array of measured motor current values [A]

        Returns:
            dict of arrays
        """
        samples = []

        for motor_current in motor_current_profile:
            samples.append(self.step(float(motor_current)))

        keys = samples[0].keys()

        return {
            key: np.array([sample[key] for sample in samples])
            for key in keys
        }