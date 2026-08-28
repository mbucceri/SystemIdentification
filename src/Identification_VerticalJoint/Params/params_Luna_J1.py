from VerticalJointId.Params.params_system import SystemParams
from VerticalJointId.Params.params_model import (
    MotorControllerParams,
    MotorParams,
    GearboxParams,
    LinearScrewParams,
    EndEffectorParams,
    EncoderParams,
)
from VerticalJointId.Params.Database.Encoder import Generic as GenericEncoders
from VerticalJointId.Params.Database.BLDC import Kollmogoren as Kollmogoren
from VerticalJointId.simulation.sim_ground_truth import VerticalJointParams

# Luna J1 joint ground truth parameters.
# Replace these values with the actual Luna_J1 values when available.
LUNA_J1_PARAMS = VerticalJointParams(
    system=SystemParams(
        dt=1e-3
    ),
    controller=MotorControllerParams(
        latency_ms=5.0,
        kp=0.1,
        ki=500.0,
        ff_winding_resistance=1.0,  # [Ohm]
        integral_saturation=1.0,    # [A]
        voltage_limit=48.0,         # [V]
    ),
    motor=Kollmogoren.KOLLMOGOREN_AKM2G_32_ML,

    gearbox=GearboxParams(
        reduction_ratio=10.0,
        inertia_motor_side=1.0e-4,
        viscous_friction=1.0e-4,
        coulomb_friction=0.02,
    ),
    screw=LinearScrewParams(
        pitch=0.03,
        viscous_friction_linear=30.0,
        coulomb_friction_linear=15.0,
        inertia_motor_side=0.0,
    ),
    end_effector=EndEffectorParams(
        mass=150.0,                 # [kg] equivalent mass of J1-J7 + IDS
    ),
    motor_encoder=GenericEncoders.GENERIC_ROTARY_ENCODER_8192_CPR,
    linear_encoder=GenericEncoders.GENERIC_LINEAR_ENCODER_4096_COUNTS_PER_MM,

    friction_smoothing_velocity=1e-3,
)


