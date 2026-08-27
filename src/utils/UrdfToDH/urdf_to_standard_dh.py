#!/usr/bin/env python3
"""Generate a PSDM-compatible standard-DH table from one serial URDF chain.

Usage:
  python urdf_to_standard_dh.py --config urdfToDhTemplate.yaml --output-dir output

Dependencies: numpy, PyYAML. SciPy is optional, only for dh_table.mat.
"""

import argparse
import csv
import json
import math
from pathlib import Path
import xml.etree.ElementTree as ET

import numpy as np
import yaml

EPS = 1e-10
# The sample URDF uses 1.57 and 3.14 for nominal pi/2 and pi rotations.
# This normalization prevents artificial near-parallel axes and extreme DH offsets.
SNAP_TOL_RAD = 1e-2


def unit(v):
    n = np.linalg.norm(v)
    if n < EPS:
        raise ValueError("A selected joint has a zero-length axis.")
    return v / n


def small(v):
    return 0.0 if abs(v) < 1e-12 else float(v)


def rpy_rotation(rpy):
    r, p, y = rpy
    cr, sr = math.cos(r), math.sin(r)
    cp, sp = math.cos(p), math.sin(p)
    cy, sy = math.cos(y), math.sin(y)
    return np.array([
        [cy * cp, cy * sp * sr - sy * cr, cy * sp * cr + sy * sr],
        [sy * cp, sy * sp * sr + cy * cr, sy * sp * cr - cy * sr],
        [-sp, cp * sr, cp * cr],
    ])


def snap_rpy(rpy):
    snapped = []
    for value in rpy:
        nearest = round(value / (math.pi / 2)) * (math.pi / 2)
        snapped.append(nearest if abs(value - nearest) <= SNAP_TOL_RAD else float(value))
    return np.array(snapped)


def origin_transform(element):
    xyz = np.zeros(3)
    rpy = np.zeros(3)
    if element is not None:
        xyz = np.fromstring(element.get("xyz", "0 0 0"), sep=" ")
        rpy = np.fromstring(element.get("rpy", "0 0 0"), sep=" ")
    used_rpy = snap_rpy(rpy)
    T = np.eye(4)
    T[:3, :3] = rpy_rotation(used_rpy)
    T[:3, 3] = xyz
    return T, rpy.tolist(), used_rpy.tolist()


def parse_urdf(path):
    joints = []
    for e in ET.parse(path).getroot().findall("joint"):
        parent = e.find("parent").get("link")
        child = e.find("child").get("link")
        axis_e = e.find("axis")
        axis = np.array([1.0, 0.0, 0.0]) if axis_e is None else np.fromstring(axis_e.get("xyz", "1 0 0"), sep=" ")
        limit = e.find("limit")
        T, rpy_original, rpy_used = origin_transform(e.find("origin"))
        joints.append({
            "name": e.get("name"), "type": e.get("type"), "parent": parent, "child": child,
            "origin": T, "axis": axis,
            "lower": None if limit is None or limit.get("lower") is None else float(limit.get("lower")),
            "upper": None if limit is None or limit.get("upper") is None else float(limit.get("upper")),
            "mimic": e.find("mimic") is not None,
            "rpy_original": rpy_original, "rpy_used": rpy_used,
        })
    return joints


def get_chain(joints, base, tool):
    by_child = {joint["child"]: joint for joint in joints}
    chain = []
    current = tool
    while current != base:
        if current not in by_child:
            raise ValueError(f"No parent chain exists from {base!r} to {tool!r}.")
        joint = by_child[current]
        chain.append(joint)
        current = joint["parent"]
    return list(reversed(chain))


def joint_motion(joint, q):
    T = np.eye(4)
    kind = "revolute" if joint["type"] == "continuous" else joint["type"]
    axis = unit(joint["axis"])
    if kind == "prismatic":
        T[:3, 3] = axis * q
    elif kind == "revolute":
        x, y, z = axis
        c, s, C = math.cos(q), math.sin(q), 1.0 - math.cos(q)
        T[:3, :3] = np.array([
            [c + x*x*C, x*y*C - z*s, x*z*C + y*s],
            [y*x*C + z*s, c + y*y*C, y*z*C - x*s],
            [z*x*C - y*s, z*y*C + x*s, c + z*z*C],
        ])
    elif kind != "fixed":
        raise ValueError(f"Unsupported joint type {joint['type']!r}: {joint['name']}")
    return T


def urdf_fk(chain, q_by_name):
    T = np.eye(4)
    active_axes = []
    for joint in chain:
        T = T @ joint["origin"]
        if joint["type"] != "fixed":
            if joint["mimic"]:
                raise ValueError(f"Mimic joint is not supported: {joint['name']}")
            if joint["type"] not in {"revolute", "continuous", "prismatic"}:
                raise ValueError(f"Unsupported joint type {joint['type']!r}: {joint['name']}")
            active_axes.append((T[:3, 3].copy(), unit(T[:3, :3] @ unit(joint["axis"])), joint))
            T = T @ joint_motion(joint, q_by_name.get(joint["name"], 0.0))
    return T, active_axes


def perpendicular(axis):
    basis = np.eye(3)[np.argmin(np.abs(axis))]
    return unit(np.cross(axis, basis))


def closest_points(p1, u, p2, v):
    """Return closest points on two lines and whether they are parallel."""
    u, v = unit(u), unit(v)
    b = float(np.dot(u, v))
    w = p1 - p2
    d, e = float(np.dot(u, w)), float(np.dot(v, w))
    den = 1.0 - b*b
    if abs(den) < EPS:
        source = p1 + np.dot(p2 - p1, u) * u
        return source, p2.copy(), True
    s = (b*e - d) / den
    t = (e - b*d) / den
    return p1 + s*u, p2 + t*v, False


def frame(origin, x, z):
    z = unit(z)
    x = unit(x - np.dot(x, z) * z)
    y = unit(np.cross(z, x))
    x = unit(np.cross(y, z))
    T = np.eye(4)
    T[:3, 0], T[:3, 1], T[:3, 2], T[:3, 3] = x, y, z, origin
    return T


def make_dh_frames(active_axes):
    """Construct frames F0...Fn, with z(i-1) aligned to active joint i."""
    n = len(active_axes)
    if n == 0:
        raise ValueError("The selected chain has no active joints.")
    origins, xs, zs = [None]*(n+1), [None]*(n+1), [None]*(n+1)
    for i, (_, axis, _) in enumerate(active_axes):
        zs[i] = axis

    if n == 1:
        origins[0], xs[0] = active_axes[0][0], perpendicular(active_axes[0][1])
    else:
        previous_x = None
        for i in range(n-1):
            p, z, _ = active_axes[i]
            next_p, next_z, _ = active_axes[i+1]
            source, target, _ = closest_points(p, z, next_p, next_z)
            separation = target - source
            if np.linalg.norm(separation) > EPS:
                x = unit(separation)
            else:
                cross = np.cross(z, next_z)
                if np.linalg.norm(cross) > EPS:
                    x = unit(cross)
                elif previous_x is not None:
                    x = unit(previous_x - np.dot(previous_x, z) * z)
                else:
                    x = perpendicular(z)
            if i == 0:
                origins[0], xs[0] = source, x
            origins[i+1], xs[i+1], previous_x = target, x, x

    # Keep the final fixed geometry in a residual transform to the requested tool link.
    origins[n], xs[n], zs[n] = origins[n-1].copy(), xs[n-1].copy(), zs[n-1].copy()
    return [frame(origins[i], xs[i], zs[i]) for i in range(n+1)]


def dh_row(T):
    R, p = T[:3, :3], T[:3, 3]
    theta = math.atan2(R[1, 0], R[0, 0])
    alpha = math.atan2(R[2, 1], R[2, 2])
    a = math.cos(theta)*p[0] + math.sin(theta)*p[1]
    d = p[2]
    if abs(R[2, 0]) > 1e-8 or abs(-math.sin(theta)*p[0] + math.cos(theta)*p[1]) > 1e-8:
        raise ValueError("Internal DH frame construction failed.")
    return [small(a), small(alpha), small(d), small(theta)]


def dh_transform(a, alpha, d, theta):
    ct, st, ca, sa = math.cos(theta), math.sin(theta), math.cos(alpha), math.sin(alpha)
    return np.array([
        [ct, -st*ca, st*sa, a*ct],
        [st, ct*ca, -ct*sa, a*st],
        [0.0, sa, ca, d],
        [0.0, 0.0, 0.0, 1.0],
    ])


def dh_fk(DH, q, T_base_dh0, T_dhn_tool):
    T = T_base_dh0.copy()
    for row, qi in zip(DH, q):
        a, alpha, d, theta, t, s = row
        if int(t) == 0:
            theta += s*qi
        else:
            d += s*qi
        T = T @ dh_transform(a, alpha, d, theta)
    return T @ T_dhn_tool


def angle_error_deg(R1, R2):
    c = np.clip((np.trace(R1.T @ R2) - 1.0) / 2.0, -1.0, 1.0)
    return math.degrees(math.acos(float(c)))


def matrix_list(T):
    return [[small(x) for x in row] for row in T]


def limits(joint, cfg):
    if joint["type"] == "continuous":
        return cfg["fk_validation"]["continuous_joint_sampling_range_rad"]
    if joint["lower"] is None or joint["upper"] is None:
        raise ValueError(f"Joint {joint['name']!r} needs finite URDF limits for validation.")
    return joint["lower"], joint["upper"]


def write_csv(path, DH, active):
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["joint", "a_m", "alpha_rad", "d_m", "theta_rad", "t", "s"])
        for joint, row in zip(active, DH):
            w.writerow([joint["name"], *[f"{x:.15g}" for x in row]])


def write_mat(path, DH, active):
    try:
        from scipy.io import savemat
    except ImportError:
        return "SciPy is not installed. dh_table.mat was not written."
    savemat(path, {"DH": DH, "joint_names": np.array([j["name"] for j in active], dtype=object)})
    return "dh_table.mat written."


def write_json(path, active_axes, DH, T_base_dh0, T_dhn_tool):
    data = {
        "joint_order": [joint["name"] for _, _, joint in active_axes],
        "dh_columns": ["a_m", "alpha_rad", "d_m", "theta_rad", "t", "s"],
        "DH": [[small(v) for v in row] for row in DH],
        "axes_in_urdf_base_at_q0": [
            {"joint": joint["name"], "point_m": [small(v) for v in p], "direction": [small(v) for v in z]}
            for p, z, joint in active_axes
        ],
        "T_urdf_base_to_dh_base": matrix_list(T_base_dh0),
        "T_dh_last_to_urdf_tool": matrix_list(T_dhn_tool),
    }
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def write_mapping_report(path, cfg, chain, active, DH, T_base_dh0, T_dhn_tool):
    snapped = [j for j in chain if j["rpy_original"] != j["rpy_used"]]
    lines = [
        "# URDF to standard-DH mapping report", "",
        f"- Base link: `{cfg['urdf']['base_link']}`",
        f"- Tool link: `{cfg['urdf']['tool_link']}`",
        "- Coordinate policy: `q_PSDM = q_URDF`.",
        "- Fixed joints on the selected chain are folded into geometry.",
        "- Continuous joints are treated as revolute.",
        "- Every generated PSDM sign is `s_i = +1`.", "",
        "## DH table", "",
        "| i | Joint | a (m) | alpha (rad) | d (m) | theta (rad) | t | s |",
        "|---:|---|---:|---:|---:|---:|---:|---:|",
    ]
    for i, (joint, row) in enumerate(zip(active, DH), 1):
        lines.append(f"| {i} | `{joint['name']}` | " + " | ".join(f"{x:.12g}" for x in row) + " |")
    lines += [
        "", "## Residual transforms", "",
        "`T_urdf_base_to_dh_base`:", "```text", np.array2string(T_base_dh0, precision=12, suppress_small=True), "```",
        "", "`T_dh_last_to_urdf_tool`:", "```text", np.array2string(T_dhn_tool, precision=12, suppress_small=True), "```",
    ]
    if snapped:
        lines += ["", "## RPY normalization", "", f"Angles within {SNAP_TOL_RAD:g} rad of a multiple of pi/2 were snapped.",
                  "This avoids artificial near-parallel axes caused by low-precision URDF literals.", "",
                  "| Joint | URDF rpy | Used rpy |", "|---|---|---|"]
        for joint in snapped:
            a = ", ".join(f"{x:.12g}" for x in joint["rpy_original"])
            b = ", ".join(f"{x:.12g}" for x in joint["rpy_used"])
            lines.append(f"| `{joint['name']}` | [{a}] | [{b}] |")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_conventions(path, cfg, active_axes):
    lines = [
        "# Robot conventions, generated draft", "",
        f"- URDF base link: `{cfg['urdf']['base_link']}`",
        f"- URDF tool link: `{cfg['urdf']['tool_link']}`",
        "- PSDM coordinate: `q_i = q_URDF,i`.",
        "- `+q` is the positive local URDF joint axis at `q = 0`.",
        "- For prismatic joints, `+q` is positive translation along that axis.",
        "- For revolute joints, `+q` follows the right-hand rule about that axis.",
        "- Motor-drive and encoder signs are outside this file and must be documented separately.", "",
        "| Joint | Type | q unit | +q axis, joint frame | +q axis, URDF base at q=0 | Lower | Upper |",
        "|---|---|---|---|---|---:|---:|",
    ]
    for _, direction, joint in active_axes:
        kind = "prismatic" if joint["type"] == "prismatic" else "revolute"
        unit_name = "m" if kind == "prismatic" else "rad"
        local = "[{}]".format(", ".join(f"{x:.12g}" for x in unit(joint["axis"])))
        base = "[{}]".format(", ".join(f"{x:.12g}" for x in direction))
        lo = "continuous" if joint["type"] == "continuous" else f"{joint['lower']:.12g}"
        hi = "continuous" if joint["type"] == "continuous" else f"{joint['upper']:.12g}"
        lines.append(f"| `{joint['name']}` | {kind} | {unit_name} | {local} | {base} | {lo} | {hi} |")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def validate_fk(path, cfg, chain, active, DH, T_base_dh0, T_dhn_tool):
    rng = np.random.default_rng(0)
    p_errors, r_errors = [], []
    for _ in range(int(cfg["fk_validation"]["random_samples"])):
        q = np.array([rng.uniform(*limits(j, cfg)) for j in active])
        urdf_T, _ = urdf_fk(chain, {j["name"]: float(v) for j, v in zip(active, q)})
        dh_T = dh_fk(DH, q, T_base_dh0, T_dhn_tool)
        p_errors.append(np.linalg.norm(urdf_T[:3, 3] - dh_T[:3, 3]))
        r_errors.append(angle_error_deg(urdf_T[:3, :3], dh_T[:3, :3]))
    pmax, rmax = max(p_errors, default=0.0), max(r_errors, default=0.0)
    ptol = float(cfg["fk_validation"]["position_tolerance_m"])
    rtol = float(cfg["fk_validation"]["orientation_tolerance_deg"])
    passed = pmax <= ptol and rmax <= rtol
    path.write_text(
        "# FK validation report\n\n"
        "The URDF and DH FK use the same normalized URDF origin rotations.\n\n"
        f"- Random samples: {int(cfg['fk_validation']['random_samples'])}\n"
        "- Random seed: 0\n"
        f"- Position tolerance: {ptol:.12g} m\n"
        f"- Orientation tolerance: {rtol:.12g} deg\n"
        f"- Maximum position error: {pmax:.12g} m\n"
        f"- Maximum orientation error: {rmax:.12g} deg\n"
        f"- Status: {'PASS' if passed else 'FAIL'}\n",
        encoding="utf-8")
    return pmax, rmax, passed


def main():
    ap = argparse.ArgumentParser(description="Generate a standard DH table from a serial URDF chain.")
    ap.add_argument("--config", required=True)
    ap.add_argument("--output-dir", required=True)
    ap.add_argument("--urdf", help="Overrides urdf.upload in the YAML configuration.")
    args = ap.parse_args()

    config_path = Path(args.config).resolve()
    cfg = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    urdf_path = Path(args.urdf).resolve() if args.urdf else (config_path.parent / cfg["urdf"]["upload"]).resolve()
    output_dir = Path(args.output_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    if cfg["coordinate_policy"]["dh_q_reference"] != "URDF joint coordinate at q = 0":
        raise ValueError("Only the URDF q=0 coordinate policy is implemented.")
    if cfg["coordinate_policy"]["joint_sign_policy"] != "URDF_coordinate":
        raise ValueError("Only the URDF-coordinate sign policy is implemented.")

    chain = get_chain(parse_urdf(urdf_path), cfg["urdf"]["base_link"], cfg["urdf"]["tool_link"])
    tool_T0, active_axes = urdf_fk(chain, {})
    active = [joint for _, _, joint in active_axes]
    frames = make_dh_frames(active_axes)

    DH = []
    for i, joint in enumerate(active, 1):
        a, alpha, d, theta = dh_row(np.linalg.inv(frames[i-1]) @ frames[i])
        DH.append([a, alpha, d, theta, 1.0 if joint["type"] == "prismatic" else 0.0, 1.0])
    DH = np.array(DH, dtype=float)
    T_base_dh0 = frames[0]
    T_dhn_tool = np.linalg.inv(frames[-1]) @ tool_T0

    out = cfg["outputs"]
    if out.get("dh_table_csv", True):
        write_csv(output_dir / "dh_table.csv", DH, active)
    mat_status = "MAT output disabled."
    if out.get("dh_table_mat", False) and cfg["dependencies"].get("allow_scipy_for_mat_output", False):
        mat_status = write_mat(output_dir / "dh_table.mat", DH, active)
    if out.get("urdf_kinematics_json", True):
        write_json(output_dir / "urdf_kinematics.json", active_axes, DH, T_base_dh0, T_dhn_tool)
    if out.get("dh_mapping_report_markdown", True):
        write_mapping_report(output_dir / "dh_mapping_report.md", cfg, chain, active, DH, T_base_dh0, T_dhn_tool)
    if out.get("conventions_sheet_draft_markdown", True):
        write_conventions(output_dir / "conventions_sheet.draft.md", cfg, active_axes)

    pmax, rmax, passed = validate_fk(output_dir / "fk_validation_report.md", cfg, chain, active, DH, T_base_dh0, T_dhn_tool)
    if not out.get("fk_validation_report_markdown", True):
        (output_dir / "fk_validation_report.md").unlink(missing_ok=True)

    print(f"Generated {len(active)}-DOF standard DH table in: {output_dir}")
    print(mat_status)
    print(f"FK validation: {'PASS' if passed else 'FAIL'}")
    print(f"Maximum errors: {pmax:.6g} m, {rmax:.6g} deg")


if __name__ == "__main__":
    main()
