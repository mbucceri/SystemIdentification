import argparse
import pathlib
import numpy as np
import matplotlib.pyplot as plt



def generate_multisine_data(
    t: np.ndarray,
    freqs_and_phases: np.ndarray,  # [(frequency Hz, phase), ...]
    bias: float,
    amplitude: float,
) -> np.ndarray:
    """
    Multisine signal around a bias value. The signal is a sum of
    sinusoids with specified frequencies and phases.

    Output:
        desired array of the sine series evaluated at times t.
    """

    signal = np.zeros_like(t)

    for f, phi in freqs_and_phases:
        signal += np.sin(2.0 * np.pi * f * t + phi)

    # Normalize to approximately [-1, 1]
    signal /= np.max(np.abs(signal))

    data = bias + amplitude * signal 

    return data


parser = argparse.ArgumentParser(description="Generate multisine data acording to the given arguments and save them to a file")
parser.add_argument("-ts", "--timeStep", help="The time step of the generated data", type=float, default=0.001)
parser.add_argument("-et", "--endTime", help="The end time of the generated data", type=float, default=10.0)
parser.add_argument("-b", "--bias", help="The bias value before the step input.", type=float, default=0.0)
parser.add_argument("-f", "--frequencies", help="An array of frequencies [Hz] in the format omega_1 omega_2 ... omega_n", type=float, nargs="+", default=1.0 )
parser.add_argument("-ph", "--phases", help="An array of phases [rad] in the format phase_1 phase_2 ... phase_n", type=float, nargs="+", default = 0.0)
parser.add_argument("-a", "--amplitude", help="The signal amplitude (max - min) over the bias", type=float, default = 1.0)
parser.add_argument("-of", "--outputFile", help="The file where to save data", type=pathlib.Path, default="./MultiSineData.dat")
parser.add_argument("-p", "--plot", help="Plot data",  action='store_true')

args = parser.parse_args()

t = np.arange(0.0, args.endTime, args.timeStep)
f = args.frequencies
ph = args.phases
if np.shape(f) != np.shape(ph):
    print ("Error. the frequency and the phases argumenst shall have the same lenght")
    exit

data = generate_multisine_data(t, np.column_stack((f, ph)), args.bias, args.amplitude)

packedData = np.column_stack((t, data))

strHeader = f"Data generated with generateMultisineData.py script."
strHeader += str.format("\nTimeStep= {ts} EndTime = {et} bias = {b} amplitude = {a}\nfrequencies = {f}\nphases = {ph}", ts=args.timeStep, et=args.endTime, b=args.bias, a=args.amplitude, f=f, ph=ph)
strHeader += "\ntime, data"
np.savetxt(fname=args.outputFile, X=packedData, header=strHeader, delimiter=",")

if args.plot:
    plt.figure()
    plt.plot(t, data, label="output data")
    plt.xlabel("Time [s]")
    plt.ylabel("data")
    plt.legend()
    plt.grid(True)

    plt.show()

