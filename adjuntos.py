"""Comprobantes de pago enviados en el cuerpo multipart; no se conservan copias locales."""

LIMITE_IMAGEN = 4 * 1024 * 1024


def leer_comprobante(archivo, pago):
    if archivo is None or not archivo.filename:
        return None
    if pago != "realizado":
        raise ValueError("Indica que ya pagaste para adjuntar un comprobante.")
    contenido = archivo.read(LIMITE_IMAGEN + 1)
    if len(contenido) > LIMITE_IMAGEN:
        raise ValueError("La imagen supera los 4 MB.")
    if contenido.startswith(b"\x89PNG\r\n\x1a\n"):
        tipo, extension = "image/png", "png"
    elif contenido.startswith(b"\xff\xd8\xff"):
        tipo, extension = "image/jpeg", "jpg"
    elif contenido[:4] == b"RIFF" and contenido[8:12] == b"WEBP":
        tipo, extension = "image/webp", "webp"
    else:
        raise ValueError("Selecciona una imagen JPG, PNG o WebP.")
    return tipo, "comprobante." + extension, contenido
