import numpy as np
import matplotlib.pyplot as plt
from simulation import sim_ground_truth as gtsim
from trajectories import multisine_trajectory 

gtparams = gtsim.VerticalJointParams()
# gtparams.system.dt = 1e-3
# gtparams.controller.latency_ms = 3.0
# 
# gtparams.end_effector.mass = 30.0
# gtparams.gearbox.reduction_ratio = 25.0
# gtparams.screw.pitch = 0.010
# 
# gtparams.encoders.motor_encoder_noise_std = 1e-4
# gtparams.encoders.linear_encoder_noise_std = 1e-5

gtVerticalJointSim = gtsim.VerticalPrismaticJointSimulator(gtparams) 

t_end = 3.0
dt = gtparams.system.dt
t = np.arange(0.0, t_end, dt)

freqs_phases = np.array([(0.2, 0.0), (0.5, 1.1), (0.9, 2.2), (1.7, 0.7), (2.8, 1.9), (4.0, 2.8)])
# freqs_phases = np.array([(0.2, 0.0), (0.5, 0.0), (0.9, 0.0), (1.7, 0.0), (2.8, 0), (4.0, 0)])
# freqs_phases = np.array([(0.2, 0.0)])
desired_current = multisine_trajectory.generate_current_excitation(
    t=t,
    freqs_and_phases=freqs_phases,
    bias_current=0.4,
    amplitude=2.0,
    ramp_time=1.0,
    current_min=-3.0,
    current_max=3.0
)

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

