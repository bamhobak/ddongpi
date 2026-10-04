-- v0.9.218 닉네임 — 3~6자(한글·영어·숫자), 다른 사람이 쓰는 이름은 못 쓴다
-- Supabase SQL Editor 에서 한 번 실행하세요. 실행 전에는 게임이 중복 검사를 건너뜁니다(글자 수·글자 종류 검사만).
--
-- 이름 장부: 이름(대소문자 무시) 하나에 기기 하나. 기기가 이름을 바꾸면 예전 이름은 풀린다.
-- 표는 아무도 직접 못 읽고 못 쓴다 — 아래 함수로만 다룬다(기기 식별자 비공개).

create table if not exists public.ddongpi_names (
  name_key   text primary key,          -- lower(name)
  name       text not null,
  device     text not null,
  created_at timestamptz not null default now()
);
create index if not exists ddongpi_names_device_idx on public.ddongpi_names (device);
alter table public.ddongpi_names enable row level security;   -- 정책 없음 = 직접 접근 불가

-- 이름 차지하기 — 'ok' | 'taken' | 'bad'
--   bad   : 3~6자 아님 · 한글(완성형)·영어·숫자 말고 다른 글자
--   taken : 다른 기기가 장부에 올려 둔 이름, 또는 장부 전부터 다른 기기가 순위표에 그 이름으로 올린 적 있음
create or replace function public.ddongpi_claim_name(nm text, dev text)
returns text
language plpgsql
security definer
set search_path = public
as $$
declare
  k text;
begin
  nm := btrim(coalesce(nm, ''));
  if dev is null or length(dev) < 4 then return 'bad'; end if;
  if char_length(nm) < 3 or char_length(nm) > 6 then return 'bad'; end if;
  if nm !~ '^[가-힣A-Za-z0-9]+$' then return 'bad'; end if;
  k := lower(nm);

  if exists (select 1 from ddongpi_names where name_key = k and device <> dev) then
    return 'taken';
  end if;
  if not exists (select 1 from ddongpi_names where name_key = k)
     and exists (select 1 from ddongpi_scores where lower(name) = k and device is not null and device <> dev) then
    return 'taken';
  end if;

  delete from ddongpi_names where device = dev and name_key <> k;   -- 예전 이름은 놓아준다
  insert into ddongpi_names (name_key, name, device) values (k, nm, dev)
    on conflict (name_key) do update set name = excluded.name;
  return 'ok';
end;
$$;

revoke all on function public.ddongpi_claim_name(text, text) from public;
grant execute on function public.ddongpi_claim_name(text, text) to anon, authenticated;
