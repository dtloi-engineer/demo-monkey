"""STEP 5 (in Blender) - stage, warm 3-point lights, sky colour, follow camera, Eevee.

    OVERRIDES = {"RIG": "BabyMonkeyRig", "HEIGHT": 0.8}
    exec(open(r".../blender/05_stage_camera.py", encoding="utf-8").read())

The camera and key/rim lights are children of an empty that copies the rig's root bone
(XY only), so the shot follows the walking character from the side-front.
"""
import math

import bmesh
import bpy

CONFIG = dict(RIG="CharacterRig", HEIGHT=0.8, STAGE_RADIUS=3.0,
              STAGE_COLOR=(0.55, 0.75, 0.45, 1), SKY=(0.55, 0.75, 0.95, 1))
CONFIG.update(globals().get("OVERRIDES", {}))


def light(col, name, kind, loc, rot, energy, color, size=None, parent=None):
    ld = bpy.data.lights.new(name, kind)
    ld.energy = energy
    ld.color = color
    if size:
        ld.size = size
    o = bpy.data.objects.new(name, ld)
    col.objects.link(o)
    o.location = loc
    o.rotation_euler = [math.radians(a) for a in rot]
    o.parent = parent
    return o


def main():
    sc = bpy.context.scene
    col = sc.collection
    rig = bpy.data.objects[CONFIG["RIG"]]
    s = CONFIG["HEIGHT"] / 0.8  # all distances were tuned for a 0.8 m character

    me = bpy.data.meshes.new("Stage")
    bm = bmesh.new()
    bmesh.ops.create_circle(bm, cap_ends=True, segments=96, radius=CONFIG["STAGE_RADIUS"] * s)
    bm.to_mesh(me)
    bm.free()
    stage = bpy.data.objects.new("Stage", me)
    col.objects.link(stage)
    mat = bpy.data.materials.new("StageMat")
    mat.use_nodes = True
    bsdf = next(n for n in mat.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
    bsdf.inputs["Base Color"].default_value = CONFIG["STAGE_COLOR"]
    bsdf.inputs["Roughness"].default_value = 0.9
    mat.diffuse_color = CONFIG["STAGE_COLOR"]
    stage.data.materials.append(mat)

    if not sc.world:
        sc.world = bpy.data.worlds.new("World")
    sc.world.use_nodes = True
    bg = next(n for n in sc.world.node_tree.nodes if n.type == "BACKGROUND")
    bg.inputs[0].default_value = CONFIG["SKY"]
    bg.inputs[1].default_value = 0.6

    fol = bpy.data.objects.new("CamFollow", None)
    col.objects.link(fol)
    c = fol.constraints.new("COPY_LOCATION")
    c.target = rig
    c.subtarget = "root"
    c.use_z = False

    light(col, "Key", "AREA", (1.2 * s, -1.4 * s, 1.6 * s), (50, 0, 40), 150 * s * s, (1.0, 0.93, 0.85), 1.0 * s, fol)
    light(col, "Rim", "AREA", (-1.0 * s, 1.3 * s, 1.4 * s), (-55, 0, -140), 120 * s * s, (1.0, 0.8, 0.6), 0.8 * s, fol)
    light(col, "Fill", "SUN", (0, 0, 3), (35, 0, -30), 1.5, (0.75, 0.85, 1.0))

    tgt = bpy.data.objects.new("CamTarget", None)
    col.objects.link(tgt)
    tgt.parent = fol
    cd = bpy.data.cameras.new("Cam")
    cd.lens = 50
    cam = bpy.data.objects.new("Cam", cd)
    col.objects.link(cam)
    cam.parent = fol
    tc = cam.constraints.new("TRACK_TO")
    tc.target = tgt
    tc.track_axis = "TRACK_NEGATIVE_Z"
    tc.up_axis = "UP_Y"
    for f, (x, y, z) in {1: (1.75, -1.1, 0.78), 100: (1.5, -1.5, 0.72),
                         160: (1.2, -1.85, 0.72), 212: (1.55, -1.55, 0.78)}.items():
        cam.location = (x * s, y * s, z * s)
        cam.keyframe_insert("location", frame=f)
    for f, z in {1: 0.42, 168: 0.42, 180: 0.5, 192: 0.42}.items():
        tgt.location = (0, -0.15 * s, z * s)
        tgt.keyframe_insert("location", frame=f)
    sc.camera = cam
    sc.render.resolution_x, sc.render.resolution_y = 1280, 720
    for eng in ("BLENDER_EEVEE_NEXT", "BLENDER_EEVEE"):
        try:
            sc.render.engine = eng
            break
        except TypeError:
            pass
    sc.frame_set(1)
    print("stage, lights and follow camera ready; engine:", sc.render.engine)


main()
