import numpy as np
import matplotlib.pyplot as plt
import sys
import os
sys.path.append(os.path.relpath("../"))
from simulation import ground_truth_simulation as gtsim

gtparams = gtsim.VerticalJointParams()
gtparams.system.dt = 1e-3
gtparams.controller.latency_ms = 3.0

gtparams.end_effector.mass = 30.0
gtparams.gearbox.reduction_ratio = 25.0
gtparams.screw.pitch = 0.010

gtparams.encoders.motor_encoder_noise_std = 1e-4
gtparams.encoders.linear_encoder_noise_std = 1e-5

gtVerticalJointSim = gtsim.VerticalPrismaticJointSimulator(gtparams)

t_end = 3.0
dt = gtparams.system.dt
t = np.arange(0.0, t_end, dt)

# Simple current profile: upward command, then lower command
#desired_current = np.zeros_like(t)
#desired_current[(t > 0.2) & (t < 1.5)] = 2.0
#desired_current[(t >= 1.5) & (t < 2.5)] = 0.5
desired_current = 2*np.sin(2*np.pi*t)


data = gtVerticalJointSim.simulate(desired_current)

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

