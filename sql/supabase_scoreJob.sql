-- 1) 통계 데이터 초기화 (증강별·직업별·최근 판 = ddongpi_runs 전체 삭제)
-- 2) 순위표(ddongpi_scores)에 직업 저장 + TOP 조회가 직업을 함께 돌려주게
-- Supabase 대시보드 -> SQL Editor 에 통째로 붙여넣고 Run.
-- 주의: ddongpi_runs 의 기존 기록은 전부 지워지며 되돌릴 수 없다. (순위표 기록은 유지)

truncate table public.ddongpi_runs;

alter table public.ddongpi_scores add column if not exists job text;

drop function if exists public.ddongpi_top(timestamptz, timestamptz, int);
create function public.ddongpi_top(since timestamptz, until timestamptz, lim int)
returns table(name text, score bigint, level integer, created_at timestamptz, augs jsonb, job text)
language sql
stable
as $$
  select s.name, s.score, s.level, s.created_at, s.augs, s.job
    from (
      -- 기기가 없는 옛 기록은 id 로 구분해서 각각 살려둔다
      select distinct on (coalesce(d.device, 'id:' || d.id::text))
             d.name, d.score, d.level, d.created_at, d.augs, d.job
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

-- 확인용
select count(*) as runs_after_reset from public.ddongpi_runs;
