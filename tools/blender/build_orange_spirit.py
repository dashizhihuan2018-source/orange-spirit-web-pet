import math
import os
from pathlib import Path

import bpy
from mathutils import Vector, noise


ROOT = Path(__file__).resolve().parents[2]
BLEND = ROOT / "assets/source/OrangeSpirit-V1.0.3.blend"
GLB = ROOT / "assets/models/orange-spirit-V1.0.3.glb"
PREVIEWS = ROOT / "assets/previews"
TEXTURES = ROOT / "assets/textures"
PASS_NAME = os.environ.get("ORANGE_PASS", "V1.0.3")
FPS = 30


def clean_scene():
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    for datablocks in (
        bpy.data.meshes, bpy.data.curves, bpy.data.armatures,
        bpy.data.materials, bpy.data.cameras, bpy.data.lights,
    ):
        for block in list(datablocks):
            datablocks.remove(block)


def collection(name, parent=None):
    col = bpy.data.collections.new(name)
    (parent.children if parent else bpy.context.scene.collection.children).link(col)
    return col


def move_to(obj, col):
    for old in list(obj.users_collection):
        old.objects.unlink(obj)
    col.objects.link(obj)


def srgb(hex_color):
    value = hex_color.lstrip("#")
    return tuple(int(value[i:i + 2], 16) / 255 for i in (0, 2, 4))


def srgb_to_linear(channel):
    return channel / 12.92 if channel <= 0.04045 else ((channel + 0.055) / 1.055) ** 2.4


def material(name, hex_color, roughness, specular=0.45, metallic=0.0):
    display_color = srgb(hex_color)
    color = tuple(srgb_to_linear(channel) for channel in display_color)
    mat = bpy.data.materials.new(name)
    mat.diffuse_color = (*display_color, 1)
    mat.use_nodes = True
    bsdf = next(node for node in mat.node_tree.nodes if node.type == "BSDF_PRINCIPLED")
    bsdf.inputs["Base Color"].default_value = (*color, 1)
    bsdf.inputs["Roughness"].default_value = roughness
    bsdf.inputs["Metallic"].default_value = metallic
    if "Specular IOR Level" in bsdf.inputs:
        bsdf.inputs["Specular IOR Level"].default_value = specular
    return mat


def create_orange_peel_normal():
    import numpy as np

    width, height = 1024, 512
    rng = np.random.default_rng(20260904)
    # Sparse oil-gland seeds blurred into discrete round pits. This avoids the
    # connected worm-like ridges produced by a continuous noise field.
    seeds = (rng.random((height, width)) > 0.982).astype(np.float32)
    field = seeds
    for _ in range(2):
        field = (
            field * 4
            + np.roll(field, 1, 0) + np.roll(field, -1, 0)
            + np.roll(field, 1, 1) + np.roll(field, -1, 1)
        ) / 8.0
    field /= max(float(field.max()), 1e-6)
    fine = rng.random((height, width), dtype=np.float32) - 0.5
    height_field = -field * 0.82 + fine * 0.035
    grad_y, grad_x = np.gradient(height_field)
    strength = 4.2
    nx = -grad_x * strength
    ny = grad_y * strength
    nz = np.ones_like(nx)
    length = np.sqrt(nx * nx + ny * ny + nz * nz)
    normal = np.stack((nx / length, ny / length, nz / length), axis=-1)
    normal = normal * 0.5 + 0.5
    alpha = np.ones((height, width, 1), dtype=np.float32)
    pixels = np.concatenate((normal, alpha), axis=-1)

    TEXTURES.mkdir(parents=True, exist_ok=True)
    path = TEXTURES / "orange-peel-normal.png"
    image = bpy.data.images.new("T_OrangeSpirit_Peel_Normal", width=width, height=height, alpha=True, float_buffer=False)
    image.colorspace_settings.name = "Non-Color"
    image.pixels.foreach_set(pixels.ravel())
    image.filepath_raw = str(path)
    image.file_format = "PNG"
    image.save()
    return image


def attach_normal_map(mat, image):
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    bsdf = next(node for node in nodes if node.type == "BSDF_PRINCIPLED")
    tex = nodes.new("ShaderNodeTexImage")
    tex.name = "TEX_OrangePeelNormal"
    tex.image = image
    tex.interpolation = "Linear"
    normal = nodes.new("ShaderNodeNormalMap")
    normal.name = "NRM_OrangePeel"
    normal.inputs["Strength"].default_value = 0.48
    links.new(tex.outputs["Color"], normal.inputs["Color"])
    links.new(normal.outputs["Normal"], bsdf.inputs["Normal"])


def smooth(obj):
    if obj.type == "MESH":
        for poly in obj.data.polygons:
            poly.use_smooth = True


def uv_sphere(name, location, scale, mat, segments=64, rings=40, texture=0.0, flatten_bottom=False):
    bpy.ops.mesh.primitive_uv_sphere_add(
        segments=segments, ring_count=rings, location=location,
    )
    obj = bpy.context.object
    obj.name = name
    if texture:
        for vertex in obj.data.vertices:
            direction = vertex.co.normalized()
            grain = noise.noise(direction * 42.0)
            fine = noise.noise(direction * 88.0)
            # Orange peel is dense micro-pitting, not broad smooth waves.
            pores = -abs(fine) ** 1.65
            vertex.co *= 1 + texture * (0.35 * grain + 0.65 * pores)
    if flatten_bottom:
        for vertex in obj.data.vertices:
            vertex.co.z = max(vertex.co.z, -0.90)
    obj.scale = scale
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    obj.data.materials.append(mat)
    smooth(obj)
    return obj


def cylinder(name, location, radius, depth, mat, vertices=48):
    bpy.ops.mesh.primitive_cylinder_add(
        vertices=vertices, radius=radius, depth=depth, location=location,
    )
    obj = bpy.context.object
    obj.name = name
    obj.data.materials.append(mat)
    bevel = obj.modifiers.new("MOD_SoftEdge", "BEVEL")
    bevel.width = min(radius * 0.22, 0.018)
    bevel.segments = 3
    smooth(obj)
    return obj


def curve_object(name, points, bevel, mat, cyclic=False):
    curve = bpy.data.curves.new(name, "CURVE")
    curve.dimensions = "3D"
    curve.resolution_u = 3
    curve.bevel_depth = bevel
    curve.bevel_resolution = 3
    spline = curve.splines.new("BEZIER")
    spline.bezier_points.add(len(points) - 1)
    for bp, point in zip(spline.bezier_points, points):
        bp.co = point
        bp.handle_left_type = "AUTO"
        bp.handle_right_type = "AUTO"
    spline.use_cyclic_u = cyclic
    obj = bpy.data.objects.new(name, curve)
    bpy.context.scene.collection.objects.link(obj)
    obj.data.materials.append(mat)
    return obj


def make_leaf(name, base, tip, half_width, mat, vein_mat):
    """Build a reference-locked almond leaf directly in world coordinates.

    The generated sheet shows long pointed leaves with a raised center ridge,
    shallow transverse cup and tapered attachment.  Building in world space
    keeps that silhouette stable in the front/right/back comparison cameras.
    """
    u_count, v_count = 31, 11
    base = Vector(base)
    tip = Vector(tip)
    direction = tip - base
    side = Vector((direction.z, 0.0, -direction.x)).normalized()

    def surface_point(u, v, front_offset=0.0):
        phase = math.sin(math.pi * u)
        width_profile = half_width * phase ** 0.70 * (0.90 + 0.10 * u)
        point = base.lerp(tip, u)
        point += side * (width_profile * v)
        # Longitudinal arch plus a shallow center groove/cup.  Negative Y is
        # toward the front comparison camera.
        point.z += 0.030 * phase * (1.0 - 0.28 * abs(v))
        point.y += -0.032 * phase * (1.0 - 0.76 * v * v) + front_offset
        return point

    verts, faces = [], []
    for iu in range(u_count):
        u = iu / (u_count - 1)
        for iv in range(v_count):
            v = -1 + 2 * iv / (v_count - 1)
            verts.append(tuple(surface_point(u, v)))
    for iu in range(u_count - 1):
        for iv in range(v_count - 1):
            a = iu * v_count + iv
            faces.append((a, a + 1, a + v_count + 1, a + v_count))
    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata(verts, [], faces)
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.scene.collection.objects.link(obj)
    obj.data.materials.append(mat)
    solid = obj.modifiers.new("MOD_LeafThickness", "SOLIDIFY")
    solid.thickness = 0.014
    bevel = obj.modifiers.new("MOD_LeafSoftness", "BEVEL")
    bevel.width = 0.0045
    bevel.segments = 3
    smooth(obj)

    veins = [curve_object(
        f"SM_{name[3:]}_Vein",
        [tuple(surface_point(0.035, 0.0, -0.007)),
         tuple(surface_point(0.50, 0.0, -0.007)),
         tuple(surface_point(0.94, 0.0, -0.007))],
        0.0026,
        vein_mat,
    )]
    index = 1
    for u in (0.28, 0.46, 0.64):
        for v in (-0.72, 0.72):
            veins.append(curve_object(
                f"SM_{name[3:]}_SideVein_{index:02d}",
                [tuple(surface_point(u, 0.0, -0.0075)),
                 tuple(surface_point(min(u + 0.14, 0.88), v, -0.0075))],
                0.00125,
                vein_mat,
            ))
            index += 1
    # The supplied back view keeps the same botanical structure readable.
    # Duplicate a restrained set on the reverse surface instead of relying on
    # thick curves bleeding through the leaf.
    veins.append(curve_object(
        f"SM_{name[3:]}_BackVein",
        [tuple(surface_point(0.035, 0.0, 0.013)),
         tuple(surface_point(0.50, 0.0, 0.013)),
         tuple(surface_point(0.94, 0.0, 0.013))],
        0.0022,
        vein_mat,
    ))
    back_index = 1
    for u in (0.30, 0.50, 0.68):
        for v in (-0.68, 0.68):
            veins.append(curve_object(
                f"SM_{name[3:]}_BackSideVein_{back_index:02d}",
                [tuple(surface_point(u, 0.0, 0.0135)),
                 tuple(surface_point(min(u + 0.13, 0.88), v, 0.0135))],
                0.0011,
                vein_mat,
            ))
            back_index += 1
    return obj, veins


def parent_to_bone(obj, armature, bone_name):
    world = obj.matrix_world.copy()
    obj.parent = armature
    obj.parent_type = "BONE"
    obj.parent_bone = bone_name
    obj.matrix_world = world


def create_rig(parts, rig_col):
    bpy.ops.object.armature_add(enter_editmode=True, location=(0, 0, 0))
    arm = bpy.context.object
    arm.name = "ARM_OrangeSpirit"
    arm.data.name = "ARM_OrangeSpirit"
    move_to(arm, rig_col)
    root = arm.data.edit_bones[0]
    root.name = "root"
    root.head = (0, 0, 0)
    root.tail = (0, 0, 0.18)
    specs = {
        "body": ((0, 0, 0.18), (0, 0, 0.88), "root"),
        "face": ((0, -0.20, 0.48), (0, -0.20, 0.74), "body"),
        "eye.L": ((-0.19, -0.22, 0.68), (-0.19, -0.22, 0.79), "face"),
        "eye.R": ((0.19, -0.22, 0.68), (0.19, -0.22, 0.79), "face"),
        "mouth": ((0, -0.23, 0.53), (0, -0.23, 0.62), "face"),
        "arm.L": ((-0.45, 0, 0.56), (-0.66, 0, 0.43), "body"),
        "arm.R": ((0.45, 0, 0.56), (0.66, 0, 0.43), "body"),
        "foot.L": ((-0.20, 0, 0.18), (-0.20, 0, 0.05), "root"),
        "foot.R": ((0.20, 0, 0.18), (0.20, 0, 0.05), "root"),
        "leaf.L": ((-0.03, 0, 1.18), (-0.36, 0, 1.34), "body"),
        "leaf.R": ((0.03, 0, 1.18), (0.36, 0, 1.34), "body"),
    }
    for name, (head, tail, parent) in specs.items():
        bone = arm.data.edit_bones.new(name)
        bone.head = head
        bone.tail = tail
        bone.parent = arm.data.edit_bones[parent]
    bpy.ops.object.mode_set(mode="POSE")
    for bone in arm.pose.bones:
        bone.rotation_mode = "XYZ"
    bpy.ops.object.mode_set(mode="OBJECT")
    for bone_name, objects in parts.items():
        for obj in objects:
            parent_to_bone(obj, arm, bone_name)
    return arm


def reset_pose(arm):
    for bone in arm.pose.bones:
        bone.location = (0, 0, 0)
        bone.rotation_euler = (0, 0, 0)
        bone.scale = (1, 1, 1)


def pose_key(arm, bone_name, frame, location=None, rotation=None, scale=None):
    bone = arm.pose.bones[bone_name]
    if location is not None:
        bone.location = location
        bone.keyframe_insert("location", frame=frame)
    if rotation is not None:
        bone.rotation_euler = rotation
        bone.keyframe_insert("rotation_euler", frame=frame)
    if scale is not None:
        bone.scale = scale
        bone.keyframe_insert("scale", frame=frame)


def action(arm, name, frame_end, keys, loop=False):
    reset_pose(arm)
    act = bpy.data.actions.new(name)
    arm.animation_data_create()
    arm.animation_data.action = act
    for bone_name, frame, location, rotation, scale in keys:
        pose_key(arm, bone_name, frame, location, rotation, scale)
    act.frame_start = 1
    act.frame_end = frame_end
    act.use_fake_user = True
    # Blender 5.2 stores keyed curves in layered Action channelbags rather than
    # exposing Action.fcurves. Keyframes already default to Bezier; the web
    # runtime owns clip repetition, so a metadata flag is sufficient here.
    act["web_loop"] = loop
    return act


def create_actions(arm):
    action(arm, "Idle", 60, [
        ("root", 1, (0, 0, 0), (0, 0, -0.018), None),
        ("root", 30, (0, 0, 0.026), (0, 0, 0.018), None),
        ("root", 60, (0, 0, 0), (0, 0, -0.018), None),
        ("leaf.L", 1, None, (0, 0.04, 0), None),
        ("leaf.L", 30, None, (0, -0.05, 0.03), None),
        ("leaf.L", 60, None, (0, 0.04, 0), None),
        ("leaf.R", 1, None, (0, -0.04, 0), None),
        ("leaf.R", 30, None, (0, 0.05, -0.03), None),
        ("leaf.R", 60, None, (0, -0.04, 0), None),
    ], loop=True)
    action(arm, "Blink", 12, [
        ("eye.L", 1, None, None, (1, 1, 1)),
        ("eye.R", 1, None, None, (1, 1, 1)),
        ("eye.L", 5, (0, 0.0432, 0.17424), None, (1, 0.28, 0.28)),
        ("eye.R", 5, (0, 0.0432, 0.17424), None, (1, 0.28, 0.28)),
        ("eye.L", 8, (0, 0.0432, 0.17424), None, (1, 0.28, 0.28)),
        ("eye.R", 8, (0, 0.0432, 0.17424), None, (1, 0.28, 0.28)),
        ("eye.L", 12, (0, 0, 0), None, (1, 1, 1)),
        ("eye.R", 12, (0, 0, 0), None, (1, 1, 1)),
    ])
    action(arm, "Listen", 48, [
        ("body", 1, None, (0, 0, 0), None),
        ("body", 18, None, (0.02, -0.06, -0.10), None),
        ("body", 34, None, (-0.01, 0.04, 0.07), None),
        ("body", 48, None, (0, 0, 0), None),
        ("leaf.L", 1, None, (0, 0, 0), None),
        ("leaf.L", 18, None, (0.12, 0, -0.10), None),
        ("leaf.L", 48, None, (0, 0, 0), None),
    ])
    action(arm, "Think", 60, [
        ("body", 1, None, (0, 0, 0), None),
        ("body", 20, None, (0.02, -0.08, -0.12), None),
        ("body", 40, None, (-0.01, 0.06, 0.10), None),
        ("body", 60, None, (0, 0, 0), None),
        ("arm.R", 20, None, (0.20, -0.35, -0.85), None),
        ("arm.R", 60, None, (0, 0, 0), None),
    ], loop=True)
    action(arm, "Speak", 24, [
        ("mouth", 1, None, None, (1, 1, 1)),
        ("mouth", 6, None, None, (1.10, 1, 1.25)),
        ("mouth", 12, None, None, (0.94, 1, 0.82)),
        ("mouth", 18, None, None, (1.12, 1, 1.30)),
        ("mouth", 24, None, None, (1, 1, 1)),
        ("body", 1, None, (0, 0, -0.02), None),
        ("body", 12, None, (0, 0, 0.02), None),
        ("body", 24, None, (0, 0, -0.02), None),
    ], loop=True)
    action(arm, "Wave", 48, [
        ("arm.R", 1, None, (0, 0, 0), None),
        ("arm.R", 10, None, (0.15, -0.25, -1.20), None),
        ("arm.R", 20, None, (-0.18, -0.22, -0.75), None),
        ("arm.R", 30, None, (0.18, -0.25, -1.20), None),
        ("arm.R", 40, None, (-0.12, -0.22, -0.78), None),
        ("arm.R", 48, None, (0, 0, 0), None),
        ("body", 10, None, (0, 0, 0.06), None),
        ("body", 30, None, (0, 0, -0.04), None),
        ("body", 48, None, (0, 0, 0), None),
    ])
    action(arm, "Celebrate", 54, [
        ("arm.L", 1, None, (0, 0, 0), None),
        ("arm.R", 1, None, (0, 0, 0), None),
        ("arm.L", 16, None, (0, 0.18, 1.18), None),
        ("arm.R", 16, None, (0, -0.18, -1.18), None),
        ("root", 1, (0, 0, 0), None, None),
        ("root", 20, (0, 0, 0.16), None, None),
        ("root", 36, (0, 0, 0), None, None),
        ("root", 44, (0, 0, 0.08), None, None),
        ("root", 54, (0, 0, 0), None, None),
        ("arm.L", 54, None, (0, 0, 0), None),
        ("arm.R", 54, None, (0, 0, 0), None),
    ])
    action(arm, "Error", 36, [
        ("body", 1, None, (0, 0, 0), None),
        ("body", 7, None, (0, 0, -0.10), None),
        ("body", 13, None, (0, 0, 0.10), None),
        ("body", 19, None, (0, 0, -0.10), None),
        ("body", 25, None, (0, 0, 0.10), None),
        ("body", 36, None, (0, 0, 0), None),
        ("leaf.L", 1, None, (0, 0, 0), None),
        ("leaf.L", 36, None, (0.32, 0, 0), None),
        ("leaf.R", 1, None, (0, 0, 0), None),
        ("leaf.R", 36, None, (-0.32, 0, 0), None),
    ])
    action(arm, "Sleep", 72, [
        ("body", 1, None, (0, 0, 0), None),
        ("body", 28, None, (0.08, 0, 0.13), None),
        ("body", 72, None, (0.08, 0, 0.13), None),
        ("eye.L", 1, None, None, (1, 1, 1)),
        ("eye.R", 1, None, None, (1, 1, 1)),
        ("eye.L", 28, None, None, (1, 1, 0.14)),
        ("eye.R", 28, None, None, (1, 1, 0.14)),
        ("eye.L", 72, None, None, (1, 1, 0.14)),
        ("eye.R", 72, None, None, (1, 1, 0.14)),
        ("leaf.L", 28, None, (0.25, 0, 0), None),
        ("leaf.R", 28, None, (-0.25, 0, 0), None),
    ], loop=True)
    action(arm, "Bounce", 36, [
        ("root", 1, (0, 0, 0), None, None),
        ("root", 6, (0, 0, 0), None, None),
        ("root", 10, (0, 0.045, 0), None, None),
        ("root", 16, (0, 0.085, 0), None, None),
        ("root", 21, (0, 0.045, 0), None, None),
        ("root", 24, (0, 0, 0), None, None),
        ("root", 29, (0, 0.035, 0), None, None),
        ("root", 33, (0, 0, 0), None, None),
        ("root", 36, (0, 0, 0), None, None),
        ("body", 1, (0, 0, 0), (0, 0, 0), None),
        ("body", 6, (0, -0.06, 0), (0.035, 0, 0), None),
        ("body", 10, (0, 0.015, 0), (-0.025, 0, 0), None),
        ("body", 16, (0, 0.005, 0), (0, 0, 0), None),
        ("body", 21, (0, 0, 0), (0.015, 0, 0), None),
        ("body", 24, (0, -0.045, 0), (0.03, 0, 0), None),
        ("body", 29, (0, 0.012, 0), (-0.018, 0, 0), None),
        ("body", 33, (0, -0.012, 0), (0.008, 0, 0), None),
        ("body", 36, (0, 0, 0), (0, 0, 0), None),
        ("foot.L", 1, (0, 0, 0), (0, 0, 0), None),
        ("foot.L", 6, (0, 0, 0), (0, -0.05, -0.08), None),
        ("foot.L", 10, (0.018, -0.012, 0), (0, 0.08, 0.08), None),
        ("foot.L", 16, (0.045, -0.035, 0), (0, -0.18, 0.20), None),
        ("foot.L", 24, (0, 0, 0), (0, 0.08, -0.08), None),
        ("foot.L", 29, (0.012, -0.008, 0), (0, -0.06, 0.06), None),
        ("foot.L", 36, (0, 0, 0), (0, 0, 0), None),
        ("foot.R", 1, (0, 0, 0), (0, 0, 0), None),
        ("foot.R", 6, (0, 0, 0), (0, 0.05, 0.08), None),
        ("foot.R", 10, (-0.018, -0.012, 0), (0, -0.08, -0.08), None),
        ("foot.R", 16, (-0.045, -0.035, 0), (0, 0.18, -0.20), None),
        ("foot.R", 24, (0, 0, 0), (0, -0.08, 0.08), None),
        ("foot.R", 29, (-0.012, -0.008, 0), (0, 0.06, -0.06), None),
        ("foot.R", 36, (0, 0, 0), (0, 0, 0), None),
        ("arm.L", 1, None, (0, 0, 0), None),
        ("arm.L", 6, None, (0.06, 0.05, -0.20), None),
        ("arm.L", 10, None, (-0.04, 0.08, 0.28), None),
        ("arm.L", 16, None, (-0.08, 0.14, 0.82), None),
        ("arm.L", 24, None, (0.08, 0.06, -0.22), None),
        ("arm.L", 29, None, (-0.03, 0.04, 0.22), None),
        ("arm.L", 36, None, (0, 0, 0), None),
        ("arm.R", 1, None, (0, 0, 0), None),
        ("arm.R", 6, None, (0.06, -0.05, 0.20), None),
        ("arm.R", 10, None, (-0.04, -0.08, -0.28), None),
        ("arm.R", 16, None, (-0.08, -0.14, -0.82), None),
        ("arm.R", 24, None, (0.08, -0.06, 0.22), None),
        ("arm.R", 29, None, (-0.03, -0.04, -0.22), None),
        ("arm.R", 36, None, (0, 0, 0), None),
        ("leaf.L", 1, None, (0, 0, 0), None),
        ("leaf.L", 6, None, (0.09, -0.025, -0.08), None),
        ("leaf.L", 10, None, (-0.06, 0.025, 0.07), None),
        ("leaf.L", 16, None, (-0.10, 0.04, 0.11), None),
        ("leaf.L", 24, None, (-0.12, 0.045, 0.14), None),
        ("leaf.L", 29, None, (0.055, -0.02, -0.065), None),
        ("leaf.L", 36, None, (0, 0, 0), None),
        ("leaf.R", 1, None, (0, 0, 0), None),
        ("leaf.R", 6, None, (-0.09, 0.025, 0.08), None),
        ("leaf.R", 10, None, (0.06, -0.025, -0.07), None),
        ("leaf.R", 16, None, (0.10, -0.04, -0.11), None),
        ("leaf.R", 24, None, (0.12, -0.045, -0.14), None),
        ("leaf.R", 29, None, (-0.055, 0.02, 0.065), None),
        ("leaf.R", 36, None, (0, 0, 0), None),
    ])
    action(arm, "Spin", 48, [
        ("root", 1, None, (0, 0, 0), None),
        ("root", 48, None, (0, math.tau, 0), None),
    ])
    action(arm, "Shy", 54, [
        ("body", 1, None, (0, 0, 0), None),
        ("body", 24, None, (0.06, 0.08, -0.08), None),
        ("body", 54, None, (0, 0, 0), None),
        ("arm.L", 24, None, (0.35, 0.20, -0.75), None),
        ("arm.R", 24, None, (0.35, -0.20, 0.75), None),
        ("arm.L", 54, None, (0, 0, 0), None),
        ("arm.R", 54, None, (0, 0, 0), None),
    ])
    action(arm, "Mischief", 42, [
        # Anticipation: the body dips and leans right without moving the root.
        ("body", 1, (0, 0, 0), (0, 0, 0), None),
        ("body", 8, (0.035, -0.035, 0), (0.025, -0.055, -0.13), None),
        ("body", 15, (0.030, -0.025, 0), (-0.015, 0.035, -0.105), None),
        ("body", 24, (0.015, -0.012, 0), (0.01, -0.025, 0.055), None),
        ("body", 32, (0.006, -0.004, 0), (0, 0.01, -0.02), None),
        ("body", 42, (0, 0, 0), (0, 0, 0), None),
        # The character keeps its left eye open and winks only with eye.R.
        ("eye.R", 1, (0, 0, 0), None, (1, 1, 1)),
        ("eye.R", 8, (0, 0, 0), None, (1, 1, 1)),
        ("eye.R", 12, (0, 0.0432, 0.17424), None, (1, 0.28, 0.28)),
        ("eye.R", 15, (0, 0.0432, 0.17424), None, (1, 0.28, 0.28)),
        ("eye.R", 20, (0, 0, 0), None, (1, 1, 1)),
        ("eye.R", 42, (0, 0, 0), None, (1, 1, 1)),
        # Offset arm beats and leaf flicks keep the pose playful but compact.
        ("arm.L", 1, None, (0, 0, 0), None),
        ("arm.L", 8, None, (0.06, 0.08, 0.35), None),
        ("arm.L", 14, None, (0.12, 0.20, 0.72), None),
        ("arm.L", 22, None, (-0.10, 0.08, 0.28), None),
        ("arm.L", 30, None, (0.04, 0.03, -0.12), None),
        ("arm.L", 42, None, (0, 0, 0), None),
        ("arm.R", 1, None, (0, 0, 0), None),
        ("arm.R", 8, None, (-0.04, -0.06, -0.25), None),
        ("arm.R", 13, None, (-0.08, -0.18, -0.76), None),
        ("arm.R", 21, None, (0.10, -0.10, -0.25), None),
        ("arm.R", 28, None, (-0.03, -0.03, 0.18), None),
        ("arm.R", 42, None, (0, 0, 0), None),
        ("leaf.L", 1, None, (0, 0, 0), None),
        ("leaf.L", 8, None, (0.06, -0.04, -0.08), None),
        ("leaf.L", 14, None, (0.14, -0.08, -0.17), None),
        ("leaf.L", 21, None, (-0.08, 0.05, 0.10), None),
        ("leaf.L", 30, None, (0.03, -0.02, -0.04), None),
        ("leaf.L", 42, None, (0, 0, 0), None),
        ("leaf.R", 1, None, (0, 0, 0), None),
        ("leaf.R", 10, None, (-0.05, 0.03, 0.06), None),
        ("leaf.R", 16, None, (-0.13, 0.08, 0.16), None),
        ("leaf.R", 24, None, (0.075, -0.045, -0.09), None),
        ("leaf.R", 32, None, (-0.025, 0.015, 0.03), None),
        ("leaf.R", 42, None, (0, 0, 0), None),
    ])
    arm.animation_data.action = bpy.data.actions["Idle"]
    reset_pose(arm)


def look_at(obj, target=(0, 0, 0.70)):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()


def setup_render(light_col, camera_col):
    scene = bpy.context.scene
    scene.render.engine = "BLENDER_EEVEE"
    scene.render.resolution_x = 720
    scene.render.resolution_y = 720
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.film_transparent = False
    scene.render.image_settings.color_mode = "RGBA"
    scene.render.fps = FPS
    scene.view_settings.view_transform = "Standard"
    scene.view_settings.look = "None"
    world = scene.world or bpy.data.worlds.new("World")
    scene.world = world
    world.use_nodes = True
    bg = world.node_tree.nodes.get("Background")
    bg.inputs["Color"].default_value = (0.94, 0.94, 0.94, 1)
    bg.inputs["Strength"].default_value = 0.55

    for name, location, energy, color, size in [
        ("LGT_Key", (-3.2, -4.0, 4.5), 360, (1.0, 1.0, 1.0), 4.2),
        ("LGT_Fill", (3.0, -2.6, 2.2), 170, (0.90, 0.95, 1.0), 3.5),
        ("LGT_Rim", (0.5, 2.8, 3.7), 230, (0.94, 1.0, 0.90), 2.5),
    ]:
        bpy.ops.object.light_add(type="AREA", location=location)
        light = bpy.context.object
        light.name = name
        light.data.energy = energy
        light.data.color = color
        light.data.shape = "DISK"
        light.data.size = size
        look_at(light)
        move_to(light, light_col)

    bpy.ops.object.camera_add(location=(0, -5.2, 0.76))
    camera = bpy.context.object
    camera.name = "CAM_OrangeSpirit"
    camera.data.type = "ORTHO"
    camera.data.ortho_scale = 1.72
    look_at(camera, (0, 0, 0.70))
    move_to(camera, camera_col)
    scene.camera = camera
    return camera


def render_views(camera, arm):
    PREVIEWS.mkdir(parents=True, exist_ok=True)
    scene = bpy.context.scene
    arm.animation_data.action = bpy.data.actions["Idle"]
    scene.frame_set(1)
    views = {
        "front": ((0, -5.2, 0.76), (0, 0, 0.70)),
        "right": ((5.2, 0, 0.76), (0, 0, 0.70)),
        "back": ((0, 5.2, 0.76), (0, 0, 0.70)),
        "three-quarter": ((3.6, -3.6, 1.00), (0, 0, 0.72)),
    }
    for label, (location, target) in views.items():
        camera.location = location
        look_at(camera, target)
        scene.render.filepath = str(PREVIEWS / f"orange-spirit-{PASS_NAME}-{label}.png")
        bpy.ops.render.render(write_still=True)


def main():
    clean_scene()
    root_col = collection("COL_OrangeSpirit")
    ref_col = collection("COL_Reference", root_col)
    geo_col = collection("COL_Geo", root_col)
    rig_col = collection("COL_Rig", root_col)
    light_col = collection("COL_Lights", root_col)
    camera_col = collection("COL_Cameras", root_col)
    export_col = collection("COL_Export", root_col)
    ref_col.hide_render = True

    orange = material("MAT_OrangeSkin_F58220", "#F58220", 0.52, 0.25)
    attach_normal_map(orange, create_orange_peel_normal())
    leaf = material("MAT_Leaf_55A630", "#55A630", 0.42, 0.35)
    leaf_dark = material("MAT_LeafVein_2F7D32", "#2F7D32", 0.48, 0.30)
    stem_mat = material("MAT_Stem_6B3E1E", "#6B3E1E", 0.58, 0.25)
    face_mat = material("MAT_Face_3A2418", "#3A2418", 0.22, 0.55)
    cheek_mat = material("MAT_Cheek_FF8F8F", "#FF8F8F", 0.44, 0.35)

    body = uv_sphere("SM_OrangeSpirit_Body", (0, 0, 0.67), (0.56, 0.47, 0.54), orange, 128, 96, 0.004, True)
    stem = cylinder("SM_OrangeSpirit_Stem", (0, 0, 1.255), 0.055, 0.20, stem_mat)
    stem.scale = (1.0, 0.88, 1.0)
    leaf_l, veins_l = make_leaf(
        "SM_OrangeSpirit_Leaf_L",
        (-0.035, 0.018, 1.205), (-0.475, -0.045, 1.392), 0.108,
        leaf, leaf_dark,
    )
    leaf_r, veins_r = make_leaf(
        "SM_OrangeSpirit_Leaf_R",
        (0.035, 0.026, 1.205), (0.505, 0.295, 1.405), 0.108,
        leaf, leaf_dark,
    )

    eye_l = uv_sphere("SM_OrangeSpirit_Eye_L", (-0.19, -0.462, 0.74), (0.052, 0.025, 0.098), face_mat, 32, 20)
    eye_r = uv_sphere("SM_OrangeSpirit_Eye_R", (0.19, -0.462, 0.74), (0.052, 0.025, 0.098), face_mat, 32, 20)
    cheek_l = uv_sphere("SM_OrangeSpirit_Cheek_L", (-0.31, -0.455, 0.60), (0.074, 0.018, 0.041), cheek_mat, 32, 18)
    cheek_r = uv_sphere("SM_OrangeSpirit_Cheek_R", (0.31, -0.455, 0.60), (0.074, 0.018, 0.041), cheek_mat, 32, 18)
    mouth = curve_object("SM_OrangeSpirit_Mouth", [
        (-0.095, -0.478, 0.605), (-0.050, -0.485, 0.560),
        (0, -0.488, 0.548), (0.050, -0.485, 0.560), (0.095, -0.478, 0.605),
    ], 0.013, face_mat)

    arm_l = uv_sphere("SM_OrangeSpirit_Arm_L", (-0.565, -0.005, 0.49), (0.09, 0.095, 0.15), orange, 40, 24, 0.001)
    arm_l.rotation_euler.y = -0.25
    arm_r = uv_sphere("SM_OrangeSpirit_Arm_R", (0.565, -0.005, 0.49), (0.09, 0.095, 0.15), orange, 40, 24, 0.001)
    arm_r.rotation_euler.y = 0.25
    foot_l = uv_sphere("SM_OrangeSpirit_Foot_L", (-0.20, -0.055, 0.105), (0.15, 0.18, 0.11), orange, 48, 28, 0.001)
    foot_r = uv_sphere("SM_OrangeSpirit_Foot_R", (0.20, -0.055, 0.105), (0.15, 0.18, 0.11), orange, 48, 28, 0.001)
    for foot in (foot_l, foot_r):
        for vertex in foot.data.vertices:
            vertex.co.z = max(vertex.co.z, -0.105)

    mesh_or_curves = [body, stem, leaf_l, leaf_r, *veins_l, *veins_r, eye_l, eye_r, cheek_l, cheek_r, mouth, arm_l, arm_r, foot_l, foot_r]
    for obj in mesh_or_curves:
        move_to(obj, geo_col)
        obj["asset_role"] = "orange_spirit_component"

    parts = {
        "body": [body, stem],
        "face": [cheek_l, cheek_r],
        "eye.L": [eye_l],
        "eye.R": [eye_r],
        "mouth": [mouth],
        "arm.L": [arm_l],
        "arm.R": [arm_r],
        "foot.L": [foot_l],
        "foot.R": [foot_r],
        "leaf.L": [leaf_l, *veins_l],
        "leaf.R": [leaf_r, *veins_r],
    }
    arm = create_rig(parts, rig_col)
    create_actions(arm)

    camera = setup_render(light_col, camera_col)
    scene = bpy.context.scene
    scene["asset_name"] = "Orange Spirit"
    scene["asset_version"] = "V1.0.3"
    scene["reference_sha256"] = "351b8c57500ef3c6f52039ddeee84ae5388bb0ca88ad88039f52d7a213ec226a"
    scene["license_note"] = "Original mascot asset; Copyright © 2026 Nankong"
    scene.frame_start = 1
    scene.frame_end = 60

    BLEND.parent.mkdir(parents=True, exist_ok=True)
    GLB.parent.mkdir(parents=True, exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=str(BLEND))
    bpy.ops.export_scene.gltf(
        filepath=str(GLB),
        export_format="GLB",
        export_animations=True,
        export_animation_mode="ACTIONS",
        export_apply=False,
        export_yup=True,
    )
    render_views(camera, arm)
    bpy.ops.wm.save_as_mainfile(filepath=str(BLEND))


main()
