NETWORK = app_net
STACK_NAME = exponentialit_stack
COMPOSE_FILE = docker-stack.yml

# ------------------------------------------------------------------------------
# Inicialización y redes
# ------------------------------------------------------------------------------

swarm-init:
	@echo "🔧 Inicializando Docker Swarm..."
	@docker swarm init

networks:
	@echo "🌐 Listando redes de Docker..."
	@docker network ls

create-network:
	@echo "🔍 Verificando si la red '$(NETWORK)' existe..."
	@if docker network inspect $(NETWORK) > /dev/null 2>&1; then \
		echo "✅ Red '$(NETWORK)' ya existe."; \
	else \
		echo "🌐 Red '$(NETWORK)' no existe. Creándola..."; \
		docker network create --driver overlay $(NETWORK); \
	fi

inspect: 
	@echo "🌐 Verificando red overlay llamada '$(NETWORK)'..."
	@docker network inspect '$(NETWORK)'

# ------------------------------------------------------------------------------
# Despliegue
# ------------------------------------------------------------------------------

deploy:	
	@echo "🚀 Desplegando el stack '$(STACK_NAME)' con espera..."
	@docker stack deploy --detach=false -c $(COMPOSE_FILE) $(STACK_NAME)
	@echo "🔍 Servicios activos del stack '$(STACK_NAME)':"
	@docker service ls --filter label=com.docker.stack.namespace=$(STACK_NAME)

deploy-safe: create-network deploy

status:
	@echo "📦 Estado general del stack '$(STACK_NAME)':"
	@echo ""

	@echo "🔸 Servicios:"
	@docker service ls --filter label=com.docker.stack.namespace=$(STACK_NAME) --format \
		"{{.Name}} {{.Replicas}}" | while read name replicas; do \
			desired=$$(echo $$replicas | cut -d'/' -f2); \
			current=$$(echo $$replicas | cut -d'/' -f1); \
			if [ "$$desired" = "$$current" ]; then \
				printf "✅ %-45s %s\n" "$$name" "OK ($$replicas)"; \
			else \
				printf "❌ %-45s %s\n" "$$name" "FALLA ($$replicas) - Ejecuta: make reload-$${name##*-}"; \
			fi; \
		done

	@echo ""
	@echo "🔸 Contenedores del stack:"
	@docker ps -a --filter "label=com.docker.stack.namespace=$(STACK_NAME)" \
		--format "  {{.Status}} \t {{.Names}}" | sort

ps:
	@echo "📋 Listando servicios activos del stack '$(STACK_NAME)'..."
	@docker service ls --filter label=com.docker.stack.namespace=$(STACK_NAME)

# ------------------------------------------------------------------------------
# Eliminación y limpieza
# ------------------------------------------------------------------------------

rm:
	@echo "🗑️ Eliminando el stack '$(STACK_NAME)'..."
	@docker stack rm $(STACK_NAME)

clean:
	@echo "🧹 Eliminando contenedores detenidos..."
	@docker ps -aq | xargs docker rm -f || true

prune:
	@echo "🔥 Eliminando recursos no utilizados (volúmenes incluidos)..."
	@docker system prune -af --volumes

up: build deploy

down: rm clean prune

# ------------------------------------------------------------------------------
# Logs
# ------------------------------------------------------------------------------

logs-admin:
	@echo "📄 Mostrando logs del servicio 'admin-django'..."
	@docker service logs $(STACK_NAME)_admin-django

logs-orchestrator:
	@echo "📄 Mostrando logs del servicio 'orchestrator'..."
	@docker service logs $(STACK_NAME)_orchestrator

logs-zoho:
	@echo "📄 Mostrando logs del servicio 'zoho-integration'..."
	@docker service logs $(STACK_NAME)_zoho-integration

logs-odoo:
	@echo "📄 Mostrando logs del servicio 'odoo-integration'..."
	@docker service logs $(STACK_NAME)_odoo-integration

logs-openai:
	@echo "📄 Mostrando logs del servicio 'openai-integration'..."
	@docker service logs $(STACK_NAME)_openai-integration

logs-nginx:
	@echo "📄 Mostrando logs del servicio 'nginx'..."
	@docker service logs $(STACK_NAME)_nginx

logs: logs-admin logs-orchestrator logs-zoho logs-openai logs-odoo logs-nginx

# Logs en tiempo real

logs-admin-follow:
	@echo "🔄 Siguiendo logs en tiempo real de 'admin-django'..."
	@docker service logs -f $(STACK_NAME)_admin-django

logs-orchestrator-follow:
	@echo "🔄 Siguiendo logs en tiempo real de 'orchestrator'..."
	@docker service logs -f $(STACK_NAME)_orchestrator

logs-zoho-follow:
	@echo "🔄 Siguiendo logs en tiempo real de 'zoho-integration'..."
	@docker service logs -f $(STACK_NAME)_zoho-integration

logs-odoo-follow:
	@echo "🔄 Siguiendo logs en tiempo real de 'odoo-integration'..."
	@docker service logs -f $(STACK_NAME)_odoo-integration

logs-openai-follow:
	@echo "🔄 Siguiendo logs en tiempo real de 'openai-integration'..."
	@docker service logs -f $(STACK_NAME)_openai-integration

logs-nginx-follow:
	@echo "🔄 Siguiendo logs en tiempo real de 'nginx'..."
	@docker service logs -f $(STACK_NAME)_nginx

logs-error-%:
	@echo "📄 Mostrando logs del último contenedor con error para '$*'..."
	@cid=$$(docker ps -a --filter "name=$(STACK_NAME)_$*" --filter "status=exited" -q | head -n 1); \
	if [ -z "$$cid" ]; then \
		echo "✅ No se encontraron contenedores con error para '$*'."; \
	else \
		docker logs $$cid; \
	fi

# ------------------------------------------------------------------------------
# Reload de servicios
# ------------------------------------------------------------------------------

reload-admin:
	@echo "♻️ Reiniciando servicio 'admin-django'..."
	@docker service update --force $(STACK_NAME)_admin-django

reload-orchestrator:
	@echo "♻️ Reiniciando servicio 'orchestrator'..."
	@docker service update --force $(STACK_NAME)_orchestrator

reload-zoho:
	@echo "♻️ Reiniciando servicio 'zoho-integration'..."
	@docker service update --force $(STACK_NAME)_zoho-integration

reload-odoo:
	@echo "♻️ Reiniciando servicio 'odoo-integration'..."
	@docker service update --force $(STACK_NAME)_odoo-integration

reload-openai:
	@echo "♻️ Reiniciando servicio 'openai-integration'..."
	@docker service update --force $(STACK_NAME)_openai-integration

reload-nginx:
	@echo "♻️ Reiniciando servicio 'nginx'..."
	@docker service update --force $(STACK_NAME)_nginx

reload: reload-admin reload-orchestrator reload-zoho reload-odoo reload-openai reload-nginx

# ------------------------------------------------------------------------------
# Shell en contenedores
# ------------------------------------------------------------------------------

shell-admin:
	@echo "🔧 Entrando al contenedor 'admin-django'..."
	@docker exec -it $$(docker ps --filter "name=$(STACK_NAME)_admin-django" --format "{{.ID}}") sh

shell-orchestrator:
	@echo "🔧 Entrando al contenedor 'orchestrator'..."
	@docker exec -it $$(docker ps --filter "name=$(STACK_NAME)_orchestrator" --format "{{.ID}}") sh

shell-zoho:
	@echo "🔧 Entrando al contenedor 'zoho-integration'..."
	@docker exec -it $$(docker ps --filter "name=$(STACK_NAME)_zoho-integration" --format "{{.ID}}") sh

shell-odoo:
	@echo "🔧 Entrando al contenedor 'odoo-integration'..."
	@docker exec -it $$(docker ps --filter "name=$(STACK_NAME)_odoo-integration" --format "{{.ID}}") sh

shell-openai:
	@echo "🔧 Entrando al contenedor 'openai-integration'..."
	@docker exec -it $$(docker ps --filter "name=$(STACK_NAME)_openai-integration" --format "{{.ID}}") sh

shell-nginx:
	@echo "🔧 Entrando al contenedor 'nginx'..."
	@docker exec -it $$(docker ps --filter "name=$(STACK_NAME)_nginx" --format "{{.ID}}") sh

# ------------------------------------------------------------------------------
# Subir imagen
# ------------------------------------------------------------------------------

build-orchestrator: 
	docker build -t exponentialit/orchestrator:v1.1.0-beta ./backend/services/orchestrator

push-orchestrator: 
	docker push exponentialit/orchestrator:v1.1.0-beta 

build-odoo: 
	docker build -t exponentialit/odoo-integration:v1.1.0-beta ./backend/services/odoo_integration

push-odoo: 
	docker push exponentialit/odoo-integration:v1.1.0-beta 

build-nginx: 
	docker build -t exponentialit/nginx:v1.1.0-beta ./nginx

push-nginx:
	docker push exponentialit/nginx:v1.1.0-beta

build-admin: 
	docker build -t exponentialit/admin-django:v1.1.0-beta ./backend/django

push-admin:
	docker push exponentialit/admin-django:v1.1.0-beta

build-zoho: 
	docker build -t exponentialit/zoho-integration:v1.1.0-beta ./backend/services/zoho_integration

push-zoho: 
	docker push exponentialit/zoho-integration:v1.1.0-beta

build-openai: 
	docker build -t exponentialit/openai-integration:v1.1.0-beta ./backend/services/openai_integration

push-openai: 
	docker push exponentialit/openai-integration:v1.1.0-beta

build: build-admin build-orchestrator build-odoo build-zoho build-openai build-nginx

push: push-admin push-orchestrator push-odoo push-zoho push-openai push-nginx

# ------------------------------------------------------------------------------
# ver envs en produccion 
# ------------------------------------------------------------------------------

env-admin:
	@echo "🌍 Variables de entorno en 'admin-django':"
	@docker exec -it $$(docker ps --filter "name=$(STACK_NAME)_admin_django" --format "{{.ID}}") printenv

env-orchestrator:
	@echo "🌍 Variables de entorno en 'orchestrator':"
	@docker exec -it $$(docker ps --filter "name=$(STACK_NAME)_orchestrator" --format "{{.ID}}") printenv

env-zoho:
	@echo "🌍 Variables de entorno en 'zoho-integration':"
	@docker exec -it $$(docker ps --filter "name=$(STACK_NAME)_zoho_integration" --format "{{.ID}}") printenv

env-odoo:
	@echo "🌍 Variables de entorno en 'odoo-integration':"
	@docker exec -it $$(docker ps --filter "name=$(STACK_NAME)_odoo_integration" --format "{{.ID}}") printenv

env-openai:
	@echo "🌍 Variables de entorno en 'openai-integration':"
	@docker exec -it $$(docker ps --filter "name=$(STACK_NAME)_openai_integration" --format "{{.ID}}") printenv

env-nginx:
	@echo "🌍 Variables de entorno en 'nginx':"
	@docker exec -it $$(docker ps --filter "name=$(STACK_NAME)_nginx" --format "{{.ID}}") printenv

envs: env-admin env-orchestrator env-zoho env-openai env-odoo env-nginx

# ------------------------------------------------------------------------------
# Reglas PHONY: siempre se ejecutan, aunque existan archivos con ese nombre
# ------------------------------------------------------------------------------

.PHONY: \
  swarm-init networks create-network \
  build deploy deploy-check status ps rm clean prune \
  up down \
  logs logs-admin logs-orchestrator logs-zoho logs-openai logs-odoo logs-nginx \
  logs-admin-follow logs-orchestrator-follow logs-zoho-follow logs-openai-follow logs-odoo-follow logs-nginx-follow logs-follow \
  reload reload-admin reload-orchestrator reload-zoho reload-openai reload-odoo reload-nginx \
  shell-admin shell-orchestrator shell-zoho shell-openai shell-odoo shell-nginx
