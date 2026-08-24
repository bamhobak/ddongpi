-- score cap: 10B -> 1T (bigint already, only constraints & policies change)

drop policy if exists ddongpi_insert on public.ddongpi_scores;
alter table public.ddongpi_scores drop constraint if exists ddongpi_score_range;
alter table public.ddongpi_scores add constraint ddongpi_score_range
  check (score >= 0 and score <= 1000000000000);
create policy ddongpi_insert on public.ddongpi_scores
  for insert to anon, authenticated
  with check (char_length(btrim(name)) between 1 and 12
              and score >= 0 and score <= 1000000000000);

drop policy if exists ddongpi_runs_insert on public.ddongpi_runs;
alter table public.ddongpi_runs drop constraint if exists ddongpi_runs_score;
alter table public.ddongpi_runs add constraint ddongpi_runs_score
  check (score >= 0 and score <= 1000000000000);
create policy ddongpi_runs_insert on public.ddongpi_runs
  for insert to anon, authenticated
  with check (score >= 0 and score <= 1000000000000);

notify pgrst, 'reload schema';
