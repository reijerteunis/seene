-- The evidence bucket the storage provider writes to. Environment rather than
-- trade record: SEEN-008 creates the tables, this creates the place raw payloads
-- and evidence live, so `supabase db reset` brings back a working environment.
--
-- Private: every read goes through a signed URL with an expiry, because an
-- evidence object is a buyer's document as often as it is an invoice.
insert into storage.buckets (id, name, public)
values ('evidence', 'evidence', false)
on conflict (id) do nothing;
