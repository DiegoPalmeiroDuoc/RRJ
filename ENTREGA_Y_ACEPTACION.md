# HospitalOps — Acta de entrega y criterios de aceptación

**Versión:** comercial 1.1 · **Fecha:** octubre de 2026 · **Cliente:** __________________ · **Proveedor:** __________________

## Paquete entregado

- Código fuente web FastAPI y plantillas Jinja2, CSS/JS sin dependencias frontend comerciales.
- Base de datos modelada con SQLAlchemy y referencia `schema.sql` PostgreSQL.
- Dockerfile, Docker Compose, `railway.json`, ejemplos de variables de entorno.
- Pruebas automatizadas y datos de demostración **solo para ambiente de desarrollo**.
- README de instalación y manual de operación por perfil, más la política de respaldos.

## Validación conjunta del cliente en staging (marcar conforme)

- [ ] El superadministrador crea, modifica y desactiva 2 hospitales de prueba.
- [ ] Cada hospital ve sus usuarios, tickets, inventario, equipos y CRM sin acceso cruzado.
- [ ] Una cuenta solicitante crea ticket; el administrador hospital confirma o rechaza; se asigna al técnico.
- [ ] Un técnico global recibe 2 tickets de 2 hospitales diferentes y solo ve esos tickets.
- [ ] Un coordinador de empresa visualiza tickets multihospital y asigna técnicos; no puede crear superadministradores.
- [ ] La empresa registra repuesto central con costo bruto, precio venta, SKU, stock y mínimo.
- [ ] Se entrega stock de bodega a un técnico; el técnico descuenta unidades en un ticket asignado; se procesa devolución.
- [ ] El Kardex almacena autor, cantidad, tipo, ticket y hospital cuando aplica.
- [ ] El inventario de hospital acepta entradas/salidas, conteos físicos y exportación a Excel.
- [ ] Los estados deshabilitados impiden acceso; la contraseña cambiada revoca sesiones previas.
- [ ] Se comprueba HTTPS con cookies seguras y protección CSRF, sin claves demo.
- [ ] Se prueba **restauración real** de PostgreSQL sobre staging con copia externa.
- [ ] Se ejecutan pruebas de carga para el tráfico y concurrentes pactados.
- [ ] Se acuerda proceso de actualizaciones, parches, ventanas de mantenimiento y contacto técnico.
- [ ] Se valida cumplimiento de protección de datos aplicable, minimización de PII y que no se incluyan datos de pacientes.

## Limitaciones explícitas del alcance recibido

- No se ha desplegado ni auditado esta copia en la infraestructura final del cliente.
- Sin MFA/SSO corporativo, integraciones ERP, firma electrónica, correo transaccional automatizado, app móvil nativa ni SLA de disponibilidad garantizado.
- Los módulos son una base operativa funcional, **no** un sistema clínico ni de historia médica.
- No incluye alta disponibilidad ni una copia de seguridad remota configurada; son servicios de infraestructura a contratar y verificar.
- Cambios estructurales posteriores requieren migraciones versionadas.

## Firmas

**Cliente:** _____________________ Fecha: ____________

**Proveedor:** ___________________ Fecha: ____________
