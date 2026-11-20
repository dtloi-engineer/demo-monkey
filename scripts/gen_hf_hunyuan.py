"""CASE B (alternative) - Image -> textured GLB with Hunyuan3D on Hugging Face.

Usage:
  python scripts/gen_hf_hunyuan.py --image views/front.png --out out/model_hy.glb
  python scripts/gen_hf_hunyuan.py --space tencent/Hunyuan3D-2 --image ... --out ...

Notes from testing (Nov 2026):
- tencent/Hunyuan3D-2.1 asks for 270 s of ZeroGPU per run - more than one day of
  free quota once anything else ran. Use it first thing, or with HF PRO.
- tencent/Hunyuan3D-2 texture step was broken server-side ("texgen_worker is not defined").
Spaces change; if a call fails, run `python scripts/gen_hf_hunyuan.py --list-api`
to print the current endpoints and adapt the keyword arguments below.
"""
import argparse
import json
import os
import shutil

from gradio_client import Client, handle_file


def walk(x):
    if isinstance(x, dict):
        for v in x.values():
            yield from walk(v)
    elif isinstance(x, (list, tuple)):
        for v in x:
            yield from walk(v)
    elif isinstance(x, str) and os.path.exists(x):
        yield x


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--space", default="tencent/Hunyuan3D-2.1")
    ap.add_argument("--image")
    ap.add_argument("--out")
    ap.add_argument("--steps", type=int, default=30)
    ap.add_argument("--octree", type=int, default=320, help="256 standard, 384 high")
    ap.add_argument("--seed", type=int, default=1234)
    ap.add_argument("--list-api", action="store_true")
    a = ap.parse_args()

    c = Client(a.space, verbose=False, token=os.environ.get("HF_TOKEN"))
    if a.list_api:
        info = c.view_api(return_format="dict", print_info=False)
        for k, v in info["named_endpoints"].items():
            print(k, [p["parameter_name"] for p in v["parameters"]])
        return
    if not (a.image and a.out):
        raise SystemExit("--image and --out are required")

    kw = dict(image=handle_file(a.image), mv_image_front=None, mv_image_back=None,
              mv_image_left=None, mv_image_right=None, steps=a.steps, guidance_scale=5.0,
              seed=a.seed, octree_resolution=a.octree, check_box_rembg=True, num_chunks=8000)
    if a.space.endswith("2.1"):
        kw["randomize_seed"] = False
    else:
        kw["caption"] = ""
    res = c.predict(**kw, api_name="/generation_all")
    print("RESULT:", json.dumps(res, default=str)[:600])
    files = [p for p in walk(res) if p.lower().endswith((".glb", ".obj"))]
    if not files:
        raise SystemExit("no mesh file in result")
    textured = [p for p in files if "textured" in p.lower()] or files
    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    shutil.copy(textured[-1], a.out)
    print("SAVED", a.out)


if __name__ == "__main__":
    main()
