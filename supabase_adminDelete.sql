-- 개발자 페이지에서 순위 기록을 지울 수 있게 하는 함수
-- 익명 키로는 여전히 delete 가 막혀 있고, 비밀번호가 맞을 때만 이 함수를 통해서 지워집니다.

create or replace function public.ddongpi_delete(pw text, ids bigint[])
returns int
language plpgsql
security definer
set search_path = public
as $$
declare n int;
begin
  if pw is distinct from '2424' then
    raise exception '비밀번호가 올바르지 않습니다';
  end if;
  delete from ddongpi_scores where id = any(ids);
  get diagnostics n = row_count;
  return n;
end $$;

revoke all on function public.ddongpi_delete(text, bigint[]) from public;
grant execute on function public.ddongpi_delete(text, bigint[]) to anon, authenticated;

notify pgrst, 'reload schema';
