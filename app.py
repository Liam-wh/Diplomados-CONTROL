import os
import re
from flask import Flask, abort, render_template, request, send_from_directory, url_for

from catalogo_vista import AREAS, AREAS_PORTADA, CURSOS, DESTACADOS, PERFILES_CURSOS, RESTO
from inscripcion import CERTIFICACION
from adjuntos import LIMITE_IMAGEN
from once import TEMAS, once
from configuracion import cargar_entorno
from asesores import asesores, buscar_asesor, whatsapp_url
from supabase_api import SupabaseError, configurado

cargar_entorno()

app = Flask(__name__, static_folder="public", static_url_path="")
app.config["MAX_CONTENT_LENGTH"] = LIMITE_IMAGEN + 65536
app.config.update(
    SECRET_KEY=os.getenv("FLASK_SECRET_KEY") or None,
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
    SESSION_COOKIE_SECURE=bool(os.getenv("VERCEL") or os.getenv("PUBLIC_SITE_URL", "").startswith("https://")),
)
app.register_blueprint(once)
app.register_blueprint(asesores)
def catalogo(*, completo=False, muestra=False):
    telefono = re.sub(r"\D", "", os.getenv("WHATSAPP_NUMBER") or "59163257678")
    supabase_activo = not muestra and configurado()
    try:
        asesor = buscar_asesor(request.args.get("asesor")) if supabase_activo else None
    except SupabaseError:
        abort(503, description="El contacto del asesor no está disponible temporalmente.")
    if asesor:
        telefono = asesor["whatsapp"]
    alcance = url_for("editorial" if completo else "home", asesor=asesor["codigo"] if asesor else None,
                      _anchor="catalogo")
    return render_template(
        "editorial.html", completo=completo, muestra=muestra, telefono=telefono,
        asesor=asesor, supabase_activo=supabase_activo, alcance=alcance, whatsapp_url=whatsapp_url,
        certificados=CERTIFICACION,
        temas=TEMAS, gemini_activo=not muestra and bool(os.getenv("GEMINI_API_KEY", "").strip()),
        form_url=os.getenv("PUBLIC_SITE_URL") or ("https://diplomados.onwi.site/" if muestra else request.url_root),
        cursos=CURSOS, perfiles_cursos=PERFILES_CURSOS,
        programas=DESTACADOS + RESTO, areas=AREAS,
        areas_portada=AREAS_PORTADA, destacados=DESTACADOS,
    )


@app.get("/")
def editorial():
    return catalogo()


@app.get("/todos")
def home():
    return catalogo(completo=True)


@app.get("/qr-titulaciones/descargar")
def descargar_qr():
    return send_from_directory(app.static_folder, "media/qr-titulaciones.png", mimetype="image/png",
                               as_attachment=True, download_name="QR-Titulaciones-ESAM.png")


@app.after_request
def permitir_catalogo_descargado(response):
    if request.path in ("/consulta", "/api/inscripciones") and request.headers.get("Origin") == "null":
        response.headers["Access-Control-Allow-Origin"] = "null"
        response.vary.add("Origin")
    return response


if __name__ == "__main__":
    import webbrowser
    from threading import Thread
    from werkzeug.serving import make_server

    try:
        servidor = make_server("127.0.0.1", 5000, app, threaded=True)
    except SystemExit:
        # Un segundo catálogo puede usar otro puerto local sin cerrar la primera instancia.
        servidor = make_server("127.0.0.1", 0, app, threaded=True)
    base = f"http://127.0.0.1:{servidor.server_port}"
    print(f"Catálogo: {base}/\nMantén abierta esta ventana.", flush=True)
    pagina = base + "/"
    Thread(target=webbrowser.open, args=(pagina,), daemon=True).start()
    try:
        servidor.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        servidor.server_close()
