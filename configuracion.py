import os
from pathlib import Path


def cargar_entorno():
    env_local = Path(__file__).with_name(".env")
    if env_local.is_file():
        for linea in env_local.read_text(encoding="utf-8-sig").splitlines():
            nombre, separador, valor = linea.partition("=")
            if separador and nombre.strip() in {
                "GEMINI_API_KEY", "GEMINI_MODEL", "PUBLIC_SITE_URL", "WHATSAPP_NUMBER",
                "SUPABASE_URL", "SUPABASE_PUBLISHABLE_KEY", "SUPABASE_SECRET_KEY", "FLASK_SECRET_KEY",
            }:
                os.environ.setdefault(nombre.strip(), valor.strip().strip("\"'"))
