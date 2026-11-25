"""Acceso HTTP a Supabase desde Flask."""
import json
import os
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode, urlsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener


class SupabaseError(Exception):
    def __init__(self, status, code=None):
        self.status = status
        self.code = code


class SinRedireccion(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def configurado():
    url = urlsplit(os.getenv("SUPABASE_URL", ""))
    return (
        (url.scheme == "https" or (url.scheme == "http" and url.hostname in {"localhost", "127.0.0.1"}))
        and bool(url.hostname) and not (url.username or url.password or url.query or url.fragment)
        and bool(os.getenv("SUPABASE_PUBLISHABLE_KEY", "").strip())
        and bool(os.getenv("SUPABASE_SECRET_KEY", "").strip())
    )


def consultar(ruta, *, params=None, datos=None, token=None, servidor=False, prefer=None, metodo=None):
    clave = os.environ["SUPABASE_SECRET_KEY" if servidor else "SUPABASE_PUBLISHABLE_KEY"].strip()
    headers = {"apikey": clave, "Accept": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    if prefer:
        headers["Prefer"] = prefer
    body = None
    if datos is not None:
        body = json.dumps(datos, ensure_ascii=False).encode("utf-8")
        headers["Content-Type"] = "application/json"
    url = os.environ["SUPABASE_URL"].rstrip("/") + ruta
    if params:
        url += "?" + urlencode(params)
    try:
        with build_opener(SinRedireccion()).open(Request(url, data=body, headers=headers, method=metodo), timeout=8) as response:
            contenido = response.read()
            return json.loads(contenido) if contenido else None
    except HTTPError as error:
        with error:
            try:
                body = json.loads(error.read(8192))
            except ValueError:
                body = {}
            code = body.get("error_code") or body.get("code") if isinstance(body, dict) else None
            raise SupabaseError(error.code, code) from None
    except (OSError, URLError, ValueError):
        raise SupabaseError(503) from None


def perfil_publico(codigo):
    if not codigo or not configurado():
        return None
    filas = consultar("/rest/v1/asesores", servidor=True, params={
        "select": "id,codigo,nombre,whatsapp", "codigo": "eq." + codigo,
        "activo": "eq.true", "limit": 1,
    })
    return filas[0] if filas else None
