# -*- coding: utf-8 -*-
"""
UI 그림 손질 — Codex 초안(assets/_gen/ui_*_raw.png)에서 게임에 쓰는 assets/ui/*.webp 를 만든다 (v0.8.53).

  python tools/build_ui.py

- 버튼(노랑·파랑): 여백 자르고 높이 120px. 게임에선 border-image 로 양 끝 반원(높이의 절반)만 두고 가운데를 늘린다.
- 순위판 틀: 안쪽을 고른 남색으로 메우고(초안 안쪽에 얼룩·반투명 구멍이 있다), 가운데 리본을 떼어 낸 뒤 그 자리를
  깨끗한 테두리 한 줄(x=170)로 이어 붙인다 → 9칸 늘리기(border-image)가 된다.
- 리본: 따로 잘라 남색 부분은 투명하게. 틀과 같은 배율로 그려야 테두리 선이 겹쳐 맞는다 — 필요한 숫자를 찍어 준다.
"""
import pathlib
import numpy as np
from PIL import Image

ROOT = pathlib.Path(__file__).resolve().parent.parent
G, O = ROOT / "assets/_gen", ROOT / "assets/ui"
O.mkdir(parents=True, exist_ok=True)
NAVY = (24, 30, 78)

for src, dst in [("ui_btn_yellow_1_raw", "btn_yellow"), ("ui_btn_blue_1_raw", "btn_blue")]:
    im = Image.open(G / (src + ".png")).convert("RGBA")
    im = im.crop(im.getbbox())
    im = im.resize((round(im.width * 120 / im.height), 120), Image.LANCZOS)
    im.save(O / (dst + ".webp"), quality=92)
    print(dst, im.size)

a = np.array(Image.open(G / "ui_board_1_raw.png").convert("RGBA").crop((4, 4, 1398, 1107))).astype(np.int32)
H, W = a.shape[:2]
RIB = (196, W - 196)                    # 리본이 덮은 가로 구간 (원본 좌표)
rib = a[0:262, RIB[0]:RIB[1]].copy()
clean = a.copy()
for x in range(RIB[0], RIB[1]):
    clean[0:300, x] = a[0:300, 170]     # 별과 리본 꼬리 사이의 깨끗한 테두리 한 줄
# 안쪽 — 테두리 안의 사각형에서 금색·밤색 테두리가 아닌 곳은 전부 고른 남색 (불투명)
y0, y1, x0, x1 = 200, 1015, 75, W - 75
sub = clean[y0:y1, x0:x1]
r, g, b, al = sub[..., 0], sub[..., 1], sub[..., 2], sub[..., 3]
m = (al < 250) | ((b > r + 15) & (b > g))
sub[m] = (*NAVY, 255)
# 리본 — 남색(판 안쪽이 비친 곳)은 투명하게
r, g, b = rib[..., 0], rib[..., 1], rib[..., 2]
rib[(b > r + 15) & (b > g)] = 0

ci = Image.fromarray(clean.astype(np.uint8)); bb = ci.getbbox(); ci = ci.crop(bb)
ri = Image.fromarray(rib.astype(np.uint8)); rb = ri.getbbox(); ri = ri.crop(rb)
s = 600 / ci.width
ci = ci.resize((600, round(ci.height * s)), Image.LANCZOS)
ri = ri.resize((round(ri.width * s), round(ri.height * s)), Image.LANCZOS)
# 거의 투명한 위쪽 줄(원본 리본 자리의 옅은 테두리)은 잘라 낸다 — 판 위 모서리 = 틀의 윗선
al = np.array(ci)[:, :, 3]
rows = np.where(al.max(1) > 100)[0]
cut = int(rows.min())
ci = ci.crop((0, cut, ci.width, int(rows.max()) + 1))
ci.save(O / "board.webp", quality=92)
# (v0.8.54 부터 리본은 아래 직사각형 리본(ui_ribbon2_2)을 쓴다 — 아치형은 ribbon_arch.webp 로 남김)
ri.save(O / "ribbon_arch.webp", quality=92)
# 틀 윗변과 리본의 위치 관계 (board.webp 픽셀 단위)
rib_top = (rb[1] - bb[1]) * s - cut                 # 판 위 모서리에서 리본 위까지 (음수면 위로 튀어나옴) — CSS 의 59
print("board", ci.size, "ribbon", ri.size, "ribbon top vs board top (webp px) = %.1f" % rib_top)


# v0.8.54 — 직사각형 리본(가운데 0~94 가 글자 칸, 양 끝 125 고정) · 모드 탭(연보라 / 고르면 민트, 양 끝 50 고정)
def strict(im):
    al = np.array(im)[:, :, 3]
    ys = np.where(al.max(1) > 100)[0]; xs = np.where(al.max(0) > 100)[0]
    return im.crop((int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1))
for src, dst in [("ui_ribbon2_2_raw", "ribbon"), ("ui_tab_on_1_raw", "tab_on"), ("ui_tab_off_1_raw", "tab_off")]:
    im = strict(Image.open(G / (src + ".png")).convert("RGBA"))
    im = im.resize((round(im.width * 120 / im.height), 120), Image.LANCZOS)
    im.save(O / (dst + ".webp"), quality=92)
    print(dst, im.size)
