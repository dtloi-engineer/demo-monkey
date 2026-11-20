"""CASE A - Image -> GLB with Hunyuan3D-2 on your own NVIDIA GPU.

Run INSIDE the Hunyuan3D-2 environment (README section 4.3):
  python /path/to/demo-monkey/scripts/gen_local_hunyuan.py --image views/front.png --out out/model.glb
  # low VRAM (~6 GB): shape only, no texture, smaller model
  python .../gen_local_hunyuan.py --image views/front.png --out out/model.glb --mini --no-texture
  # multi-view model (front/back/left/right)
  python .../gen_local_hunyuan.py --views-dir views --out out/model.glb --mv

API follows the README of Tencent/Hunyuan3D-2 (hy3dgen package); check it if the library changed.
"""
import argparse
import os

from PIL import Image


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--image")
    ap.add_argument("--views-dir")
    ap.add_argument("--out", required=True)
    ap.add_argument("--steps", type=int, default=50)
    ap.add_argument("--octree", type=int, default=380)
    ap.add_argument("--seed", type=int, default=1234)
    ap.add_argument("--mini", action="store_true", help="use Hunyuan3D-2mini (less VRAM)")
    ap.add_argument("--mv", action="store_true", help="use Hunyuan3D-2mv with --views-dir")
    ap.add_argument("--no-texture", action="store_true")
    a = ap.parse_args()

    import torch
    from hy3dgen.rembg import BackgroundRemover
    from hy3dgen.shapegen import Hunyuan3DDiTFlowMatchingPipeline

    rembg = BackgroundRemover()

    def prep(path):
        img = Image.open(path).convert("RGBA")
        return rembg(img) if img.mode == "RGB" or img.getextrema()[3][0] == 255 else img

    if a.mv:
        repo, sub = "tencent/Hunyuan3D-2mv", "hunyuan3d-dit-v2-mv"
        image = {k: prep(os.path.join(a.views_dir, f"{k}.png"))
                 for k in ("front", "back", "left", "right")
                 if os.path.exists(os.path.join(a.views_dir, f"{k}.png"))}
        tex_image = os.path.join(a.views_dir, "front.png")
    else:
        repo, sub = ("tencent/Hunyuan3D-2mini", "hunyuan3d-dit-v2-mini") if a.mini else ("tencent/Hunyuan3D-2", None)
        image = prep(a.image)
        tex_image = a.image

    kw = {"subfolder": sub} if sub else {}
    shape = Hunyuan3DDiTFlowMatchingPipeline.from_pretrained(repo, **kw)
    mesh = shape(image=image, num_inference_steps=a.steps, octree_resolution=a.octree,
                 generator=torch.manual_seed(a.seed), output_type="trimesh")[0]

    if not a.no_texture:
        from hy3dgen.texgen import Hunyuan3DPaintPipeline
        del shape
        torch.cuda.empty_cache()
        paint = Hunyuan3DPaintPipeline.from_pretrained("tencent/Hunyuan3D-2")
        mesh = paint(mesh, image=prep(tex_image))

    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    mesh.export(a.out)
    print("SAVED", a.out)


if __name__ == "__main__":
    main()
