# HospitalOps — Gestión hospitalaria multi-cliente

Aplicación web **runnable**, en español, con clientes (hospitales) aislados, tickets sujetos a confirmación administrativa, solicitantes aprobados por admins, inventario/Kardex, conteo físico, equipos, CRM tipo Kanban, personalización por hospital y skeletons durante la carga.

**Stack:** FastAPI + Python 3.11+, SQLAlchemy 2, Jinja2, JavaScript vanilla, CSS responsive y SQLite (desarrollo). PostgreSQL y Docker Compose disponibles para despliegue. Sin dependencias JS ni CDN. Interfaz server-rendered con widgets de carga asíncrona.

## Inicio rápido: Windows PowerShell

```powershell
cd hospitalops
py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
Copy-Item .env.example .env
# Abrir .env y reemplazar SESSION_SECRET por una cadena aleatoria larga
python seed.py
python -m uvicorn app.main:app --reload --port 8000
```

Si PowerShell bloquea la activación, ejecuta `Set-ExecutionPolicy -Scope Process Bypass` en esa terminal o usa `.venv\Scripts\python.exe` explícitamente.

## Inicio rápido: macOS / Linux

```bash
cd hospitalops
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
cp .env.example .env
# Cambia SESSION_SECRET antes de publicar la aplicación
python seed.py
python -m uvicorn app.main:app --reload --port 8000
```

Abre **http://127.0.0.1:8000**. La base `hospitalops.db` se crea automáticamente durante el arranque o al ejecutar el seed. El seed se ejecuta **solo si no existen usuarios** y jamás reemplaza datos existentes.

### Usuarios de demostración

Todos usan contraseña temporal **`DemoSeguro2026!`**. Cuentas simuladas; no usar públicamente ni en producción.

| Rol | Correo | Hospital |
|---|---|---|
| Superadministrador | `root@hospitalops.example` | Todos |
| Administrador cliente | `admin@norte.example` | Hospital Demo Norte |
| Coordinador | `coordinador@norte.example` | Hospital Demo Norte |
| Técnico | `tecnico@norte.example` | Hospital Demo Norte |
| Solicitante | `solicitante@norte.example` | Hospital Demo Norte |
| Cuenta pendiente | `pendiente@norte.example` | Hospital Demo Norte |
| Admin segundo hospital | `admin@sur.example` | Hospital Demo Sur |
| Solicitante segundo hospital | `solicitante@sur.example` | Hospital Demo Sur |

**Flujo sugerido:** entra con superadmin para ver los dos hospitales. Ingresa luego con `admin@norte.example`, ve **Aprobaciones** y valida a `pendiente@norte.example`. Con `solicitante@norte.example` crea un ticket; vuelve a entrar como administrador para confirmarlo, asígnalo a un técnico y haz seguimiento.

## Vistas incluidas

| Vista | Ruta | Acceso |
|---|---|---|
| Login | `/login` | Público |
| Registro (solicitud de aprobación) | `/register` | Público |
| Estado pendiente / rechazado | `/pending` | Solicitante en revisión |
| Dashboard con métricas asíncronas | `/dashboard` | Todos los aprobados |
| Clientes / hospitales | `/hospitals` | Superadmin |
| Crear / editar / activar / desactivar hospital | `/hospitals/new`, `/hospitals/{id}/edit` | Superadmin |
| Usuarios y privilegios | `/users`, `/users/new`, `/users/{id}/edit` | Administrador |
| Aprobar / rechazar cuentas | `/approvals` | Administrador |
| Áreas / servicios | `/departments` | Administrador |
| Tickets (listar y filtrar) | `/tickets` | Todos; alcance por rol |
| Crear ticket | `/tickets/new` | Aprobados |
| Detalle, conversación y ciclo de vida | `/tickets/{id}` | Autorizados |
| Inventario de consumibles | `/inventory` | Personal autorizado |
| Nueva / edición ficha de producto | `/inventory/new`, `/inventory/{id}/edit` | Gestores |
| Kardex: entrada / salida / ajuste | `/inventory/{id}` | Lectura personal, escritura gestores |
| Exportar inventario CSV | `/inventory/export/csv` | Gestores |
| Conteos físicos / conciliaciones | `/counts`, `/counts/{id}` | Personal autorizado |
| Equipos / activos | `/assets`, `/assets/new`, `/assets/{id}/edit` | Personal autorizado |
| CRM con oportunidades por etapa | `/crm` | Gestores |
| Contactos CRM | `/crm/contacts`, `/crm/contacts/new`, `/crm/contacts/{id}/edit` | Gestores |
| Crear / editar oportunidad | `/crm/opportunities/new`, `/crm/opportunities/{id}/edit` | Gestores |
| Personalización de portal / módulos | `/settings` | Administrador |
| Bitácora / auditoría | `/audit` | Administrador |
| Salud del servicio | `/health` | Público |

## Roles y permisos

- **Superadministrador:** crea, edita y desactiva hospitales; selecciona hospital activo en la barra superior; configura, consulta y administra sus módulos. No se crean más superadministradores desde la interfaz.
- **Administrador hospital:** administra usuarios de su hospital, aprueba altas y confirma o rechaza tickets; asigna técnicos, opera inventario y CRM y personaliza branding y módulos.
- **Coordinador:** consulta tickets y coordina asignaciones / estados **tras** confirmación administrativa; administra productos, Kardex, activos, conteos y CRM; no valida solicitudes ni cuentas.
- **Técnico:** consulta equipos/productos y su stock (no costos ni precios); trabaja únicamente en tickets que le hayan asignado (o que haya solicitado personalmente), comenta y actualiza el estado; no asigna técnicos ni modifica el inventario.
- **Solicitante:** se registra eligiendo un hospital y un cargo; queda **pendiente** hasta que lo apruebe un admin; crea tickets que deben confirmarse, consulta solo los suyos, comenta y acepta el cierre de los resueltos.

**Aislamiento de datos:** el hospital del usuario procede de la sesión y de la BBDD; no de un campo editable del formulario. Las consultas de los módulos y la validación de referencias (usuarios, activos, productos, oportunidades) incluyen `hospital_id`. Un superadmin puede cambiar el hospital activo, sin mezcla de datos entre sesiones de clientes normales.

## Flujos funcionales

### Solicitudes y mesa de ayuda

1. Solicitante se registra: estado `pending`.
2. Admin autoriza en `/approvals` → `approved`.
3. Solicitante crea ticket: estado `pendiente`.
4. Admin pulsa **Confirmar ticket**: estado `abierto`, guarda `confirmed_by_id` y fecha.
5. Coordinador asigna técnico; técnico actualiza `en_proceso` → `resuelto`.
6. Solicitante **acepta solución** → `cerrado`; administración también puede cerrar o reabrir.
7. Comentarios externos visibles en ticket; **notas internas** solo para personal técnico y administrativo.

### Inventario y equipos

- Los artículos tienen **SKU por hospital, código de barras, nombre, categoría, ubicación, costo bruto, precio de venta, stock, stock mínimo y activo/inactivo**.
- Precio bruto = **costo bruto de adquisición**, en CLP. El sistema **no calcula IVA**, impuesto de venta, margen ni emisión de facturas; puedes adaptar estas reglas más adelante.
- Creación: stock inicial registrado como movimiento `inicial`.
- Edición: la ficha **no** permite modificar stock sin historial.
- Kardex: entradas, salidas, ajuste de saldo, usuario, fecha, razón y stock final. No permite saldos negativos.
- Conteos: captura snapshot del stock, entrada de cantidad física por artículo y conciliación con movimientos `conteo`. Si otro movimiento modificó existencias durante el conteo, se bloquea el cierre y debe generarse un conteo nuevo.
- Equipos/activos registran identificación, serie, localización y categoría y pueden asociarse a tickets.
- CSV exportable con prevención básica de fórmulas maliciosas.

### CRM y personalización

- CRM: contactos con cargo, área, teléfono y email, oportunidades con responsable, monto, fecha prevista y etapas **Nuevo → Contactado → Propuesta → Negociación → Ganado / Perdido**.
- Cada hospital define **nombre del portal, color corporativo y activación de tickets, inventario y CRM**. Los módulos se controlan también en el backend: ocultar un enlace no sustituye validar autorización.
- Skeletons: tarjetas de métricas usan placeholders animados hasta que responde `/api/dashboard`; la navegación de páginas muestra un skeleton mientras se carga el siguiente contenido. La interfaz tiene diseño responsive.

## Estructura del código

```text
hospitalops/
├── app/
│   ├── __init__.py
│   ├── main.py               # Rutas web, reglas de negocio, permisos, API dashboard
│   ├── models.py             # Modelos SQLAlchemy
│   ├── database.py           # Configuración SQLite / PostgreSQL
│   ├── security.py           # Password hashing PBKDF2
│   ├── static/
│   │   ├── styles.css
│   │   └── app.js
│   └── templates/            # Vistas Jinja2 HTML server-side
├── tests/
│   └── test_app.py
├── seed.py                   # Datos ficticios para pruebas
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
├── .env.example
└── README.md
```

## Tests

```bash
pip install -r requirements-dev.txt
pytest -q
```

Los tests cubren CSRF, registro/aprobación, ciclo de tickets, privacidad entre hospitales, inventario y conteo, roles y personalización.

## PostgreSQL (sin Docker)

En `.env` configura una instancia propia:

```ini
DATABASE_URL=postgresql+psycopg://usuario:clave@localhost:5432/hospitalops
SESSION_SECRET=una-clave-larga-aleatoria-unica
SESSION_HTTPS_ONLY=true
```

Para generar una clave segura (PowerShell o terminal):

```bash
python -c "import secrets; print(secrets.token_urlsafe(48))"
```

Crea previamente la base de datos y ejecuta `python -m uvicorn app.main:app --host 0.0.0.0 --port 8000`. **El `create_all()` inicial es apropiado para prototipos**, pero para evolución real de esquemas se recomienda agregar **Alembic** antes de usar datos de producción.

## Docker Compose

En un archivo `.env` en la raíz, define **por lo menos** `POSTGRES_PASSWORD` y `SESSION_SECRET` (además de las demás variables deseadas). Luego:

```bash
docker compose up --build -d
# Solo para pruebas, primera ejecución opcional:
docker compose exec web python seed.py
```

La aplicación estará en `http://localhost:8000`. Para salir: `docker compose down`. Para detener y **eliminar los datos** de PostgreSQL: `docker compose down -v` (destructivo).

## Seguridad y estado del producto

Esta entrega es una **base funcional/MVP**, no un software clínico certificado. No almacena fichas médicas ni resultados de pacientes y no se debe utilizar como historia clínica. Las validaciones incluyen: contraseñas con PBKDF2 salted, cookies de sesión firmadas/HttpOnly, formularios CSRF, autorización por rol, aislamiento por hospital, estado de cuentas, validación de relaciones, bitácora de operaciones y ORM contra SQL injection.

Antes de instalar en hospitales reales: **HTTPS + proxy inverso, rate limiting y bloqueo de intentos de login, 2FA/SSO institucional, política de contraseñas, correos de invitación y restablecimiento, respaldos probados, recuperación, logs externos, monitoreo, permisos por departamento, auditoría de cambios más exhaustiva, paginación de tablas, pruebas E2E y de penetración, migraciones con Alembic y evaluación de requisitos legales aplicables (incluida la normativa chilena de protección de datos).** La configuración demo y su contraseña deben eliminarse antes de producción.

El módulo de inventario no integra lector físico dedicado, compras ERP ni facturación; un escáner USB que escriba el código como teclado puede usarse con el campo de código de barras. El sistema no envía email ni notificaciones externas por defecto.

## Solución de problemas

- **`No module named fastapi`**: activa el entorno virtual y ejecuta `pip install -r requirements.txt`.
- **Puerto ocupado**: usa `--port 8001`.
- **Base SQLite reiniciada**: verifica que ejecutas desde la raíz del proyecto; `DATABASE_URL=sqlite:///./hospitalops.db` es relativo al directorio actual.
- **Sesión/cookie inválida**: borra la cookie local después de cambiar `SESSION_SECRET`.
- **CSRF inválido**: recarga la página y vuelve a enviar el formulario.
- **No aparece CRM/inventario**: revisa el rol del usuario y las opciones de `/settings`.
- **No existe hospital**: crea el primer hospital con un superadministrador. El seed demo inicial es lo más sencillo para la primera puesta en marcha.

## Puesta en marcha sin datos ficticios

Si no deseas cargar el seed de prueba, no ejecutes `python seed.py`. En una base vacía ejecuta:

```bash
python create_admin.py
python -m uvicorn app.main:app --reload
```

El asistente `create_admin.py` pide nombre, correo y contraseña segura para el superadministrador. Inicia sesión con esa cuenta, crea el primer hospital en **Clientes**, selecciona ese hospital e incorpora usuarios desde el panel.

Consulta [ERD.md](ERD.md) y [schema.sql](schema.sql) para explorar el modelo de datos. La pantalla Inventario permite capturar códigos de barras con el navegador cuando la API `BarcodeDetector` y los permisos HTTPS/cámara están disponibles; si no lo están, admite entrada manual o lector USB tipo teclado.

## Capturas de la interfaz

El directorio `previews/` incluye capturas de referencia (login, dashboard, tickets, inventario, CRM y adaptación móvil). Son vistas generadas desde los templates reales con datos ficticios, para inspeccionar el diseño antes de instalar.
