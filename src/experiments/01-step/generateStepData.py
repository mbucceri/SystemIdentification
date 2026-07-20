import argparse
import pathlib
import numpy as np
import matplotlib.pyplot as plt


parser = argparse.ArgumentParser(description="Generate step data acording to the given arguments and save them to a file")
parser.add_argument("-ts", "--timeStep", help="The time step of the generated data", type=float, default=0.001)
parser.add_argument("-et", "--endTime", help="The end time of the generated data", type=float, default=10.0)
parser.add_argument("-b", "--bias", help="The bias value before the step input.", type=float, default=0.0)
parser.add_argument("-st", "--stepTime", help="The time at which the step occours", type=float, default=1.0 )
parser.add_argument("-sh", "--stepHeight", help="The height of the step on top of the bias", type=float, default = 1.0)
parser.add_argument("-of", "--outputFile", help="The file where to save data", type=pathlib.Path, default="./stepData.dat")
parser.add_argument("-p", "--plot", help="Plot data",  action='store_true')

args = parser.parse_args()

t = np.arange(0.0, args.endTime, args.timeStep)
data = np.full_like(t, args.bias)
data = data + args.stepHeight * (t > args.stepTime)

packedData = np.column_stack((t, data))

strHeader = f"Data generated with generateStepData.py script."
strHeader += str.format("\nTimeStep= {ts} EndTime = {et} bias = {b} stepTime = {st} stepHeight = {sh}", ts=args.timeStep, et=args.endTime, b=args.bias, st=args.stepTime, sh=args.stepHeight)
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

