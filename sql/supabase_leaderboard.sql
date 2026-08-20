-- 이피재피똥피 전체 랭킹 테이블
-- Supabase 대시보드 → SQL Editor 에 붙여넣고 Run 하면 됩니다. 여러 번 실행해도 안전합니다.

create table if not exists public.ddongpi_scores (
  id         bigserial primary key,
  name       text        not null,
  score      integer     not null,
  level      integer,
  created_at timestamptz not null default now(),
  constraint ddongpi_name_len    check (char_length(btrim(name)) between 1 and 12),
  constraint ddongpi_score_range check (score >= 0 and score <= 100000000)
);

create index if not exists ddongpi_scores_rank_idx
  on public.ddongpi_scores (score desc, created_at asc);

alter table public.ddongpi_scores enable row level security;

-- 누구나 읽기 가능(랭킹판), 쓰기는 형식이 맞는 새 기록 등록만 허용. 수정/삭제는 불가.
drop policy if exists ddongpi_read on public.ddongpi_scores;
create policy ddongpi_read on public.ddongpi_scores
  for select to anon, authenticated using (true);

drop policy if exists ddongpi_insert on public.ddongpi_scores;
create policy ddongpi_insert on public.ddongpi_scores
  for insert to anon, authenticated
  with check (char_length(btrim(name)) between 1 and 12 and score >= 0 and score <= 100000000);

grant select, insert on public.ddongpi_scores to anon, authenticated;
grant usage, select on sequence public.ddongpi_scores_id_seq to anon, authenticated;

notify pgrst, 'reload schema';

-- 이미 만들어진 테이블의 점수 상한을 100만 → 1억으로 올릴 때는 아래만 실행하면 됩니다.
-- alter table public.ddongpi_scores drop constraint if exists ddongpi_score_range;
-- alter table public.ddongpi_scores add constraint ddongpi_score_range
--   check (score >= 0 and score <= 100000000);
