"""Cut a character sheet into square view images for multi-view 3D generation.

Usage:
  python scripts/crop_turnaround.py SHEET.png OUT_DIR \
      --box front=568,48,800,352 --box right=800,48,985,352 \
      --box back=1005,48,1225,352 --box left=1228,48,1425,352 \
      [--ref-size 1536x1024] [--size 768] [--blank-top front=40]

Boxes are x0,y0,x1,y1 in pixels of a reference size (default: the sheet's own size).
The defaults above match assets/baby_monkey/character_sheet.png.

Which side is "right"? The view where the character faces the viewer's RIGHT
shows the character's RIGHT side. Get this wrong and multi-view models come out mirrored.

Tip: let Claude open the sheet image, read off the boxes, run this, and look at
OUT_DIR/contact_sheet.png to confirm each crop holds exactly one clean view.
"""
import argparse
import os

from PIL import Image, ImageDraw

DEFAULT_BOXES = {
    "front": (568, 48, 800, 352),
    "right": (800, 48, 985, 352),
    "back": (1005, 48, 1225, 352),
    "left": (1228, 48, 1425, 352),
}


def parse_box(s):
    name, coords = s.split("=")
    return name, tuple(int(v) for v in coords.split(","))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("sheet")
    ap.add_argument("out_dir")
    ap.add_argument("--box", action="append", type=parse_box, help="name=x0,y0,x1,y1")
    ap.add_argument("--ref-size", default=None, help="WxH the boxes were measured on")
    ap.add_argument("--size", type=int, default=768)
    ap.add_argument("--blank-top", action="append", default=[],
                    help="name=pixels: paint over a label at the top of that crop")
    a = ap.parse_args()

    im = Image.open(a.sheet).convert("RGB")
    W, H = im.size
    rw, rh = (int(v) for v in a.ref_size.split("x")) if a.ref_size else (W, H)
    sx, sy = W / rw, H / rh
    boxes = dict(a.box) if a.box else DEFAULT_BOXES
    blank = dict((k, int(v)) for k, v in (b.split("=") for b in a.blank_top))
    os.makedirs(a.out_dir, exist_ok=True)

    tiles = []
    for name, (x0, y0, x1, y1) in boxes.items():
        crop = im.crop((int(x0 * sx), int(y0 * sy), int(x1 * sx), int(y1 * sy)))
        w, h = crop.size
        side = max(w, h)
        bg_color = crop.getpixel((3, h - 3))
        sq = Image.new("RGB", (side, side), bg_color)
        sq.paste(crop, ((side - w) // 2, (side - h) // 2))
        sq = sq.resize((a.size, a.size), Image.LANCZOS)
        if name in blank:
            ImageDraw.Draw(sq).rectangle([0, 0, a.size, blank[name]], fill=sq.getpixel((a.size - 5, a.size - 5)))
        path = os.path.join(a.out_dir, f"{name}.png")
        sq.save(path)
        tiles.append(sq)
        print("saved", path)

    sheet = Image.new("RGB", (a.size * len(tiles), a.size))
    for i, t in enumerate(tiles):
        sheet.paste(t, (i * a.size, 0))
    sheet.resize((len(tiles) * 384, 384)).save(os.path.join(a.out_dir, "contact_sheet.png"))
    print("check", os.path.join(a.out_dir, "contact_sheet.png"))


if __name__ == "__main__":
    main()
