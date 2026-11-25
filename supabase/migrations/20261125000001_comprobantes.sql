begin;

alter table public.inscripciones
    add column comprobante_imagen bytea,
    add column comprobante_tipo text,
    add constraint comprobante_valido check (
        (comprobante_imagen is null and comprobante_tipo is null)
        or (comprobante_imagen is not null and comprobante_tipo is not null
            and comprobante_tipo in ('image/png', 'image/jpeg', 'image/webp')
            and octet_length(comprobante_imagen) between 1 and 4194304)
    );

commit;
