#!/usr/bin/env python3
"""Make the doc's web copies (WebP, under 1 MB) from the full-size masters kept locally in source/doc_masters/.

Each copy is as wide as its largest showing needs: twice its box on a 1440 px screen, or its printed box at
300 dpi, never wider than the master. Quality steps down from 90 to 80 to fit under 1 MB; past that the width
steps down. Boxes were measured in the browser on 2026-11-19 (CSS px, object-fit: cover).

    python3 documents/web_copies.py          # from the repo root; writes documents/assets/NAME.webp
"""
import io
import math
import os

from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MASTERS = os.path.join(ROOT, "source", "doc_masters")
ASSETS = os.path.join(ROOT, "documents", "assets")
LIMIT = 1 << 20                      # 1 MB, the repo's ceiling for one binary
PRINT_SCALE = 300 / 96               # 300 dpi print from 96 px-per-inch CSS
PLATE = (227, 151)                   # print plates: three across a Letter page, 3:2

# name: (screen box at 1440 px wide, printed box)
BOXES = {
    "artist_h": ((88, 88), (88, 88)),                # colophon portrait, a circle
    "ref1_pereda": ((102, 77), PLATE),
    "ref3_oosterwijck": ((102, 77), PLATE),
    "ref4_obelisk": ((102, 77), PLATE),
    "ref5_russo": ((102, 77), PLATE),
    "self_h": ((130, 156), (130, 156)),              # the to-scale figure beside the basin
    "self_portrait": ((1440, 900), (816, 1056)),     # the hero, full screen and the full-bleed printed cover
}


def cover_width(box, aspect):
    """Source width an image needs to cover a box without upscaling (object-fit: cover)."""
    w, h = box
    return max(w, h * aspect)


def target_width(master, screen, printed):
    aspect = master.width / master.height
    need = max(2 * cover_width(screen, aspect), PRINT_SCALE * cover_width(printed, aspect))
    return min(master.width, math.ceil(need))


def encode(image, width):
    """Best WebP of image at width under LIMIT, trying quality 90, 85, 80; None if none fits."""
    small = image.resize((width, round(image.height * width / image.width)), Image.LANCZOS)
    for quality in (90, 85, 80):
        buf = io.BytesIO()
        small.save(buf, "WEBP", quality=quality, method=6)
        if buf.tell() < LIMIT:
            return buf.getvalue(), quality
    return None


def make_copy(name, screen, printed):
    path = next((os.path.join(MASTERS, name + ext) for ext in (".png", ".jpg") if os.path.exists(os.path.join(MASTERS, name + ext))), None)
    if not path:
        raise SystemExit(f"no master for {name} in {MASTERS}")
    master = Image.open(path).convert("RGB")
    width = target_width(master, screen, printed)
    while not (result := encode(master, width)):
        width = int(width * 0.9)
    data, quality = result
    with open(os.path.join(ASSETS, name + ".webp"), "wb") as out:
        out.write(data)
    print(f"{name:18} {os.path.getsize(path) // 1024:6} KB -> {len(data) // 1024:4} KB  {width}px wide  q{quality}")


if __name__ == "__main__":
    for name, (screen, printed) in BOXES.items():
        make_copy(name, screen, printed)
