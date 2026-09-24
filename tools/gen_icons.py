# -*- coding: utf-8 -*-
"""
icon_list.NEW 의 아이콘을 한꺼번에 뽑는다 — 이미 뽑은 것(assets/_gen/ic_<이름>_1.png)은 건너뛴다.

  python tools/gen_icons.py            # Codex(구독)로 6개씩 동시에 — 한도에 걸리면 거기서 멈춘다
  python tools/gen_icons.py api        # OpenAI API 로 (돈이 나간다 — 사용자가 허락했을 때만!)

기본은 Codex 만 쓴다. API 는 사용자가 허락할 때만 쓰기로 했다(2026-09-24) — 한도에 걸려도 저절로 넘어가지 않는다.
API 는 작은 아이콘이라 quality medium, 분당 입력 그림 한도 때문에 3개씩·실패하면 40초 쉬고 다시.
진행 기록은 assets/_gen/ic_run.log.
"""
import os, pathlib, subprocess, sys, threading, time
from concurrent.futures import ThreadPoolExecutor

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent
GEN = ROOT / "assets" / "_gen"
sys.path.insert(0, str(HERE))
from icon_list import NEW, STYLE

REF = "assets/_gen/b2_sit_2.png"     # 방울이 — 화풍 참고
limit_hit = threading.Event()
lock = threading.Lock()
GEN.mkdir(parents=True, exist_ok=True)
LOG = open(GEN / "ic_run.log", "a", encoding="utf-8")


def say(*a):
    with lock:
        LOG.write(time.strftime("%H:%M:%S ") + " ".join(str(x) for x in a) + "\n"); LOG.flush()


def done(slug):
    return (GEN / ("ic_%s_1.png" % slug)).exists()


def run(args):
    r = subprocess.run([sys.executable] + args, cwd=ROOT, capture_output=True)
    return (r.stdout + r.stderr).decode("utf-8", "replace")


def by_codex(item):
    _, slug, desc = item
    if done(slug) or limit_hit.is_set():
        return
    out = run(["tools/gen_codex.py", "ic_" + slug, desc + " " + STYLE, "--ref", REF, "--n", "1", "--jobs", "1"])
    if "usage limit" in out:
        limit_hit.set()
    say("codex", slug, "OK" if done(slug) else "FAIL " + out[-200:].replace("\n", " "))


def by_api(item):
    _, slug, desc = item
    for _ in range(6):
        if done(slug):
            return
        out = run(["tools/gen_sprite.py", "ic_" + slug, desc + " " + STYLE, "--ref", REF, "--n", "1", "--quality", "medium"])
        if done(slug):
            say("api", slug, "OK"); return
        say("api", slug, "retry", out[-160:].replace("\n", " "))
        time.sleep(40)
    say("api", slug, "GAVEUP")


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else "codex"
    if mode == "codex":
        with ThreadPoolExecutor(6) as ex:
            list(ex.map(by_codex, NEW))
        say("codex 끝 · 한도", limit_hit.is_set())
    if mode == "api":
        with ThreadPoolExecutor(3) as ex:
            list(ex.map(by_api, [i for i in NEW if not done(i[1])]))
    miss = [i[1] for i in NEW if not done(i[1])]
    say("전부 끝 · 못 뽑은 것", miss)
    print("못 뽑은 것:", miss)


if __name__ == "__main__":
    main()
