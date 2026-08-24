-- 점수 상한 100억 -> 1조. bigint 는 그대로 담을 수 있어 제약·정책만 갈아끼운다.
-- Supabase 대시보드 -> SQL Editor 에 통째로 붙여넣고 Run. 여러 번 실행해도 안전하다.

-- 순위표
drop policy if exists ddongpi_insert on public.ddongpi_scores;
alter table public.ddongpi_scores drop constraint if exists ddongpi_score_range;
alter table public.ddongpi_scores add constraint ddongpi_score_range
  check (score >= 0 and score <= 1000000000000);
create policy ddongpi_insert on public.ddongpi_scores
  for insert to anon, authenticated
  with check (char_length(btrim(name)) between 1 and 12
              and score >= 0 and score <= 1000000000000);

-- 플레이 기록
drop policy if exists ddongpi_runs_insert on public.ddongpi_runs;
alter table public.ddongpi_runs drop constraint if exists ddongpi_runs_score;
alter table public.ddongpi_runs add constraint ddongpi_runs_score
  check (score >= 0 and score <= 1000000000000);
create policy ddongpi_runs_insert on public.ddongpi_runs
  for insert to anon, authenticated
  with check (score >= 0 and score <= 1000000000000);

notify pgrst, 'reload schema';

-- 확인용
select conname, pg_get_constraintdef(oid)
  from pg_constraint
 where conname in ('ddongpi_score_range', 'ddongpi_runs_score');
