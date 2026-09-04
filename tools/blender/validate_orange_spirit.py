import json
import sys
from pathlib import Path

import bpy
from mathutils import Vector


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_BLEND = ROOT / "assets/source/OrangeSpirit-V1.0.3.blend"
DEFAULT_GLB = ROOT / "assets/models/orange-spirit-V1.0.3.glb"
REPORT = ROOT / "docs/orange-spirit-model-validation.json"
REQUIRED_ACTIONS = {
    "Idle", "Blink", "Listen", "Think", "Speak", "Wave",
    "Celebrate", "Error", "Sleep", "Bounce", "Spin", "Shy", "Mischief",
}
MAX_TRIANGLES = 70_000
MAX_MATERIALS = 8
MAX_GLB_BYTES = 6 * 1024 * 1024


def arg_after_double_dash():
    if "--" not in sys.argv:
        return DEFAULT_BLEND
    args = sys.argv[sys.argv.index("--") + 1 :]
    return Path(args[0]).expanduser().resolve() if args else DEFAULT_BLEND


def fail_early(path: Path):
    payload = {"status": "FAIL", "errors": [f"missing blend file: {path}"]}
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(payload, ensure_ascii=False))
    raise SystemExit(2)


def main():
    blend = arg_after_double_dash()
    if not blend.exists():
        fail_early(blend)

    bpy.ops.wm.open_mainfile(filepath=str(blend))
    meshes = [obj for obj in bpy.data.objects if obj.type == "MESH"]
    armatures = [obj for obj in bpy.data.objects if obj.type == "ARMATURE"]
    triangles = sum(len(poly.vertices) - 2 for obj in meshes for poly in obj.data.polygons)
    materials = {slot.material.name for obj in meshes for slot in obj.material_slots if slot.material}
    actions = {action.name for action in bpy.data.actions}
    collections = {collection.name for collection in bpy.data.collections}
    errors = []

    if len(armatures) != 1 or armatures[0].name != "ARM_OrangeSpirit":
        errors.append("scene must contain exactly ARM_OrangeSpirit")
    if "COL_OrangeSpirit" not in collections or "COL_Export" not in collections:
        errors.append("required collections are missing")
    missing_actions = sorted(REQUIRED_ACTIONS - actions)
    unexpected_actions = sorted(actions - REQUIRED_ACTIONS)
    if missing_actions or unexpected_actions:
        errors.append(f"action set mismatch: missing={missing_actions}, unexpected={unexpected_actions}")
    if triangles > MAX_TRIANGLES:
        errors.append(f"triangle budget exceeded: {triangles} > {MAX_TRIANGLES}")
    if len(materials) > MAX_MATERIALS:
        errors.append(f"material budget exceeded: {len(materials)} > {MAX_MATERIALS}")
    if any(not obj.name.startswith("SM_") for obj in meshes):
        errors.append("all mesh objects must use SM_ prefix")
    if any(not name.startswith("MAT_") for name in materials):
        errors.append("all materials must use MAT_ prefix")

    glb_size = DEFAULT_GLB.stat().st_size if DEFAULT_GLB.exists() else 0
    if glb_size == 0:
        errors.append(f"missing GLB: {DEFAULT_GLB}")
    elif glb_size > MAX_GLB_BYTES:
        errors.append(f"GLB budget exceeded: {glb_size} > {MAX_GLB_BYTES}")

    bounds = []
    for obj in meshes:
        bounds.extend(obj.matrix_world @ Vector(corner) for corner in obj.bound_box)
    min_xyz = [min(v[i] for v in bounds) for i in range(3)]
    max_xyz = [max(v[i] for v in bounds) for i in range(3)]
    if min_xyz[2] < -0.015 or min_xyz[2] > 0.03:
        errors.append(f"floor contact out of tolerance: minZ={min_xyz[2]:.4f}")

    payload = {
        "status": "PASS" if not errors else "FAIL",
        "blend": str(blend.relative_to(ROOT) if blend.is_relative_to(ROOT) else blend.name),
        "glb": str(DEFAULT_GLB.relative_to(ROOT)),
        "meshes": len(meshes),
        "triangles": triangles,
        "materials": sorted(materials),
        "actions": sorted(actions),
        "armature": armatures[0].name if len(armatures) == 1 else None,
        "bounds": {"min": [round(v, 4) for v in min_xyz], "max": [round(v, 4) for v in max_xyz]},
        "glb_bytes": glb_size,
        "errors": errors,
    }
    REPORT.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(payload, ensure_ascii=False))
    raise SystemExit(0 if not errors else 1)


main()
