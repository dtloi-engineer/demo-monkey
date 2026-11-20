"""Check this machine and recommend a 3D generation path.

Run:  python scripts/check_env.py

Prints what is installed (GPU/VRAM, Blender, uv, git, HF token present or not)
and recommends:
  Case A - generate locally on your own NVIDIA GPU (enough VRAM)
  Case B - generate on Hugging Face Spaces (free ZeroGPU quota, needs HF_TOKEN)
The token value is never printed.
"""
import os
import shutil
import subprocess
import sys

# Rough VRAM needs (GB). Verify against each project's README before buying hardware.
NEEDS = {
    "TRELLIS (image -> textured GLB)": 16,
    "Hunyuan3D-2 shape + texture": 16,
    "Hunyuan3D-2mini shape only (no texture)": 6,
}


def run(cmd):
    try:
        return subprocess.run(cmd, capture_output=True, text=True, timeout=20).stdout.strip()
    except Exception:
        return ""


def gpus():
    if not shutil.which("nvidia-smi"):
        return []
    out = run(["nvidia-smi", "--query-gpu=name,memory.total", "--format=csv,noheader,nounits"])
    res = []
    for line in out.splitlines():
        if "," in line:
            name, mem = line.rsplit(",", 1)
            try:
                res.append((name.strip(), int(mem.strip()) / 1024))
            except ValueError:
                pass
    return res


def find_blender():
    exe = shutil.which("blender")
    if exe:
        return exe
    roots = [r"C:\Program Files\Blender Foundation", "/Applications/Blender.app/Contents/MacOS"]
    for root in roots:
        if os.path.isdir(root):
            for dirpath, _, files in os.walk(root):
                for f in files:
                    if f.lower() in ("blender.exe", "blender"):
                        return os.path.join(dirpath, f)
    return None


def main():
    print(f"Python      : {sys.version.split()[0]}")
    for tool in ("git", "uv", "uvx"):
        print(f"{tool:<12}: {shutil.which(tool) or 'MISSING'}")
    b = find_blender()
    print(f"Blender     : {b or 'not found on PATH (fine if installed elsewhere)'}")
    print(f"HF_TOKEN    : {'set' if os.environ.get('HF_TOKEN') else 'NOT set'}")

    g = gpus()
    if not g:
        print("GPU         : no NVIDIA GPU detected")
    for name, vram in g:
        print(f"GPU         : {name} ({vram:.1f} GB VRAM)")

    best = max((v for _, v in g), default=0)
    print("\nLocal generation capability:")
    for k, need in NEEDS.items():
        ok = "OK " if best >= need else "NO "
        print(f"  [{ok}] {k}: needs ~{need} GB")

    print("\nRecommendation:")
    if best >= 16:
        print("  Case A: generate locally (README section 4). Hugging Face is optional.")
    else:
        print("  Case B: generate on Hugging Face (README section 5).")
        if not os.environ.get("HF_TOKEN"):
            print("  -> Create a free token at https://huggingface.co/settings/tokens (Read) and set HF_TOKEN.")


if __name__ == "__main__":
    main()
