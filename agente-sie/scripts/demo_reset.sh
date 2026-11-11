#!/usr/bin/env sh
# Reinicia la base de la compuerta y vuelve a sembrar Odoo (vigencias = hoy). Ejecutar antes de exponer.
set -eu
cd "$(dirname "$0")/.."
docker compose exec -T compuerta python /seed/seed_odoo.py --reiniciar
echo "Listo: compuerta reiniciada y Odoo refrescado. Las sesiones de chat de n8n conservan memoria: abra un chat nuevo."
