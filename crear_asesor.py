"""Alta de asesores desde el equipo administrador."""
import re
import tkinter as tk
from tkinter import messagebox, ttk

from configuracion import cargar_entorno
from supabase_api import SupabaseError, configurado, consultar


def crear_asesor(usuario, nombre, correo, whatsapp, clave):
    usuario = usuario.strip().lower()
    nombre = nombre.strip()
    correo = correo.strip()
    whatsapp = re.sub(r"[ +().-]", "", whatsapp.strip())
    if not re.fullmatch(r"[a-z0-9][a-z0-9-]{0,39}", usuario):
        raise ValueError("Usa entre 1 y 40 letras, números o guiones para el usuario. Empieza con una letra o un número.")
    if not 1 <= len(nombre) <= 120 or not nombre.isprintable():
        raise ValueError("Escribe el nombre del asesor (hasta 120 caracteres).")
    if not re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+", correo) or len(correo) > 254:
        raise ValueError("Escribe un correo válido para la cuenta de Supabase.")
    if not re.fullmatch(r"[1-9][0-9]{7,14}", whatsapp):
        raise ValueError("Incluye el código de país en el WhatsApp del asesor.")
    if not clave or len(clave) > 256:
        raise ValueError("Escribe una contraseña de hasta 256 caracteres.")

    existente = consultar("/rest/v1/asesores", servidor=True,
                          params={"select": "id", "codigo": "eq." + usuario, "limit": 1})
    if existente:
        raise ValueError("Ese usuario ya está asignado a un asesor.")
    try:
        cuenta = consultar("/auth/v1/admin/users", servidor=True, datos={
            "email": correo, "password": clave, "email_confirm": True,
        })
    except SupabaseError as error:
        if error.code in ("email_exists", "user_already_exists"):
            # Permite retomar un alta interrumpida o vincular una cuenta existente.
            try:
                acceso = consultar("/auth/v1/token", params={"grant_type": "password"},
                                   datos={"email": correo, "password": clave})
            except SupabaseError as login_error:
                if login_error.status in (400, 401, 403, 422):
                    raise ValueError("Ese correo ya existe. Usa su contraseña actual y verifica que la cuenta esté confirmada.") from None
                raise
            cuenta = acceso["user"]
        elif error.status in (400, 422):
            raise ValueError("Supabase rechazó los datos de la cuenta. Revisa el correo y los requisitos de contraseña del proyecto.") from None
        else:
            raise

    try:
        consultar("/rest/v1/asesores", servidor=True, prefer="return=minimal", datos={
            "id": cuenta["id"], "codigo": usuario, "nombre": nombre, "whatsapp": whatsapp,
        })
    except SupabaseError as error:
        if error.status == 409:
            raise ValueError("El usuario o la cuenta ya tiene un perfil. Revisa la tabla asesores.") from None
        if error.status == 403:
            raise ValueError("La cuenta existe. Aplica la migración 20261125000002_alta_asesores.sql y repite el alta con el mismo correo y contraseña.") from None
        raise ValueError("No se pudo confirmar el perfil. Revisa la conexión y repite el alta con el mismo correo y contraseña.") from None
    return usuario


def main():
    cargar_entorno()
    ventana = tk.Tk()
    ventana.title("UPI Alumni · Crear asesor")
    ventana.resizable(False, False)
    if not configurado():
        messagebox.showerror("Configuración", "Completa los datos de Supabase en .env.", parent=ventana)
        ventana.destroy()
        return
    marco = ttk.Frame(ventana, padding=20)
    marco.grid()
    campos = {}
    for fila, (campo, etiqueta) in enumerate((
        ("usuario", "Usuario de acceso"), ("nombre", "Nombre del asesor"),
        ("correo", "Correo del asesor"), ("whatsapp", "WhatsApp con código de país"),
        ("clave", "Contraseña"), ("confirmar", "Repite la contraseña"),
    )):
        ttk.Label(marco, text=etiqueta).grid(row=fila, column=0, sticky="w", padx=(0, 12), pady=5)
        entrada = ttk.Entry(marco, width=36, show="*" if campo in ("clave", "confirmar") else "")
        entrada.grid(row=fila, column=1, pady=5)
        campos[campo] = entrada

    def guardar():
        datos = {k: entrada.get() for k, entrada in campos.items()}
        if datos.pop("confirmar") != datos["clave"]:
            messagebox.showerror("Crear asesor", "Las dos contraseñas deben coincidir.", parent=ventana)
            return
        boton.state(["disabled"])
        ventana.update_idletasks()
        try:
            usuario = crear_asesor(**datos)
        except ValueError as error:
            messagebox.showerror("Crear asesor", str(error), parent=ventana)
        except SupabaseError as error:
            messagebox.showerror("Crear asesor", f"Supabase no confirmó la operación (HTTP {error.status}). Revisa la conexión y las claves.", parent=ventana)
        else:
            for entrada in campos.values():
                entrada.delete(0, "end")
            messagebox.showinfo("Asesor creado", f"{usuario} ya puede entrar a /asesores con su contraseña.", parent=ventana)
        finally:
            boton.state(["!disabled"])

    boton = ttk.Button(marco, text="Crear asesor", command=guardar)
    boton.grid(row=len(campos), column=1, sticky="e", pady=(12, 0))
    campos["usuario"].focus_set()
    ventana.mainloop()


if __name__ == "__main__":
    main()
