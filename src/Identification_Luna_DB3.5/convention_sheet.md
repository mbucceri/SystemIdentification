# Robot conventions

## Base frame
- Origin: [physical description]
- +X: [description]
- +Y: [description]
- +Z: [description]
- Gravity vector g, unit and upward: [0, 0, 1]
- Reference posture q_ref: [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]

## Joint conventions
| Joint | Type | q unit | +q direction, local physical meaning | Direction frame | q=0 definition | t_i | s_i | Lower | Upper | Positive generalized effort |
|---|---|---|---|---|---|---:|---:|---:|---:|---|
| J1 | prismatic | m | Child link translates along +Z_J1 | J1 | Fully retracted | 1 | 1 | -0.001 | 0.751 | [torque convention] |




---
# Examples
| J1 | revolute | rad | Right-hand rotation about +Z_J1 | J1 | [description] | 0 | [±1] | [value] | [value] | [torque convention] |
| P3 | prismatic | m | Child link translates along +Z_P3 | P3 | [description] | 1 | [±1] | [value] | [value] | [force convention] |