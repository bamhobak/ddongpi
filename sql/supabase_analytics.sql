-- 이피재피똥피 플레이 기록 수집 (증강 선택 통계용)
-- Supabase 대시보드 → SQL Editor 에 붙여넣고 Run. 여러 번 실행해도 안전합니다.
--
-- 핵심: 익명 키로는 "넣기만" 되고 "읽기"는 막습니다.
--       그래서 플레이어는 남의 기록은 물론 자기 기록도 볼 수 없고,
--       개발자만 대시보드(서비스 권한)에서 조회할 수 있습니다.

create table if not exists public.ddongpi_runs (
  id         bigserial primary key,
  created_at timestamptz not null default now(),
  score      integer not null,
  level      integer,
  secs       integer,          -- 생존 시간(초)
  stars      integer,          -- 먹은 별 개수
  augs       jsonb not null default '{}'::jsonb,   -- {증강id: 중첩횟수}
  constraint ddongpi_runs_score check (score >= 0 and score <= 100000000)
);

create index if not exists ddongpi_runs_time_idx on public.ddongpi_runs (created_at desc);

alter table public.ddongpi_runs enable row level security;

-- 등록만 허용 (조회 정책은 만들지 않는다 = 익명은 읽을 수 없음)
drop policy if exists ddongpi_runs_insert on public.ddongpi_runs;
create policy ddongpi_runs_insert on public.ddongpi_runs
  for insert to anon, authenticated
  with check (score >= 0 and score <= 100000000);

grant insert on public.ddongpi_runs to anon, authenticated;
grant usage, select on sequence public.ddongpi_runs_id_seq to anon, authenticated;
revoke select on public.ddongpi_runs from anon, authenticated;

notify pgrst, 'reload schema';


-- ─────────────────────────────────────────────────────────
-- 아래는 통계를 볼 때 쓰는 조회문 (대시보드에서 실행)
-- ─────────────────────────────────────────────────────────

-- 1) 증강별 채택 횟수 · 평균 중첩 · 그 증강을 든 판의 평균 점수
-- select k as augment,
--        count(*)                        as 채택판수,
--        sum(v::int)                     as 총중첩,
--        round(avg(v::int), 2)           as 평균중첩,
--        round(avg(r.score))             as 평균점수
--   from public.ddongpi_runs r, lateral jsonb_each_text(r.augs) t(k, v)
--  group by k
--  order by 채택판수 desc;

-- 2) 증강을 하나도 안 든 판 대비 성적 비교
-- select case when augs = '{}'::jsonb then '증강 없음' else '증강 있음' end as 구분,
--        count(*) as 판수, round(avg(score)) as 평균점수, round(avg(secs)) as 평균생존
--   from public.ddongpi_runs group by 1;

-- 3) 최근 플레이 50판
-- select created_at, score, level, secs, stars, augs
--   from public.ddongpi_runs order by created_at desc limit 50;

-- 4) 전체 요약
-- select count(*) as 총판수,
--        round(avg(score)) as 평균점수,
--        max(score) as 최고점수,
--        round(avg(secs)) as 평균생존초,
--        round(avg(stars), 2) as 평균별개수
--   from public.ddongpi_runs;
