# HospitalOps Comercial 1.1 — Resumen de entrega

**Destino:** empresa de soporte técnico con más de 20 hospitales y ~30 técnicos.

## Incluido

- Plataforma web con administración de hospitales, clientes y usuarios por rol.
- Mesa de ayuda con aprobación de ticket, asignación, seguimiento, comentarios y cierre validado.
- Pantalla central para coordinadores de la empresa con tickets de varios hospitales.
- Técnicos globales que trabajan para varios hospitales sin poder consultar tickets ajenos.
- Bodega central del prestador con costo bruto, precio venta, SKU, stock y mínimo, ajustes y registros Kardex.
- Entrega de repuestos a técnicos, control por profesional, consumo contra ticket propio y devoluciones.
- Inventario por hospital, activos, conteos físicos, exportación y CRM.
- Cambio/restablecimiento de contraseñas y revocación de sesiones; roles de empresa inasignables a usuarios hospitalarios.
- CSRF, cabeceras seguras, limitación de intentos de autenticación persistida en BD, cookies seguras exigidas en producción y control de tenants.
- Docker, PostgreSQL, integración de despliegue Railway, 18 tablas SQL, 34 vistas HTML y documentación de operación.
- 24 pruebas automatizadas que cubren autorización, operaciones y flujos críticos.

## No incluido / condicionado

- No incorpora MFA/SSO ni pruebas de penetración de terceros.
- No integra notificaciones por correo, SLA contractual automático ni ERP de clientes.
- No se probó esta versión contra PostgreSQL gestionado en un entorno cloud, ni con concurrencia real de 30 técnicos; las pruebas ejecutadas son locales sobre SQLite.
- No se desplegó en Railway ni se activaron backups o monitoreo de cuenta externa.
- No posee migraciones versionadas para cambios futuros: iniciar una BD nueva o preparar migración supervisada de una previa.
- Las capturas de `previews/` corresponden a la interfaz base y no incluyen todas las vistas agregadas.
- No es un sistema clínico ni un repositorio apto para datos sensibles de pacientes.

## Recomendación de venta

Producto funcional para **demostración, propuesta comercial y piloto controlado con datos ficticios**. La puesta en marcha productiva requiere terminar y documentar las verificaciones de `ENTREGA_Y_ACEPTACION.md` en un entorno de staging con el cliente. No se declara cumplimiento normativo ni alta disponibilidad sin validación externa.
