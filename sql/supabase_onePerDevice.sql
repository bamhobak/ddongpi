-- 한 기기당 랭킹에 한 줄만 올라가게 하기
-- 기록 자체는 전부 남기되, 순위표를 만들 때 기기별 최고 점수 하나만 골라냅니다.

-- 1) 기기 식별용 컬럼 (기존 기록은 null 로 남고, 각각 별개로 취급됩니다)
alter table public.ddongpi_scores add column if not exists device text;

create index if not exists ddongpi_scores_device_idx
  on public.ddongpi_scores (device, score desc);

-- 2) 순위표 조회 함수 — 기기별 최고 기록만 추려서 점수순으로 돌려줍니다.
--    since / until 로 기간을 잘라서 이번 주·지난주를 모두 이 함수로 처리합니다.
create or replace function public.ddongpi_top(since timestamptz, until timestamptz, lim int)
returns table(name text, score integer, level integer, created_at timestamptz)
language sql
stable
as $$
  select s.name, s.score, s.level, s.created_at
    from (
      -- 기기가 없는 옛 기록은 id 로 구분해서 각각 살려둔다
      select distinct on (coalesce(d.device, 'id:' || d.id::text))
             d.name, d.score, d.level, d.created_at
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
