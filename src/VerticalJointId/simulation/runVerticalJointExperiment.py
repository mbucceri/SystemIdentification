from __future__ import annotations

import numpy as np
import matplotlib.pyplot as plt
import argparse
import pathlib
import utils.loadsave

from VerticalJointId.simulation import params_system as SystemParams 
from VerticalJointId.simulation import params_model as ModelParams

# ============================================================
# Adapt these imports to your actual project names
# ============================================================
from VerticalJointId.simulation.sim_ground_truth import (
    VerticalJointParams,
    VerticalJointState,
    VerticalPrismaticJointSimulator,
    motor_to_linear_gain,
)


# ============================================================
# Main simulation script
# ============================================================

def main() -> None:
    # --------------------------------------------------------
    # 0. Argument parsing
    # --------------------------------------------------------
    parser = argparse.ArgumentParser(description="Run the vertical joint ground truth simulation model using the input data")
    parser.add_argument("-if", "--inputFile", help="The input data file", type=pathlib.Path, default="./inputData.csv")
    parser.add_argument("-of", "--outputFile", help="The output file containing the simulated data", type=pathlib.Path, default="./groundTruth.csv")
    parser.add_argument("-p", "--plot", help="Plot data",  action='store_true')

    args = parser.parse_args()

    # --------------------------------------------------------
    # 1. Get input data
    # --------------------------------------------------------
    inputData = utils.loadsave.load_array(args.inputFile)

    # --------------------------------------------------------
    # 1. Setup ground truth simulation 
    # --------------------------------------------------------
    initial_state = VerticalJointState(
        motor_current=0.0,
        motor_angle=0.0,
        motor_speed=0.0,
        controller_integral=0.0,
    )

    sim = VerticalPrismaticJointSimulator(
        params=VerticalJointParams(),
        initial_state=initial_state,
        seed=10,
    )

    # --------------------------------------------------------
    # 2. Run the simulation
    # --------------------------------------------------------
    simulatedData = sim.simulate(inputData["signal"])

    # Enrich simulated data with input signals
    simulatedData["time"] = inputData["time"]
    simulatedData["commanded_current"] = inputData["signal"]

    # --------------------------------------------------------
    # 3. Save and plot results
    # --------------------------------------------------------
    utils.loadsave.save_dict(args.outputFile, simulatedData, "This is the header")

    if args.plot:
        plot_results(simulatedData)

def plot_results(
    data: dict,
) -> None:
    plt.figure()
    plt.plot(data["time"], data["linear_position"], label="true position")
    plt.plot(data["time"], data["linear_encoder"], label="linear encoder", alpha=0.7)
    plt.xlabel("Time [s]")
    plt.ylabel("Linear position [m]")
    plt.legend()
    plt.grid(True)

    plt.figure()
    plt.plot(data["time"], data["motor_current"], label="motor current")
    plt.plot(data["time"], data["desired_current"], "--", label="desired current")
    plt.plot(data["time"], data["delayed_current_command"], ":", label="delayed command")
    plt.xlabel("Time [s]")
    plt.ylabel("Current [A]")
    plt.legend()
    plt.grid(True)

    plt.figure()
    plt.plot(data["time"], data["drive_voltage"], ":", label="drive voltage")
    plt.xlabel("Time [s]")
    plt.ylabel("Voltage [V]")
    plt.legend()
    plt.grid(True)

    plt.figure()
    plt.plot(data["time"], data["net_torque"], label ="net torque")
    plt.plot(data["time"], data["tau_motor"], label="motor torque")
    plt.plot(data["time"], data["tau_gravity"], label="gravity torque")
    plt.plot(data["time"], data["tau_gearbox_friction"], label="torque gearbox friction")
    plt.plot(data["time"], data["tau_screw_friction"],  label="torque screw friction")
    plt.plot(data["time"], data["tau_screw_friction"],  label="torque screw friction")
    plt.xlabel("Time [s]")
    plt.ylabel("Torque [Nm]")
    plt.legend()
    plt.grid(True)

    plt.show()


if __name__ == "__main__":
    main()