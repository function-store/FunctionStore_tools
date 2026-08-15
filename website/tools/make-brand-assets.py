"""PLACEHOLDER brand assets for tools.functionstore.xyz.

There is no square FNSTools logo in the repo -- icons/main.png is a
1658x108 toolbar strip and icons/Fx.png is 50x19, both UI chrome rather
than a mark. This draws a stand-in so the site is not shipping broken
images, and is meant to be deleted once a real mark exists.

    python3 website/tools/make-brand-assets.py

Writes website/favicon.png (256x256) and website/og-image.png (1200x630).
"""

import os

from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.dirname(HERE)

BG = (10, 10, 10)
AMBER = (251, 191, 36)
DIM = (163, 163, 163)

FONTS = [
    '/System/Library/Fonts/Supplemental/Menlo.ttc',
    '/System/Library/Fonts/Monaco.ttf',
    '/System/Library/Fonts/SFNSMono.ttf',
    '/System/Library/Fonts/Helvetica.ttc',
]


def font(size):
    for path in FONTS:
        if os.path.exists(path):
            try:
                return ImageFont.truetype(path, size)
            except Exception:
                continue
    return ImageFont.load_default()


def centered(draw, box, text, fnt, fill):
    l, t, r, b = draw.textbbox((0, 0), text, font=fnt)
    x = box[0] + (box[2] - box[0] - (r - l)) / 2 - l
    y = box[1] + (box[3] - box[1] - (b - t)) / 2 - t
    draw.text((x, y), text, font=fnt, fill=fill)


def favicon(size=256):
    # 4x supersample so the rounded corners are not jagged
    s = size * 4
    img = Image.new('RGBA', (s, s), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([0, 0, s - 1, s - 1], radius=int(s * 0.22), fill=AMBER)
    centered(d, (0, -int(s * 0.02), s, s), 'fx', font(int(s * 0.52)), BG)
    return img.resize((size, size), Image.LANCZOS)


def og(w=1200, h=630):
    img = Image.new('RGB', (w, h), BG)
    d = ImageDraw.Draw(img)
    mark = favicon(112)
    img.paste(mark, (80, 80), mark)
    d.text((216, 96), 'FNSTools', font=font(52), fill=(245, 245, 245))
    d.text((216, 160), 'by Function Store', font=font(24), fill=DIM)
    d.text((80, 300), 'TouchDesigner,', font=font(76), fill=(245, 245, 245))
    d.text((80, 386), 'minus the busywork.', font=font(76), fill=AMBER)
    d.text((80, 520), 'tools.functionstore.xyz  ·  free & open source',
           font=font(26), fill=DIM)
    d.rectangle([0, h - 6, w, h], fill=AMBER)
    return img


if __name__ == '__main__':
    favicon().save(os.path.join(OUT, 'favicon.png'))
    og().save(os.path.join(OUT, 'og-image.png'))
    print('wrote website/favicon.png and website/og-image.png (placeholders)')
