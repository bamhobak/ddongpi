# -*- coding: utf-8 -*-
"""
ChatGPT 구독(Codex)으로 캐릭터 그림을 뽑는 도구 — gen_sprite.py 와 쓰는 법·결과 규격이 같다.

  python tools/gen_codex.py <이름> "<프롬프트>" [--ref 참고그림 ...] [--n 4] [--jobs 2]

- API 키 대신 Codex CLI 의 ChatGPT 로그인을 쓴다 (VS Code 의 Codex 확장이 로그인돼 있으면 된다).
  크레딧은 안 나가고 구독의 Codex 사용 한도에서 빠진다. 한도에 걸리면 gen_sprite.py(API)로 돌린다.
- Codex 에 내장된 image_gen 도구가 그린다. 한 번 부를 때 한 장이라 --n 장이면 n 번 부른다
  (--jobs 개씩 동시에, 한 번에 1분 반쯤).
- 결과는 gen_sprite.py 와 같다: assets/_gen/<이름>_<번호>_raw.png (받은 그대로) 와
  <이름>_<번호>.png (여백 자르고 높이 320px). --raw 면 자르기·맞추기를 건너뛴다.
- --bg opaque 면 투명 배경을 요청하지 않는다 (배경 그림용, 보통 --raw 와 같이).
- codex.exe 는 환경변수 CODEX_EXE → PATH 의 codex → VS Code 확장 폴더 순으로 찾는다.
"""
import argparse, glob, json, os, pathlib, shutil, subprocess, sys, tempfile, time
from concurrent.futures import ThreadPoolExecutor
from PIL import Image

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from gen_sprite import ROOT, OUT, trim, fit_h   # 자르기·크기 맞추기는 API 판과 똑같이

CODEX_HOME = pathlib.Path(os.environ.get("CODEX_HOME") or pathlib.Path.home() / ".codex")


def find_codex():
    exe = os.environ.get("CODEX_EXE") or shutil.which("codex")
    if exe:
        return exe
    hits = glob.glob(str(pathlib.Path.home() / ".vscode/extensions/openai.chatgpt-*/bin/windows-x86_64/codex.exe"))
    if not hits:
        sys.exit("codex.exe 를 못 찾았습니다 (VS Code Codex 확장 설치·로그인 또는 CODEX_EXE 지정)")
    return max(hits, key=os.path.getmtime)        # 가장 최근 확장 버전


def wrap(prompt, bg):
    """Codex 가 코드를 짜거나 파일을 옮기지 않고 그림 한 장만 그리게 못 박는다."""
    head = ("Use your built-in image generation tool (image_gen) to create exactly ONE image from the spec below. "
            "Do not run any shell commands, do not write code or scripts, do not save, copy or move any files — "
            "just generate the single image and then reply with the word done.\n")
    if bg != "opaque":
        head += "The image must have a transparent background (preserve the alpha).\n"
    return head + "\nImage spec:\n" + prompt


def one(exe, args, i):
    """한 장 뽑아서 (번호, 받은 파일 경로 또는 None, 오류 문구) 를 돌려준다."""
    tmp = tempfile.mkdtemp(prefix="gen_codex_")
    cmd = [exe, "exec", "--skip-git-repo-check", "--ephemeral", "-s", "read-only", "-C", tmp, "--json"]
    for p in args.ref:
        cmd += ["-i", str(pathlib.Path(p).resolve())]
    cmd.append("-")                                # 프롬프트는 표준입력으로 (-i 가 뒤 인자를 삼키므로)
    t0 = time.time()
    try:
        r = subprocess.run(cmd, input=wrap(args.prompt, args.bg).encode("utf-8"),
                           capture_output=True, timeout=args.timeout)
    except subprocess.TimeoutExpired:
        return i, None, "%d초 안에 끝나지 않음" % args.timeout
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    thread, last, errs = None, "", []
    for line in r.stdout.decode("utf-8", "replace").splitlines():
        try:
            e = json.loads(line)
        except ValueError:
            continue
        if e.get("type") == "thread.started":
            thread = e.get("thread_id")
        it = e.get("item") or {}
        if it.get("type") == "agent_message":
            last = it.get("text", "")
        if e.get("type") in ("error", "turn.failed"):
            errs.append(json.dumps(e, ensure_ascii=False)[:400])
    # 내장 도구는 그림을 $CODEX_HOME/generated_images/<스레드>/ 에 남긴다
    pngs = []
    if thread:
        pngs = glob.glob(str(CODEX_HOME / "generated_images" / thread / "*.png"))
    if not pngs:                                   # 스레드를 못 읽었으면 이번 실행 뒤에 생긴 그림으로
        pngs = [p for p in glob.glob(str(CODEX_HOME / "generated_images" / "*" / "*.png"))
                if os.path.getmtime(p) >= t0]
        if len(pngs) > 1:
            pngs = []                              # 동시에 돈 다른 장과 섞일 수 있으니 포기
    if not pngs:
        msg = " / ".join(errs) or last or r.stderr.decode("utf-8", "replace")[-400:]
        return i, None, "그림 없음: " + msg.strip()
    return i, max(pngs, key=os.path.getmtime), ""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("name")
    ap.add_argument("prompt")
    ap.add_argument("--ref", nargs="*", default=[])
    ap.add_argument("--n", type=int, default=4)
    ap.add_argument("--jobs", type=int, default=2, help="동시에 부를 개수")
    ap.add_argument("--bg", default="transparent", help="transparent | opaque")
    ap.add_argument("--raw", action="store_true", help="자르기·크기 맞추기 없이 그대로 (배경 그림용)")
    ap.add_argument("--timeout", type=int, default=600)
    args = ap.parse_args()

    exe = find_codex()
    OUT.mkdir(parents=True, exist_ok=True)
    t0 = time.time()
    with ThreadPoolExecutor(max_workers=max(1, args.jobs)) as ex:
        results = list(ex.map(lambda i: one(exe, args, i), range(1, args.n + 1)))
    saved, failed = [], []
    for i, src, err in results:
        if not src:
            failed.append((i, err))
            continue
        raw_p = OUT / ("%s_%d_raw.png" % (args.name, i))
        shutil.copyfile(src, raw_p)
        raw = Image.open(raw_p).convert("RGBA")
        im = raw if args.raw else fit_h(trim(raw))
        p = OUT / ("%s_%d.png" % (args.name, i))
        im.save(p, optimize=True)
        saved.append((p, im.size))
    print("%.0f초 · codex(ChatGPT 구독) · %d장" % (time.time() - t0, len(saved)))
    for p, sz in saved:
        print("  %s  %dx%d" % (p.relative_to(ROOT), sz[0], sz[1]))
    for i, err in failed:
        print("  #%d 실패: %s" % (i, err))
    if not saved:
        sys.exit(1)


if __name__ == "__main__":
    main()
