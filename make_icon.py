"""Generate the ElectronStore app icon (.png + .ico).

Creates a dark rounded-square tile with a sky-blue lightning bolt, matching the
app palette (#0f172a background, #38bdf8 accent).

Run once (only needed again if you change the artwork):
    python make_icon.py

Outputs icon.png (256px) and icon.ico (multi-size) in this folder.

Uses Pillow to draw each size and ImageMagick to assemble the multi-size .ico,
because some Pillow builds only write a single frame for ICO.
"""

import shutil
import subprocess
from pathlib import Path

from PIL import Image, ImageDraw

HERE = Path(__file__).resolve().parent
SIZES = [16, 24, 32, 48, 64, 128, 256]

BG = (15, 23, 42, 255)        # #0f172a slate-900
ACCENT = (56, 189, 248, 255)  # #38bdf8 sky-500


def draw_icon(size: int) -> Image.Image:
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    radius = max(1, size // 12)
    d.rounded_rectangle([0, 0, size - 1, size - 1], radius=radius, fill=BG)
    u = size / 100.0
    bolt = [
        (56 * u, 22 * u), (30 * u, 56 * u), (46 * u, 56 * u),
        (42 * u, 78 * u), (70 * u, 42 * u), (53 * u, 42 * u), (63 * u, 22 * u),
    ]
    d.polygon(bolt, fill=ACCENT)
    return img


def main():
    icon_png = HERE / "icon.png"
    icon_ico = HERE / "icon.ico"

    draw_icon(256).save(icon_png)

    # Build multi-size .ico
    if shutil.which("magick") or shutil.which("convert"):
        tmp = [HERE / f"_ico_{s}.png" for s in SIZES]
        for s, p in zip(SIZES, tmp):
            draw_icon(s).save(p)
        tool = "magick" if shutil.which("magick") else "convert"
        subprocess.run([tool, *[str(p) for p in tmp], str(icon_ico)], check=True)
        for p in tmp:
            p.unlink(missing_ok=True)
    else:
        # Fallback: single-size icon if ImageMagick is unavailable.
        draw_icon(256).save(icon_ico, format="ICO", sizes=[(256, 256)])

    print(f"Wrote {icon_png} and {icon_ico}")


if __name__ == "__main__":
    main()
