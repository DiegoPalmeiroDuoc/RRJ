#!/usr/bin/env bash
# Ejecución desde estación segura con cliente PostgreSQL y DATABASE_URL privada.
set -euo pipefail
: "${DATABASE_URL:?Debes exportar DATABASE_URL de PostgreSQL}"
: "${BACKUP_DIR:?Debes indicar una carpeta externa con control de acceso}"
mkdir -p "$BACKUP_DIR"
chmod 700 "$BACKUP_DIR"
STAMP=$(date -u +%Y%m%dT%H%M%SZ)
OUT="$BACKUP_DIR/hospitalops-$STAMP.dump"
CONN="${DATABASE_URL/postgresql+psycopg:\/\//postgresql:\/\/}"
pg_dump --format=custom --no-owner --no-acl --file="$OUT" "$CONN"
chmod 600 "$OUT"
echo "Respaldo creado: $OUT"
echo 'Importante: cifrar, transferir a otro proveedor y probar restauración; una carpeta local NO es respaldo externo.'
