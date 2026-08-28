# Robot conventions

## Base frame
- Origin: The frame is located at the center of the robot wheels, with the Z-axis pointing up, the X-axis pointing forward, and the Y-axis pointing to the left.
- +X: It points forward, aligned along the arm boom when the arm is at its retracted position
- +Y: It will point to the left of the arm boom when the arm is at its retracted position
- +Z: It will point upward.
- Gravity vector g, unit and upward: [0, 0, 1]
- Reference posture q_ref: [0, 0, 0, 0, 0, 0, 0]

## Joint conventions

| Joint | Type | q unit | +q direction, unit vector | Direction frame | q=0 definition | PSDM t_i | PSDM s_i | Lower | Upper | Positive generalized effort, unit vector |
|---|---|---|---|---|---|---:|---:|---:|---:|---|
| `starman_arm_joint1` | prismatic | m | [0, 0, 1] | J1 | Fully retracted | 1 | +1 | -0.001 | 0.751 | [0, 0, 1] |
| `starman_arm_joint2` | revolute | rad | [0, 0, 1] | J2 | Fully retracted | 0 | +1 | -1.57952297305 | 1.57952297305 | [0, 0, 1] |
| `starman_arm_joint3` | prismatic | m | [0, 0, 1] | J3 | Fully retracted | 1 | +1 | -0.001 | 0.751 | [0, 0, 1] |
| `starman_arm_joint4` | revolute | rad | [0, 0, 1] | J4 | Fully retracted | 0 | +1 | continuous | continuous | [0, 0, 1] |
| `starman_arm_joint5` | revolute | rad | [0, 0, 1] | J5 | Fully retracted | 0 | +1 | -1.5271630955 | 1.5271630955 | [0, 0, 1] |
| `starman_arm_joint6` | revolute | rad | [0, 0, 1] | J6 | Fully retracted | 0 | +1 | -0.00872664625997 | 3.04559954473 | [0, 0, 1] |
| `starman_arm_joint7` | revolute | rad | [0, 0, 1] | J7 | Fully retracted | 0 | +1 | continuous | continuous | [0, 0, 1] |

For a revolute joint, the positive generalized-effort vector is a torque axis and positive effort follows the right-hand rule. For a prismatic joint, it is a force direction.
