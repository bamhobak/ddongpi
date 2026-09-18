-- 순위표에 '강아지로 뛰었는지'를 함께 남기고, TOP 조회가 그 값을 돌려주게 한다.
-- (로고의 '재피'로 시작하면 직업 강아지로 뛴다 — 순위표에도 강아지 모습으로 선다)
-- Supabase 대시보드 -> SQL Editor 에 통째로 붙여넣고 Run. 여러 번 실행해도 안전하다.

alter table public.ddongpi_scores add column if not exists fullown boolean;
alter table public.ddongpi_scores add column if not exists dog boolean;

drop function if exists public.ddongpi_top(timestamptz, timestamptz, int);
create function public.ddongpi_top(since timestamptz, until timestamptz, lim int)
returns table(name text, score bigint, level integer, created_at timestamptz,
              augs jsonb, job text, fullown boolean, dog boolean)
language sql
stable
as $$
  select s.name, s.score, s.level, s.created_at, s.augs, s.job, s.fullown, s.dog
    from (
      -- 기기가 없는 옛 기록은 id 로 구분해서 각각 살려둔다
      select distinct on (coalesce(d.device, 'id:' || d.id::text))
             d.name, d.score, d.level, d.created_at, d.augs, d.job, d.fullown, d.dog
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
