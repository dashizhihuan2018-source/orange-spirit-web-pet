#!/usr/bin/env python3
import argparse
import hashlib
import json
import struct
from pathlib import Path

MINIMUM_ACTIONS = {"Idle", "Blink", "Listen", "Think", "Speak", "Wave", "Celebrate", "Error", "Sleep"}


def glb_json(path: Path):
    with path.open("rb") as handle:
        magic, version, length = struct.unpack("<4sII", handle.read(12))
        if magic != b"glTF" or version != 2 or length != path.stat().st_size:
            raise ValueError("invalid GLB header")
        chunk_length, chunk_type = struct.unpack("<II", handle.read(8))
        if chunk_type != 0x4E4F534A:
            raise ValueError("first GLB chunk is not JSON")
        return json.loads(handle.read(chunk_length).decode("utf-8").rstrip(" \t\r\n\0"))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("root", type=Path)
    parser.add_argument("--max-triangles", type=int, default=70000)
    parser.add_argument("--max-materials", type=int, default=8)
    parser.add_argument("--max-glb-mb", type=float, default=6)
    parser.add_argument("--config", type=Path, default=Path("web-pet-release.json"))
    args = parser.parse_args()
    root = args.root.resolve()
    config_path = args.config if args.config.is_absolute() else root / args.config
    config = json.loads(config_path.read_text(encoding="utf-8")) if config_path.exists() else {}
    required_actions = set(config.get("requiredActions", sorted(MINIMUM_ACTIONS)))
    release_paths = tuple(Path(item) for item in config.get("glbCopies", []))
    blends = list(root.rglob("*.blend"))
    glbs = list(root.rglob("*.glb"))
    sheets = [path for path in root.rglob("*.png") if "three-view" in path.name]
    errors = []
    if not blends:
        errors.append("missing editable .blend")
    if not glbs:
        errors.append("missing .glb")
    if not sheets:
        errors.append("missing three-view sheet")
    reports = []
    for glb in glbs:
        data = glb_json(glb)
        actions = {item.get("name", "") for item in data.get("animations", [])}
        missing = sorted(MINIMUM_ACTIONS - actions)
        materials = len(data.get("materials", []))
        triangles = 0
        accessors = data.get("accessors", [])
        for mesh in data.get("meshes", []):
            for primitive in mesh.get("primitives", []):
                if primitive.get("mode", 4) == 4:
                    accessor = primitive.get("indices", primitive.get("attributes", {}).get("POSITION"))
                    if accessor is not None:
                        triangles += accessors[accessor]["count"] // 3
        if missing:
            errors.append(f"{glb.name}: missing baseline actions {missing}")
        if materials > args.max_materials:
            errors.append(f"{glb.name}: {materials} materials")
        if triangles > args.max_triangles:
            errors.append(f"{glb.name}: {triangles} triangles")
        if glb.stat().st_size > args.max_glb_mb * 1024 * 1024:
            errors.append(f"{glb.name}: exceeds GLB size budget")
        reports.append({"file": str(glb.relative_to(root)), "bytes": glb.stat().st_size, "triangles": triangles, "materials": materials, "actions": sorted(actions)})
    release_hashes = []
    for relative in release_paths:
        glb = root / relative
        if not glb.exists():
            errors.append(f"{relative}: missing configured runtime GLB")
            continue
        actions = {item.get("name", "") for item in glb_json(glb).get("animations", [])}
        missing = sorted(required_actions - actions)
        unexpected = sorted(actions - required_actions)
        if missing or unexpected:
            errors.append(f"{relative}: action set mismatch missing={missing} unexpected={unexpected}")
        release_hashes.append({"file": str(relative), "sha256": hashlib.sha256(glb.read_bytes()).hexdigest()})
    if release_hashes and len(release_hashes) == len(release_paths) and len({item["sha256"] for item in release_hashes}) != 1:
        errors.append("configured runtime GLB hashes do not match")
    payload = {
        "status": "PASS" if not errors else "FAIL",
        "root": str(root),
        "config": str(config_path.relative_to(root)) if config_path.exists() else None,
        "blend_count": len(blends),
        "three_view_count": len(sheets),
        "glbs": reports,
        "release": {"version": config.get("version"), "actions": sorted(required_actions), "hashes": release_hashes},
        "errors": errors,
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    raise SystemExit(0 if not errors else 1)


if __name__ == "__main__":
    main()
