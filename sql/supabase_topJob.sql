-- Per-job weekly TOP list. Same as ddongpi_top but filtered by job,
-- so each device's best run WITH THAT JOB is used (not its overall best).
-- Paste into Supabase SQL Editor and Run. Safe to run more than once.

drop function if exists public.ddongpi_top_job(timestamptz, timestamptz, int, text);
create function public.ddongpi_top_job(since timestamptz, until timestamptz, lim int, jb text)
returns table(name text, score bigint, level integer, created_at timestamptz, augs jsonb, job text)
language sql
stable
as $$
  select s.name, s.score, s.level, s.created_at, s.augs, s.job
    from (
      select distinct on (coalesce(d.device, 'id:' || d.id::text))
             d.name, d.score, d.level, d.created_at, d.augs, d.job
        from public.ddongpi_scores d
       where d.created_at >= since
         and (until is null or d.created_at < until)
         and d.job = jb
       order by coalesce(d.device, 'id:' || d.id::text), d.score desc, d.created_at asc
    ) s
   order by s.score desc, s.created_at asc
   limit lim;
$$;

grant execute on function public.ddongpi_top_job(timestamptz, timestamptz, int, text)
  to anon, authenticated;

notify pgrst, 'reload schema';
