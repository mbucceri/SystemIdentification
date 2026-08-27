# Robot conventions, generated draft

- URDF base link: `starman_arm_link_cart`
- URDF tool link: `starman_arm_ids`
- PSDM coordinate: `q_i = q_URDF,i`.
- `+q` is the positive local URDF joint axis at `q = 0`.
- For prismatic joints, `+q` is positive translation along that axis.
- For revolute joints, `+q` follows the right-hand rule about that axis.
- Motor-drive and encoder signs are outside this file and must be documented separately.

| Joint | Type | q unit | +q axis, joint frame | +q axis, URDF base at q=0 | Lower | Upper |
|---|---|---|---|---|---:|---:|
| `starman_arm_joint1` | prismatic | m | [0, 0, 1] | [0, 0, 1] | 0 | 0.75 |
| `starman_arm_joint2` | revolute | rad | [0, 0, 1] | [0, 0, 1] | -1.57079632679 | 1.57079632679 |
| `starman_arm_joint3` | prismatic | m | [0, 0, 1] | [0, 1, 6.12323399574e-17] | 0 | 0.75 |
| `starman_arm_joint4` | revolute | rad | [0, 0, 1] | [0, 0, 1] | continuous | continuous |
| `starman_arm_joint5` | revolute | rad | [0, 0, 1] | [1, 6.12323399574e-17, 6.12323399574e-17] | -1.57079632679 | 1.57079632679 |
| `starman_arm_joint6` | revolute | rad | [0, 0, -1] | [1, 6.12323399574e-17, -6.12323399574e-17] | -0.05 | 3.25 |
| `starman_arm_joint7` | revolute | rad | [0, 0, 1] | [-1.14279424602e-16, -3.05844121635e-17, -1] | continuous | continuous |
