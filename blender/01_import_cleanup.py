"""STEP 1 (in Blender) - import a generated GLB, clean it, size it, stand it on the ground.

Run through MCP for Blender (execute_blender_code), e.g.:
    OVERRIDES = {"GLB": r"D:/path/demo-monkey/out/model.glb", "NAME": "BabyMonkey", "HEIGHT": 0.8}
    exec(open(r"D:/path/demo-monkey/blender/01_import_cleanup.py", encoding="utf-8").read())
or open it in Blender's Text Editor, edit CONFIG and press Run Script.

What it does
- creates/uses a scene, imports the GLB, unparents the mesh from the glTF root empty
- applies transforms, merges duplicate vertices (TRELLIS meshes are triangle soup)
- removes a flat "ground disc" that image-to-3D models often build from the shadow
- scales to HEIGHT metres, centres X, feet at Z=0 (model faces -Y = Blender front)
After running, LOOK at the model (front/right/back) before rigging.
"""
import math

import bmesh
import bpy
import mathutils

CONFIG = dict(
    GLB=None,              # absolute path to the .glb (required)
    NAME="Character",      # object name for the mesh
    HEIGHT=0.8,            # metres, top of head/ears to feet
    MERGE_DIST=0.0003,     # merge-by-distance in model units before scaling
    REMOVE_DISC=True,
    NEW_SCENE=None,        # e.g. "BabyMonkey" to import into a fresh scene
)
CONFIG.update(globals().get("OVERRIDES", {}))


def remove_ground_disc(me):
    """Delete large flat horizontal layers that stick out far beyond the body."""
    bm = bmesh.new()
    bm.from_mesh(me)
    bm.normal_update()
    zs = [v.co.z for v in bm.verts]
    zmin, zmax = min(zs), max(zs)
    h = zmax - zmin
    bins = {}
    for f in bm.faces:
        if abs(f.normal.z) > 0.9:
            c = f.calc_center_median()
            bins.setdefault(int((c.z - zmin) / (h * 0.01)), []).append(f)
    removed = 0
    for b, faces in bins.items():
        faces = [f for f in faces if f.is_valid]  # an earlier bin may have deleted some
        if not faces:
            continue
        zc = zmin + (b + 0.5) * h * 0.01
        band = h * 0.03
        body = [v.co for v in bm.verts if abs(v.co.z - zc) < band * 3 and abs(v.co.z - zc) > band]
        if len(body) < 20:
            continue
        cx = sum(p.x for p in body) / len(body)
        cy = sum(p.y for p in body) / len(body)
        radii = sorted(math.hypot(p.x - cx, p.y - cy) for p in body)
        body_r = radii[int(len(radii) * 0.98)]
        fr = max(math.hypot(v.co.x - cx, v.co.y - cy) for f in faces for v in f.verts)
        if fr < body_r * 1.6 or len(faces) < 50:
            continue
        kill_f = [f for f in bm.faces if f.is_valid and abs(f.normal.z) > 0.9
                  and all(abs(v.co.z - zc) < band for v in f.verts)]
        bmesh.ops.delete(bm, geom=kill_f, context="FACES")
        kill_v = [v for v in bm.verts if abs(v.co.z - zc) < band
                  and math.hypot(v.co.x - cx, v.co.y - cy) > body_r * 1.05]
        bmesh.ops.delete(bm, geom=kill_v, context="VERTS")
        removed += len(kill_f) + len(kill_v)
        print(f"disc removed at z={zc:.3f}: body radius {body_r:.3f}, layer radius {fr:.3f}")
    bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_faces], context="VERTS")
    bm.to_mesh(me)
    bm.free()
    return removed


def main():
    if not CONFIG["GLB"]:
        raise SystemExit("Set OVERRIDES['GLB'] to the absolute path of the .glb")
    if CONFIG["NEW_SCENE"]:
        sc = bpy.data.scenes.get(CONFIG["NEW_SCENE"]) or bpy.data.scenes.new(CONFIG["NEW_SCENE"])
        bpy.context.window.scene = sc
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=CONFIG["GLB"])
    new = [o for o in bpy.data.objects if o not in before]
    meshes = [o for o in new if o.type == "MESH"]
    if not meshes:
        raise SystemExit("GLB had no mesh")
    m = max(meshes, key=lambda o: len(o.data.vertices))
    for o in meshes:
        if o is not m:
            bpy.data.objects.remove(o)
    mw = m.matrix_world.copy()
    m.parent = None
    m.matrix_world = mw
    for o in new:
        if o.name in bpy.data.objects and o is not m and o.type == "EMPTY":
            bpy.data.objects.remove(o)
    m.name = CONFIG["NAME"]
    bpy.ops.object.select_all(action="DESELECT")
    m.select_set(True)
    bpy.context.view_layer.objects.active = m
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)

    bm = bmesh.new()
    bm.from_mesh(m.data)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=CONFIG["MERGE_DIST"])
    bm.to_mesh(m.data)
    bm.free()
    if CONFIG["REMOVE_DISC"]:
        remove_ground_disc(m.data)

    co = [v.co for v in m.data.vertices]
    zmin = min(c.z for c in co)
    zmax = max(c.z for c in co)
    cx = (min(c.x for c in co) + max(c.x for c in co)) / 2
    cy = (min(c.y for c in co) + max(c.y for c in co)) / 2
    s = CONFIG["HEIGHT"] / (zmax - zmin)
    for v in m.data.vertices:
        v.co = mathutils.Vector(((v.co.x - cx) * s, (v.co.y - cy) * s, (v.co.z - zmin) * s))
    m.data.update()
    co = [v.co for v in m.data.vertices]
    dims = [round(max(c[i] for c in co) - min(c[i] for c in co), 3) for i in range(3)]
    print(f"{m.name}: {len(m.data.vertices)} verts, size {dims} m (x, y, z)")


main()
