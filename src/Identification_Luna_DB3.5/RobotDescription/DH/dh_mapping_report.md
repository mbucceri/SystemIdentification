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
| 1 | `starman_arm_joint1` | 0.06525 | 0 | 0 | 0 | 1 | 1 |
| 2 | `starman_arm_joint2` | 0 | 1.57079632679 | 0.03045 | 1.57079632679 | 0 | 1 |
| 3 | `starman_arm_joint3` | 0 | 1.57079632679 | 0.7216 | 0 | 1 | 1 |
| 4 | `starman_arm_joint4` | 0 | 1.57079632679 | 0.13775 | 1.57079632679 | 0 | 1 |
| 5 | `starman_arm_joint5` | 0.2571 | 3.14159265359 | -0.02807 | 1.57079632679 | 0 | 1 |
| 6 | `starman_arm_joint6` | 0.12 | -1.57079632679 | -0.028 | -1.51843644924 | 0 | 1 |
| 7 | `starman_arm_joint7` | 0 | 0 | 0 | 0 | 0 | 1 |

## Residual transforms

`T_urdf_base_to_dh_base`:
```text
[[1.     0.     0.     0.    ]
 [0.     1.     0.     0.    ]
 [0.     0.     1.     1.2525]
 [0.     0.     0.     1.    ]]
```

`T_dh_last_to_urdf_tool`:
```text
[[ 0.      0.     -1.      0.    ]
 [-0.     -1.     -0.      0.    ]
 [-1.      0.      0.      0.0559]
 [ 0.      0.      0.      1.    ]]
```
