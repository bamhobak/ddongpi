# -*- coding: utf-8 -*-
"""그림의 일부만 OpenAI 로 고친다 (가림판). 나머지(머리·귀 등)는 한 픽셀도 안 바뀐다.
  python tools/edit_region.py <원본.png> <이름> "<프롬프트>" --box x0,y0,x1,y1 [--box ...] [--n 2]
  box 는 그림 크기에 대한 비율(0~1). 여러 개 주면 합친 영역을 고친다. 결과는 assets/_gen/<이름>_<번호>.png"""
import argparse, base64, io, os, pathlib, sys, requests
from PIL import Image, ImageDraw, ImageFilter
ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
from gen_sprite import trim, fit_h
ap = argparse.ArgumentParser()
ap.add_argument("src"); ap.add_argument("name"); ap.add_argument("prompt")
ap.add_argument("--box", action="append", default=[]); ap.add_argument("--n", type=int, default=2)
ap.add_argument("--model", default="gpt-image-2")
a = ap.parse_args()
im = Image.open(a.src).convert("RGBA"); W, H = im.size
mask = Image.new("L", (W, H), 255)              # 255 = 그대로 둔다
d = ImageDraw.Draw(mask)
for b in a.box:
    x0, y0, x1, y1 = [float(v) for v in b.split(",")]
    d.rectangle([x0 * W, y0 * H, x1 * W, y1 * H], fill=0)   # 0 = 고친다
m = Image.new("RGBA", (W, H), (0, 0, 0, 255)); m.putalpha(mask)
bi, bm = io.BytesIO(), io.BytesIO(); im.save(bi, "PNG"); m.save(bm, "PNG")
m.save(ROOT / "assets/_gen" / (a.name + "_mask.png"))
r = requests.post("https://api.openai.com/v1/images/edits",
                  headers={"Authorization": "Bearer " + os.environ["OPENAI_API_KEY"]},
                  data={"model": a.model, "prompt": a.prompt, "n": str(a.n), "size": "%dx%d" % (W, H),
                        "quality": "high", "background": "transparent", "output_format": "png"},
                  files=[("image[]", ("src.png", bi.getvalue(), "image/png")), ("mask", ("mask.png", bm.getvalue(), "image/png"))],
                  timeout=600)
if r.status_code != 200: sys.exit("OpenAI 오류 %d: %s" % (r.status_code, r.text[:600]))
for i, it in enumerate(r.json()["data"], 1):
    raw = Image.open(io.BytesIO(base64.b64decode(it["b64_json"]))).convert("RGBA")
    raw.save(ROOT / "assets/_gen" / ("%s_%d_raw.png" % (a.name, i)))
    fit_h(trim(raw)).save(ROOT / "assets/_gen" / ("%s_%d.png" % (a.name, i)), optimize=True)
    print("  assets/_gen/%s_%d.png" % (a.name, i))
