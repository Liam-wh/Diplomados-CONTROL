# UPI Alumni · ONCE

## De GitHub a Vercel

1. Extrae el ZIP. Sube el contenido de la carpeta a un repositorio de GitHub, incluidos .gitignore y vercel.json. app.py debe quedar en la raíz del repositorio.
2. En Vercel selecciona Add New → Project e importa ese repositorio. Usa la raíz del repositorio como Root Directory. Vercel detecta Flask.
3. Antes de desplegar, agrega GEMINI_API_KEY en Environment Variables. Pega la clave como valor y selecciona Production. Si también pruebas despliegues de Preview, configúrala en ese entorno. Obtén tu clave en [Google AI Studio](https://aistudio.google.com/apikey).
4. Pulsa Deploy. Si agregaste la variable después, abre Deployments y selecciona Redeploy. Para tu dominio, usa Settings → Domains y sigue los registros DNS indicados.
5. Abre la URL publicada, pulsa ONCE y envía una pregunta. La etiqueta «Con Gemini» después de la respuesta confirma una consulta real. Ante un fallo, la guía local sigue disponible y el pie del chat indica el motivo disponible. El modelo predeterminado es gemini-3.5-flash-lite. Ante saturación o tiempo de espera agotado, ONCE intenta con Gemini 3.5 Flash como respaldo de Flash-Lite dentro del tiempo disponible. Puedes elegir otro modelo compatible con salida JSON estructurada mediante GEMINI_MODEL en Vercel.

## Probar en Windows y VS Code

Con Python 3.12 instalado, abre esta carpeta en VS Code. Copia .env.example como .env y completa GEMINI_API_KEY solo en tu equipo. Desde la terminal ejecuta `.\Abrir-Alumni.cmd`. La clave se carga en Flask. El navegador se comunica con /api/once y el servidor consulta a Google por HTTPS.

## Admisiones

El formulario registra las solicitudes en Supabase. El panel «QR de pago» conserva la imagen original de titulaciones y ofrece su descarga. El botón de WhatsApp abre la conversación con +591 63257678 para que el participante adjunte el comprobante.


## Supabase y asesores

1. Aplica las migraciones de `supabase/migrations/` en orden de nombre con Supabase CLI o SQL Editor. Si ya instalaste el proyecto, aplica solo las migraciones pendientes.
2. Habilita correo y contraseña en Supabase Auth. Para dar de alta un asesor desde Windows, abre `Crear-asesor.cmd` en el equipo que tiene el archivo `.env`. Introduce el usuario, el nombre del asesor, su correo, su WhatsApp internacional y la contraseña elegida. La herramienta vincula la cuenta de Supabase Auth con el perfil. Si ya creaste la cuenta en Auth, usa su correo confirmado y su contraseña actual.
3. En Vercel configura `SUPABASE_URL`, `SUPABASE_PUBLISHABLE_KEY`, `SUPABASE_SECRET_KEY`, `FLASK_SECRET_KEY` y `PUBLIC_SITE_URL` para el entorno que vayas a desplegar. Usa una clave aleatoria de Flask, por ejemplo la salida de `python -c "import secrets; print(secrets.token_hex(32))"`. Guarda las claves secretas en el entorno del servidor. En local puedes completar `.env` a partir de `.env.example`. `WHATSAPP_NUMBER` define el teléfono general.
4. Pulsa **Asesores** en el catálogo o abre `/asesores`. El icono del ojo permite ver la contraseña. Marca **Mantener mi sesión durante 7 días** para recuperar el acceso al abrir el mismo navegador. **Cerrar sesión** elimina ese acceso. Desde `/dashboard` puedes compartir tu catálogo. El catálogo compartido usa el WhatsApp del asesor. Las solicitudes enviadas desde ese enlace aparecen en su panel. El enlace de WhatsApp de cada inscripción requiere que el participante haya indicado su número.

Las solicitudes del catálogo general quedan sin asesor asignado. En Supabase, la tabla `public.inscripciones` guarda los datos y la imagen opcional del comprobante en la misma fila. El asesor puede descargarla desde su panel. El formulario confirma la inscripción cuando Supabase acepta el registro. Si falla, conserva el borrador para reintentar.


En el panel, los indicadores y el Excel corresponden a todos los resultados de los filtros activos. El monto suma los pagos declarados por los participantes y queda sujeto a verificación. Desde **Mi cuenta**, el asesor puede editar su nombre, usuario y WhatsApp del catálogo, y guardar su sede y cargo. Cambiar el usuario cambia el enlace del catálogo. Cambiar solo el WhatsApp actualiza el destino de los botones en el mismo enlace. Para cambiar el correo de acceso o la contraseña, el asesor debe introducir su contraseña actual. Si Supabase pide confirmar el correo, el panel muestra la dirección pendiente.
