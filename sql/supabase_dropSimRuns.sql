-- Remove rows written by headless simulation runs, keep every real play.
--
-- The game asks for a name before it lets anyone start, so every real run
-- carries one. Rows with an empty name came from an automated browser that
-- had no saved name - those are the ones to drop.
--
-- Counts are printed before and after so you can see exactly what went.
-- Paste into Supabase -> SQL Editor and Run.

select count(*) filter (where name is null or btrim(name) = '') as sim_rows_to_delete,
       count(*) filter (where name is not null and btrim(name) <> '') as real_rows_kept,
       count(*) as total_before
  from public.ddongpi_runs;

delete from public.ddongpi_runs
 where name is null or btrim(name) = '';

select count(*) as total_after from public.ddongpi_runs;
