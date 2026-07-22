from __future__ import annotations

import argparse
import numpy as np
import matplotlib.pyplot as plt
from scipy.optimize import least_squares

import VerticalJointId.simulation.params_system as SystemParams 
import VerticalJointId.simulation.params_model as ModelParams
import analyze_uncertainities as AnalyzeUncertainities
import utils.loadsave


# ============================================================
# Adapt these imports to your actual project names
# ============================================================
from VerticalJointId.simulation.sim_ground_truth import (
    VerticalJointParams,
    VerticalJointState,
    VerticalPrismaticJointSimulator,
    motor_to_linear_gain,
)

from VerticalJointId.simulation.sim_simplified import (
    SimplifiedVerticalJointParams,
    SimplifiedVerticalJointState,
    SimplifiedVerticalPrismaticJointSimulator,
)


# ============================================================
# Excitation trajectory
# ============================================================

def holding_current_ground_truth(params: VerticalJointParams) -> float:
    """
    Current required to hold the vertical axis approximately still
    against gravity, ignoring friction and acceleration.

        Kt * i_hold = m*g*kx

    therefore:

        i_hold = m*g*kx / Kt
    """
    kx = motor_to_linear_gain(params)

    return (
        params.end_effector.mass
        * params.system.gravity
        * kx
        / params.motor.torque_constant
    )


#def generate_current_excitation(
#    t: np.ndarray,
#    bias_current: float,
#    amplitude: float,
#    current_min: float,
#    current_max: float,
#) -> np.ndarray:
#    """
#    Multisine current excitation around a bias current.
#
#    The signal contains low and medium frequencies so that the model
#    can observe slow gravity/friction effects and acceleration effects.
#
#    Output:
#        desired current command [A] for the ground-truth model.
#    """
#
#    # Frequencies in Hz. Keep them moderate for a first test.
#    freqs_phases = np.array([(0.2, 0.0), (0.5, 1.1), (0.9, 2.2), (1.7, 0.7), (2.8, 1.9), (4.0, 2.8)])
#    current = multisine_trajectory.generate_current_excitation(
#        t=t,
#        freqs_and_phases=freqs_phases,
#        bias_current=bias_current,
#        amplitude=amplitude,
#        ramp_time=1.0,
#        current_min=current_min,
#        current_max=current_max,
#    )
#
#    return current


# ============================================================
# Ground truth data generation
# ============================================================


    """
#def build_ground_truth_params() -> VerticalJointParams:
#    Configure the detailed model.
#
#    Replace these values with the tuned values you are currently using.
#    # """
#    params = VerticalJointParams()
# 
#    params.system.dt = 1e-3
#    params.system.gravity = 9.80665
#    params.controller.latency_ms = 3.0
#    params.controller.kp = 20.0
#    params.controller.ki = 500.0
#    params.controller.voltage_limit = 48.0
#    params.motor.torque_constant = 0.08
#    params.motor.back_emf_constant = 0.08
#    params.motor.rotor_inertia = 2.0e-4
#    params.motor.winding_resistance = 1.2
#    params.motor.winding_inductance = 1.5e-3
#    params.gearbox.reduction_ratio = 25.0
#    params.gearbox.inertia_motor_side = 1.0e-4
#    params.gearbox.viscous_friction = 1.0e-4
#    params.gearbox.coulomb_friction = 0.02
#    params.screw.pitch = 0.005
#    params.screw.viscous_friction_linear = 30.0
#    params.screw.coulomb_friction_linear = 15.0
#    params.screw.inertia_motor_side = 0.0
#    params.end_effector.mass = 4.0
#    params.encoders.linear_encoder_noise_std = 2.0e-5
#    params.encoders.motor_encoder_noise_std = 1.0e-4
#    return params

def load_ground_truth_dataset(path:str ) -> dict:

    print(f"Loading ground truth (real experiment) data: {path}")
    gtData = utils.loadsave.load_array(path)
    return gtData

# ============================================================
# Simplified model setup
# ============================================================

def ideal_current_force_gain_from_plate_data(
    efficiency: float = 1.0,
) -> float:
    """
    Ideal linear force per ampere.

        motor torque = Kt * i

        screw torque after gearbox = Kt*i*N*eta

        linear force = screw_torque * 2*pi / pitch

    Therefore:

        Kf = Kt * N * eta * 2*pi / pitch
    """
    return (
        ModelParams.MotorParams.torque_constant
        * ModelParams.GearboxParams.reduction_ratio
        * efficiency
        * 2.0
        * np.pi
        / ModelParams.LinearScrewParams.pitch
    )


def build_simplified_params_from_plate_data(
) -> SimplifiedVerticalJointParams:
    """
    Fixed configuration of the simplified model.

    The values inside dynamics will be overwritten during identification.
    """
    params = SimplifiedVerticalJointParams()

    # params.system.dt = SystemParams.SystemParams.dt
    # params.system.gravity = SystemParams.SystemParams.gravity

    # params.kinematics.gearbox_reduction_ratio = ModelParams.GearboxParams.reduction_ratio
    # params.kinematics.screw_pitch = ModelParams.LinearScrewParams.pitch

    # # Some initial nominal values.
    # params.dynamics.load_mass = 0.85*ModelParams.LinearScrewParams.load_mass  # [kg]
    # params.dynamics.equivalent_mass = 0.85* ModelParams.LinearScrewParams.equivalent_mass  # [kg]
    # params.dynamics.current_force_gain = ideal_current_force_gain_from_plate_data(
    #     efficiency=0.8,
    # )
    # params.dynamics.viscous_friction = 0.8 * ModelParams.LinearScrewParams.viscous_friction_linear
    # params.dynamics.coulomb_friction = 0.8 * ModelParams.LinearScrewParams.coulomb_friction_linear
    # params.dynamics.friction_smoothing_velocity = 1.0e-4

    # # For identification, usually do not add noise in the simplified model.
    # params.encoders.linear_encoder_noise_std = 0.0
    # params.encoders.motor_encoder_noise_std = 0.0

    return params


# ============================================================
# Theta mapping
# ============================================================

def theta_to_params(
    theta: np.ndarray,
    params: SimplifiedVerticalJointParams,
) -> None:
    """
    theta = [
        equivalent_mass,
        current_force_gain,
        viscous_friction,
        coulomb_friction,
    ]
    """
    params.dynamics.equivalent_mass = theta[0]
    params.dynamics.current_force_gain = theta[1]
    params.dynamics.viscous_friction = theta[2]
    params.dynamics.coulomb_friction = theta[3]


def params_to_theta(
    params: SimplifiedVerticalJointParams,
) -> np.ndarray:
    return np.array(
        [
            params.dynamics.equivalent_mass,
            params.dynamics.current_force_gain,
            params.dynamics.viscous_friction,
            params.dynamics.coulomb_friction,
        ],
        dtype=float,
    )


# ============================================================
# Simulation wrapper for optimizer
# ============================================================

def run_simplified_model(
    theta: np.ndarray,
    measured_motor_current: np.ndarray,
    base_params: SimplifiedVerticalJointParams,
    initial_position: float,
    initial_speed: float = 0.0,
) -> dict:
    """
    Run simplified model with candidate theta.

    Important:
    - Create a fresh params object or overwrite a local copy per iteration.
    - Create a fresh simulator per iteration.
    - Reset initial state per iteration.
    """

    # Make a lightweight copy by rebuilding from base values manually.
    # This avoids accidental state carry-over during optimization.
    params = SimplifiedVerticalJointParams()

    params.system.dt = base_params.system.dt
    params.system.gravity = base_params.system.gravity

    params.kinematics.gearbox_reduction_ratio = (
        base_params.kinematics.gearbox_reduction_ratio
    )
    params.kinematics.screw_pitch = base_params.kinematics.screw_pitch

    params.dynamics.load_mass = base_params.dynamics.load_mass
    params.dynamics.friction_smoothing_velocity = (
        base_params.dynamics.friction_smoothing_velocity
    )

    params.encoders.linear_encoder_noise_std = 0.0
    params.encoders.motor_encoder_noise_std = 0.0

    theta_to_params(theta, params)

    initial_state = SimplifiedVerticalJointState(
        linear_position=initial_position,
        linear_speed=initial_speed,
    )

    sim = SimplifiedVerticalPrismaticJointSimulator(
        params=params,
        initial_state=initial_state,
        seed=1,
    )

    return sim.simulate(measured_motor_current)


# ============================================================
# Residual function
# ============================================================

def residual_function(
    theta: np.ndarray,
    measured_motor_current: np.ndarray,
    measured_linear_position: np.ndarray,
    base_params: SimplifiedVerticalJointParams,
    initial_position: float,
) -> np.ndarray:
    """
    Residual used by scipy.optimize.least_squares.

    For first attempt, use only linear position residual.

    Later you can add:
    - velocity residual
    - motor encoder residual
    - current residual, if the simplified model includes electrical dynamics
    """

    sim_data = run_simplified_model(
        theta=theta,
        measured_motor_current=measured_motor_current,
        base_params=base_params,
        initial_position=initial_position,
        initial_speed=0.0,
    )

    simulated_position = sim_data["linear_position"]

    residual = simulated_position - measured_linear_position

    # Scale residual to millimeters to improve numerical conditioning.
    # 0.001 m = 1 mm
    residual_scaled = residual / 1.0e-3

    return residual_scaled


# ============================================================
# Main identification script
# ============================================================

def main() -> None:
    # --------------------------------------------------------
    # 0. Argument parsing
    # --------------------------------------------------------
    arg_parser = argparse.ArgumentParser(description="Vertical joint system identification")
    arg_parser.add_argument("--gtPath", "-gt", type=str, required=True, help="Path to the ground truth dataset file")
    arg_parser.add_argument("--thetaPath", "-th", type=str, required=False, help="Path to the identified theta values file")
    args = arg_parser.parse_args()
    if args.gtPath is None:
        raise ValueError("Ground truth dataset path (--gtPath) is required.")
    
    # --------------------------------------------------------
    # 1. Load real experiment data data
    # --------------------------------------------------------
    gt = load_ground_truth_dataset(args.gtPath)

    # gt_params = gt["params"]
    t = gt["time"]

    # Simplified model input: measured motor current, not desired current.
    measured_motor_current = gt["motor_current"]

    # Synthetic measurement: linear encoder.
    measured_linear_position = gt["linear_encoder"]

    # Initial condition from measurement
    initial_position = measured_linear_position[0]

    # --------------------------------------------------------
    # 2. Build simplified model base params
    # --------------------------------------------------------
    simplified_params = build_simplified_params_from_plate_data()

    theta_initial = params_to_theta(simplified_params)

    print("\nInitial theta:")
    print_theta(theta_initial)

    # --------------------------------------------------------
    # 3. Define bounds
    # --------------------------------------------------------
    lower_bounds = np.array(
        [
            0.1,       # equivalent_mass [kg]
            100.0,     # current_force_gain [N/A]
            0.0,       # viscous_friction [N s/m]
            0.0,       # coulomb_friction [N]
        ],
        dtype=float,
    )

    upper_bounds = np.array(
        [
            100000.0,    # equivalent_mass [kg]
            10000.0,    # current_force_gain [N/A]
            10000.0,     # viscous_friction [N s/m]
            1000.0,     # coulomb_friction [N]
        ],
        dtype=float,
    )

    # --------------------------------------------------------
    # 4. Run least_squares
    # --------------------------------------------------------
    result = least_squares(
        fun=residual_function,
        x0=theta_initial,
        bounds=(lower_bounds, upper_bounds),
        args=(
            measured_motor_current,
            measured_linear_position,
            simplified_params,
            initial_position,
        ),
        x_scale=np.array([5.0, 2000.0, 50.0, 20.0]),
        verbose=2,
        max_nfev=100, 
    )

    theta_identified = result.x

    print("\nOptimization status:")
    print(result.message)

    print("\nIdentified theta:")
    print_theta(theta_identified)

    # --------------------------------------------------------
    # 5. Compare ground truth and identified simplified model
    # --------------------------------------------------------
    identified_data = run_simplified_model(
        theta=theta_identified,
        measured_motor_current=measured_motor_current,
        base_params=simplified_params,
        initial_position=initial_position,
        initial_speed=0.0,
    )

    plot_results(
        t=gt["time"],
        desired_current=gt["desired_current"],
        measured_motor_current=measured_motor_current,
        measured_position=measured_linear_position,
        identified_position=identified_data["linear_position"],
    )

    # --------------------------------------------------------
    # 5. Analyze the residual pattern
    # --------------------------------------------------------
    e_linear_position = measured_linear_position - identified_data["linear_position"]
    
    # Smoot measured position and derive speed and acceleration (on smoothed data)
    x_smooth, v, a = AnalyzeUncertainities.compute_smoothed_kinematics(gt["time"], measured_linear_position)

    # Build operating masks to get region of: reversal speed, hig/low speed and accel, positive/negative motion
    masks = AnalyzeUncertainities.build_operating_masks(v, a)

    for name, mask in masks.items():
        AnalyzeUncertainities.print_metrics(name, e_linear_position[mask])

    # --------------------------------------------------------
    # 6. Plot the residual pattern
    # --------------------------------------------------------
    AnalyzeUncertainities.diagnostic_scatter_plots(gt["time"], e_linear_position, x_smooth, v, a, identified_data["motor_current"])

def print_theta(theta: np.ndarray) -> None:
    names = [
        "equivalent_mass [kg]",
        "current_force_gain [N/A]",
        "viscous_friction [N s/m]",
        "coulomb_friction [N]",
    ]

    for name, value in zip(names, theta):
        print(f"  {name:30s}: {value: .6g}")


def plot_results(
    t: np.ndarray,
    desired_current: np.ndarray,
    measured_motor_current: np.ndarray,
    measured_position: np.ndarray,
    identified_position: np.ndarray,
) -> None:
    position_error = identified_position - measured_position

    plt.figure()
    plt.plot(t, desired_current, label="desired current command")
    plt.plot(t, measured_motor_current, label="measured motor current")
    plt.xlabel("Time [s]")
    plt.ylabel("Current [A]")
    plt.grid(True)
    plt.legend()

    plt.figure()
    plt.plot(t, measured_position, label="ground truth linear encoder")
    plt.plot(t, identified_position, "--", label="identified simplified model")
    plt.xlabel("Time [s]")
    plt.ylabel("Linear position [m]")
    plt.grid(True)
    plt.legend()

    plt.figure()
    plt.plot(t, position_error * 1000.0)
    plt.xlabel("Time [s]")
    plt.ylabel("Position error [mm]")
    plt.grid(True)

    plt.show()

if __name__ == "__main__":
    main()