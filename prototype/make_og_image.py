"""Draw the 1200x630 link-preview image (frontend/static/og-image.png).

It mirrors the home page's music-stand panel: the headline, a line of solfa
with the current syllable lit, and a keyboard with its key lit.

Usage: python make_og_image.py
"""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

HERE = Path(__file__).resolve().parent
FONTS = HERE / "frontend" / "node_modules" / "@fontsource-variable" / "bricolage-grotesque" / "files"
OUT = HERE / "frontend" / "static" / "og-image.png"

INDIGO, IVORY, LAMP, MUTED, KEY_LINE, BLACK_KEY = "#1e2350", "#fffdf6", "#ffc62b", "#a9aed0", "#c9cbdb", "#1b1d33"
W, H = 1200, 630
LINE = ["mi", "re", "do", "re", "mi", "mi", "mi"]
LIT = 2  # "do", played on C4


def font(size: int, weight: str = "Bold") -> ImageFont.FreeTypeFont:
    f = ImageFont.truetype(str(FONTS / "bricolage-grotesque-latin-standard-normal.woff2"), size)
    f.set_variation_by_name(weight)
    return f


def main() -> None:
    img = Image.new("RGB", (W, H), INDIGO)
    d = ImageDraw.Draw(img)

    # Logo: three rising bars, the last one lit.
    for i, (x, y) in enumerate(((72, 86), (94, 72), (116, 52))):
        d.rounded_rectangle((x, y, x + 16, 108), radius=4, fill=LAMP if i == 2 else IVORY)
    d.text((146, 56), "SolfaFlow", font=font(44, "ExtraBold"), fill=IVORY)

    d.text((72, 150), "Hear a song.", font=font(76, "ExtraBold"), fill=IVORY)
    d.text((72, 232), "Play it in tonic solfa.", font=font(76, "ExtraBold"), fill=IVORY)

    x = 72
    syl_font = font(48, "SemiBold")
    for i, syl in enumerate(LINE):
        width = d.textlength(syl, font=syl_font)
        if i == LIT:
            d.rounded_rectangle((x - 14, 352, x + width + 14, 420), radius=12, fill=LAMP)
        d.text((x, 356), syl, font=syl_font, fill=INDIGO if i == LIT else IVORY)
        x += width + 40

    # One octave and a bit of keyboard, C4 lit.
    left, top, key_w, key_h = 72, 470, 58, 118
    whites = 15
    for i in range(whites):
        fill = LAMP if i == 0 else IVORY
        d.rounded_rectangle((left + i * key_w, top, left + (i + 1) * key_w - 2, top + key_h), radius=6,
                            fill=fill, outline=KEY_LINE)
    for i in range(whites - 1):
        if i % 7 in (0, 1, 3, 4, 5):  # black keys after C, D, F, G, A
            bx = left + (i + 1) * key_w - key_w * 0.3
            d.rounded_rectangle((bx, top, bx + key_w * 0.6, top + key_h * 0.58), radius=5, fill=BLACK_KEY)
    d.text((W - 72, H - 50), "Free", font=font(30, "SemiBold"), fill=MUTED, anchor="rs")
    img.save(OUT, optimize=True)
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
