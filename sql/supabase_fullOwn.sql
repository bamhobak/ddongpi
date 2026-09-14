-- 순위표에 '풀소유로 진화했는지'를 함께 남기고, TOP 조회가 그 값을 돌려주게 한다.
-- (무소유로 시작해 코인 셋을 연달아 먹으면 풀소유로 진화한다 — 순위표 캐릭터 그림이 바뀐다)
-- Supabase 대시보드 -> SQL Editor 에 통째로 붙여넣고 Run. 여러 번 실행해도 안전하다.
-- 열 이름을 full 이 아니라 fullown 으로 둔 것은 FULL 이 SQL 예약어이기 때문이다.

alter table public.ddongpi_scores add column if not exists fullown boolean;

drop function if exists public.ddongpi_top(timestamptz, timestamptz, int);
create function public.ddongpi_top(since timestamptz, until timestamptz, lim int)
returns table(name text, score bigint, level integer, created_at timestamptz,
              augs jsonb, job text, fullown boolean)
language sql
stable
as $$
  select s.name, s.score, s.level, s.created_at, s.augs, s.job, s.fullown
    from (
      -- 기기가 없는 옛 기록은 id 로 구분해서 각각 살려둔다
      select distinct on (coalesce(d.device, 'id:' || d.id::text))
             d.name, d.score, d.level, d.created_at, d.augs, d.job, d.fullown
        from public.ddongpi_scores d
       where d.created_at >= since
         and (until is null or d.created_at < until)
       order by coalesce(d.device, 'id:' || d.id::text), d.score desc, d.created_at asc
    ) s
   order by s.score desc, s.created_at asc
   limit lim;
$$;

drop function if exists public.ddongpi_top_job(timestamptz, timestamptz, int, text);
create function public.ddongpi_top_job(since timestamptz, until timestamptz, lim int, jb text)
returns table(name text, score bigint, level integer, created_at timestamptz,
              augs jsonb, job text, fullown boolean)
language sql
stable
as $$
  select s.name, s.score, s.level, s.created_at, s.augs, s.job, s.fullown
    from (
      select distinct on (coalesce(d.device, 'id:' || d.id::text))
             d.name, d.score, d.level, d.created_at, d.augs, d.job, d.fullown
        from public.ddongpi_scores d
       where d.created_at >= since
         and (until is null or d.created_at < until)
         and d.job = jb
       order by coalesce(d.device, 'id:' || d.id::text), d.score desc, d.created_at asc
    ) s
   order by s.score desc, s.created_at asc
   limit lim;
$$;

grant execute on function public.ddongpi_top(timestamptz, timestamptz, int)
  to anon, authenticated;
grant execute on function public.ddongpi_top_job(timestamptz, timestamptz, int, text)
  to anon, authenticated;

notify pgrst, 'reload schema';
