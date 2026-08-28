import numpy as np
from VerticalJointId.Params.params_model import EncoderParams

GENERIC_ROTARY_ENCODER_512_CPR = EncoderParams(
    encoder_noise_std=0.5*(2 * np.pi)/512.0,    # 0.5 times the quantization step to account for noise
    encoder_quantization=(2 * np.pi)/512.0      # [rad/count]
)

GENERIC_ROTARY_ENCODER_1024_CPR = EncoderParams(
    encoder_noise_std=(2 * np.pi)/1024.0 ,      # 1 times the quantization step to account for noise
    encoder_quantization=(2 * np.pi)/1024.0     # [rad/count]
)

GENERIC_ROTARY_ENCODER_2048_CPR = EncoderParams(
    encoder_noise_std=2*(2 * np.pi)/2048.0,     # 2 times the quantization step to account for noise,
    encoder_quantization=(2 * np.pi)/2048.0     # [rad/count]
)

GENERIC_ROTARY_ENCODER_4096_CPR = EncoderParams(
    encoder_noise_std=3*(2 * np.pi)/4096.0,     # 3 times the quantization step to account for noise,
    encoder_quantization=(2 * np.pi)/4096.0     # [rad/count]
)

GENERIC_ROTARY_ENCODER_8192_CPR = EncoderParams(
    encoder_noise_std=4*(2 * np.pi)/8192.0,     # 4 times the quantization step to account for noise,
    encoder_quantization=(2 * np.pi)/8192.0     # [rad/count]
)

GENERIC_LINEAR_ENCODER_4096_COUNTS_PER_MM = EncoderParams(
    encoder_noise_std=3 * (0.001/4096.0),       # 3 times the quantization step to account for noise
    encoder_quantization=0.001/4096.0           # [m/count]

)

