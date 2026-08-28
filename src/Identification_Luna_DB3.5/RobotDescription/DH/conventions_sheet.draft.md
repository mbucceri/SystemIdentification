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
| `starman_arm_joint1` | prismatic | m | [0, 0, 1] | [0, 0, 1] | -0.001 | 0.751 |
| `starman_arm_joint2` | revolute | rad | [0, 0, 1] | [0, 0, 1] | -1.57952297305 | 1.57952297305 |
| `starman_arm_joint3` | prismatic | m | [0, 0, 1] | [1, 6.12323399574e-17, 6.12323399574e-17] | -0.001 | 0.751 |
| `starman_arm_joint4` | revolute | rad | [0, 0, 1] | [1.22464679915e-16, 7.49879891331e-33, -1] | continuous | continuous |
| `starman_arm_joint5` | revolute | rad | [0, 0, 1] | [-1.22464679915e-16, 1, -6.12323399574e-17] | -1.5271630955 | 1.5271630955 |
| `starman_arm_joint6` | revolute | rad | [0, 0, 1] | [1.28873986044e-16, -1, -6.10645063698e-17] | -0.00872664625997 | 3.04559954473 |
| `starman_arm_joint7` | revolute | rad | [0, 0, 1] | [0.0523359562429, 6.49322292313e-18, -0.998629534755] | continuous | continuous |
