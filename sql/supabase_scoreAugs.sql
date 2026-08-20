-- 순위표 기록에도 그 판에서 고른 증강을 함께 저장한다 (개발자 통계 화면에서 확인용)

alter table public.ddongpi_scores add column if not exists augs jsonb not null default '{}'::jsonb;

-- 순위 조회 함수가 증강까지 함께 돌려주도록 갱신
create or replace function public.ddongpi_top(since timestamptz, until timestamptz, lim int)
returns table(name text, score integer, level integer, created_at timestamptz, augs jsonb)
language sql
stable
as $$
  select s.name, s.score, s.level, s.created_at, s.augs
    from (
      -- 기기가 없는 옛 기록은 id 로 구분해서 각각 살려둔다
      select distinct on (coalesce(d.device, 'id:' || d.id::text))
             d.name, d.score, d.level, d.created_at, d.augs
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
