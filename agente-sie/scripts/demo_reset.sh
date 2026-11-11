#!/usr/bin/env sh
# Reinicia la base de la compuerta y vuelve a sembrar Odoo (vigencias = hoy). Ejecutar antes de exponer.
set -eu
cd "$(dirname "$0")/.."
docker compose exec -T compuerta python /seed/seed_odoo.py --reiniciar
# Vacía el buzón local del dueño (Mailpit); si no está levantado, no pasa nada.
curl -s -X DELETE "http://localhost:${MAILPIT_PORT:-8025}/api/v1/messages" >/dev/null 2>&1 || true
echo "Listo: compuerta reiniciada y Odoo refrescado. Las sesiones de chat de n8n conservan memoria: abra un chat nuevo."
