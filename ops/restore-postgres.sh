#!/usr/bin/env bash
# Restauración DESTRUCTIVA: solo staging salvo cambio aprobado.
set -euo pipefail
: "${DATABASE_URL:?Debes indicar base destino explícita}"
: "${RESTORE_FILE:?Indicar archivo .dump a restaurar}"
: "${CONFIRM_RESTORE:?Exige CONFIRM_RESTORE=RESTORE_TO_STAGING para evitar accidentes}"
if [ "$CONFIRM_RESTORE" != 'RESTORE_TO_STAGING' ]; then
  echo 'Confirma explícitamente una restauración en staging. Abortado.' >&2
  exit 2
fi
if [ ! -f "$RESTORE_FILE" ]; then echo 'Archivo inexistente' >&2; exit 1; fi
CONN="${DATABASE_URL/postgresql+psycopg:\/\//postgresql:\/\/}"
pg_restore --clean --if-exists --no-owner --no-acl --dbname="$CONN" "$RESTORE_FILE"
echo 'Restauración completada. Ejecutar pruebas en staging.'
