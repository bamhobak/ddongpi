-- 대전모드 '기록 대전' (v0.8.33) — 두 폰 대전·기록 대전을 한 판 할 때마다 내 캐릭터가 움직인 길(0.1초마다 자리·높이)을 남긴다.
-- 빠른 대전에서 10초 안에 상대가 없으면 여기서 남의 기록 하나를 골라 그 움직임을 따라 하는 상대와 붙는다.
-- Supabase 대시보드 > SQL Editor 에 붙여 넣고 한 번 실행하면 된다. (여러 번 실행해도 괜찮다)

create table if not exists public.ddongpi_vs_ghosts (
  id         bigserial primary key,
  created_at timestamptz not null default now(),
  name       text not null default '',
  job        text not null default 'none',
  secs       integer not null,
  trace      jsonb not null,                 -- [[x, 높이], ...] 0.1초마다
  constraint ddongpi_vs_ghosts_secs check (secs between 10 and 600),
  constraint ddongpi_vs_ghosts_name check (char_length(name) <= 12),
  constraint ddongpi_vs_ghosts_job  check (char_length(job) <= 16),
  constraint ddongpi_vs_ghosts_size check (pg_column_size(trace) < 80000)
);

create index if not exists ddongpi_vs_ghosts_time_idx on public.ddongpi_vs_ghosts (created_at desc);

alter table public.ddongpi_vs_ghosts enable row level security;

drop policy if exists ddongpi_vs_ghosts_insert on public.ddongpi_vs_ghosts;
create policy ddongpi_vs_ghosts_insert on public.ddongpi_vs_ghosts
  for insert to anon, authenticated
  with check (secs between 10 and 600);

drop policy if exists ddongpi_vs_ghosts_select on public.ddongpi_vs_ghosts;
create policy ddongpi_vs_ghosts_select on public.ddongpi_vs_ghosts
  for select to anon, authenticated
  using (true);

grant insert, select on public.ddongpi_vs_ghosts to anon, authenticated;
grant usage, select on sequence public.ddongpi_vs_ghosts_id_seq to anon, authenticated;

notify pgrst, 'reload schema';
