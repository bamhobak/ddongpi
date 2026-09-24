# -*- coding: utf-8 -*-
"""
아이콘 시트 만들기 — icon_list 의 REUSE(이미 있는 게임 그림)와 NEW(뽑아 둔 assets/_gen/ic_<이름>_1_raw.png)를
칸 96px(게임에선 30px 안팎으로 그려서 충분) · 한 줄 COLS 칸짜리 assets/icons.webp 한 장으로 모으고, index.html 의 ICON_KEYS(칸 순서)를 고쳐 쓴다.

  python tools/build_icons.py

- 아직 안 뽑은 아이콘은 빠진다 → 게임에서는 그 이모지가 원래 이모지로 나온다.
- 미리보기(이모지·이름·실제 크기)를 assets/_gen/_preview/icons_sheet.png 로 남긴다.
"""
import json, pathlib, re, sys
from PIL import Image, ImageDraw, ImageFont

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(HERE))
from icon_list import NEW, REUSE
from gen_sprite import trim

CELL, PAD, COLS = 96, 3, 10


def fit(im):
    im = trim(im.convert("RGBA"))
    k = (CELL - 2 * PAD) / max(im.size)
    im = im.resize((max(1, round(im.width * k)), max(1, round(im.height * k))), Image.LANCZOS)
    c = Image.new("RGBA", (CELL, CELL), (0, 0, 0, 0))
    c.alpha_composite(im, ((CELL - im.width) // 2, (CELL - im.height) // 2))
    return c


def main():
    cells = []                                    # (이모지, 이름, 그림)
    for key, f in REUSE.items():
        cells.append((key, f, fit(Image.open(ROOT / "assets" / (f + ".png")))))
    missing = []
    for key, slug, _ in NEW:
        p = ROOT / "assets" / "_gen" / ("ic_%s_1_raw.png" % slug)
        if p.exists():
            cells.append((key, slug, fit(Image.open(p))))
        else:
            missing.append(slug)
    rows = (len(cells) + COLS - 1) // COLS
    sheet = Image.new("RGBA", (COLS * CELL, rows * CELL), (0, 0, 0, 0))
    for i, (_, _, im) in enumerate(cells):
        sheet.alpha_composite(im, ((i % COLS) * CELL, (i // COLS) * CELL))
    out = ROOT / "assets" / "icons.webp"
    sheet.save(out, "WEBP", quality=85, method=6)

    keys = [k for k, _, _ in cells]
    html = ROOT / "index.html"
    s = html.read_text(encoding="utf-8")
    block = ("/*ICONS-BEGIN*/ const ICON_KEYS = %s; const ICON_COLS = %d, ICON_ROWS = %d, ICON_CELL = %d; /*ICONS-END*/"
             % (json.dumps(keys, ensure_ascii=False), COLS, rows, CELL))
    s2, n = re.subn(r"/\*ICONS-BEGIN\*/.*?/\*ICONS-END\*/", lambda m: block, s, flags=re.S)
    if n != 1:
        sys.exit("index.html 에 /*ICONS-BEGIN*/ … /*ICONS-END*/ 자리가 없습니다")
    html.write_text(s2, encoding="utf-8")

    # 미리보기 — 큰 그림 + 게임 크기(28px)
    font = ImageFont.truetype("C:/Windows/Fonts/malgunbd.ttf", 13)
    PC, PW, PH = 8, 150, 128
    prows = (len(cells) + PC - 1) // PC
    pv = Image.new("RGBA", (PC * PW, prows * PH), (120, 190, 230, 255))
    d = ImageDraw.Draw(pv)
    for i, (key, name, im) in enumerate(cells):
        x, y = (i % PC) * PW, (i // PC) * PH
        pv.alpha_composite(im.resize((96, 96), Image.LANCZOS), (x + 4, y + 4))
        pv.alpha_composite(im.resize((28, 28), Image.LANCZOS), (x + 106, y + 40))
        d.text((x + 6, y + 104), name, font=font, fill=(20, 30, 60))
    prev = ROOT / "assets" / "_gen" / "_preview" / "icons_sheet.png"
    prev.parent.mkdir(parents=True, exist_ok=True)
    pv.convert("RGB").save(prev)
    print("아이콘 %d개 (재사용 %d · 새로 %d) → %s  %dKB" % (len(cells), len(REUSE), len(cells) - len(REUSE),
                                                  out.relative_to(ROOT), out.stat().st_size // 1024))
    if missing:
        print("아직 없는 것(이모지로 남음):", missing)


if __name__ == "__main__":
    main()
