from __future__ import annotations

from dataclasses import dataclass, field
from collections import deque
import numpy as np
from simulation import params_system as psys
from simulation import params_model as pmod

@dataclass
class VerticalJointParams:
    system: psys.SystemParams = field(default_factory=psys.SystemParams)
    controller: pmod.MotorControllerParams = field(default_factory=pmod.MotorControllerParams)
    motor: pmod.MotorParams = field(default_factory=pmod.MotorParams)
    gearbox: pmod.GearboxParams = field(default_factory=pmod.GearboxParams)
    screw: pmod.LinearScrewParams = field(default_factory=pmod.LinearScrewParams)
    end_effector: pmod.EndEffectorParams = field(default_factory=pmod.EndEffectorParams)
    encoders: pmod.EncoderParams = field(default_factory=pmod.EncoderParams)

    # Small velocity used to smooth Coulomb/static friction
    friction_smoothing_velocity: float = 1e-3  # [rad/s]


# ============================================================
# State
# ============================================================

@dataclass
class VerticalJointState:
    motor_current: float = 0.0       # i [A]
    motor_angle: float = 0.0         # theta_m [rad]
    motor_speed: float = 0.0         # omega_m [rad/s]
    controller_integral: float = 0.0 # integral of current error
    tau_motor: float = 0.0
    tau_gravity: float = 0.0
    tau_gearbox_friction: float = 0.0
    tau_screw_friction: float = 0.0
    net_torque: float = 0.0
    alpha: float = 0.0
    j_eq: float = 0.0


# ============================================================
# Component-level functions
# ============================================================

def motor_to_linear_gain(params: VerticalJointParams) -> float:
    """
    Returns kx such that:
        x = kx * theta_motor
    """
    pitch = params.screw.pitch
    reduction = params.gearbox.reduction_ratio
    return pitch / (2.0 * np.pi * reduction)


def reflected_screw_friction_motor_side(
    params: VerticalJointParams,
) -> tuple[float, float]:
    """
    Convert screw linear friction parameters to motor-side torque parameters.

    Linear viscous friction:
        F = b_linear * v

    Since:
        v = kx * omega_motor
        tau_motor = F * kx

    Therefore:
        tau = b_linear * kx^2 * omega_motor

    Coulomb friction:
        tau_c_motor = F_c * kx
    """
    kx = motor_to_linear_gain(params)

    b_motor = params.screw.viscous_friction_linear * kx**2
    tau_c_motor = params.screw.coulomb_friction_linear * kx

    return b_motor, tau_c_motor


def equivalent_motor_side_inertia(params: VerticalJointParams) -> float:
    """
    Total motor-side inertia.
    """
    kx = motor_to_linear_gain(params)

    j_motor = params.motor.rotor_inertia
    j_gearbox = params.gearbox.inertia_motor_side
    j_screw = params.screw.inertia_motor_side
    j_mass = params.end_effector.mass * kx**2

    return j_motor + j_gearbox + j_screw + j_mass


def smooth_coulomb_friction(
    omega: float,
    viscous: float,
    coulomb: float,
    omega_eps: float,
) -> float:
    """
    Smooth approximation of viscous + Coulomb/static friction.

    tau = b*omega + tau_c*tanh(omega/omega_eps)

    This avoids discontinuity at zero speed and is suitable for numerical
    simulation and later parameter identification.
    """
    return viscous * omega + coulomb * np.tanh(omega / omega_eps)


def gravity_torque_motor_side(params: VerticalJointParams) -> float:
    """
    Gravity torque reflected to motor side.

    If positive motor torque lifts the mass upward, gravity opposes positive motion.
    """
    kx = motor_to_linear_gain(params)
    gt = params.end_effector.mass * params.system.gravity * kx
    return gt


def controller_step(
    desired_current: float,
    measured_current: float,
    motor_speed: float,
    state: VerticalJointState,
    params: VerticalJointParams,
) -> float:
    """
    PI current controller.

    Input:
        desired_current: delayed current reference [A]

    Output:
        motor drive voltage [V]

    Includes simple feedforward compensation:
        R*i_ref + Ke*omega

    This makes the controller behave like a current controller rather than
    just a raw voltage amplifier.
    """
    dt = params.system.dt
    ctrl = params.controller
    motor = params.motor
    iSaturation = ctrl.integral_saturation
    ff_R = ctrl.ff_winding_resistance

    error = desired_current - measured_current
    state.controller_integral += error * dt
    state.controller_integral = np.clip(state.controller_integral, -iSaturation, iSaturation)

    voltage = (
        ctrl.kp * error
        + ctrl.ki * state.controller_integral
        + ff_R * desired_current
        + motor.back_emf_constant * motor_speed
    )

    voltage = np.clip(voltage, -ctrl.voltage_limit, ctrl.voltage_limit)

    return voltage


def motor_electrical_step(
    drive_voltage: float,
    state: VerticalJointState,
    params: VerticalJointParams,
) -> None:
    """
    DC motor electrical dynamics:

        L di/dt = V - R i - Ke omega
    """
    dt = params.system.dt
    motor = params.motor

    di_dt = (
        drive_voltage
        - motor.winding_resistance * state.motor_current
        - motor.back_emf_constant * state.motor_speed
    ) / motor.winding_inductance

    state.motor_current += dt * di_dt


def mechanical_step(
    state: VerticalJointState,
    params: VerticalJointParams,
) -> None:
    """
    Motor-side mechanical dynamics:

        J_eq * domega/dt =
            tau_motor
            - tau_gravity
            - tau_gearbox_friction
            - tau_screw_friction
    """
    dt = params.system.dt
    omega = state.motor_speed

    motor = params.motor
    gearbox = params.gearbox

    state.j_eq = equivalent_motor_side_inertia(params)

    state.tau_motor = motor.torque_constant * state.motor_current

    state.tau_gravity = gravity_torque_motor_side(params)

    state.tau_gearbox_friction = smooth_coulomb_friction(
        omega=omega,
        viscous=gearbox.viscous_friction,
        coulomb=gearbox.coulomb_friction,
        omega_eps=params.friction_smoothing_velocity,
    )

    screw_viscous_motor, screw_coulomb_motor = reflected_screw_friction_motor_side(params)

    tau_screw_friction = smooth_coulomb_friction(
        omega=omega,
        viscous=screw_viscous_motor,
        coulomb=screw_coulomb_motor,
        omega_eps=params.friction_smoothing_velocity,
    )

    state.net_torque = (
        state.tau_motor
        - state.tau_gravity
        - state.tau_gearbox_friction
        - state.tau_screw_friction
    )

    state.alpha = state.net_torque / state.j_eq

    # Semi-implicit Euler integration
    state.motor_speed += dt * state.alpha
    state.motor_angle += dt * state.motor_speed


def ideal_kinematics(
    state: VerticalJointState,
    params: VerticalJointParams,
) -> dict:
    """
    Converts motor-side state into linear axis state.
    """
    kx = motor_to_linear_gain(params)

    x = kx * state.motor_angle
    v = kx * state.motor_speed

    return {
        "motor_angle": state.motor_angle,
        "motor_speed": state.motor_speed,
        "linear_position": x,
        "linear_speed": v,
    }


def quantize(value: float, quantum: float | None) -> float:
    if quantum is None or quantum <= 0.0:
        return value

    return quantum * np.round(value / quantum)


def encoder_measurements(
    state: VerticalJointState,
    params: VerticalJointParams,
    rng: np.random.Generator,
) -> dict:
    """
    Motor and linear encoder measurements.
    """
    enc = params.encoders
    kin = ideal_kinematics(state, params)

    motor_angle_meas = kin["motor_angle"]
    linear_position_meas = kin["linear_position"]

    if enc.motor_encoder_noise_std > 0.0:
        motor_angle_meas += rng.normal(0.0, enc.motor_encoder_noise_std)

    if enc.linear_encoder_noise_std > 0.0:
        linear_position_meas += rng.normal(0.0, enc.linear_encoder_noise_std)

    motor_angle_meas = quantize(
        motor_angle_meas,
        enc.motor_encoder_quantization,
    )

    linear_position_meas = quantize(
        linear_position_meas,
        enc.linear_encoder_quantization,
    )

    return {
        "motor_encoder": motor_angle_meas,
        "linear_encoder": linear_position_meas,
    }


# ============================================================
# Full simulator
# ============================================================

class VerticalPrismaticJointSimulator:
    def __init__(
        self,
        params: VerticalJointParams,
        initial_state: VerticalJointState | None = None,
        seed: int = 1,
    ) -> None:
        self.params = params
        self.state = initial_state or VerticalJointState()
        self.rng = np.random.default_rng(seed)

        dt = params.system.dt
        latency_s = params.controller.latency_ms * 1e-3
        delay_steps = int(round(latency_s / dt))

        self.current_command_buffer = deque(
            [0.0] * max(delay_steps, 1),
            maxlen=max(delay_steps, 1),
        )

        self.time = 0.0

    def step(self, desired_current: float) -> dict:
        """
        Advance simulation by one fixed timestep.

        Input:
            desired_current [A]

        Returns:
            dictionary of true states and measured outputs
        """
        p = self.params
        s = self.state

        # ----------------------------------------------------
        # Controller latency
        # ----------------------------------------------------
        self.current_command_buffer.append(desired_current)
        delayed_current_command = self.current_command_buffer[0]

        # ----------------------------------------------------
        # Motor current controller
        # ----------------------------------------------------
        drive_voltage = controller_step(
            desired_current=delayed_current_command,
            measured_current=s.motor_current,
            motor_speed=s.motor_speed,
            state=s,
            params=p,
        )

        # ----------------------------------------------------
        # DC motor electrical dynamics
        # ----------------------------------------------------
        motor_electrical_step(
            drive_voltage=drive_voltage,
            state=s,
            params=p,
        )

        # ----------------------------------------------------
        # Mechanical dynamics
        # ----------------------------------------------------
        mechanical_step(
            state=s,
            params=p,
        )

        # ----------------------------------------------------
        # Outputs
        # ----------------------------------------------------
        kin = ideal_kinematics(s, p)
        enc = encoder_measurements(s, p, self.rng)

        j_eq = equivalent_motor_side_inertia(p)
        kx = motor_to_linear_gain(p)

        output = {
            "time": self.time,
            "desired_current": desired_current,
            "delayed_current_command": delayed_current_command,
            "drive_voltage": drive_voltage,
            "motor_current": s.motor_current,
            "motor_angle": s.motor_angle,
            "motor_speed": s.motor_speed,
            "linear_position": kin["linear_position"],
            "linear_speed": kin["linear_speed"],
            "motor_encoder": enc["motor_encoder"],
            "linear_encoder": enc["linear_encoder"],
            "equivalent_inertia_motor_side": j_eq,
            "motor_to_linear_gain": kx,
            "tau_motor": s.tau_motor,
            "tau_gravity": s.tau_gravity,
            "tau_gearbox_friction": s.tau_gearbox_friction,
            "tau_screw_friction": s.tau_screw_friction,
            "net_torque": s.net_torque,
            "motor_acceleration": s.alpha,
            "equivalent_inertia_motor_side": s.j_eq,
            "reflected_mass_inertia": p.end_effector.mass * kx**2,
        }

        self.time += p.system.dt

        return output

    def simulate(self, desired_current_profile: np.ndarray) -> dict:
        """
        Simulate a complete input profile.

        desired_current_profile:
            array of desired current commands [A]

        Returns:
            dict of arrays
        """
        samples = []

        for current_command in desired_current_profile:
            samples.append(self.step(float(current_command)))

        keys = samples[0].keys()

        return {
            key: np.array([sample[key] for sample in samples])
            for key in keys
        }
