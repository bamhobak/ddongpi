# -*- coding: utf-8 -*-
"""
OpenAI 로 캐릭터 그림을 뽑는 도구.

  python tools/gen_sprite.py <이름> "<프롬프트>" [--ref 참고그림 ...] [--n 4] [--model gpt-image-2]

- 키는 환경변수 OPENAI_API_KEY 에서 읽는다 (파일에 적지 않는다).
- --ref 를 주면 /images/edits 로 보내 참고 그림의 화풍을 따라가게 한다. 없으면 /images/generations.
- 배경을 투명하게 받아 테두리 여백을 잘라 내고, 높이 320px 로 맞춘다 (게임 그림 규격).
- 결과는 assets/_gen/<이름>_<번호>.png 로 남는다. 고른 것만 assets/ 로 옮겨 쓴다.
  (_gen 은 배포하지 않는다 — .gitignore)
"""
import argparse, base64, io, os, pathlib, sys, time
import requests
from PIL import Image

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "assets" / "_gen"
API = "https://api.openai.com/v1/images"
TARGET_H = 320          # 게임 그림 높이 (bangul_right.png 와 같게)


def trim(im, pad=4):
    """알파가 거의 없는 테두리를 잘라 낸다 (반투명 먼지까지 치우려고 문턱을 둔다)."""
    a = im.getchannel("A").point(lambda v: 255 if v > 12 else 0)
    box = a.getbbox()
    if not box:
        return im
    l, t, r, b = box
    return im.crop((max(0, l - pad), max(0, t - pad), min(im.width, r + pad), min(im.height, b + pad)))


def fit_h(im, h=TARGET_H):
    w = round(im.width * h / im.height)
    return im.resize((w, h), Image.LANCZOS)


def call(args):
    key = os.environ.get("OPENAI_API_KEY")
    if not key:
        sys.exit("OPENAI_API_KEY 가 없습니다")
    hdr = {"Authorization": "Bearer " + key}
    common = {"model": args.model, "prompt": args.prompt, "n": str(args.n),
              "size": args.size, "quality": args.quality,
              "background": "transparent", "output_format": "png"}
    if args.ref:
        files = [("image[]", (pathlib.Path(p).name, open(p, "rb"), "image/png")) for p in args.ref]
        r = requests.post(API + "/edits", headers=hdr, data=common, files=files, timeout=600)
    else:
        body = dict(common); body["n"] = args.n
        r = requests.post(API + "/generations", headers=hdr, json=body, timeout=600)
    if r.status_code != 200:
        sys.exit("OpenAI 오류 %d: %s" % (r.status_code, r.text[:800]))
    return r.json()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("name")
    ap.add_argument("prompt")
    ap.add_argument("--ref", nargs="*", default=[])
    ap.add_argument("--n", type=int, default=4)
    ap.add_argument("--model", default="gpt-image-2")
    ap.add_argument("--size", default="1024x1024")
    ap.add_argument("--quality", default="high")
    args = ap.parse_args()

    OUT.mkdir(parents=True, exist_ok=True)
    t0 = time.time()
    d = call(args)
    saved = []
    for i, item in enumerate(d.get("data", []), 1):
        raw = Image.open(io.BytesIO(base64.b64decode(item["b64_json"]))).convert("RGBA")
        (OUT / ("%s_%d_raw.png" % (args.name, i))).write_bytes(base64.b64decode(item["b64_json"]))
        im = fit_h(trim(raw))
        p = OUT / ("%s_%d.png" % (args.name, i))
        im.save(p, optimize=True)
        saved.append((p, im.size))
    print("%.0f초 · %s · %d장" % (time.time() - t0, args.model, len(saved)))
    for p, sz in saved:
        print("  %s  %dx%d" % (p.relative_to(ROOT), sz[0], sz[1]))
    u = d.get("usage")
    if u:
        print("  usage:", u)


if __name__ == "__main__":
    main()
