-- Per-pet summary for the developer page (runs, average score, best score, average survival).
-- The pet a run took is stored in ddongpi_runs.augs as the key 'pet:<id>'.
-- Runs without a pet key are counted as 'none', but only from when pets launched (v0.7.11,
-- 2026-09-18 22:20 KST) so older runs from before pets existed do not pile into 'none'.
-- Separate function on purpose: ddongpi_stats is left untouched.
-- Paste the whole file into Supabase -> SQL Editor and Run. Safe to run twice.

create or replace function public.ddongpi_pet_stats(pw text)
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

  select coalesce(jsonb_agg(jsonb_build_object('pet', p, 'runs', n, 'avg', av, 'best', bs, 'secs', se)
                            order by n desc), '[]'::jsonb)
    into result
    from (
      select p, count(*) as n, round(avg(score)) as av, max(score) as bs, round(avg(secs)) as se
        from (
          select coalesce((select substr(k, 5) from jsonb_object_keys(coalesce(r.augs, '{}'::jsonb)) k
                            where k like 'pet:%' limit 1), 'none') as p,
                 r.score, r.secs, r.created_at
            from ddongpi_runs r
        ) x
       where p <> 'none' or created_at >= timestamptz '2026-09-18 13:20:20+00'
       group by p
    ) q;

  return result;
end $$;

revoke all on function public.ddongpi_pet_stats(text) from public;
grant execute on function public.ddongpi_pet_stats(text) to anon, authenticated;

notify pgrst, 'reload schema';
