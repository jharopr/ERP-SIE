# Reinicia la base de la compuerta y vuelve a sembrar Odoo (vigencias = hoy). Ejecutar antes de exponer.
$ErrorActionPreference = "Stop"
Set-Location (Join-Path $PSScriptRoot "..")
docker compose exec -T compuerta python /seed/seed_odoo.py --reiniciar
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
# Vacía el buzón local del dueño (Mailpit); si no está levantado, no pasa nada.
try { Invoke-RestMethod -Method Delete -Uri "http://localhost:8025/api/v1/messages" | Out-Null } catch { }
Write-Output "Listo: compuerta reiniciada y Odoo refrescado. Abra un chat nuevo en n8n."
