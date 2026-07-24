from VerticalJointId.Params.params_model import MotorParams


KOLLMOGOREN_AKM2G_32_ML = MotorParams(
    torque_constant=0.201,          # [Nm/A]
    back_emf_constant=0.125,        # [V/(rad/s)]
    rotor_inertia=0.813e-4,         # [kg*m^2
    winding_resistance=0.24,        # [Ohm]
    winding_inductance=0.57e-3,     # [H]
    viscous_friction = 7.4485e-5    # [Nm/rad/s]
)

