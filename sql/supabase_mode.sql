-- 스테이지(아이템전 / 노템전)별 순위표.
-- 기록에 mode 칸을 붙이고(비어 있으면 아이템전), TOP 조회 함수가 md 인자로 스테이지를 고르게 한다.
-- md 를 안 주면 아이템전 — 예전 호출도 그대로 돈다.
-- Supabase 대시보드 -> SQL Editor 에 통째로 붙여넣고 Run. 여러 번 실행해도 안전하다.

alter table public.ddongpi_scores add column if not exists mode text;

drop function if exists public.ddongpi_top(timestamptz, timestamptz, int);
drop function if exists public.ddongpi_top(timestamptz, timestamptz, int, text);
create function public.ddongpi_top(since timestamptz, until timestamptz, lim int, md text default 'item')
returns table(name text, score bigint, level integer, created_at timestamptz,
              augs jsonb, job text, fullown boolean, dog boolean)
language sql
stable
as $$
  select s.name, s.score, s.level, s.created_at, s.augs, s.job, s.fullown, s.dog
    from (
      select distinct on (coalesce(d.device, 'id:' || d.id::text))
             d.name, d.score, d.level, d.created_at, d.augs, d.job, d.fullown, d.dog
        from public.ddongpi_scores d
       where d.created_at >= since
         and (until is null or d.created_at < until)
         and coalesce(d.mode, 'item') = coalesce(md, 'item')
       order by coalesce(d.device, 'id:' || d.id::text), d.score desc, d.created_at asc
    ) s
   order by s.score desc, s.created_at asc
   limit lim;
$$;

drop function if exists public.ddongpi_top_job(timestamptz, timestamptz, int, text);
drop function if exists public.ddongpi_top_job(timestamptz, timestamptz, int, text, text);
create function public.ddongpi_top_job(since timestamptz, until timestamptz, lim int, jb text, md text default 'item')
returns table(name text, score bigint, level integer, created_at timestamptz,
              augs jsonb, job text, fullown boolean, dog boolean)
language sql
stable
as $$
  select s.name, s.score, s.level, s.created_at, s.augs, s.job, s.fullown, s.dog
    from (
      select distinct on (coalesce(d.device, 'id:' || d.id::text))
             d.name, d.score, d.level, d.created_at, d.augs, d.job, d.fullown, d.dog
        from public.ddongpi_scores d
       where d.created_at >= since
         and (until is null or d.created_at < until)
         and d.job = jb
         and coalesce(d.mode, 'item') = coalesce(md, 'item')
       order by coalesce(d.device, 'id:' || d.id::text), d.score desc, d.created_at asc
    ) s
   order by s.score desc, s.created_at asc
   limit lim;
$$;

grant execute on function public.ddongpi_top(timestamptz, timestamptz, int, text)
  to anon, authenticated;
grant execute on function public.ddongpi_top_job(timestamptz, timestamptz, int, text, text)
  to anon, authenticated;

notify pgrst, 'reload schema';
