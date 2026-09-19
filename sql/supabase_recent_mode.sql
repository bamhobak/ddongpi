-- Latest 20 runs for one stage mode, for the developer page ("recent runs" tabs).
-- md = 'item'   -> runs that carry no 'mode:*' key (the default stage)
-- md = 'noitem' -> runs whose augs carry 'mode:noitem' (tower climb)
-- md = 'pure'   -> runs whose augs carry 'mode:pure' (bare-hands duel)
-- Separate function on purpose: ddongpi_stats is left untouched.
-- Paste the whole file into Supabase -> SQL Editor and Run. Safe to run twice.

create or replace function public.ddongpi_recent_mode(pw text, md text)
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

  select coalesce(jsonb_agg(jsonb_build_object(
           'name', q.name, 'job', q.job, 'score', q.score, 'secs', q.secs,
           'level', q.level, 'ver', q.ver, 'augs', q.augs) order by q.created_at desc), '[]'::jsonb)
    into result
    from (
      select * from ddongpi_runs r
       where case when md = 'item'
                  then not (coalesce(r.augs ? 'mode:noitem', false) or coalesce(r.augs ? 'mode:pure', false))
                  else coalesce(r.augs ? ('mode:' || md), false) end
       order by r.created_at desc
       limit 20
    ) q;

  return result;
end $$;

revoke all on function public.ddongpi_recent_mode(text, text) from public;
grant execute on function public.ddongpi_recent_mode(text, text) to anon, authenticated;

notify pgrst, 'reload schema';
