# HospitalOps Comercial 1.1 — Empresa de soporte multihospital

Aplicación web en español para **una empresa prestadora de servicios técnicos** que administra más de 20 clientes hospitalarios y alrededor de 30 técnicos, con una sola plataforma y separación por institución.

> **Estado de entrega:** código fuente, vistas, pruebas automatizadas, contenedorización y manuales disponibles. **No se declara producción certificada**: es obligatorio completar un piloto en infraestructura real, respaldo/restauración verificados, revisión de seguridad independiente y aceptación del cliente. No incluye servicio de hosting ni cuentas externas ya contratadas.

## Instalación en Windows / VS Code (sin datos de demo)

Abre la carpeta `hospitalops` del ZIP (contiene `requirements.txt` y `app/`):

```powershell
py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
Copy-Item .env.example .env
python -c "import secrets; print(secrets.token_urlsafe(48))"
# Pega el valor en SESSION_SECRET del archivo .env
python create_admin.py
python -m uvicorn app.main:app --reload --port 8000
```

Visita http://127.0.0.1:8000. Si el asistente de creación de administrador no encuentra tablas, el comando `create_admin.py` invoca `init_db()` automáticamente. `seed.py` es exclusivamente para demostración en **una BD vacía de pruebas** (genera cuentas con contraseña conocida); no usarlo para ningún entorno del cliente.

## Instalación local Docker + PostgreSQL

Crear `.env` con `POSTGRES_PASSWORD` largo, `SESSION_SECRET` aleatorio y `SESSION_HTTPS_ONLY=false` para HTTP local (no usar esos valores en servidor público). Después:

```bash
docker compose up --build -d
docker compose exec web python create_admin.py
```

Accede a http://127.0.0.1:8000. PostgreSQL conserva datos en el volumen `postgres_data`. No es un sustituto de un respaldo externo. Para el entorno público se recomienda Railway + PostgreSQL con HTTPS, no publicar Docker Compose directo a internet.

## Funcionalidad por perfil

| Perfil | Alcance |
|---|---|
| Superadministrador (`superadmin`) | Todos los hospitales, equipo global, bodega empresa, configuración y auditoría |
| Coordinador empresa (`coordinador_global`) | Tickets de todos los hospitales, asignaciones y bodega empresa, sin creación de superadmins |
| Técnico empresa (`tecnico_global`) | Tickets que tiene asignados en **cualquier hospital** y su propia dotación de repuestos |
| Administrador hospital (`admin_cliente`) | Usuarios, aprobaciones, tickets, inventario y módulos de **su hospital** |
| Coordinador hospital (`coordinador`) | Operaciones y asignaciones de su hospital |
| Técnico hospital (`tecnico`) | Tickets asignados dentro de su hospital, accesos de inventario limitados |
| Solicitante (`solicitante`) | Crea tickets, revisa **solo los suyos**, comenta y acepta resolución |

Las cuentas globales se crean únicamente desde `/equipo` por el superadministrador y no tienen `hospital_id` asociado. Los administradores hospitalarios no pueden asignar roles globales.

## Vistas principales

| Ruta | Función |
|---|---|
| `/login`, `/perfil` | Acceso y cambio de contraseña |
| `/hospitals` | Altas/bajas/edición de clientes |
| `/operaciones/tickets` | Centro multihospital con filtros y paginación de 50 tickets |
| `/equipo` | Alta/desactivación del personal de la empresa |
| `/mis-tickets` | Tickets multihospital asignados a cada técnico global |
| `/bodega` | Bodega central, costos, precios, stock y movimientos |
| `/bodega/export/csv` | Descarga del stock de empresa |
| `/mis-repuestos` | Consumo de repuestos asociado a ticket por técnico |
| `/dashboard` | Resumen de hospital activo y métricas diferidas |
| `/tickets`, `/tickets/new`, `/tickets/{id}` | Solicitudes, aprobación administrativa, asignación, seguimiento, cierre |
| `/users`, `/approvals`, `/departments` | Cuentas, aprobaciones, áreas y cargos |
| `/inventory`, `/counts`, `/assets` | Inventario por hospital, Kardex, conteos físicos, equipos |
| `/crm`, `/crm/contacts`, `/crm/opportunities/new` | Pipeline, contactos y oportunidades |
| `/settings`, `/audit` | Personalización y registro de actividad |
| `/health`, `/ready` | Estado de proceso y disponibilidad real de BD |

Hay más vistas y formularios específicos en `app/templates/`.

## Flujos comerciales

1. Crear hospitales desde `/hospitals`; configurar su marca en `/settings` desde la cuenta que corresponda.
2. Crear administradores de cada hospital desde `/users`, con el hospital seleccionado.
3. Crear coordinadores y técnicos **de la empresa** desde `/equipo` (rol global).
4. El solicitante crea un ticket; el administrador hospitalario lo confirma; el coordinador de empresa lo asigna desde la bandeja de operaciones; el técnico lo gestiona en `/mis-tickets`; el solicitante valida la solución.
5. Registrar repuestos propios de la empresa en `/bodega`, entregarlos a técnicos, registrar consumo desde `/mis-repuestos` indicando ticket y recuperar repuestos con devoluciones.
6. Para inventario **del hospital**, usar `/inventory` y `/counts`: es diferente de la bodega de la empresa.

## Seguridad implementada

- Contraseñas PBKDF2-HMAC-SHA256 con salt único; sesión HTTP-only firmada con secreto; modo `Secure` obligatorio en producción.
- Tokens CSRF para formularios; encabezados CSP, anti-iframe, nosniff y HSTS en producción.
- Limitación de intentos fallidos persistida en BD (8 por cuenta/15 minutos, más umbral global de IP); el proveedor cloud debe añadir WAF/rate limiting de borde según carga.
- Revocación de sesiones cuando se cambia o restablece una contraseña; bloqueo inmediato al desactivar usuarios u hospitales.
- Acceso del técnico global **solo por asignación**, usuarios hospitalarios con aislamiento por `hospital_id`, y inventario de empresa solo visible para personal proveedor autorizado.
- Registro público deshabilitado por defecto en producción. Los usuarios se dan de alta desde el panel.
- No se guarda información clínica, diagnóstico ni historia médica en el sistema por diseño. La empresa debe instruir a solicitantes a no ingresar datos sensibles en campos libres.
- No se ejecuta `seed.py` en producción; nunca publicar contraseñas demo.

**Controles pendientes de validación externa**: MFA/SSO, pruebas de penetración, pruebas de carga real, backup y restauración, plan de incidentes, alta disponibilidad, monitoreo 24/7 y evaluación legal del tratamiento de datos en Chile. Se exige como condición contractual si el cliente lo necesita.

## Producción en Railway (orden exacto)

1. Crear un repositorio **privado** GitHub con todos los archivos de `hospitalops` en la raíz y enviar a `main`. No subir `.env`, archivos `.db` o respaldos.
2. Crear proyecto en Railway. Añadir base `Postgres` desde `+ New`.
3. Añadir servicio `GitHub Repo` conectado al repositorio. Railway detecta `Dockerfile` y `railway.json`. `railway.json` usa `/ready` como healthcheck.
4. En `web → Variables`, registrar:

```text
APP_ENV=production
DATABASE_URL=${{Postgres.DATABASE_URL}}
SESSION_SECRET=<salida de python -c "import secrets; print(secrets.token_urlsafe(48))">
SESSION_HTTPS_ONLY=true
ALLOW_SELF_REGISTRATION=false
ALLOWED_HOSTS=<dominio.up.railway.app de tu servicio>
```

Si aún no se puede obtener el nombre del dominio al configurar variables, crear primero un dominio Railway en `Networking`; o usar **temporalmente** `ALLOWED_HOSTS=*.up.railway.app`, cambiándolo luego por el dominio exacto. Si el servicio PostgreSQL tiene otro nombre, cambiar `Postgres` en la referencia por el nombre real. No copiar secretos en GitHub ni capturas.
5. Crear/validar el dominio Railway, HTTPS y logs. El entorno se niega a iniciar si falta secreto, PostgreSQL, HTTPS seguro o `ALLOWED_HOSTS`.
6. En consola del servicio web (`railway ssh -s NOMBRE_SERVICIO` tras instalar y vincular CLI), ejecutar `python create_admin.py` **una sola vez**.
7. Comprobar `/ready`, acceder por HTTPS, crear un hospital y ejecutar el recorrido de aceptación en `ENTREGA_Y_ACEPTACION.md`.
8. Contratar/habilitar respaldos nativos **y una copia externa independiente**. Probar restauración trimestral; añadir monitoreo externo de uptime, alertas y límites de gasto.
9. Activar dominio propio del cliente y cambiar `ALLOWED_HOSTS` para incluirlo, quitar patrones temporales.

Railway es un servicio externo. El equipo que opere el sistema debe confirmar el precio y la configuración actual del proveedor. `Dockerfile` utiliza usuario sin privilegios y escucha el puerto `$PORT` asignado.

## Pruebas

```bash
pip install -r requirements-dev.txt
python -m pytest -q
```

Las pruebas cubren aislamiento entre instituciones, aprobación de usuarios y tickets, movimientos de stock, gestión CRM, equipo global, inventario central, permisos del personal multihospital, contraseñas y bloqueos de login.

### Base de datos y evolución

`app/database.py` configura SQLite en desarrollo y PostgreSQL en producción. `Base.metadata.create_all` solo crea tablas faltantes; **no modifica columnas existentes ni reemplaza una estrategia de migraciones versionadas**. Para una instalación nueva sobre PostgreSQL limpio es suficiente para el esquema incluido. Para evolucionar una BD existente: sacar backup, comparar esquema, preparar y revisar una migración SQL/Alembic en staging antes del despliegue. `schema.sql` es una referencia del esquema inicial y no un mecanismo de actualización automática.

### Consideraciones contractuales

La entrega del ZIP por sí sola no transfiere propiedad intelectual, dominio, credenciales de Railway ni derechos exclusivos: deben definirse por contrato. El cliente debe aceptar el alcance de módulos, procedimiento de respaldo, SLA y roles de responsabilidad. Ver `ENTREGA_Y_ACEPTACION.md`.
