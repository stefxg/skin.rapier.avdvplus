#!/usr/bin/env python3
"""Génère les drapeaux HDR10+ et HDR Vivid dans le style des drapeaux Rapier (default + white).
Usage : python3 make_flags.py <skin_dir>"""
import sys, os
from PIL import Image, ImageDraw, ImageFont

skin = sys.argv[1]
FONT = os.path.join(skin, 'fonts', 'default.ttf')

def text_rows(im, fg):
    w, h = im.size
    rows = [y for y in range(h) if any(im.getpixel((x, y))[:3] == fg for x in range(w))]
    return rows[0], rows[-1]

def build(theme):
    base = Image.open(os.path.join(skin, 'media/flagging', theme, 'video/hdr10.png')).convert('RGBA')
    w, h = base.size
    bg = base.getpixel((58, h // 2))
    fg = (189, 215, 249) if theme == 'default' else (227, 227, 227)
    top, bot = text_rows(base, fg)
    cap = bot - top + 1
    col = base.crop((58, 0, 59, h))            # colonne de fond (sans texte, sans arrondi)
    left = base.crop((0, 0, 5, h))             # bord gauche arrondi
    right = base.crop((w - 5, 0, w, h))        # bord droit arrondi

    def canvas(width):
        c = Image.new('RGBA', (width, h), (0, 0, 0, 0))
        for x in range(5, width - 5):
            c.paste(col, (x, 0))
        c.paste(left, (0, 0)); c.paste(right, (width - 5, 0))
        return c

    out = {}
    # HDR10+ : texte d'origine + signe plus
    plus_w = 18
    c = canvas(w + plus_w)
    c.paste(base.crop((5, 0, w - 5, h)), (5, 0))
    d = ImageDraw.Draw(c)
    cx, cy, r, t = w - 4 + plus_w // 2 - 1, (top + bot) // 2, cap // 2 - 2, max(3, cap // 7)
    d.rectangle((cx - r, cy - t // 2, cx + r, cy - t // 2 + t - 1), fill=fg + (255,))
    d.rectangle((cx - t // 2, cy - r, cx - t // 2 + t - 1, cy + r), fill=fg + (255,))
    out['hdr10plus.png'] = c

    # HDR Vivid : texte dessiné avec la police de la skin
    def text_flag(txt):
        size = cap
        f = ImageFont.truetype(FONT, size)
        while f.getbbox('H')[3] - f.getbbox('H')[1] < cap and size < 60:
            size += 1; f = ImageFont.truetype(FONT, size)
        bb = f.getbbox(txt)
        tw = bb[2] - bb[0]
        width = tw + 2 * 9
        c = canvas(width)
        d = ImageDraw.Draw(c)
        d.text((9 - bb[0], top - f.getbbox('H')[1]), txt, font=f, fill=fg + (255,))
        return c
    out['hdrvivid.png'] = text_flag('HDR VIVID')

    for name, im in out.items():
        p = os.path.join(skin, 'media/flagging', theme, 'video', name)
        im.save(p, optimize=True)
        print(p, im.size)

for th in ('default', 'white'):
    build(th)

# Fond vierge pour les badges texte (profil Dolby Vision, FEL/MEL…)
for th in ('default', 'white'):
    base = Image.open(os.path.join(skin, 'media/flagging', th, 'video/hdr10.png')).convert('RGBA')
    w, h = base.size
    col = base.crop((58, 0, 59, h))
    c = Image.new('RGBA', (48, h), (0, 0, 0, 0))
    for x in range(5, 43):
        c.paste(col, (x, 0))
    c.paste(base.crop((0, 0, 5, h)), (0, 0)); c.paste(base.crop((w - 5, 0, w, h)), (43, 0))
    p = os.path.join(skin, 'media/flagging', th, 'video', 'flagbox.png')
    c.save(p, optimize=True); print(p, c.size)
