# Reinicia la base de la compuerta y vuelve a sembrar Odoo (vigencias = hoy). Ejecutar antes de exponer.
$ErrorActionPreference = "Stop"
Set-Location (Join-Path $PSScriptRoot "..")
docker compose exec -T compuerta python /seed/seed_odoo.py --reiniciar
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
Write-Output "Listo: compuerta reiniciada y Odoo refrescado. Abra un chat nuevo en n8n."
