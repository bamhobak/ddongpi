# -*- coding: utf-8 -*-
"""게임과 같은 식으로(아래 끝 = 발선, 가로 = cx, 높이 = 2r·adj/head) 모든 캐릭터의 헤엄 첫 장·맞은 그림을 나란히"""
import re, sys
from PIL import Image, ImageDraw, ImageFont
ROOT = "g:/vscode/!android/game/이피저피똥피/"; A = ROOT + "assets/"
s = open(ROOT + "index.html", encoding="utf-8").read()
SETS = [("SPR_BANGUL", "bangul"), ("SPR_PJ", "powerj"), ("SPR_FORTUNE", "fortune"), ("SPR_LEV", "levitator"), ("SPR_FIT", "fit"), ("SPR_MONK", "monk"), ("SPR_FULL", "full")]
SPACE = sys.argv[2] == "space"
R = 30
try: f = ImageFont.truetype("malgun.ttf", 15)
except: f = None


def params(name):
    i = s.index("  const %s = {" % name); j = s.index("};", i); b = s[i:j]; out = {}
    for key in ["right", "hurt"]:
        m = re.search(key + r":\s*\{[^}]*?aspect:\s*([\d.]+),\s*head:\s*([\d.]+),\s*cx:\s*([\d.]+),\s*cy:\s*([\d.]+),\s*adj:\s*([\d.]+)", b)
        out[key] = dict(zip(["aspect", "head", "cx", "cy", "adj"], map(float, m.groups())))
    return out


W = 180; H = 260; FOOT = 220
c = Image.new("RGBA", (W * len(SETS), H * 2), (40, 44, 60, 255)); d = ImageDraw.Draw(c)
for k, (name, f_) in enumerate(SETS):
    nm = name + ("_SPACE" if SPACE else ""); fl = f_ + ("_space" if SPACE else "")
    p = params(nm)
    sh_im = Image.open(A + fl + "_swim_sheet.webp").convert("RGBA"); cw, ch = sh_im.width // 7, sh_im.height // 7
    imgs = {"right": sh_im.crop((0, 0, cw, ch)), "hurt": Image.open(A + fl + "_hurt.png").convert("RGBA")}
    for row, key in enumerate(["right", "hurt"]):
        q = p[key]; sh = 2 * R * q["adj"] / q["head"]; sw = sh * q["aspect"]
        im = imgs[key].resize((max(1, int(sw)), max(1, int(sh))))
        x0 = k * W + W // 2; y0 = row * H
        c.alpha_composite(im, (int(x0 - sw * q["cx"]), int(y0 + FOOT - sh)))
        d.line((k * W, y0 + FOOT, k * W + W, y0 + FOOT), fill=(255, 80, 80, 120))
        d.line((x0, y0, x0, y0 + H), fill=(80, 255, 80, 60))
        d.text((k * W + 4, y0 + 4), nm.replace("SPR_", "") + " " + key, fill=(255, 210, 63), font=f)
c.convert("RGB").save(sys.argv[1])
