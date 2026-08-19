-- 개발자용 통계 조회 함수
-- 익명 키는 여전히 ddongpi_runs 를 직접 읽을 수 없고, 이 함수를 통해서만
-- 그것도 비밀번호가 맞을 때만 "집계 결과"를 받아갈 수 있습니다.
-- (security definer = 함수가 테이블 주인 권한으로 실행됨)

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
          select t.k                        as k,
                 count(*)                   as n,
                 round(avg(t.v::int), 2)     as st,
                 round(avg(r.score))         as sc
            from ddongpi_runs r, lateral jsonb_each_text(r.augs) t(k, v)
           group by t.k
        ) s
    ), '[]'::jsonb),
    'recent', coalesce((
      select jsonb_agg(jsonb_build_object(
               'score', q.score, 'secs', q.secs, 'level', q.level, 'augs', q.augs))
        from (select * from ddongpi_runs order by created_at desc limit 20) q
    ), '[]'::jsonb)
  ) into result;

  return result;
end $$;

revoke all on function public.ddongpi_stats(text) from public;
grant execute on function public.ddongpi_stats(text) to anon, authenticated;

notify pgrst, 'reload schema';
