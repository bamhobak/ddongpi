-- 플레이 기록에 직업을 함께 남기고, 개발자 통계에서 직업별로 볼 수 있게 한다.
-- Supabase 대시보드 -> SQL Editor 에 통째로 붙여넣고 Run. 여러 번 실행해도 안전하다.
-- (한글 리터럴은 클립보드 인코딩 문제를 피하려고 SQL 에 넣지 않았다. 표시는 게임 쪽에서 바꾼다.)

alter table public.ddongpi_runs add column if not exists job text;

create or replace function public.ddongpi_stats(pw text)
returns jsonb
language plpgsql
security definer
set search_path = public
as $$
declare result jsonb;
begin
  if pw is distinct from '2424' then
    raise exception 'wrong password';
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
          select coalesce(ver, '(none)') as v, count(*) as n,
                 round(avg(score)) as sc, round(avg(secs)) as se
            from ddongpi_runs group by coalesce(ver, '(none)')
        ) q
    ), '[]'::jsonb),
    'jobs', coalesce((
      select jsonb_agg(jsonb_build_object('job', v, 'runs', n, 'avg', av, 'best', bs, 'secs', se)
                       order by n desc)
        from (
          select coalesce(nullif(btrim(job), ''), '(none)') as v,
                 count(*) as n, round(avg(score)) as av, max(score) as bs,
                 round(avg(secs)) as se
            from ddongpi_runs
           group by coalesce(nullif(btrim(job), ''), '(none)')
        ) q
    ), '[]'::jsonb),
    'recent', coalesce((
      select jsonb_agg(jsonb_build_object(
               'name', q.name, 'job', q.job, 'score', q.score, 'secs', q.secs,
               'level', q.level, 'ver', q.ver, 'augs', q.augs))
        from (select * from ddongpi_runs order by created_at desc limit 20) q
    ), '[]'::jsonb)
  ) into result;

  return result;
end $$;

revoke all on function public.ddongpi_stats(text) from public;
grant execute on function public.ddongpi_stats(text) to anon, authenticated;

notify pgrst, 'reload schema';
