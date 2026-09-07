-- Wipe the play-record table that feeds the dev stats screen.
--
-- WHAT GOES:  every row of ddongpi_runs - summary, per-object score share,
--             augment picks, per-version table, per-job table, recent runs.
-- WHAT STAYS: ddongpi_scores, so the title-screen TOP 10 and the weekly
--             ranking are untouched.
--
-- This cannot be undone. Paste into Supabase -> SQL Editor and Run.

-- how many rows are about to go (shown before the delete)
select count(*) as runs_before_reset from public.ddongpi_runs;

truncate table public.ddongpi_runs;

select count(*) as runs_after_reset from public.ddongpi_runs;
