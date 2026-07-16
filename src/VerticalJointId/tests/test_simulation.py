import numpy as np
import matplotlib.pyplot as plt
import sys
import os
sys.path.append(os.path.relpath("../"))
from simulation import simplified_simulation as ssim

sparams = ssim.SimplifiedVerticalJointParams()
sparams.system.dt = 1e-3
# sparams.controller.latency_ms = 3.0

sparams.dynamics.equivalent_mass = 7.0
sparams.dynamics.load_mass = 7.0
sparams.kinematics.gearbox_reduction_ratio = 25.0
sparams.kinematics.screw_pitch = 0.010

sparams.encoders.motor_encoder_noise_std = 1e-4
sparams.encoders.linear_encoder_noise_std = 1e-5

sVerticalJointSim = ssim.SimplifiedVerticalPrismaticJointSimulator(sparams)

t_end = 3.0
dt = sparams.system.dt
t = np.arange(0.0, t_end, dt)

# Simple current profile: upward command, then lower command
#desired_current = np.zeros_like(t)
#desired_current[(t > 0.2) & (t < 1.5)] = 2.0
#desired_current[(t >= 1.5) & (t < 2.5)] = 0.5
desired_current = 2*np.sin(2*np.pi*t)


data = sVerticalJointSim.simulate(desired_current)

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

# plt.figure()
# plt.plot(data["time"], data["drive_voltage"], ":", label="drive voltage")
# plt.xlabel("Time [s]")
# plt.ylabel("Voltage [V]")
# plt.legend()
# plt.grid(True)

# plt.figure()
# plt.plot(data["time"], data["net_torque"], label ="net torque")
# plt.plot(data["time"], data["tau_motor"], label="motor torque")
# plt.plot(data["time"], data["tau_gravity"], label="gravity torque")
# plt.plot(data["time"], data["tau_gearbox_friction"], label="torque gearbox friction")
# plt.plot(data["time"], data["tau_screw_friction"],  label="torque screw friction")
# plt.plot(data["time"], data["tau_screw_friction"],  label="torque screw friction")
# plt.xlabel("Time [s]")
# plt.ylabel("Torque [Nm]")
# plt.legend()
# plt.grid(True)

plt.show()

