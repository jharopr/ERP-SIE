# Validación de la plataforma integrada

Fecha: 11/11/2026, hora de Perú. Entorno: Windows, Docker Desktop, Odoo 18.0-20261102, PostgreSQL 16, n8n 2.46.7 y compuerta Python 3.12.

| Comprobación | Resultado y evidencia |
| --- | --- |
| Compilación e instalación | Cinco servicios saludables; módulo `mys_erp` instalado en Odoo real |
| Datos | 50 referencias de catálogo y 2 SKU PC3; ocho clientes, un proveedor, seis leads y cotizaciones versionadas |
| Pruebas automatizadas | 34 pruebas aprobadas; motor, equivalencia PC2, casos PC3, permisos, sesiones, origen, búsqueda y consulta diferida |
| Contrato histórico | Copia del simulador conservada byte a byte, comprobada con SHA-256 |
| Casos PC3 con Odoo real | 6/6 aprobados, stock intacto y pedido nulo; ver `../agente-sie/evidencias/resultados.md` |
| Caída PC3-F01 | Bandera ADMIN documentada; recuperación de la misma solicitud. La caída está simulada, el resto del escenario lee Odoo real |
| Plataforma | 40/40 comprobaciones, incluyendo los 50 precios leídos de Odoo y ACL de lectura; [sistema.json](sistema.json) |
| Casos CAT | Normal, faltante y descuento con productos del Excel; resultado estable ante reintento e inventario intacto |
| n8n sin modelo | W3 ejecutó el caso normal y W2 registró una decisión autenticada del dueño en la bitácora; [n8n.json](n8n.json) |
| Formularios y chat | Sin autenticación devuelven 401; el formulario del dueño usa credencial independiente |
| Backup | Ejecución real: dump PostgreSQL y archivos de volúmenes, con pausa/reanudación de los tres servicios que escriben. Backup privado ignorado por Git |
| Sintaxis y configuración | Python AST, XML Odoo, JSON de flujos, `node --check`, Compose raíz y entrada compatible del agente válidos |

## Límites de la verificación

- No se ejecutó W1 con Gemini: falta una clave del proveedor. No se presenta una conversación determinista como salida de un modelo. Las transcripciones históricas del agente se conservan con su propia fecha y alcance.
- La revisión visual se intentó y se detuvo: la herramienta de uso del equipo no pudo verificar con suficiente confianza la URL de Chrome. Las rutas HTTP, sesiones y resultados de los servicios sí se verificaron.
- No se desplegó un dominio/TLS productivo ni se ensayó una restauración destructiva. Se generó un backup y se conserva la guía de restauración.
- No se ejecutó la instalación en un segundo equipo limpio. La instalación y las verificaciones corresponden a este equipo local.
- Los registros comerciales, inventario y reservas son sintéticos; no prueban ventas o disponibilidad real de la empresa.
- Una corrida CAT-002 coincidió con la prueba de indisponibilidad F01 y quedó PENDIENTE. Se reanudó con Odoo restablecido y se repitió la verificación sin resets paralelos: 40/40. El resultado final está en el JSON con su fecha de ejecución real.

## Reproducción

Desde `app/`, ejecutar de forma secuencial:

```powershell
.venv\Scripts\python scripts/probar.py
python -X utf8 agente-sie/scripts/ejecutar_casos.py --caida bandera
python scripts/verificar_sistema.py
python scripts/probar_n8n.py
```

La prueba del formulario registra una decisión sobre CAT-002. Para repetirla después de una decisión ya cerrada, refrescar la demo antes de ejecutar la secuencia. Los servicios se mantienen levantados al finalizar.
