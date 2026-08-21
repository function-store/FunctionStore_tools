"""Brand assets for tools.functionstore.xyz, built from the real FNSTools
mark in icons/FNSLogo*.png (flat monogram + the feedback-pinwheel variant).
Recolors the source art to the site's own token palette (see the :root
block in website/index.html / docs.css) rather than shipping a second,
hand-maintained copy of those colors.

    python3 website/tools/make-brand-assets.py

Writes website/favicon.png (256x256) and website/og-image.png (1200x630).
"""

import os

from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.dirname(HERE)
ICONS = os.path.join(os.path.dirname(OUT), 'icons')

BG = (10, 10, 10)          # --bg
TEXT = (245, 245, 245)     # --text
TEXT_DIM = (163, 163, 163) # --text-dim
ACCENT = (251, 191, 36)    # --accent

FONTS = [
    # Windows
    'C:/Windows/Fonts/consola.ttf',
    'C:/Windows/Fonts/CascadiaMono.ttf',
    # macOS
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


def recolor_flat(im, rgb):
    """Replace every non-transparent pixel with a flat `rgb`, keeping the
    source alpha as-is. The source art is a single-tone mark (a white
    monogram, or a white pinwheel faded through alpha) so this is enough
    to reskin it into any accent color without touching its shape."""
    im = im.convert('RGBA')
    solid = Image.new('RGBA', im.size, rgb + (0,))
    solid.putalpha(im.split()[3])
    return solid


def mark(size, color, crop=True):
    im = Image.open(os.path.join(ICONS, 'FNSLogo.png'))
    im = recolor_flat(im, color)
    if crop:
        im = im.crop(im.getbbox())
    scale = size / max(im.size)
    return im.resize((max(1, int(im.width * scale)), max(1, int(im.height * scale))), Image.LANCZOS)


def favicon(size=256):
    # 4x supersample so the rounded corners and mark edges are not jagged
    s = size * 4
    img = Image.new('RGBA', (s, s), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([0, 0, s - 1, s - 1], radius=int(s * 0.22), fill=ACCENT)
    glyph = mark(int(s * 0.6), BG)
    img.alpha_composite(glyph, ((s - glyph.width) // 2, (s - glyph.height) // 2))
    return img.resize((size, size), Image.LANCZOS)


def watermark(height):
    """A large, dim, accent-colored copy of the feedback-pinwheel mark,
    meant to bleed off the edge of the og-image as a background texture --
    same radial-glow language as .hero::before / .cfg-band in docs.css."""
    im = Image.open(os.path.join(ICONS, 'FNSLogo_fbd.png'))
    im = recolor_flat(im, ACCENT)
    scale = height / im.height
    im = im.resize((int(im.width * scale), height), Image.LANCZOS)
    r, g, b, a = im.split()
    return Image.merge('RGBA', (r, g, b, a.point(lambda v: int(v * 0.16))))


def og(w=1200, h=630):
    canvas = Image.new('RGBA', (w, h), BG + (255,))
    wm = watermark(int(h * 1.4))
    canvas.alpha_composite(wm, (w - int(wm.width * 0.6), (h - wm.height) // 2))
    img = canvas.convert('RGB')

    d = ImageDraw.Draw(img)
    chip = favicon(112)
    img.paste(chip, (80, 80), chip)
    d.text((216, 96), 'FNSTools', font=font(52), fill=TEXT)
    d.text((216, 160), 'by Function Store', font=font(24), fill=TEXT_DIM)
    d.text((80, 300), 'TouchDesigner,', font=font(76), fill=TEXT)
    d.text((80, 386), 'minus the busywork.', font=font(76), fill=ACCENT)
    d.text((80, 520), 'tools.functionstore.xyz  ·  free & open source',
           font=font(26), fill=TEXT_DIM)
    d.rectangle([0, h - 6, w, h], fill=ACCENT)
    return img


if __name__ == '__main__':
    favicon().save(os.path.join(OUT, 'favicon.png'))
    og().save(os.path.join(OUT, 'og-image.png'))
    print('wrote website/favicon.png and website/og-image.png')
