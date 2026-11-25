"""Lectura, filtrado y exportación de las inscripciones del asesor."""
from decimal import Decimal
from io import BytesIO
from unicodedata import normalize, combining

import xlsxwriter

from supabase_api import consultar


def texto_busqueda(valor):
    return "".join(c for c in normalize("NFD", valor.casefold()) if not combining(c))


def inscripciones(token, asesor_id):
    filas = []
    params = {"select": "id,nombre,correo,whatsapp,datos,creado_en,comprobante_tipo",
              "asesor_id": "eq." + asesor_id, "order": "id.asc", "limit": 500}
    while True:
        lote = consultar("/rest/v1/inscripciones", token=token, params=params)
        if not lote:
            break
        filas.extend(lote)
        params["id"] = "gt." + lote[-1]["id"]
    for fila in filas:
        datos = fila["datos"]
        fila["fecha"] = datos.get("Fecha de solicitud de inscripción (Bolivia)", "")
        fila["programa"] = datos.get("Programa", "")
        fila["pagado"] = datos.get("Pago declarado", "").startswith("Realizado")
        fila["monto"] = Decimal(datos.get("Monto declarado (Bs)") or "0")
        fila["ci"] = datos.get("CI del estudiante", "")
    return sorted(filas, key=lambda r: (r["creado_en"], r["id"]), reverse=True)


def filtrar(filas, filtros):
    consulta = texto_busqueda(filtros["q"])
    resultado = []
    for fila in filas:
        if filtros["programa"] and fila["programa"] != filtros["programa"]:
            continue
        if filtros["pago"] and filtros["pago"] != ("declarado" if fila["pagado"] else "pendiente"):
            continue
        if filtros["desde"] and fila["fecha"] < filtros["desde"]:
            continue
        if filtros["hasta"] and fila["fecha"] > filtros["hasta"]:
            continue
        contacto = " ".join(str(fila[k] or "") for k in ("nombre", "correo", "ci", "whatsapp"))
        if not consulta or consulta in texto_busqueda(contacto):
            resultado.append(fila)
    return resultado


def exportar_excel(filas):
    salida = BytesIO()
    opciones = {"in_memory": True, "strings_to_formulas": False, "strings_to_urls": False}
    with xlsxwriter.Workbook(salida, opciones) as libro:
        hoja = libro.add_worksheet("Inscripciones")
        cabecera = libro.add_format({"bold": True, "bg_color": "#134E4A", "font_color": "#FFFFFF"})
        moneda = libro.add_format({"num_format": '#,##0.00'})
        titulos = ["Fecha de inscripción", "Estudiante", "CI", "Correo", "WhatsApp", "Programa",
                   "Estado de pago", "Monto declarado (Bs)", "Fecha de pago", "Certificación", "Sede", "Perfil"]
        hoja.write_row(0, 0, titulos, cabecera)
        for i, fila in enumerate(filas, 1):
            d = fila["datos"]
            hoja.write_row(i, 0, [fila["fecha"], fila["nombre"], fila["ci"], fila["correo"],
                                  fila["whatsapp"], fila["programa"], d.get("Pago declarado")])
            if fila["pagado"]:
                hoja.write_number(i, 7, float(fila["monto"]), moneda)
            hoja.write_row(i, 8, [d.get("Fecha de pago"), d.get("Tipo de certificación"),
                                  d.get("Sede indicada"), d.get("Perfil declarado")])
        for col, ancho in enumerate([21, 30, 18, 36, 20, 64, 48, 24, 18, 30, 25, 22]):
            hoja.set_column(col, col, ancho)
        hoja.set_row(0, 26)
        hoja.freeze_panes(1, 2)
        hoja.autofilter(0, 0, len(filas), len(titulos) - 1)
    return salida.getvalue()
