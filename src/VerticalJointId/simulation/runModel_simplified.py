from __future__ import annotations

import numpy as np
import matplotlib.pyplot as plt
import argparse
import pathlib
import utils.loadsave

from VerticalJointId.simulation import params_system as SystemParams 
from VerticalJointId.simulation import params_model as ModelParams

import VerticalJointId.simulation.sim_simplified as simpleSim 

# ============================================================
# Main simulation script
# ============================================================

def main() -> None:
    # --------------------------------------------------------
    # 0. Argument parsing
    # --------------------------------------------------------
    parser = argparse.ArgumentParser(description="Run the vertical joint simplified simulation model using the input data")
    parser.add_argument("-if", "--inputFile", help="The input data file", type=pathlib.Path, default="./inputData.csv")
    parser.add_argument("-of", "--outputFile", help="The output file containing the simulated data", type=pathlib.Path, default="./groundTruth.csv")
    parser.add_argument("-p", "--plot", help="Plot data",  action='store_true')

    args = parser.parse_args()

    # --------------------------------------------------------
    # 1. Get input data
    # --------------------------------------------------------
    inputData = utils.loadsave.load_array(args.inputFile)

    # --------------------------------------------------------
    # 1. Setup simplified simulation 
    # --------------------------------------------------------
    initial_state = simpleSim.SimplifiedVerticalJointState(
        linear_position=0.0,
        linear_speed=0.0)

    sim = simpleSim.SimplifiedVerticalPrismaticJointSimulator(
        params=simpleSim.SimplifiedVerticalJointParams(),
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
    plt.xlabel("Time [s]")
    plt.ylabel("Current [A]")
    plt.legend()
    plt.grid(True)

    plt.figure()
    plt.plot(data["time"], data["linear_acceleration"], ":", label="linear acceleration")
    plt.xlabel("Time [s]")
    plt.ylabel("Acceleration [m/s^2]")
    plt.legend()
    plt.grid(True)

    plt.figure()
    plt.plot(data["time"], data["force_motor"], label ="force motor")
    plt.plot(data["time"], data["force_gravity"], label="gravity force")
    plt.plot(data["time"], data["force_friction"], label="friction force")
    plt.plot(data["time"], data["net_force"], label="net force")
    plt.xlabel("Time [s]")
    plt.ylabel("Force [N]")
    plt.legend()
    plt.grid(True)

    plt.show()


if __name__ == "__main__":
    main()