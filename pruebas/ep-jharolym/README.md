# Verificación del aporte de arquitectura

Este bloque comprueba la vigencia de los diagramas de Jharolym y su coherencia con los resultados existentes de Benjamín. Reutiliza las evidencias de cliente nuevo del público general en tienda física, sin duplicar JSON ni cambiar el simulador.

Desde la raíz del repositorio, con Python 3 y biblioteca estándar:

```powershell
python arquitectura/diagramas/generar_diagramas_ep.py --check
```

La comprobación contrasta solicitudes y campos esperados con los resultados guardados, exige casos y controles satisfactorios, mantiene `order_id = null`, revisa el vínculo de la señal conceptual P2P y compara los SVG versionados con la salida reproducible del generador. Termina con código distinto de cero ante una inconsistencia. No modifica las evidencias ni los gráficos.

Para regenerar las figuras después de revisar un cambio:

```powershell
python arquitectura/diagramas/generar_diagramas_ep.py
```

## Evidencia funcional compartida

| Caso | Resultado de referencia | Archivo existente |
| --- | --- | --- |
| EP-N01 | ACEPTADA / VALIDADA | [EP-N01.json](../ep-benjamin/evidencias/EP-N01.json) |
| EP-S01 | PROMESA_CONDICIONADA / DISPONIBILIDAD_PARCIAL | [EP-S01.json](../ep-benjamin/evidencias/EP-S01.json) |
| EP-E01 | RECHAZADA / DESCUENTO_SIN_APROBACION | [EP-E01.json](../ep-benjamin/evidencias/EP-E01.json) |

La ejecución funcional se reproduce siguiendo el [método de Benjamín](../ep-benjamin/README.md). Si se cambian fixtures, primero revisar y regenerar sus evidencias; después actualizar los diagramas. `--check` verifica coherencia documental, no sustituye la ejecución del contrato ni prueba permisos de Odoo o concurrencia real.

Consultar la [arquitectura](../../arquitectura/crm-erp-ep.md) y las [fuentes del aporte](../../fuentes/ep-jharolym.md) para interpretar los resultados y sus límites.
