-- 이피저피똥피 대전모드 랭킹 (다승 · 승률) — v0.8.45
-- 두 폰 대전이 끝날 때마다 각 기기가 제 결과 한 줄(이겼나/졌나)을 남기고, 순위는 기기별로 모아서 셉니다.
-- 매주 초기화하지 않습니다(전체 기간 누적). Supabase 대시보드 → SQL Editor 에 붙여넣고 Run. 여러 번 실행해도 안전합니다.

create table if not exists public.ddongpi_vs_results (
  id         bigserial primary key,
  device     text        not null,
  name       text        not null,
  win        boolean     not null,
  opp        text,
  created_at timestamptz not null default now(),
  constraint ddongpi_vs_name_len   check (char_length(btrim(name)) between 1 and 12),
  constraint ddongpi_vs_device_len check (char_length(device) between 4 and 40),
  constraint ddongpi_vs_opp_len    check (opp is null or char_length(opp) <= 12)
);

create index if not exists ddongpi_vs_results_device_idx on public.ddongpi_vs_results (device, created_at desc);

alter table public.ddongpi_vs_results enable row level security;

-- 쓰기는 형식이 맞는 새 줄 등록만. 읽기·수정·삭제는 불가(기기 식별자를 남에게 보이지 않게) — 순위는 아래 함수로만 본다
drop policy if exists ddongpi_vs_insert on public.ddongpi_vs_results;
create policy ddongpi_vs_insert on public.ddongpi_vs_results
  for insert to anon, authenticated
  with check (char_length(btrim(name)) between 1 and 12
              and char_length(device) between 4 and 40
              and (opp is null or char_length(opp) <= 12));

grant insert on public.ddongpi_vs_results to anon, authenticated;
grant usage, select on sequence public.ddongpi_vs_results_id_seq to anon, authenticated;

-- 순위 — kind 'wins'(다승: 승 수) / 'rate'(승률: min_games 판 이상만). 이름은 그 기기의 가장 최근 이름.
-- dev 에 내 기기 식별자를 주면 내 줄에 me = true (식별자 자체는 돌려주지 않는다)
create or replace function public.ddongpi_vs_top(kind text, lim int, min_games int, dev text)
returns table(name text, wins int, losses int, games int, rate numeric, me boolean)
language sql
stable
security definer
set search_path = public
as $$
  with agg as (
    select r.device,
           (array_agg(r.name order by r.created_at desc))[1] as name,
           count(*) filter (where r.win)::int      as wins,
           count(*) filter (where not r.win)::int  as losses,
           count(*)::int                           as games
      from public.ddongpi_vs_results r
     group by r.device
  )
  select a.name, a.wins, a.losses, a.games,
         round(a.wins::numeric * 100 / a.games, 1) as rate,
         (dev is not null and a.device = dev)    as me
    from agg a
   where (kind = 'wins' and a.wins > 0)
      or (kind = 'rate' and a.games >= greatest(1, min_games))
   order by case when kind = 'rate' then a.wins::numeric / a.games end desc nulls last,
            a.wins desc, a.games asc
   limit least(greatest(lim, 1), 50);
$$;

grant execute on function public.ddongpi_vs_top(text, int, int, text) to anon, authenticated;

notify pgrst, 'reload schema';
