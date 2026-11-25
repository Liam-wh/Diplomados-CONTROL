begin;

create table public.asesores (
    id uuid primary key references auth.users(id) on delete cascade,
    codigo text not null unique check (codigo ~ '^[a-z0-9][a-z0-9-]{0,39}$'),
    nombre text not null check (length(btrim(nombre)) between 1 and 120),
    whatsapp text not null check (whatsapp ~ '^[1-9][0-9]{7,14}$'),
    activo boolean not null default true
);

create table public.inscripciones (
    id uuid primary key,
    asesor_id uuid references public.asesores(id) on delete set null,
    programa_id integer not null,
    nombre text not null,
    correo text not null,
    whatsapp text check (whatsapp ~ '^[1-9][0-9]{7,14}$'),
    datos jsonb not null,
    creado_en timestamptz not null default now()
);

create index inscripciones_asesor_fecha
    on public.inscripciones (asesor_id, creado_en desc, id desc);

alter table public.asesores enable row level security;
alter table public.inscripciones enable row level security;
revoke all on public.asesores, public.inscripciones from public, anon, authenticated;
grant select on public.asesores, public.inscripciones to authenticated;
grant select on public.asesores to service_role;
grant insert, select (id) on public.inscripciones to service_role;

create policy asesor_lee_su_perfil
    on public.asesores for select to authenticated
    using (activo and (select auth.uid()) = id);

create policy asesor_lee_sus_inscripciones
    on public.inscripciones for select to authenticated
    using (
        asesor_id = (select auth.uid())
        and exists (select 1 from public.asesores where id = asesor_id and activo)
    );

commit;
