# -*- coding: utf-8 -*-
"""
한 장처럼 이어지는 긴 배경 — 스테이지마다 한 칸씩, 앞 칸 윗부분을 아래에 깔아 주고 위로 이어 그리게 한다 (Codex).

  python tools/gen_long.py 1 2 3        (칸 번호 = 스테이지 번호, 앞 칸이 있어야 이어 그린다)
  python tools/gen_long.py 2 --n 3      (한 칸에 몇 장 뽑아 이음매가 가장 잘 맞는 걸 고를지)

- 칸 크기 960x1700 (Codex 세로 그림 비율 9:16). 결과 assets/_gen/long/tile_NN.png (고른 것) · tile_NN_c*.png (후보)
- 이음매: 앞 칸 위 OVER px 를 새 칸 아래에 깔아 그리게 하고, 새 칸의 아래 띠를 앞 칸 위 띠에 맞춰
  (세로 어긋남을 찾아) 부드럽게 섞는다 → assets/_gen/long/strip.png 는 1칸부터 이어 붙인 긴 그림 미리보기.
"""
import argparse, pathlib, subprocess, sys, shutil
from PIL import Image, ImageChops, ImageStat

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "assets/_gen/long"
TW, TH = 960, 1700
OVER = 420                     # 앞 칸 위에서 가져와 새 칸 아래에 깔아 주는 높이
BLEND = 220                    # 실제로 섞는 띠 높이

STYLE = ("A tall vertical (portrait 9:16) scrolling background painting for a cute casual mobile game where a puppy "
  "floats higher and higher from a flower meadow up through a dreamy sky and out into space. One continuous world: "
  "this picture is ONE SECTION of a single very long painting. Art style: premium cute casual mobile game illustration, "
  "soft painterly cel shading with gentle gradients, thin soft dark outlines, rich but harmonious pastel colors, "
  "lots of charming small details at the LEFT and RIGHT edges, while the CENTER column stays calmer and lower in "
  "contrast so small falling objects remain easy to read. Whimsical and storybook-like — it does NOT need to be "
  "realistic; take the stage name literally and playfully. No characters, no animals, no people, no text, no letters, "
  "no UI, no frame. "
  "VERY IMPORTANT for gameplay: the CENTRAL HALF of the width must stay mostly OPEN — just the soft sky/space gradient "
  "with at most a few tiny faint sparkles; put every big or detailed object (clouds, props, planets, decorations) in "
  "the LEFT and RIGHT thirds, partly cut off by the edges. ")
CONT = ("The attached FIRST image is the painting so far: only its BOTTOM strip is painted, the flat gray area above it "
  "is empty canvas. Fill the whole empty gray area by continuing the painting UPWARD seamlessly from that strip — "
  "match its colors, lighting, sky gradient and any clouds or objects that cross the boundary exactly, and keep the "
  "bottom strip itself unchanged. As you go up, transition smoothly into the new stage described below; the top of "
  "the image is fully the new stage. ")
STAGE = {
  1: "STAGE 'Roly-poly Flower Meadow' (the very first, lowest section): the bottom 20% is a lush soft rolling flower "
     "meadow seen from just above the grass — gentle round hills covered in daisies, buttercups, clover and tiny pink "
     "flowers, a few dandelion puffs, butterflies' worth of sparkle but no animals. Above it a bright clear morning "
     "blue sky with a few big fluffy cute clouds, dandelion seeds and flower petals floating up the sky.",
  2: "STAGE 'Rainbow Blanket': the sky turns a soft sunny blue and huge soft RAINBOW-colored patchwork quilt blankets "
     "drift across the sky like gentle flying carpets — draped over clouds at the left and right edges, with cozy "
     "stitched patches, little pom-pom tassels and soft folds; pastel rainbow ribbons trail between them.",
  3: "STAGE 'Cotton Candy Sea' (솜사탕 = fluffy spun-sugar COTTON CANDY / candy floss, NOT hard candy): "
     "at the left and right edges, banks of FLUFFY COTTON CANDY FLOSS in pastel pink, lilac and baby blue pile up into "
     "gentle rolling waves like a fluffy ocean shore, with a few big round cotton-candy puffs on simple white paper "
     "sticks bobbing like buoys; thin wisps of floss drift across, soft sugar sparkles. Texture of spun sugar threads. "
     "ABSOLUTELY NO lollipops, NO swirl candies, NO hard candies, NO candy canes, NO waterfalls, NO islands.",
  4: "STAGE 'Feather Sky': a brighter, higher sky where giant soft white and pastel FEATHERS float and drift gently "
     "like slow boats, some fluffy downy feathers swirling at the edges, tiny wisps of cloud, a light airy mood.",
  5: "STAGE 'Cloud Stripes': the sky deepens to a richer blue and the clouds become long neat horizontal STRIPES of "
     "soft pastel cloud bands (pink, peach, white) stretching in from the edges like ribbons, a few tiny stars begin.",
  6: "STAGE 'Sparkle Ripples': high in a deep blue-to-navy sky, shimmering SPARKLY RIPPLE waves of light flow in from "
     "the sides like a gentle glittering sea surface in the air, little twinkling sparkles, first real stars.",
  7: "STAGE 'Aurora Curtain': night sky; big soft flowing AURORA CURTAINS in mint green, pink and violet hang and ripple "
     "down from the top-left and top-right like real stage curtains with soft folds, many small twinkling stars.",
  8: "STAGE 'Shooting Star Village': deep indigo night; cute tiny cottages and lanterns perched on little floating "
     "star-shaped islands at the edges — a VILLAGE of shooting stars, with friendly shooting stars streaking by with "
     "pastel trails, a starry sky.",
  9: "STAGE 'Blue Summit': the very TOP of the blue sky — the atmosphere ends: the bottom shows the glowing cyan-blue "
     "curved rim of the sky like a mountain summit edge of light, above it near-black navy space full of stars.",
  10: "STAGE 'Roly-poly Earth': space; a big cute ROUND cartoon Earth (blue oceans, green lands, white swirl clouds) "
      "partly visible at the left or right edge, a tiny satellite, dark starry space.",
  11: "STAGE 'Moon Neighborhood': space; a big cute pale round MOON at one edge with tiny cozy moon houses, little "
      "ladders and lanterns on it (a neighborhood on the moon), soft craters, purple starry space.",
  12: "STAGE 'Floating Pebbles': cute chunky pastel ROCKS and pebbles of many sizes FLOATING lazily in dark purple "
      "space at the edges (an asteroid field), some with tiny sparkly crystals, twinkling stars.",
  13: "STAGE 'Starlight River': a dreamy flowing RIVER made of starlight — pastel pink, lavender and mint glittering "
      "stream of stars curving across the edges of deep blue space, little sparkles like fish.",
  14: "STAGE 'Pitch-dark Space': very dark blue-black deep space, sparse tiny stars, two tiny faint distant galaxies "
      "at the edges, quiet and lonely, a hint of a faint purple glow far above.",
  15: "STAGE 'Scary Hole': darker purple space with soft violet mist bands swirling inward toward a dark spooky "
      "black-hole opening that starts to appear at the TOP, a little scary but still cute, few stars.",
  16: "STAGE 'Glowing Donut': a huge glowing DONUT-shaped ring of light (an accretion disk) in pastel orange, pink and "
      "gold — drawn like a giant glazed sparkly donut with sprinkles of light — around a black center, mostly at the "
      "edges, dark purple space.",
  17: "STAGE 'Rainbow Hula Hoop': giant glowing RAINBOW HULA-HOOP rings of light spinning around a cute black hole, "
      "several colorful hoops tilted at different angles at the edges, soft purple space, stars being pulled in.",
  18: "STAGE 'Poop Boss's House' (the final stage, inside the black hole): a surreal dark purple dreamy space where the "
      "Poop Boss lives — at the left and right edges a whimsical cute palace made of chocolate-brown soft-serve swirl "
      "towers with little golden crowns, tiny flags and glowing windows, floating swirly pink and cyan light threads. "
      "No faces, no characters.",
}


def gray_canvas(prev):
    """앞 칸 위 OVER px 를 아래에 깐 회색 판 — 이걸 보고 위로 이어 그린다"""
    c = Image.new("RGB", (TW, TH), (128, 128, 128))
    c.paste(prev.crop((0, 0, TW, OVER)), (0, TH - OVER))
    return c


def fit(im):
    im = im.convert("RGB")
    s = TW / im.width
    return im.resize((TW, round(im.height * s)), Image.LANCZOS).crop((0, 0, TW, TH)) if round(im.height * s) >= TH \
        else im.resize((TW, TH), Image.LANCZOS)


def seam(prev, new):
    """새 칸 아래 띠가 앞 칸 위 띠와 가장 잘 맞는 세로 어긋남(dy)과 그때의 차이"""
    ref = prev.crop((0, 0, TW, BLEND)).convert("L").resize((240, BLEND // 4))
    best = (1e9, 0)
    for dy in range(-90, 91, 3):           # 새 칸 안에서 앞 칸 맨 위가 와야 할 자리 = TH-OVER+dy
        y = TH - OVER + dy
        if y < 0 or y + BLEND > TH:
            continue
        cand = new.crop((0, y, TW, y + BLEND)).convert("L").resize((240, BLEND // 4))
        d = sum(ImageStat.Stat(ImageChops.difference(ref, cand)).mean)
        best = min(best, (d, dy))
    return best


def gen(n, k):
    """칸 n 을 k 장 뽑는다 — 후보 경로 목록"""
    refs = []
    prompt = STYLE + STAGE[n]
    if n > 1:
        prev = Image.open(OUT / ("tile_%02d.png" % (n - 1))).convert("RGB")
        gc = OUT / ("_canvas_%02d.png" % n); gray_canvas(prev).save(gc); refs.append(str(gc))
        prompt = STYLE + CONT + STAGE[n]
    refs.append(str(OUT / "style.png"))
    name = "long_%02d" % n
    cmd = [sys.executable, str(ROOT / "tools/gen_codex.py"), name, prompt, "--ref", *refs,
           "--n", str(k), "--jobs", str(k), "--bg", "opaque", "--raw"]
    subprocess.run(cmd, cwd=ROOT, check=False)
    return sorted(p for p in (ROOT / "assets/_gen").glob(name + "_*.png") if not p.stem.endswith("_raw"))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("tiles", type=int, nargs="+")
    ap.add_argument("--n", type=int, default=2)
    a = ap.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    if not (OUT / "style.png").exists():                        # 화풍 참고 — 홈 배경(Codex, 같은 그림체)
        Image.open(ROOT / "assets/bg/home_bangul.webp").convert("RGB").resize((480, 835)).save(OUT / "style.png")
    for n in a.tiles:
        cands = gen(n, a.n)
        if not cands:
            sys.exit("tile %d: 그림을 못 받음 (Codex 한도·오류)" % n)
        scored = []
        for i, p in enumerate(cands):
            im = fit(Image.open(p)); cp = OUT / ("tile_%02d_c%d.png" % (n, i + 1)); im.save(cp)
            if n > 1:
                d, dy = seam(Image.open(OUT / ("tile_%02d.png" % (n - 1))).convert("RGB"), im)
            else:
                d, dy = 0, 0
            scored.append((d, dy, cp)); print("tile %d 후보 %d: 이음매 차이 %.1f (dy %d)" % (n, i + 1, d, dy))
        d, dy, cp = min(scored)
        shutil.copy(cp, OUT / ("tile_%02d.png" % n))
        (OUT / ("tile_%02d.dy" % n)).write_text(str(dy))
        print("tile %d → %s" % (n, cp.name))
    build_strip()


def build_strip():
    """1칸부터 이어 붙인 긴 그림 — 새 칸의 (TH-OVER+dy) 줄이 앞 칸 맨 위와 같은 자리, 그 아래 BLEND 를 섞는다"""
    tiles = []
    n = 1
    while (OUT / ("tile_%02d.png" % n)).exists():
        dy = int((OUT / ("tile_%02d.dy" % n)).read_text()) if n > 1 else 0
        tiles.append((Image.open(OUT / ("tile_%02d.png" % n)).convert("RGB"), dy)); n += 1
    strip = tiles[0][0]
    for im, dy in tiles[1:]:
        y0 = TH - OVER + dy                      # 새 칸에서 앞 그림 맨 위에 해당하는 줄
        add = y0                                 # 새로 위에 붙는 높이
        out = Image.new("RGB", (TW, strip.height + add))
        out.paste(strip, (0, add))
        top = im.crop((0, 0, TW, y0 + BLEND))
        mask = Image.new("L", (TW, y0 + BLEND), 255)
        for y in range(BLEND):                   # 아래로 갈수록 앞 그림이 드러나게
            mask.paste(round(255 * (1 - y / BLEND)), (0, y0 + y, TW, y0 + y + 1))
        base = out.crop((0, 0, TW, y0 + BLEND))
        out.paste(Image.composite(top, base, mask), (0, 0))
        strip = out
    strip.save(OUT / "strip.png")
    prev = strip.resize((TW // 4, strip.height // 4)); prev.save(OUT / "strip_small.png")
    print("strip", strip.size)


if __name__ == "__main__":
    main()
