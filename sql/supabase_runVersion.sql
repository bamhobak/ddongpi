-- 플레이 기록에 게임 버전을 함께 남기고, 통계 함수도 버전별로 볼 수 있게 갱신

alter table public.ddongpi_runs add column if not exists ver text;

create or replace function public.ddongpi_stats(pw text)
returns jsonb
language plpgsql
security definer
set search_path = public
as $$
declare result jsonb;
begin
  if pw is distinct from '2424' then
    raise exception '비밀번호가 올바르지 않습니다';
  end if;

  select jsonb_build_object(
    'summary', (
      select jsonb_build_object(
        'runs',      count(*),
        'avg_score', coalesce(round(avg(score)), 0),
        'max_score', coalesce(max(score), 0),
        'avg_secs',  coalesce(round(avg(secs)), 0),
        'avg_stars', coalesce(round(avg(stars), 2), 0)
      ) from ddongpi_runs
    ),
    'augs', coalesce((
      select jsonb_agg(
               jsonb_build_object('id', k, 'picks', n, 'stack', st, 'score', sc)
               order by n desc)
        from (
          select t.k as k, count(*) as n,
                 round(avg(t.v::int), 2) as st, round(avg(r.score)) as sc
            from ddongpi_runs r, lateral jsonb_each_text(r.augs) t(k, v)
           group by t.k
        ) s
    ), '[]'::jsonb),
    'vers', coalesce((
      select jsonb_agg(jsonb_build_object('ver', v, 'runs', n, 'score', sc, 'secs', se)
                       order by v desc)
        from (
          select coalesce(ver, '(없음)') as v, count(*) as n,
                 round(avg(score)) as sc, round(avg(secs)) as se
            from ddongpi_runs group by coalesce(ver, '(없음)')
        ) q
    ), '[]'::jsonb),
    'recent', coalesce((
      select jsonb_agg(jsonb_build_object(
               'score', q.score, 'secs', q.secs, 'level', q.level,
               'ver', q.ver, 'augs', q.augs))
        from (select * from ddongpi_runs order by created_at desc limit 20) q
    ), '[]'::jsonb)
  ) into result;

  return result;
end $$;

revoke all on function public.ddongpi_stats(text) from public;
grant execute on function public.ddongpi_stats(text) to anon, authenticated;

notify pgrst, 'reload schema';
