"""STEP 2 (in Blender) - orthographic front + side renders to place joints precisely.

    OVERRIDES = {"MESH": "BabyMonkey", "OUT_DIR": r"D:/path/demo-monkey/out"}
    exec(open(r".../blender/02_render_reference.py", encoding="utf-8").read())

Writes OUT_DIR/ref_front.png and ref_side.png (512x512) and prints the pixel -> metre mapping:
    front: x = (px - 256) * k          z = Zc + (256 - py) * k
    side : y = (px - 256) * k          z = Zc + (256 - py) * k      (screen right = +Y = back)
Then run  python scripts/grid_overlay.py OUT_DIR/ref_front.png OUT_DIR/ref_side.png
and read joint pixels (chin, shoulders, elbows, wrists, hips, knees, ankles) off the grid image.
"""
import math
import os

import bpy

CONFIG = dict(MESH="Character", OUT_DIR=None, RES=512, MARGIN=1.12)
CONFIG.update(globals().get("OVERRIDES", {}))


def main():
    sc = bpy.context.scene
    m = bpy.data.objects[CONFIG["MESH"]]
    h = m.dimensions.z
    w = max(m.dimensions.x, m.dimensions.y)
    scale = max(h, w) * CONFIG["MARGIN"]
    zc = h / 2
    cam_data = bpy.data.cameras.get("RefCam") or bpy.data.cameras.new("RefCam")
    cam_data.type = "ORTHO"
    cam_data.ortho_scale = scale
    cam = bpy.data.objects.get("RefCam") or bpy.data.objects.new("RefCam", cam_data)
    if cam.name not in sc.collection.objects:
        sc.collection.objects.link(cam)
    old = (sc.camera, sc.render.engine, sc.render.resolution_x, sc.render.resolution_y, sc.render.filepath)
    sc.camera = cam
    sc.render.resolution_x = sc.render.resolution_y = CONFIG["RES"]
    try:
        sc.render.engine = "BLENDER_WORKBENCH"
    except TypeError:
        pass
    sc.display.shading.color_type = "TEXTURE"
    out = CONFIG["OUT_DIR"] or bpy.path.abspath("//")
    os.makedirs(out, exist_ok=True)
    for name, loc, rot in (("front", (0, -10, zc), (90, 0, 0)), ("side", (10, 0, zc), (90, 0, 90))):
        cam.location = loc
        cam.rotation_euler = [math.radians(a) for a in rot]
        sc.render.filepath = os.path.join(out, f"ref_{name}.png")
        bpy.ops.render.render(write_still=True)
    sc.camera, eng, sc.render.resolution_x, sc.render.resolution_y, sc.render.filepath = old
    try:
        sc.render.engine = eng
    except TypeError:
        pass
    cam.hide_set(True)
    cam.hide_render = True
    k = scale / CONFIG["RES"]
    half = CONFIG["RES"] // 2
    print(f"saved {out}/ref_front.png, ref_side.png")
    print(f"k = {k:.6f} m/px, Zc = {zc:.4f}")
    print(f"front: x=(px-{half})*k  z=Zc+({half}-py)*k | side: y=(px-{half})*k  z=Zc+({half}-py)*k")


main()
