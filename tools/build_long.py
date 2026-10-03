# -*- coding: utf-8 -*-
"""
긴 배경(assets/_gen/long/strip.png)을 게임용 조각으로 자르고, index.html 의 LONG 상수를 새로 쓴다.

  python tools/build_long.py

- 조각: assets/bg/long/cNN.webp — 아래(꽃밭)부터 CH px 씩. 마지막 조각은 남은 만큼.
- 상수: LONG_H(전체 높이) · LONG_CH(조각 높이) · LONG_N(조각 수) · LONG_ANCH(스테이지마다 그 칸 한가운데, 아래에서 잰 px)
  게임은 스테이지 k 의 한가운데 시각(k-0.5)에 화면 가운데가 LONG_ANCH[k-1] 에 오도록 그림을 내린다.
"""
import pathlib, re, sys
from PIL import Image

ROOT = pathlib.Path(__file__).resolve().parent.parent
LONG = ROOT / "assets/_gen/long"
OUT = ROOT / "assets/bg/long"
sys.path.insert(0, str(ROOT / "tools"))
from gen_long import TH, OVER, build_strip      # 칸 크기·이어 붙이기는 gen_long 과 같게

CH = 1024
Q = 74
# 이음매에 걸려 찌그러진 것 위에 덮는 그림 — (파일, 가운데 x, 가운데 y(위에서 잰 px), 폭)
PATCHES = [
    ("patch_earth.png", 170, 10393, 565),      # v0.9.139 10스테이지 지구 — 10·11칸 이음매에 걸려 납작해졌다
]


def grade_seams(strip, span=700, cap=28.0):
    """v0.9.199 칸끼리 색감 맞추기 — 이음매 위·아래 띠의 색 차이(중앙값, 옆으로 아주 넓게 뭉갬)를 반씩 나눠
    위아래 span 줄에 걸쳐 서서히 메운다. 그림은 그대로, 색만 바뀐다"""
    import numpy as np
    from gen_long import BLEND
    A = np.asarray(strip, dtype=np.float32).copy(); H, W = A.shape[:2]
    top, n = TH, 2
    k = 481; ker = np.ones(k) / k
    while (LONG / ("tile_%02d.png" % n)).exists():
        dy = int((LONG / ("tile_%02d.dy" % n)).read_text()); y0 = TH - OVER + dy
        s0 = H - top; s1 = s0 + BLEND                       # 섞인 띠 [s0, s1]
        up = np.median(A[s0 - 180:s0 - 30], axis=0); dn = np.median(A[s1 + 30:s1 + 180], axis=0)   # 열마다
        d = np.stack([np.convolve(np.pad((dn - up)[:, c], k // 2, mode="edge"), ker, mode="valid") for c in range(3)], axis=1)
        d = np.clip(d, -cap, cap)
        # 고침 c(y): 위로 멀리 0 → 섞인 띠 위끝 s0 에서 +d/2 → 띠 안에서 곧게 -d/2 로 → 아래끝 s1 에서 -d/2 → 아래로 멀리 0 (끊김 없이)
        for y in range(max(0, s0 - span), min(H, s1 + span)):
            if y < s0:   u = 1 - (s0 - y) / span; c = 0.5 * u * u * (3 - 2 * u)
            elif y <= s1: c = 0.5 - (y - s0) / max(1, s1 - s0)
            else:        u = 1 - (y - s1) / span; c = -0.5 * u * u * (3 - 2 * u)
            A[y] += d * c
        top += y0; n += 1
    return Image.fromarray(np.clip(A, 0, 255).astype(np.uint8))


def main():
    build_strip()
    strip = Image.open(LONG / "strip.png").convert("RGB")
    H = strip.height
    for f, cx, cy, w in PATCHES:
        im = Image.open(LONG / f).convert("RGBA")
        im = im.resize((w, round(im.height * w / im.width)), Image.LANCZOS)
        strip.paste(im, (round(cx - im.width / 2), round(cy - im.height / 2)), im)
    strip = grade_seams(strip)
    strip.save(LONG / "strip_patched.png")
    # 칸마다 아래에서 잰 한가운데 — build_strip 과 같은 셈
    anch, top = [TH / 2], TH
    n = 2
    while (LONG / ("tile_%02d.png" % n)).exists():
        dy = int((LONG / ("tile_%02d.dy" % n)).read_text())
        y0 = TH - OVER + dy
        anch.append(top + y0 - TH / 2)
        top += y0
        n += 1
    assert abs(top - H) < 2, (top, H)
    OUT.mkdir(parents=True, exist_ok=True)
    for old in OUT.glob("c*.webp"):
        old.unlink()
    k, total = 0, 0
    while k * CH < H:
        b0, b1 = k * CH, min(H, (k + 1) * CH)            # 아래에서 잰 범위
        piece = strip.crop((0, H - b1, strip.width, H - b0))
        p = OUT / ("c%02d.webp" % k)
        piece.save(p, quality=Q, method=6)
        total += p.stat().st_size
        k += 1
    print("조각 %d개 · %.0fKB · 높이 %d · 칸 %d" % (k, total / 1024, H, len(anch)))
    P = ROOT / "index.html"
    s = P.read_text(encoding="utf-8")
    new = ("/*LONG-BEGIN*/ const LONG_H = %d, LONG_CH = %d, LONG_N = %d, LONG_V = %d, LONG_ANCH = [%s]; /*LONG-END*/"
           % (H, CH, k, total % 100000, ", ".join(str(round(a)) for a in anch)))   # LONG_V — 조각이 바뀌면 주소도 바뀌게(옛 그림 캐시 방지)
    s2, cnt = re.subn(r"/\*LONG-BEGIN\*/.*?/\*LONG-END\*/", new, s, flags=re.S)
    if cnt != 1:
        sys.exit("index.html 에 LONG 표시가 없다")
    P.write_bytes(s2.encode("utf-8"))
    print(new)


if __name__ == "__main__":
    main()
