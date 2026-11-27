"""Acceso de asesores, catálogo compartido y registro de inscripciones."""
from datetime import datetime, timedelta, timezone
from functools import wraps
import os
import re
from secrets import compare_digest, token_urlsafe
from time import time
from urllib.parse import quote
from uuid import UUID, uuid4

from flask import Blueprint, Response, abort, flash, current_app, jsonify, make_response, redirect, render_template, request, session, url_for

from adjuntos import leer_comprobante
from catalogo_vista import INSCRIBIBLES
from inscripcion import preparar, texto
from panel_datos import exportar_excel, filtrar, inscripciones
from supabase_api import SupabaseError, configurado, consultar, perfil_publico

asesores = Blueprint("asesores", __name__)


def whatsapp_url(numero="", mensaje=""):
    return "https://wa.me/" + numero + ("?text=" + quote(mensaje, safe="") if mensaje else "")


def buscar_asesor(codigo):
    if re.fullmatch(r"[a-z0-9][a-z0-9-]{0,39}", codigo or ""):
        return perfil_publico(codigo)
    return None


def guardar_inscripcion(form, programa, campos, adjunto):
    codigo = form.get("referencia_asesor", "")
    asesor = buscar_asesor(codigo)
    if codigo and not asesor:
        raise ValueError("El enlace del asesor ya no está activo. Abre el catálogo general para continuar.")
    numero = re.sub(r"[ +().-]", "", form.get("whatsapp", "").strip())
    if numero and not re.fullmatch(r"[1-9][0-9]{7,14}", numero):
        raise ValueError("Escribe un WhatsApp válido e incluye el código de país.")
    referencia = form.get("intento")
    try:
        referencia = str(UUID(referencia)) if referencia else str(uuid4())
    except ValueError:
        raise ValueError("La referencia de la solicitud es inválida. Vuelve a abrir el formulario.") from None
    if numero:
        campos["WhatsApp del estudiante"] = "+" + numero
    fila = {
        "id": referencia, "asesor_id": asesor["id"] if asesor else None,
        "programa_id": programa["id"], "nombre": campos["Nombre del estudiante"],
        "correo": campos["Correo del estudiante"], "whatsapp": numero or None, "datos": campos,
    }
    if adjunto:
        tipo, _, contenido = adjunto
        fila["comprobante_tipo"] = tipo
        fila["comprobante_imagen"] = "\\x" + contenido.hex()
        if not form.get("comprobante"):
            campos.pop("Enlace al comprobante", None)
    consultar("/rest/v1/inscripciones", servidor=True, params={"on_conflict": "id"},
              prefer="resolution=ignore-duplicates,return=minimal", datos=fila)


@asesores.post("/consulta")
@asesores.post("/api/inscripciones")
def registrar():
    if not configurado():
        return jsonify(message="El registro de inscripciones no está disponible."), 503
    form = request.form
    programa = INSCRIBIBLES.get(form.get("program", type=int))
    try:
        inscripcion = preparar(form, programa)
        adjunto = leer_comprobante(request.files.get("attachment"), form.get("pago"))
        guardar_inscripcion(form, programa, inscripcion, adjunto)
    except ValueError as error:
        return jsonify(message=str(error)), 400
    except SupabaseError:
        return jsonify(message="No pudimos confirmar el registro. Tus datos siguen en el formulario."), 503
    return jsonify(status="registered"), 201


def privada(vista):
    @wraps(vista)
    def respuesta(*args, **kwargs):
        result = make_response(vista(*args, **kwargs))
        result.headers["Cache-Control"] = "private, no-store"
        result.headers["Referrer-Policy"] = "no-referrer"
        result.headers["X-Robots-Tag"] = "noindex"
        return result
    return respuesta


def perfil(token):
    filas = consultar("/rest/v1/asesores", token=token, params={
        "select": "id,codigo,nombre,whatsapp", "limit": 1,
    })
    return filas[0] if filas else None


def configurado_acceso():
    return configurado() and bool(current_app.secret_key)


def login_pagina(error=None, status=200):
    listo = configurado_acceso()
    csrf = session.setdefault("asesor_csrf", token_urlsafe(32)) if listo else ""
    return render_template("asesores.html", login=True, listo=listo, csrf=csrf, error=error), status


def csrf_valido():
    esperado = session.get("asesor_csrf", "")
    enviado = request.form.get("csrf", "")
    return bool(esperado and enviado.isascii() and compare_digest(esperado, enviado))


@asesores.route("/asesores", methods=["GET", "POST"])
@privada
def login():
    if not configurado_acceso():
        return login_pagina(status=503)
    if request.method == "GET":
        return login_pagina()
    if not csrf_valido():
        return login_pagina("La página caducó. Vuelve a ingresar tus datos.", 400)
    usuario = request.form.get("usuario", request.form.get("email", "")).strip()
    password = request.form.get("password", "")
    if not usuario or not password or len(usuario) > 254 or len(password) > 256:
        return login_pagina("Revisa tu usuario y contraseña.", 400)
    try:
        email = usuario
        esperado = None
        if "@" not in usuario:
            asesor = buscar_asesor(usuario.lower())
            if not asesor:
                return login_pagina("Revisa tu usuario y contraseña.", 401)
            esperado = asesor["id"]
            cuenta = consultar("/auth/v1/admin/users/" + esperado, servidor=True)
            email = cuenta.get("email")
            if not email:
                return login_pagina("Revisa tu usuario y contraseña.", 401)
        acceso = consultar("/auth/v1/token", params={"grant_type": "password"},
                           datos={"email": email, "password": password})
        token = acceso["access_token"]
        actual = perfil(token)
        if not actual or (esperado and actual["id"] != esperado):
            return login_pagina("Esta cuenta no tiene un perfil de asesor activo.", 403)
    except SupabaseError as error:
        if error.status == 429:
            return login_pagina("Demasiados intentos. Espera un momento y vuelve a probar.", 429)
        if error.status in (400, 401, 403, 422):
            return login_pagina("Revisa tu usuario y contraseña.", 401)
        return login_pagina("El servicio de acceso no está disponible en este momento.", 503)
    session.clear()
    session["asesor_inicio"] = int(time())
    session["asesor_token"] = token
    session["asesor_expira"] = int(time()) + min(acceso.get("expires_in", 3600), 3600)
    session["asesor_csrf"] = token_urlsafe(32)
    return redirect(url_for(".dashboard"), 303)


def volver_al_acceso():
    session.clear()
    return redirect(url_for(".login"))


def con_asesor(vista):
    @wraps(vista)
    def protegida(*args, **kwargs):
        token = session.get("asesor_token")
        if not configurado_acceso() or not token or session.get("asesor_expira", 0) <= time():
            return volver_al_acceso()
        try:
            asesor = perfil(token)
            if not asesor:
                return volver_al_acceso()
            return vista(token, asesor, *args, **kwargs)
        except SupabaseError as error:
            if error.status == 401:
                return volver_al_acceso()
            return render_template("asesores.html", error="Supabase no pudo completar la consulta. Vuelve a intentarlo.",
                                   csrf=session["asesor_csrf"]), 503
    return protegida


@asesores.get("/dashboard")
@asesores.get("/dashboard/inscripciones.xlsx", endpoint="excel")
@privada
@con_asesor
def dashboard(token, asesor):
    filtros = {k: request.args.get(k, "").strip() for k in ("q", "programa", "pago", "desde", "hasta")}
    todas = inscripciones(token, asesor["id"])
    filas = filtrar(todas, filtros)
    if request.endpoint == "asesores.excel":
        return Response(exportar_excel(filas), mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        headers={"Content-Disposition": 'attachment; filename="inscripciones.xlsx"'})
    paginas = max(1, (len(filas) + 24) // 25)
    pagina = min(paginas, max(1, request.args.get("pagina", 1, type=int)))
    base = (os.getenv("PUBLIC_SITE_URL") or request.url_root).rstrip("/")
    enlace = base + url_for("home", asesor=asesor["codigo"], _anchor="catalogo")
    inicio = session.get("asesor_inicio")
    zona = timezone(timedelta(hours=-4))
    fecha_inicio = datetime.fromtimestamp(inicio, zona) if inicio else None
    if not inicio:
        ultimo = consultar("/auth/v1/user", token=token).get("last_sign_in_at")
        if ultimo:
            fecha_inicio = datetime.fromisoformat(ultimo.replace("Z", "+00:00")).astimezone(zona)
            session["asesor_inicio"] = int(fecha_inicio.timestamp())
    return render_template(
        "asesores.html", asesor=asesor, csrf=session["asesor_csrf"], enlace=enlace,
        compartir=whatsapp_url(mensaje="Te comparto el catálogo de cursos y diplomados UPI Alumni: " + enlace),
        filas=filas[(pagina-1)*25:pagina*25], total=len(filas), pagados=sum(f["pagado"] for f in filas),
        monto=sum(f["monto"] for f in filas), filtros=filtros, pagina=pagina, paginas=paginas,
        programas=sorted({f["programa"] for f in todas}), inicio=fecha_inicio, whatsapp_url=whatsapp_url,
        enlaces={k: v for k, v in filtros.items() if v},
    )


@asesores.route("/dashboard/cuenta", methods=["GET", "POST"])
@privada
@con_asesor
def cuenta(token, asesor):
    identidad = consultar("/auth/v1/user", token=token)

    def mostrar(error=None, status=200):
        return render_template("asesores.html", cuenta=True, asesor=asesor, csrf=session["asesor_csrf"],
                               identidad=identidad, profesional=identidad.get("user_metadata") or {},
                               error_cuenta=error), status
    if request.method == "GET":
        return mostrar()
    if not csrf_valido():
        return mostrar("La página caducó. Recarga antes de guardar.", 400)
    accion = request.form.get("accion")
    if accion == "perfil":
        nombre = request.form.get("nombre", "").strip()
        codigo = request.form.get("usuario", "").strip().lower()
        if not 1 <= len(nombre) <= 120 or not nombre.isprintable() or not re.fullmatch(r"[a-z0-9][a-z0-9-]{0,39}", codigo):
            return mostrar("Revisa el nombre y el formato del usuario.", 400)
        cambios = {"nombre": nombre, "codigo": codigo}
        if "whatsapp" in request.form:
            numero = re.sub(r"[ ().-]", "", request.form["whatsapp"].strip()).removeprefix("+")
            if not re.fullmatch(r"[1-9][0-9]{7,14}", numero):
                return mostrar("Escribe tu WhatsApp con el código de país, por ejemplo +591 7000 0000.", 400)
            cambios["whatsapp"] = numero
        try:
            actualizado = consultar("/rest/v1/asesores", servidor=True, metodo="PATCH",
                         params={"id": "eq."+asesor["id"], "activo": "eq.true", "select": "id"},
                         prefer="return=representation", datos=cambios)
        except SupabaseError as error:
            if error.status == 409:
                return mostrar("Ese usuario ya está en uso. Elige otro.", 409)
            raise
        if not actualizado:
            return volver_al_acceso()
        flash("Datos del asesor actualizados.")
        return redirect(url_for(".cuenta"), 303)
    if accion == "profesional":
        try:
            datos = {campo: texto(request.form, campo, campo.capitalize(), 120, obligatorio=False)
                     for campo in ("sede", "cargo")}
        except ValueError as error:
            return mostrar(str(error), 400)
        consultar("/auth/v1/user", token=token, metodo="PUT", datos={"data": datos})
        flash("Sede y cargo guardados.")
        return redirect(url_for(".cuenta"), 303)
    if accion not in ("correo", "clave"):
        abort(400)
    actual = request.form.get("actual", "")
    if not actual or len(actual) > 256:
        return mostrar("Introduce tu contraseña actual.", 400)
    if accion == "correo":
        correo = request.form.get("correo", "").strip()
        if len(correo) > 254 or not re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+", correo):
            return mostrar("Escribe un correo electrónico válido.", 400)
        if correo.casefold() == identidad["email"].casefold():
            return mostrar("El nuevo correo coincide con tu correo actual.", 400)
        cambio = {"email": correo}
    else:
        nueva = request.form.get("nueva", "")
        if not nueva or len(nueva) > 256 or nueva != request.form.get("confirmar"):
            return mostrar("Revisa la nueva contraseña y su confirmación.", 400)
        cambio = {"password": nueva}
    try:
        acceso = consultar("/auth/v1/token", params={"grant_type":"password"},
                           datos={"email": identidad["email"], "password": actual})
        if acceso["user"]["id"] != asesor["id"]:
            return volver_al_acceso()
        actualizado = consultar("/auth/v1/user", metodo="PUT", token=acceso["access_token"], datos=cambio)
    except SupabaseError as error:
        if error.status == 429:
            return mostrar("Demasiados intentos. Vuelve a probar en unos minutos.", 429)
        if error.status in (400, 401, 403, 422):
            if accion == "correo":
                return mostrar("No se pudo cambiar el correo. Revisa la dirección y la contraseña actual.", 400)
            return mostrar("Comprueba la contraseña actual y elige una nueva que cumpla los requisitos de Supabase.", 400)
        raise
    if accion == "correo":
        if actualizado.get("email", "").casefold() == correo.casefold():
            flash("Correo de acceso actualizado.")
        else:
            flash("Cambio solicitado. Revisa el correo actual y el nuevo para completar la confirmación.")
        return redirect(url_for(".cuenta"), 303)
    session.clear()
    flash("Contraseña actualizada. Inicia sesión con tu nueva contraseña.")
    return redirect(url_for(".login"), 303)


@asesores.post("/dashboard/inscripciones/<uuid:inscripcion_id>/eliminar")
@privada
@con_asesor
def eliminar_inscripcion(token, asesor, inscripcion_id):
    if not csrf_valido():
        abort(400, description="La página caducó. Recarga el panel antes de eliminar.")
    eliminadas = consultar("/rest/v1/inscripciones", servidor=True, metodo="DELETE",
                           params={"id": "eq." + str(inscripcion_id), "asesor_id": "eq." + asesor["id"],
                                   "select": "id"}, prefer="return=representation")
    flash("Inscripción eliminada." if eliminadas else "La inscripción ya no está disponible en tu panel.")
    filtros = {k: request.args[k] for k in ("pagina", "q", "pago", "programa", "desde", "hasta")
               if request.args.get(k)}
    return redirect(url_for(".dashboard", **filtros), 303)


@asesores.get("/dashboard/comprobantes/<uuid:inscripcion_id>")
@privada
def comprobante(inscripcion_id):
    token = session.get("asesor_token")
    if not configurado_acceso() or not token or session.get("asesor_expira", 0) <= time():
        return redirect(url_for(".login"))
    try:
        filas = consultar("/rest/v1/inscripciones", token=token, params={
            "select": "comprobante_tipo,comprobante_imagen", "id": "eq." + str(inscripcion_id),
            "comprobante_tipo": "not.is.null", "limit": 1,
        })
    except SupabaseError as error:
        if error.status in (401, 403):
            return volver_al_acceso()
        abort(503)
    if not filas:
        abort(404)
    fila = filas[0]
    extension = {"image/png": "png", "image/jpeg": "jpg", "image/webp": "webp"}[fila["comprobante_tipo"]]
    disposicion = "inline" if request.args.get("vista") == "1" else "attachment"
    return Response(bytes.fromhex(fila["comprobante_imagen"][2:]), mimetype=fila["comprobante_tipo"],
                    headers={"Content-Disposition": f'{disposicion}; filename="comprobante.{extension}"',
                             "X-Content-Type-Options": "nosniff"})


@asesores.post("/asesores/salir")
@privada
def salir():
    if not csrf_valido():
        return "La página caducó. Vuelve al panel para cerrar sesión.", 400
    token = session.get("asesor_token")
    session.clear()
    if token and configurado_acceso():
        try:
            consultar("/auth/v1/logout", token=token, params={"scope": "local"}, datos={})
        except SupabaseError:
            pass
    return redirect(url_for(".login"), 303)
