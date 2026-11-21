# Atajos (Linux/macOS o Git Bash). En PowerShell use los comandos equivalentes del README.
PY ?= python3
# Git Bash en Windows convierte rutas como /seed/... a rutas de Windows; esto lo evita.
export MSYS_NO_PATHCONV=1

.PHONY: up seed n8n demo-reset evidencias evidencias-bandera verificar test workflows zip down limpiar

up:            ## Levanta db, odoo, compuerta y n8n
	docker compose up -d --build

seed:          ## Crea la base mys_demo, instala módulos y carga datos sintéticos
	docker compose exec -T compuerta python /plataforma/seed_sistema.py

n8n:           ## Credenciales desde .env + importación y activación de W1, W2, W3
	$(PY) scripts/importar_n8n.py

demo-reset:    ## Reinicia la compuerta y refresca Odoo (vigencias = hoy)
	sh scripts/demo_reset.sh

evidencias:    ## 6 casos PC3 sin LLM; F01 detiene y arranca el contenedor odoo
	$(PY) scripts/ejecutar_casos.py

evidencias-bandera: ## Igual, pero F01 con la bandera ADMIN (no detiene Odoo)
	$(PY) scripts/ejecutar_casos.py --caida bandera

verificar:     ## Salud de los servicios
	$(PY) scripts/verificar_entorno.py

test:          ## Pruebas de la compuerta (requiere compuerta/requirements-dev.txt)
	cd compuerta && $(PY) -m pytest -q

workflows:     ## Regenera los JSON de n8n desde el generador y el prompt
	$(PY) scripts/generar_workflows.py

zip:           ## Arma GE703_PC3_Agente_G7_MYS.zip sin .env ni datos
	$(PY) scripts/empaquetar.py

down:          ## Detiene los servicios (conserva volúmenes)
	docker compose down

limpiar:       ## Detiene y BORRA volúmenes (Odoo, compuerta, n8n)
	docker compose down -v
