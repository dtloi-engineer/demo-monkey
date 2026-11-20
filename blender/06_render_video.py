"""STEP 6 (in Blender) - render the animation to an MP4 (H.264).

    OVERRIDES = {"OUT": r"D:/path/demo-monkey/out/monkey.mp4", "PERCENT": 100}
    exec(open(r".../blender/06_render_video.py", encoding="utf-8").read())

Rendering blocks Blender until done: 212 frames at 720p in Eevee take minutes on a mid GPU,
much longer on old cards (GTX 1050: start with PERCENT=50). For a quick check, render a
few frames with the MCP `look` tool (mode="frames") instead.
Enum names are read at runtime because they differ between Blender versions.
"""
import bpy

CONFIG = dict(OUT=None, PERCENT=100, SAMPLES=32)
CONFIG.update(globals().get("OVERRIDES", {}))


def set_enum(owner, prop, wanted):
    items = [i.identifier for i in owner.bl_rna.properties[prop].enum_items]
    for w in wanted:
        if w in items:
            setattr(owner, prop, w)
            return w
    raise RuntimeError(f"{prop}: none of {wanted} in {items}")


def main():
    if not CONFIG["OUT"]:
        raise SystemExit("Set OVERRIDES['OUT'] to an absolute .mp4 path")
    sc = bpy.context.scene
    r = sc.render
    im = r.image_settings
    if "media_type" in im.bl_rna.properties:  # Blender 5.x splits image vs video
        set_enum(im, "media_type", ["VIDEO"])
    set_enum(im, "file_format", ["FFMPEG"])
    set_enum(r.ffmpeg, "format", ["MPEG4"])
    set_enum(r.ffmpeg, "codec", ["H264"])
    set_enum(r.ffmpeg, "constant_rate_factor", ["HIGH", "MEDIUM"])
    r.resolution_percentage = CONFIG["PERCENT"]
    if hasattr(sc, "eevee") and hasattr(sc.eevee, "taa_render_samples"):
        sc.eevee.taa_render_samples = CONFIG["SAMPLES"]
    r.filepath = CONFIG["OUT"]
    bpy.ops.render.render(animation=True)
    print("rendered", CONFIG["OUT"])


main()
