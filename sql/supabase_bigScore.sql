-- 점수 상한을 1억 → 100억으로 올린다.
-- integer 는 최대 약 21억이라 컬럼 타입부터 bigint 로 바꿔야 한다.
-- Supabase 대시보드 → SQL Editor 에 통째로 붙여넣고 실행. (기존 기록은 그대로 유지)
--
-- 주의: 점수를 참조하는 정책(policy)이 붙어 있으면 타입을 바꿀 수 없다.
--       그래서 정책을 먼저 지우고 → 타입을 바꾸고 → 정책을 다시 만든다.

-- ── 1) 순위표 ──────────────────────────────────────────────
drop policy if exists ddongpi_insert on public.ddongpi_scores;
drop policy if exists "insert scores" on public.ddongpi_scores;

alter table public.ddongpi_scores drop constraint if exists ddongpi_score_range;
alter table public.ddongpi_scores alter column score type bigint;
alter table public.ddongpi_scores add constraint ddongpi_score_range
  check (score >= 0 and score <= 10000000000);

create policy ddongpi_insert on public.ddongpi_scores
  for insert to anon, authenticated
  with check (char_length(btrim(name)) between 1 and 12
              and score >= 0 and score <= 10000000000);

-- 읽기 정책은 점수를 참조하지 않으므로 그대로 두고, 혹시 없으면 만들어 둔다
drop policy if exists ddongpi_read on public.ddongpi_scores;
create policy ddongpi_read on public.ddongpi_scores
  for select to anon, authenticated using (true);

-- ── 2) 플레이 기록(증강 통계) ────────────────────────────────
drop policy if exists ddongpi_runs_insert on public.ddongpi_runs;
drop policy if exists "insert runs" on public.ddongpi_runs;

alter table public.ddongpi_runs drop constraint if exists ddongpi_runs_score;
alter table public.ddongpi_runs alter column score type bigint;
alter table public.ddongpi_runs add constraint ddongpi_runs_score
  check (score >= 0 and score <= 10000000000);

create policy ddongpi_runs_insert on public.ddongpi_runs
  for insert to anon, authenticated
  with check (score >= 0 and score <= 10000000000);

-- ── 3) 순위 조회 함수 — 반환 타입도 bigint 로 ────────────────
--     (반환 타입이 바뀌므로 반드시 drop 후 다시 만든다)
drop function if exists public.ddongpi_top(timestamptz, timestamptz, int);
create function public.ddongpi_top(since timestamptz, until timestamptz, lim int)
returns table(name text, score bigint, level integer, created_at timestamptz, augs jsonb)
language sql
stable
as $$
  select s.name, s.score, s.level, s.created_at, s.augs
    from (
      -- 기기가 없는 옛 기록은 id 로 구분해서 각각 살려둔다
      select distinct on (coalesce(d.device, 'id:' || d.id::text))
             d.name, d.score, d.level, d.created_at, d.augs
        from public.ddongpi_scores d
       where d.created_at >= since
         and (until is null or d.created_at < until)
       order by coalesce(d.device, 'id:' || d.id::text), d.score desc, d.created_at asc
    ) s
   order by s.score desc, s.created_at asc
   limit lim;
$$;

grant execute on function public.ddongpi_top(timestamptz, timestamptz, int)
  to anon, authenticated;

notify pgrst, 'reload schema';

-- 확인용 — 두 컬럼이 bigint 로 바뀌었는지
select table_name, column_name, data_type
  from information_schema.columns
 where table_name in ('ddongpi_scores', 'ddongpi_runs')
   and column_name = 'score';
