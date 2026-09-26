# -*- coding: utf-8 -*-
"""캐릭터 크기·위치 맞추기 (v0.8.80)
그림은 '아래 끝 = 발선(FOOT)', '가로 cx = 몸 자리'로 그려지고 높이 sh = 2r·adj/head 다.
1) 헤엄(이동) 그림 — 몸(가장 큰 덩어리들) 넓이의 제곱근이 모든 캐릭터에서 같게 되도록 right.adj 를 정한다.
2) 맞은 그림 — 몸 넓이가 이동 그림과 같게 hurt.adj 를 정하고, 몸 한가운데가 이동 그림 몸 한가운데와 같은 자리에 오도록
   그림 아래에 투명 여백을 붙이고(위로 올림) hurt.cx 를 정한다. 원본은 assets/_gen/hurt_orig/ 에서 늘 다시 만든다.
"""
import re, sys, json
import numpy as np
from PIL import Image
from scipy import ndimage

ROOT = "g:/vscode/!android/game/이피저피똥피/"
A = ROOT + "assets/"
SETS = [("SPR_BANGUL", "bangul_swim_sheet.webp", "bangul_hurt"), ("SPR_BANGUL_SPACE", "bangul_space_swim_sheet.webp", "bangul_space_hurt"),
        ("SPR_PJ", "powerj_swim_sheet.webp", "powerj_hurt"), ("SPR_PJ_SPACE", "powerj_space_swim_sheet.webp", "powerj_space_hurt"),
        ("SPR_FORTUNE", "fortune_swim_sheet.webp", "fortune_hurt"), ("SPR_FORTUNE_SPACE", "fortune_space_swim_sheet.webp", "fortune_space_hurt"),
        ("SPR_LEV", "levitator_swim_sheet.webp", "levitator_hurt"), ("SPR_LEV_SPACE", "levitator_space_swim_sheet.webp", "levitator_space_hurt"),
        ("SPR_FIT", "fit_swim_sheet.webp", "fit_hurt"), ("SPR_FIT_SPACE", "fit_space_swim_sheet.webp", "fit_space_hurt"),
        ("SPR_MONK", "monk_swim_sheet.webp", "monk_hurt"), ("SPR_MONK_SPACE", "monk_space_swim_sheet.webp", "monk_space_hurt"),
        ("SPR_FULL", "full_swim_sheet.webp", "full_hurt"), ("SPR_FULL_SPACE", "full_space_swim_sheet.webp", "full_space_hurt")]
SIZE_MUL = {"SPR_LEV": 0.92, "SPR_LEV_SPACE": 0.92,   # 무무·풀소유 — 복슬털로 커 보여 10% 작게 (사용자 확인)
            "SPR_MONK": 0.9, "SPR_MONK_SPACE": 0.9, "SPR_FULL": 0.9, "SPR_FULL_SPACE": 0.9}     # 소라 — 날개는 넓이를 크게 잡으니 조금 더 작게(보이는 몸이 비슷하도록)

s = open(ROOT + "index.html", encoding="utf-8").read()


def block(name):
    i = s.index("  const %s = {" % name); j = s.index("};", i)
    return i, j


def params(name):
    i, j = block(name); b = s[i:j]; out = {}
    for key in ["right", "hurt"]:
        m = re.search(key + r":\s*\{[^}]*?aspect:\s*([\d.]+),\s*head:\s*([\d.]+),\s*cx:\s*([\d.]+),\s*cy:\s*([\d.]+),\s*adj:\s*([\d.]+)", b)
        out[key] = dict(zip(["aspect", "head", "cx", "cy", "adj"], map(float, m.groups())))
    return out


def body(im):
    """몸 덩어리(가장 큰 것의 8% 넘는 덩어리들) — 넓이 비율, 가운데(비율)"""
    a = np.array(im)[:, :, 3] > 60
    lab, n = ndimage.label(a)
    sizes = ndimage.sum(a, lab, range(1, n + 1))
    keep = np.isin(lab, [k + 1 for k, v in enumerate(sizes) if v >= sizes.max() * 0.08])
    ys, xs = np.where(keep)
    h, w = a.shape
    return keep.sum() / (w * h), (xs.min() + xs.max()) / 2 / w, (ys.min() + ys.max()) / 2 / h


def sheet_frames(f):
    sh = Image.open(A + f).convert("RGBA"); cw, ch = sh.width // 7, sh.height // 7
    return [sh.crop(((i % 7) * cw, (i // 7) * ch, (i % 7 + 1) * cw, (i // 7 + 1) * ch)) for i in range(0, 49, 3)]


R = 1.0   # 판정 반지름 단위
rows = {}
for name, sheet, hurt in SETS:
    p = params(name)
    fr = sheet_frames(sheet)
    m = np.median(np.array([body(f) for f in fr]), 0)
    rows[name] = dict(p=p, rb=m, hurt=hurt)
# 1) 이동 그림 크기 — 몸 넓이 제곱근 (판정 반지름 단위)
def drawn_size(q, area_frac):
    sh = 2 * R * q["adj"] / q["head"]; sw = sh * q["aspect"]
    return np.sqrt(area_frac * sh * sw)
sizes = {n: drawn_size(r["p"]["right"], r["rb"][0]) for n, r in rows.items()}
target = 2.25                                  # v0.8.80 에 잰 가운데값 (다시 돌려도 같게 고정)
print("이동 그림 크기(판정 반지름 단위) — 목표 %.2f" % target)
new = {}
for n, r in rows.items():
    q = r["p"]["right"]
    k = target * SIZE_MUL.get(n, 1) / sizes[n]
    adj_r = round(q["adj"] * k, 4)
    sh_r = 2 * R * adj_r / q["head"]; sw_r = sh_r * q["aspect"]
    dx = sw_r * (r["rb"][1] - q["cx"]); dy = -sh_r * (1 - r["rb"][2])          # 몸 가운데 (발선 기준)
    size_r = target * SIZE_MUL.get(n, 1)
    # 2) 맞은 그림
    im = Image.open(A + "_gen/hurt_orig/" + r["hurt"] + ".png").convert("RGBA")
    area, bcx, bcy = body(im)
    qh = r["p"]["hurt"]
    fh0, fw0 = im.height, im.width
    # 크기: sqrt(area·sh·sw) = size_r,  sw = sh·aspect → sh = size_r / sqrt(area·aspect)
    asp0 = fw0 / fh0
    sh_h = size_r / np.sqrt(area * asp0)
    # 몸 가운데 높이: 아래에 여백 P(픽셀) → 새 높이 fh0+P, 몸 가운데는 위에서 bcy·fh0 로 그대로
    # 그려진 높이 sh_new = sh_h·(fh0+P)/fh0 (몸 크기는 그대로),  dy_h = -(sh_new - sh_h·bcy) → dy
    need = -dy                                   # 발선에서 몸 가운데까지(위로 +)
    cur = sh_h * (1 - bcy)
    P = max(0.0, (need - cur) / sh_h * fh0)
    Pi = int(round(P))
    out = Image.new("RGBA", (fw0, fh0 + Pi), (0, 0, 0, 0)); out.alpha_composite(im, (0, 0))
    out.save(A + r["hurt"] + ".png")
    fh1 = fh0 + Pi
    sh_new = sh_h * fh1 / fh0
    head_h = qh["head"] * fh0 / fh1                     # 얼굴 크기 비율(새 높이 기준)
    adj_h = round(sh_new * head_h / (2 * R), 4)
    cy_h = round(qh["cy"] * fh0 / fh1, 3)
    sw_new = sh_new * (fw0 / fh1)
    cx_h = round(bcx - dx / sw_new, 3)
    new[n] = dict(ratio=fh0 / fh1, right_adj=adj_r, hurt=dict(aspect=round(fw0 / fh1, 4), head=round(head_h, 4), cx=cx_h, cy=cy_h, adj=adj_h))
    print("%-18s 이동 크기 %.2f→%.2f  맞음: 여백 %d px, 몸 가운데 맞춤 (여전히 낮음 %.2f)" % (n, sizes[n], size_r, Pi, max(0, cur - need)))
json.dump(new, open(sys.argv[1], "w"), indent=1)
