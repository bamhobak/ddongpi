# -*- coding: utf-8 -*-
"""
긴 배경의 가운데 칸 하나만 다시 — 아래(앞 칸 위 끝)와 위(지금 칸 위 끝 = 다음 칸이 이어 받은 자리)를 둘 다 깔아 주고
사이만 채워 그리게 한다. 위아래 띠는 그려진 뒤 원래 그림과 다시 섞어 이음매를 맞춘다. 다음 칸들은 다시 안 그려도 된다.

  python tools/gen_long_mid.py 3 [--n 3]
결과: assets/_gen/long/tile_NN.png 를 바꾸고(옛 것은 tile_NN_old.png), 후보는 tile_NN_m*.png
"""
import argparse, pathlib, shutil, subprocess, sys
from PIL import Image, ImageChops, ImageStat

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
from gen_long import OUT, TW, TH, OVER, STYLE, STAGE, fit

KEEP = 300          # 위아래로 원래 그림을 깔아 주는 높이
MIX = 200           # 그려진 뒤 원래 그림과 섞는 띠

MID = ("The attached FIRST image is a section of one long vertical painting with its TOP strip and BOTTOM strip already "
  "painted and the flat gray area between them empty. Fill the gray area so the painting flows seamlessly from the "
  "bottom strip up into the top strip: the sky color must change gradually and smoothly from the bottom strip's blue "
  "to the top strip's blue — NO horizontal bands, NO horizon lines, NO sudden color steps. Match the colors, lighting "
  "and any clouds or objects that cross both boundaries exactly, and keep both strips unchanged. ")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("tile", type=int)
    ap.add_argument("--n", type=int, default=3)
    ap.add_argument("--again", action="store_true", help="새로 안 뽑고 받아 둔 후보로 다시 섞기만")
    ap.add_argument("--cont", action="store_true", help="아래에서 이어 그리고(gen_long 방식) 위는 원래 그림과 넓게 섞기")
    a = ap.parse_args()
    n = a.tile
    cur = OUT / ("tile_%02d.png" % n)
    old = OUT / ("tile_%02d_old.png" % n)
    if not old.exists():
        shutil.copy(cur, old)
    old_im = Image.open(old).convert("RGB")
    prev = Image.open(OUT / ("tile_%02d.png" % (n - 1))).convert("RGB")
    dy = int((OUT / ("tile_%02d.dy" % n)).read_text())
    y0 = TH - OVER + dy                      # 이 칸에서 앞 칸 맨 위가 오는 줄
    canvas = Image.new("RGB", (TW, TH), (128, 128, 128))
    canvas.paste(old_im.crop((0, 0, TW, KEEP)), (0, 0))                       # 위 — 다음 칸이 이어 받은 그대로
    canvas.paste(prev.crop((0, 0, TW, TH - y0)), (0, y0))                     # 아래 — 앞 칸 위 끝 (이음매 자리부터)
    cp = OUT / ("_mid_%02d.png" % n); canvas.save(cp)
    if a.cont:
        return cont(a, n, old_im, prev, y0)
    name = "longmid_%02d" % n
    if "--again" not in sys.argv:
      for p in (ROOT / "assets/_gen").glob(name + "_*.png"):
        p.unlink()
      subprocess.run([sys.executable, str(ROOT / "tools/gen_codex.py"), name, STYLE + MID + STAGE[n],
                    "--ref", str(cp), str(OUT / "style.png"), "--n", str(a.n), "--jobs", str(a.n), "--bg", "opaque", "--raw"], cwd=ROOT)
    cands = sorted(p for p in (ROOT / "assets/_gen").glob(name + "_*.png") if not p.stem.endswith("_raw"))
    if not cands:
        sys.exit("그림을 못 받음")
    best = None
    for i, p in enumerate(cands):
        im = fit(Image.open(p))
        # 위아래 띠가 원래와 얼마나 같은지
        dt = sum(ImageStat.Stat(ImageChops.difference(im.crop((0, 0, TW, KEEP)), canvas.crop((0, 0, TW, KEEP)))).mean)
        db = sum(ImageStat.Stat(ImageChops.difference(im.crop((0, y0, TW, TH)), canvas.crop((0, y0, TW, TH)))).mean)
        # 위 띠를 원래 그림과 섞는다 (아래 띠는 build_strip 이 앞 칸과 섞는다)
        mask = Image.new("L", (TW, KEEP + MIX), 0)
        for y in range(KEEP + MIX):
            mask.paste(255 if y < KEEP - MIX // 2 else max(0, round(255 * (1 - (y - (KEEP - MIX // 2)) / MIX))), (0, y, TW, y + 1))
        im.paste(old_im.crop((0, 0, TW, KEEP + MIX)), (0, 0), mask)
        # 아래 — Codex 가 이음매 자리(y0)에 색 계단(가로줄)을 남긴다. 그 위 BMIX 줄의 색을 앞 칸 맨 위 색에 서서히 맞추고,
        #        y0 아래는 앞 칸 그림 그대로 둔다
        import numpy as np
        BMIX = 420
        a_ = np.asarray(im, dtype=np.float32).copy()
        pv = np.asarray(prev, dtype=np.float32)
        g = a_[y0 - 24:y0].mean(axis=0); t = pv[0:24].mean(axis=0)            # 열마다 위·아래 색
        k = 61; ker = np.ones(k) / k                                         # 옆으로 뭉개 얼룩 없이
        d = np.stack([np.convolve(np.pad((t - g)[:, c], k // 2, mode="edge"), ker, mode="valid") for c in range(3)], axis=1)
        for y in range(y0 - BMIX, y0):
            w = ((y - (y0 - BMIX)) / BMIX) ** 1.6
            a_[y] += d * w
        a_[y0:TH] = pv[0:TH - y0]
        im = Image.fromarray(np.clip(a_, 0, 255).astype(np.uint8))
        mp = OUT / ("tile_%02d_m%d.png" % (n, i + 1)); im.save(mp)
        print("후보 %d: 위 %.1f · 아래 %.1f" % (i + 1, dt, db))
        if best is None or dt + db < best[0]:
            best = (dt + db, mp)
    shutil.copy(best[1], cur)
    print("tile %d → %s" % (n, best[1].name))


TOPMIX = 560


def cont(a, n, old_im, prev, y0):
    from gen_long import gray_canvas, CONT, seam
    import numpy as np
    name = "longc_%02d" % n
    gc = OUT / ("_cont_%02d.png" % n); gray_canvas(prev).save(gc)
    extra = (" Keep the sky the SAME clear blue as the bottom strip all the way up — no darker or lighter horizontal bands, "
             "no horizon. The TOP of the image must look like the attached SECOND image's top (same sky color, the start of a "
             "feather-filled sky).")
    if not a.again:
        for p in (ROOT / "assets/_gen").glob(name + "_*.png"):
            p.unlink()
        top = OUT / ("_top_%02d.png" % n); old_im.crop((0, 0, TW, 900)).save(top)
        subprocess.run([sys.executable, str(ROOT / "tools/gen_codex.py"), name, STYLE + CONT + STAGE[n] + extra,
                        "--ref", str(gc), str(top), str(OUT / "style.png"), "--n", str(a.n), "--jobs", str(a.n), "--bg", "opaque", "--raw"], cwd=ROOT)
    cands = sorted(p for p in (ROOT / "assets/_gen").glob(name + "_*.png") if not p.stem.endswith("_raw"))
    if not cands:
        sys.exit("그림을 못 받음")
    best = None
    for i, p in enumerate(cands):
        im = fit(Image.open(p))
        d, dy = seam(prev, im)
        # 위 TOPMIX 줄을 원래 칸의 위(다음 칸이 이어 받은 자리)로 서서히 — 맨 위 120줄은 원래 그대로
        A = np.asarray(im, dtype=np.float32).copy(); O = np.asarray(old_im, dtype=np.float32)
        # 하늘색을 위로 갈수록 원래 칸 위 색에 맞춘다 — 열마다 차이를 옆으로 뭉개 1300줄에 걸쳐 서서히 (가로 띠가 안 생기게)
        k = 121; ker = np.ones(k) / k
        dlt = (O[0:260].mean(axis=0) - A[0:260].mean(axis=0))
        dlt = np.stack([np.convolve(np.pad(dlt[:, c], k // 2, mode="edge"), ker, mode="valid") for c in range(3)], axis=1)
        for y in range(0, 1300):
            u = 1 - y / 1300; A[y] += dlt * (u * u * (3 - 2 * u))
        out = A.copy()
        for y in range(0, TOPMIX):
            w = 1.0 if y < 120 else (1 - (y - 120) / (TOPMIX - 120)) ** 1.3
            out[y] = O[y] * w + A[y] * (1 - w)
        im2 = Image.fromarray(np.clip(out, 0, 255).astype(np.uint8))
        dt = sum(ImageStat.Stat(ImageChops.difference(im.crop((0, 0, TW, 300)), old_im.crop((0, 0, TW, 300)))).mean)
        mp = OUT / ("tile_%02d_k%d.png" % (n, i + 1)); im2.save(mp); (OUT / ("tile_%02d_k%d.dy" % (n, i + 1))).write_text(str(dy))
        print("후보 %d: 아래 이음매 %.1f (dy %d) · 위 차이 %.1f" % (i + 1, d, dy, dt))
        if best is None or d + dt < best[0]:
            best = (d + dt, mp, dy)
    shutil.copy(best[1], OUT / ("tile_%02d.png" % n)); (OUT / ("tile_%02d.dy" % n)).write_text(str(best[2]))
    print("tile %d → %s" % (n, best[1].name))


if __name__ == "__main__":
    main()
