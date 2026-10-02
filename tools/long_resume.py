# -*- coding: utf-8 -*-
"""
긴 배경 칸을 끝까지 이어 그린다 — 없는 칸부터 하나씩. Codex 한도에 걸리면 풀리는 시각(오류 문구)까지
또는 30분 기다렸다가 같은 칸부터 다시. 진행은 assets/_gen/long/resume.log 에 남는다.

  python tools/long_resume.py [마지막칸=18] [--n 2]
"""
import datetime as dt, pathlib, re, subprocess, sys, time

ROOT = pathlib.Path(__file__).resolve().parent.parent
LONG = ROOT / "assets/_gen/long"
LOG = LONG / "resume.log"
LAST = int(sys.argv[1]) if len(sys.argv) > 1 and sys.argv[1].isdigit() else 18
N = sys.argv[sys.argv.index("--n") + 1] if "--n" in sys.argv else "2"


def log(msg):
    line = "%s %s" % (dt.datetime.now().strftime("%m-%d %H:%M:%S"), msg)
    print(line, flush=True)
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(line + "\n")


def wait_secs(text):
    """오류 문구에서 다시 쓸 수 있는 시각을 찾는다 — 못 찾으면 30분"""
    m = re.search(r"try again (?:at|in)\s+([^\".]+)", text, re.I)
    if m:
        s = m.group(1).strip()
        mm = re.search(r"(\d+)\s*(hour|hr|h)\b.*?(\d+)?\s*(min|m)?", s, re.I)
        mins = re.search(r"(\d+)\s*min", s, re.I); hrs = re.search(r"(\d+)\s*h", s, re.I)
        if mins or hrs:
            return (int(hrs.group(1)) * 3600 if hrs else 0) + (int(mins.group(1)) * 60 if mins else 0) + 120
        for fmt in ("%I:%M %p", "%H:%M", "%b %d, %Y %I:%M %p", "%B %d %I:%M %p"):
            try:
                t = dt.datetime.strptime(s.replace("st", "").replace("nd", "").replace("rd", "").replace("th", ""), fmt)
                now = dt.datetime.now()
                if t.year == 1900:
                    t = t.replace(year=now.year, month=now.month, day=now.day)
                    if t < now:
                        t += dt.timedelta(days=1)
                return max(120, (t - now).total_seconds() + 120)
            except ValueError:
                pass
    return 1800


def main():
    tries = 0
    while True:
        todo = [n for n in range(1, LAST + 1) if not (LONG / ("tile_%02d.png" % n)).exists()]
        if not todo:
            log("끝 — 1~%d칸 다 그렸다" % LAST)
            return
        n = todo[0]
        log("%d칸 그리는 중" % n)
        r = subprocess.run([sys.executable, str(ROOT / "tools/gen_long.py"), str(n), "--n", N],
                           cwd=ROOT, capture_output=True, text=True, encoding="utf-8", errors="replace")
        out = (r.stdout or "") + (r.stderr or "")
        if (LONG / ("tile_%02d.png" % n)).exists():
            tries = 0
            for line in out.splitlines():
                if line.startswith("tile "):
                    log("  " + line)
            continue
        tries += 1
        tail = " | ".join(l for l in out.splitlines()[-4:] if l.strip())[:400]
        limited = re.search(r"usage limit|rate.?limit|quota|try again", out, re.I)
        w = wait_secs(out) if limited else 120
        if not limited and tries >= 4:
            log("%d칸 4번 실패 — 멈춤: %s" % (n, tail))
            sys.exit(2)
        log("%d칸 실패(%s) — %d분 기다렸다 다시: %s" % (n, "한도" if limited else "오류", w // 60, tail))
        time.sleep(w)


if __name__ == "__main__":
    main()
