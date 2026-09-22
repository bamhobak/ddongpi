# -*- coding: utf-8 -*-
"""지대 배경 2~18 을 새 그림체(zone01)로 다시 뽑는다. 2개씩 동시에 (한도에 걸리면 기다렸다 다시).
   python tools/gen_zones.py [지대번호 ...]   (없으면 2~18 전부)"""
import subprocess, sys, pathlib, time
from concurrent.futures import ThreadPoolExecutor
ROOT = pathlib.Path(__file__).resolve().parent.parent
COMMON = ("A tall vertical scrolling background for one stage of a cute game where a puppy floats higher and higher "
  "from a grassy meadow up into the sky and out into space. Use the FIRST reference image ONLY for ART STYLE "
  "(it is the finished first stage: kawaii sticker look, soft rounded shapes, thin soft dark outlines, smooth pastel cel "
  "shading, gentle and dreamy). Use the SECOND reference image (the old background of THIS stage) for the content and "
  "palette, but redraw everything in the new style. The picture scrolls upward during play, so the BOTTOM of the image "
  "should feel slightly closer to the previous (lower) stage and the TOP slightly closer to the next (higher) stage. "
  "Keep the middle of the image calm and uncluttered with low contrast so small falling objects stay easy to read. "
  "No characters, no animals, no people, no text, no UI. "
  "IMPORTANT: this stage is high up in the sky or in space, so there is NO ground at all — do not draw any grass, "
  "meadow, hills, flowers, trees, rocks on the ground or land anywhere in the image. STAGE: ")
# 첫 판에서 1단계 그림(발밑 잔디 언덕 포함)을 화풍 참고로 넣었더니 4~14단계까지 발밑에 언덕을 그렸다 —
# 참고 그림은 하늘 부분만 잘라 쓰고(style_sky.png), 땅 금지를 못 박는다. (2·3단계는 첫 판 것을 쓴다)
Z = {
 2: "'On the Hill' — a slightly deeper blue daytime sky, soft fluffy clouds and a faint pastel rainbow arc; at the very bottom only the tips of distant soft rocky hilltops peeking up. Bright and cheerful.",
 3: "'Sea of Clouds' — the puppy has risen above the clouds: a thick soft fluffy sea of white clouds fills the bottom quarter, with more cloud puffs scattered higher up against a clear blue sky.",
 4: "'Edge of the Troposphere' — a deeper clear blue sky with only a few thin wispy clouds, the cloud sea far below at the very bottom, and the first tiny faint stars appearing near the top.",
 5: "'Stratosphere' — deep blue sky turning darker toward the top, long thin streaky high-altitude clouds, a few twinkling stars, a tiny distant weather balloon far away.",
 6: "'Ozone Layer' — a navy-to-teal sky with soft glowing turquoise haze bands drifting across, more little stars twinkling, calm and cool.",
 7: "'Aurora Zone' — a deep night-blue sky with big soft flowing curtains of green, mint and pink aurora light, lots of small twinkling stars. Magical.",
 8: "'Mesosphere' — a dark indigo night sky full of cute twinkling stars, a few soft shooting stars with pastel trails, faint thin silvery night clouds near the bottom.",
 9: "'Karman Line' — the edge of space: near-black navy at the top with many stars, and at the bottom the glowing curved rim of the Earth's atmosphere as a soft bright cyan arc.",
 10: "'Low Earth Orbit' — a big cute cartoon Earth with soft outlines (blue oceans, green continents, white swirl clouds) filling the bottom of the image, dark starry space above.",
 11: "'Lunar Orbit' — a big cute round pale moon with soft craters in the lower middle, a tiny Earth far away, dark purple starry space around.",
 12: "'Asteroid Belt' — cute chunky pastel asteroid rocks of various sizes floating in dark purple space with twinkling stars, rocks mostly near the left and right edges.",
 13: "'Milky Way' — a dreamy pastel pink, lavender and mint milky-way band flowing diagonally across a deep blue space full of little stars and sparkles.",
 14: "'Deep Space' — very dark blue-black space, sparse little stars, a couple of tiny faint distant galaxies, and far away near the top a tiny black dot with a faint purple glow.",
 15: "'Threshold of Darkness' — dark purple space with soft swirling violet mist bands curling toward a growing dark center near the top, fewer stars. Mysterious but still cute.",
 16: "'Accretion Disk' — a huge fiery pastel orange, pink and gold swirling disk of light around a black center, glowing streaks, dark purple space. Dramatic but soft.",
 17: "'Event Horizon' — a giant cute black hole with a glowing rainbow-colored ring filling the upper half of the image, soft purple space and stars being pulled toward it below.",
 18: "'Inside the Black Hole' — a surreal dreamy dark purple and indigo space inside the black hole, softly glowing twisting threads of pink and cyan light looping everywhere, tiny sparkles. Strange and magical.",
}
# '마지막엔 블랙홀로' 라고 적었더니 5·6·7·10·11단계 위쪽에 블랙홀을 미리 그려 넣었다 — 13단계까지는 금지
NO_BH = " There is NO black hole, vortex or dark swirl anywhere in this stage."
def run(n):
    cmd = [sys.executable, str(ROOT / "tools" / "gen_sprite.py"), "zone%02d" % n, COMMON + Z[n] + (NO_BH if n <= 13 else ""),
           "--ref", str(ROOT / "assets/_gen/style_sky.png"), str(ROOT / ("assets/_gen/zone%02d_old.png" % n)),
           "--bg", "opaque", "--raw", "--size", "960x2304", "--n", "2"]
    # OpenAI 분당 이미지 한도(rate_limit_exceeded)에 걸리면 기다렸다 다시 — 4개 동시엔 걸렸다
    for attempt in range(6):
        r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace", cwd=ROOT)
        out = r.stdout + r.stderr
        if r.returncode == 0 or "rate_limit" not in out:
            break
        time.sleep(45 + attempt * 30)
    return n, r.returncode, out.strip().splitlines()[-3:]
todo = [int(a) for a in sys.argv[1:]] or list(range(2, 19))
with ThreadPoolExecutor(2) as ex:
    for n, rc, tail in ex.map(run, todo):
        print("zone%02d rc=%d | %s" % (n, rc, " / ".join(tail)), flush=True)
