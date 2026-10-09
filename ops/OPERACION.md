# Operación, respaldos e incidentes — HospitalOps

## Preparación operativa previa al contrato

- Contratar PostgreSQL persistente y app HTTPS con dominio del cliente; separar `staging` y `production`.
- Activar notificaciones de errores/caídas y presupuestos o alertas de consumo en Railway.
- En Postgres habilitar backups gestionados del proveedor y conservar una **copia independiente cifrada** de otra región/proveedor con acceso mínimo. Comprobar opciones y retención del plan contratado.
- Establecer recuperación esperada con el cliente (RPO/RTO) y documentar responsables, acceso de emergencia, conservación de datos y contacto de incidentes.
- Configurar la retención de `login_attempts`: por ejemplo limpieza programada de intentos de más de 30 días, previa revisión de requisitos legales y auditoría; estos registros no deben acumularse indefinidamente.

## Respaldo externo con PostgreSQL Client

El script `backup-postgres.sh` requiere `pg_dump`, `DATABASE_URL` y `BACKUP_DIR`. **No** se ejecuta automáticamente por el software. Se recomienda programarlo en una estación operativa privada que pueda conectarse a la BD, con cifrado en tránsito y repositorio externo controlado. No pongas las credenciales en la línea de comandos visible ni las subas a Git.

```bash
export DATABASE_URL='postgresql://usuario:<password>@host:5432/hospitalops'
export BACKUP_DIR='/ruta/segura/backups'
bash ops/backup-postgres.sh
```

Después cifra el archivo y súbelo a almacenamiento externo. Debes implementar y probar **rotación** de copias según contrato. El mero resultado exitoso de `pg_dump` no demuestra restaurabilidad.

## Ensayo de restauración

Usar una **base temporal vacía de staging**, nunca producción sin autorización y snapshot previo:

```bash
export DATABASE_URL='postgresql://staging_user:<password>@staging-host:5432/hospitalops_restore'
export RESTORE_FILE='/ruta/segura/backups/hospitalops-YYYYMMDDTHHMMSSZ.dump'
export CONFIRM_RESTORE='RESTORE_TO_STAGING'
bash ops/restore-postgres.sh
```

Verificar usuario, hospitales, recuento de tickets y Kardex; documentar fecha, tiempo de restauración y evidencia. `pg_restore` requiere base destino existente y permisos adecuados.

## Actualizaciones

1. Descargar backup antes de modificar base de datos.
2. Crear rama de feature en GitHub y ejecutar CI.
3. Actualizar staging y probar datos existentes, sesiones, tickets de dos hospitales y movimientos de stock.
4. Para cambios de estructura posteriores al esquema inicial, preparar migración SQL versionada, revisada y probada, antes de desplegar código. `create_all` no migra tablas.
5. Publicar a producción, vigilar `/ready` y los logs, y tener un procedimiento de reversión que sea compatible con la base de datos.

## Incidentes frecuentes

- `503 /ready`: PostgreSQL indisponible, URL de conexión incorrecta, red bloqueada o tablas fallidas.
- `403`: acceso denegado por rol, hospital desactivado o ticket no asignado.
- `429` en login: intentos erróneos en 15 minutos; verificar origen y no desactivar los límites sin evaluar el riesgo.
- Fallas de inventario: revisar los movimientos de proveedor (`provider_movements`) o hospital (`inventory_movements`); no editar directamente tablas sin registro de ajuste.
- Errores tras despliegue: consultar logs, cambios de variables, estado de Postgres y versión instalada.

## Datos personales

No registrar nombres de pacientes, RUT, tratamientos, diagnósticos ni información clínica. Evitar subir respaldos a canales informales. Preparar políticas de privacidad, roles de tratamiento y eliminación/retención antes de operar con instituciones reales.
