-- Leave the "no possessions" job out of the per-object score share.
-- That job multiplies the whole score by a growing factor, so its runs would
-- swamp the average share and hide what the other jobs actually earn from.
-- Paste the whole file into Supabase -> SQL Editor and Run. Safe to run twice.
-- (No Korean literals here on purpose - the clipboard mangles them.)

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
    -- average of the per-run share, so one huge run cannot drag the picture
    'src', coalesce((
      select jsonb_agg(jsonb_build_object('k', k, 'pct', pct, 'runs', n)
                       order by pct desc)
        from (
          select t.k as k,
                 round(avg((t.v)::numeric), 1) as pct,
                 count(*) as n
            from ddongpi_runs r, lateral jsonb_each_text(r.src) t(k, v)
           where r.src is not null
             and coalesce(nullif(btrim(r.job), ''), '') <> 'powerp'
           group by t.k
        ) q
    ), '[]'::jsonb),
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
