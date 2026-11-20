"""CASE B - Image(s) -> textured GLB with TRELLIS on Hugging Face (free ZeroGPU quota).

Usage:
  # single image
  python scripts/gen_hf_trellis.py --front views/front.png --out out/model.glb
  # multi-view (best quality when a turnaround sheet exists)
  python scripts/gen_hf_trellis.py --views-dir views --out out/model.glb

Needs: pip install -r requirements-hf.txt, and env var HF_TOKEN (Read token).
Quota: a free account gets a few minutes of ZeroGPU per day; one run at these
settings asks for ~120 s. On "exceeded your ZeroGPU quota" wait for the reset
(the error says how long) or use Hugging Face PRO.
"""
import argparse
import os
import shutil

from gradio_client import Client, handle_file

SPACE = "trellis-community/TRELLIS"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--front", help="front image (used alone, or as the main view)")
    ap.add_argument("--views-dir", help="folder with front.png right.png back.png left.png")
    ap.add_argument("--out", required=True)
    ap.add_argument("--steps", type=int, default=30, help="sampling steps for both stages (UI default 12)")
    ap.add_argument("--simplify", type=float, default=0.90, help="0.90-0.98; lower keeps more faces")
    ap.add_argument("--texture", type=int, default=2048, help="512-2048")
    ap.add_argument("--seed", type=int, default=1234)
    ap.add_argument("--algo", default="multidiffusion", choices=["multidiffusion", "stochastic"])
    a = ap.parse_args()

    token = os.environ.get("HF_TOKEN")
    if not token:
        print("WARNING: HF_TOKEN not set - running anonymously (very small quota).")

    views = []
    front = a.front
    if a.views_dir:
        for n in ("front", "right", "back", "left"):
            p = os.path.join(a.views_dir, f"{n}.png")
            if os.path.exists(p):
                views.append(p)
        front = front or os.path.join(a.views_dir, "front.png")
    if not front or not os.path.exists(front):
        raise SystemExit("front image not found")

    c = Client(SPACE, verbose=False, token=token)
    try:
        c.predict(api_name="/start_session")
    except Exception as e:  # older/newer Space builds may not expose it
        print("start_session skipped:", e)

    multi = [{"image": handle_file(p), "caption": None} for p in views] if len(views) > 1 else []
    print(f"Generating with {len(multi) or 1} view(s), steps={a.steps}, simplify={a.simplify}, texture={a.texture} ...")
    res = c.predict(
        image=handle_file(front), multiimages=multi, seed=a.seed,
        ss_guidance_strength=7.5, ss_sampling_steps=a.steps,
        slat_guidance_strength=3.0, slat_sampling_steps=a.steps,
        multiimage_algo=a.algo if multi else "stochastic",
        mesh_simplify=a.simplify, texture_size=a.texture,
        api_name="/generate_and_extract_glb",
    )
    glb = next((x for x in res if isinstance(x, str) and x.endswith(".glb") and os.path.exists(x)), None)
    if not glb:
        raise SystemExit(f"No GLB in result: {res}")
    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    shutil.copy(glb, a.out)
    print("SAVED", a.out, os.path.getsize(a.out), "bytes")


if __name__ == "__main__":
    main()
