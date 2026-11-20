"""Overlay a pixel grid on reference renders (32 px cells, green every 128 px) and join them.

Usage: python scripts/grid_overlay.py out/ref_front.png out/ref_side.png [--out out/ref_grid.png]
"""
import argparse

from PIL import Image, ImageDraw


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("images", nargs="+")
    ap.add_argument("--out", default=None)
    a = ap.parse_args()
    tiles = []
    for p in a.images:
        im = Image.open(p).convert("RGB")
        d = ImageDraw.Draw(im)
        w, h = im.size
        for k in range(0, max(w, h) + 1, 32):
            c = (0, 255, 0) if k % 128 == 0 else (80, 80, 80)
            d.line([(k, 0), (k, h)], fill=c)
            d.line([(0, k), (w, k)], fill=c)
        tiles.append(im)
    out = Image.new("RGB", (sum(t.width for t in tiles), max(t.height for t in tiles)))
    x = 0
    for t in tiles:
        out.paste(t, (x, 0))
        x += t.width
    path = a.out or a.images[0].rsplit(".", 1)[0] + "_grid.png"
    out.save(path)
    print("saved", path)


if __name__ == "__main__":
    main()
