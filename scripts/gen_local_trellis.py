"""CASE A - Image(s) -> textured GLB with TRELLIS on your own NVIDIA GPU (~16 GB VRAM).

Run this INSIDE the TRELLIS environment (see README section 4.2), from the TRELLIS repo folder
or with it on PYTHONPATH:

  python /path/to/demo-monkey/scripts/gen_local_trellis.py --views-dir views --out out/model.glb
  python /path/to/demo-monkey/scripts/gen_local_trellis.py --front views/front.png --out out/model.glb

Same parameters as the Hugging Face script, so results are comparable.
API follows the official example_multi_image.py / example.py of microsoft/TRELLIS;
check them if the library changed.
"""
import argparse
import os

os.environ.setdefault("SPCONV_ALGO", "native")  # recommended by TRELLIS for single runs

from PIL import Image  # noqa: E402
from trellis.pipelines import TrellisImageTo3DPipeline  # noqa: E402
from trellis.utils import postprocessing_utils  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--front")
    ap.add_argument("--views-dir")
    ap.add_argument("--out", required=True)
    ap.add_argument("--steps", type=int, default=30)
    ap.add_argument("--simplify", type=float, default=0.90)
    ap.add_argument("--texture", type=int, default=2048)
    ap.add_argument("--seed", type=int, default=1234)
    ap.add_argument("--algo", default="multidiffusion", choices=["multidiffusion", "stochastic"])
    a = ap.parse_args()

    pipe = TrellisImageTo3DPipeline.from_pretrained("microsoft/TRELLIS-image-large")
    pipe.cuda()
    ss = {"steps": a.steps, "cfg_strength": 7.5}
    slat = {"steps": a.steps, "cfg_strength": 3.0}

    views = []
    if a.views_dir:
        views = [Image.open(os.path.join(a.views_dir, f"{n}.png"))
                 for n in ("front", "right", "back", "left")
                 if os.path.exists(os.path.join(a.views_dir, f"{n}.png"))]
    if len(views) > 1:
        out = pipe.run_multi_image(views, seed=a.seed, sparse_structure_sampler_params=ss,
                                   slat_sampler_params=slat, mode=a.algo)
    else:
        img = Image.open(a.front or os.path.join(a.views_dir, "front.png"))
        out = pipe.run(img, seed=a.seed, sparse_structure_sampler_params=ss, slat_sampler_params=slat)

    glb = postprocessing_utils.to_glb(out["gaussian"][0], out["mesh"][0],
                                      simplify=a.simplify, texture_size=a.texture)
    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    glb.export(a.out)
    print("SAVED", a.out)


if __name__ == "__main__":
    main()
