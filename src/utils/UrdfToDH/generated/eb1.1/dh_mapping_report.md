# URDF to standard-DH mapping report

- Base link: `starman_arm_link_cart`
- Tool link: `starman_arm_ids`
- Coordinate policy: `q_PSDM = q_URDF`.
- Fixed joints on the selected chain are folded into geometry.
- Continuous joints are treated as revolute.
- Every generated PSDM sign is `s_i = +1`.

## DH table

| i | Joint | a (m) | alpha (rad) | d (m) | theta (rad) | t | s |
|---:|---|---:|---:|---:|---:|---:|---:|
| 1 | `starman_arm_joint1` | 0.0117153745139 | 0 | 0 | 0 | 1 | 1 |
| 2 | `starman_arm_joint2` | 0 | 1.57079632679 | 0.036 | 0.694738276197 | 0 | 1 |
| 3 | `starman_arm_joint3` | 0 | 1.57079632679 | 0.797289 | 3.14159265359 | 1 | 1 |
| 4 | `starman_arm_joint4` | 0 | 1.57079632679 | -0.161843 | 1.57079632679 | 0 | 1 |
| 5 | `starman_arm_joint5` | 0.25 | 0 | 0.03 | -1.57079632679 | 0 | 1 |
| 6 | `starman_arm_joint6` | 0.1199 | -1.57079632679 | -0.03 | -1.57079632679 | 0 | 1 |
| 7 | `starman_arm_joint7` | 0 | 0 | 0 | 0 | 0 | 1 |

## Residual transforms

`T_urdf_base_to_dh_base`:
```text
[[-0.768221279597 -0.640184399664  0.              0.009         ]
 [ 0.640184399664 -0.768221279597  0.              0.13          ]
 [ 0.              0.              1.              1.16405       ]
 [ 0.              0.              0.              1.            ]]
```

`T_dh_last_to_urdf_tool`:
```text
[[-0.              0.001592652916 -0.999998731728  0.            ]
 [-0.             -0.999998731728 -0.001592652916  0.            ]
 [-1.             -0.              0.              0.044588835   ]
 [ 0.              0.              0.              1.            ]]
```

## RPY normalization

Angles within 0.01 rad of a multiple of pi/2 were snapped.
This avoids artificial near-parallel axes caused by low-precision URDF literals.

| Joint | URDF rpy | Used rpy |
|---|---|---|
| `starman_arm_joint3` | [-1.57, 0, 0] | [-1.57079632679, 0, 0] |
| `starman_arm_joint4` | [1.57, 0, 0] | [1.57079632679, 0, 0] |
| `starman_arm_joint5` | [-1.57, 0, -1.57] | [-1.57079632679, 0, -1.57079632679] |
| `starman_arm_joint6` | [3.14, 0, 0] | [3.14159265359, 0, 0] |
| `starman_arm_joint7` | [1.57, 0.523, 0] | [1.57079632679, 0.523, 0] |
| `starman_arm_ids_adapter` | [0, 1.57, -2.617] | [0, 1.57079632679, -2.617] |
