"""STEP 3 (in Blender) - build a biped armature (+ optional curly tail) and skin the mesh.

    OVERRIDES = {"MESH": "BabyMonkey"}          # joints default to the baby monkey (0.8 m tall)
    exec(open(r".../blender/03_rig_biped.py", encoding="utf-8").read())

For a NEW character: run 02_render_reference.py, read the joint pixels, convert to metres
and pass them as OVERRIDES["JOINTS"] (same keys as below). Model must face -Y, feet at Z=0.

Lessons baked in (each one cost a debugging round):
- Bone roll is recalculated to GLOBAL_NEG_Y so every limb bends on predictable axes:
    thigh/shin/upper_arm/forearm rot X+ = swing FORWARD, shin X- = bend knee
    upper_arm Z+ (L) / Z- (R) = raise arm sideways
    spine/head rot X+ = lean/nod forward, Y = twist, Z = side tilt
    hips location Y = up/down, root location Y = move forward (world -Y)
- Automatic (heat) weights FAIL on small or open AI meshes ("Bone Heat Weighting failed").
  Fix: scale everything x10, skin, scale back.
- Big-head characters: arm weights leak into cheeks/ears -> raising arms melts the face.
  Fix: every vertex above HEAD_LOCK_Z goes 100% to head (short blend to neck).
"""
import bmesh
import bpy

Y = -0.04
CONFIG = dict(
    MESH="Character",
    RIG="CharacterRig",
    # bone: (head, tail, parent, connected)
    JOINTS={
        "root": ((0, 0, 0), (0, -0.15, 0), None, False),
        "hips": ((0, Y, 0.20), (0, Y, 0.27), "root", False),
        "spine": ((0, Y, 0.27), (0, Y, 0.36), "hips", True),
        "neck": ((0, Y, 0.36), (0, -0.02, 0.40), "spine", True),
        "head": ((0, -0.02, 0.40), (0, -0.02, 0.70), "neck", True),
        "upper_arm.L": ((0.105, -0.05, 0.345), (0.18, -0.05, 0.255), "spine", False),
        "forearm.L": ((0.18, -0.05, 0.255), (0.212, -0.065, 0.175), "upper_arm.L", True),
        "hand.L": ((0.212, -0.065, 0.175), (0.216, -0.075, 0.12), "forearm.L", True),
        "thigh.L": ((0.072, Y, 0.21), (0.08, -0.04, 0.112), "hips", False),
        "shin.L": ((0.08, -0.04, 0.112), (0.085, -0.025, 0.045), "thigh.L", True),
        "foot.L": ((0.085, -0.025, 0.045), (0.09, -0.13, 0.02), "shin.L", True),
    },
    MIRROR=True,           # build .R bones by mirroring X of the .L bones
    # Optional procedural tail (None to skip). Points in metres, base first.
    TAIL_POINTS=[(0, 0.085, 0.235), (0, 0.15, 0.205), (0, 0.215, 0.195), (0, 0.27, 0.225),
                 (0, 0.295, 0.285), (0, 0.28, 0.345), (0, 0.235, 0.365), (0, 0.20, 0.335),
                 (0, 0.205, 0.295), (0, 0.235, 0.285), (0, 0.255, 0.305), (0, 0.245, 0.325)],
    TAIL_RADIUS=0.024,
    TAIL_COLOR=(0.34, 0.085, 0.03, 1),
    HEAD_LOCK_Z=0.385,     # vertices above -> 100% head
    NECK_BLEND=0.025,
    CHEST_CENTER=(0.33, 0.075),  # (min z, half width): no arm weights in this chest strip
    WEIGHT_SCALE=10.0,
)
CONFIG.update(globals().get("OVERRIDES", {}))
NON_DEFORM = {"root"}


def build_tail(sc):
    pts = CONFIG["TAIL_POINTS"]
    cu = bpy.data.curves.new("TailCurve", "CURVE")
    cu.dimensions = "3D"
    sp = cu.splines.new("BEZIER")
    sp.bezier_points.add(len(pts) - 1)
    for i, (bp, p) in enumerate(zip(sp.bezier_points, pts)):
        bp.co = p
        bp.handle_left_type = bp.handle_right_type = "AUTO"
        bp.radius = 1.0 - 0.55 * i / (len(pts) - 1)
    cu.bevel_depth = CONFIG["TAIL_RADIUS"]
    cu.bevel_resolution = 4
    cu.resolution_u = 12
    cu.use_fill_caps = True
    t = bpy.data.objects.new(CONFIG["MESH"] + "Tail", cu)
    sc.collection.objects.link(t)
    bpy.ops.object.select_all(action="DESELECT")
    t.select_set(True)
    bpy.context.view_layer.objects.active = t
    bpy.ops.object.convert(target="MESH")
    t = bpy.context.active_object
    mat = bpy.data.materials.new("TailFur")
    mat.use_nodes = True
    bsdf = next(n for n in mat.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
    bsdf.inputs["Base Color"].default_value = CONFIG["TAIL_COLOR"]
    bsdf.inputs["Roughness"].default_value = 0.8
    mat.diffuse_color = CONFIG["TAIL_COLOR"]
    t.data.materials.clear()
    t.data.materials.append(mat)
    bpy.ops.object.shade_smooth()
    return t


def build_armature(sc):
    arm = bpy.data.armatures.new(CONFIG["RIG"])
    rig = bpy.data.objects.new(CONFIG["RIG"], arm)
    sc.collection.objects.link(rig)
    bpy.ops.object.select_all(action="DESELECT")
    rig.select_set(True)
    bpy.context.view_layer.objects.active = rig
    bpy.ops.object.mode_set(mode="EDIT")
    eb = arm.edit_bones
    joints = dict(CONFIG["JOINTS"])
    if CONFIG["MIRROR"]:
        for n, (h, t, p, c) in list(joints.items()):
            if n.endswith(".L"):
                mir = lambda v: (-v[0], v[1], v[2])
                pr = p[:-2] + ".R" if p and p.endswith(".L") else p
                joints[n[:-2] + ".R"] = (mir(h), mir(t), pr, c)
    made = {}
    pending = dict(joints)
    while pending:
        for n, (h, t, p, c) in list(pending.items()):
            if p and p not in made:
                continue
            b = eb.new(n)
            b.head, b.tail = h, t
            b.use_deform = n not in NON_DEFORM
            if p:
                b.parent = made[p]
                b.use_connect = c
            made[n] = b
            del pending[n]
    tail_bones = []
    if CONFIG["TAIL_POINTS"]:
        prev = "hips"
        pts = CONFIG["TAIL_POINTS"]
        for i in range(len(pts) - 1):
            n = f"tail.{i:02d}"
            b = eb.new(n)
            b.head, b.tail = pts[i], pts[i + 1]
            b.parent = made[prev]
            b.use_connect = i > 0
            made[n] = b
            tail_bones.append(n)
            prev = n
    for b in eb:
        b.select = b.select_head = b.select_tail = (b.name not in tail_bones and b.name != "root")
    bpy.ops.armature.calculate_roll(type="GLOBAL_NEG_Y")
    for b in eb:
        b.select = b.select_head = b.select_tail = b.name in tail_bones
    if tail_bones:
        bpy.ops.armature.calculate_roll(type="GLOBAL_POS_X")
    bpy.ops.object.mode_set(mode="OBJECT")
    rig.show_in_front = True
    return rig, tail_bones


def apply_scale(objs, s):
    bpy.ops.object.select_all(action="DESELECT")
    for o in objs:
        o.select_set(True)
        o.scale = (s, s, s)
        o.location = o.location * s
    bpy.context.view_layer.objects.active = objs[0]
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)


def dseg(p, a, b):
    ab = b - a
    t = max(0.0, min(1.0, (p - a).dot(ab) / ab.length_squared))
    return (p - (a + ab * t)).length


def skin_body(rig, body, tail_bones):
    s = CONFIG["WEIGHT_SCALE"]
    apply_scale([rig, body], s)
    for n in tail_bones:
        rig.data.bones[n].use_deform = False
    bpy.ops.object.select_all(action="DESELECT")
    body.select_set(True)
    rig.select_set(True)
    bpy.context.view_layer.objects.active = rig
    bpy.ops.object.parent_set(type="ARMATURE_AUTO")
    for n in tail_bones:
        rig.data.bones[n].use_deform = True
    deform = [b for b in rig.data.bones if b.use_deform and b.name not in tail_bones]
    filled = 0
    for v in body.data.vertices:
        if not any(g.weight > 0.01 for g in v.groups):
            n = min(deform, key=lambda b: dseg(v.co, b.head_local, b.tail_local)).name
            (body.vertex_groups.get(n) or body.vertex_groups.new(name=n)).add([v.index], 1.0, "REPLACE")
            filled += 1
    print(f"auto weights done, {filled} unweighted verts filled by nearest bone")
    # detach, scale back, re-attach
    mw = body.matrix_world.copy()
    body.parent = None
    body.matrix_world = mw
    for md in list(body.modifiers):
        body.modifiers.remove(md)
    apply_scale([rig, body], 1.0 / s)
    body.parent = rig
    md = body.modifiers.new("Armature", "ARMATURE")
    md.object = rig


def lock_head(body):
    vg = {g.name: g for g in body.vertex_groups}
    for n in ("head", "neck", "spine"):
        vg.setdefault(n, body.vertex_groups.new(name=n))
    idx = {g.index: g.name for g in body.vertex_groups}
    arm = {n for n in vg if n.split(".")[0] in ("upper_arm", "forearm", "hand")}
    hz, nb = CONFIG["HEAD_LOCK_Z"], CONFIG["NECK_BLEND"]
    cz, cw = CONFIG["CHEST_CENTER"]
    for v in body.data.vertices:
        z = v.co.z
        if z > hz:
            for g in list(v.groups):
                vg[idx[g.group]].remove([v.index])
            if z > hz + nb:
                vg["head"].add([v.index], 1.0, "REPLACE")
            else:
                t = (z - hz) / nb
                vg["head"].add([v.index], t, "REPLACE")
                vg["neck"].add([v.index], 1 - t, "REPLACE")
        elif z > cz and abs(v.co.x) < cw:
            for g in list(v.groups):
                if idx[g.group] in arm:
                    vg[idx[g.group]].remove([v.index])
            if not any(g.weight > 0.01 for g in v.groups):
                vg["spine"].add([v.index], 1.0, "REPLACE")
    bpy.ops.object.select_all(action="DESELECT")
    body.select_set(True)
    bpy.context.view_layer.objects.active = body
    bpy.ops.object.mode_set(mode="WEIGHT_PAINT")
    bpy.ops.object.vertex_group_smooth(group_select_mode="ALL", factor=0.5, repeat=3)
    bpy.ops.object.vertex_group_normalize_all(lock_active=False)
    bpy.ops.object.mode_set(mode="OBJECT")


def skin_tail(rig, tail, tail_bones):
    tail.parent = rig
    md = tail.modifiers.new("Armature", "ARMATURE")
    md.object = rig
    bones = [rig.data.bones[n] for n in tail_bones]
    for b in bones:
        tail.vertex_groups.new(name=b.name)
    for v in tail.data.vertices:
        (d0, n0), (d1, n1) = sorted((dseg(v.co, b.head_local, b.tail_local), b.name) for b in bones)[:2]
        w0 = 1.0 if d1 - d0 > 0.02 else 0.5 + (d1 - d0) / 0.04
        tail.vertex_groups[n0].add([v.index], w0, "REPLACE")
        if w0 < 1:
            tail.vertex_groups[n1].add([v.index], 1 - w0, "REPLACE")


def main():
    sc = bpy.context.scene
    body = bpy.data.objects[CONFIG["MESH"]]
    body.vertex_groups.clear()
    for md in list(body.modifiers):
        body.modifiers.remove(md)
    bm = bmesh.new()
    bm.from_mesh(body.data)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=0.002)  # close cracks so heat weights work
    bm.to_mesh(body.data)
    bm.free()
    tail = build_tail(sc) if CONFIG["TAIL_POINTS"] else None
    rig, tail_bones = build_armature(sc)
    skin_body(rig, body, tail_bones)
    lock_head(body)
    if tail:
        skin_tail(rig, tail, tail_bones)
    for b in rig.pose.bones:
        b.rotation_mode = "XYZ"
    print(f"rig '{rig.name}': {len(rig.data.bones)} bones; tail: {bool(tail)}")


main()
