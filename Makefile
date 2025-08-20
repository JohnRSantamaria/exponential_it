# Variables
REGISTRY=exponentialit
STACK_NAME = exponentialit_stack
COMPOSE_FILE = docker-stack.yml
NETWORK = app_net
VERSION = v1.2.0-dev

# ------------------------------------------------------------------------------
# Inicialización y redes
# ------------------------------------------------------------------------------
swarm-init: ## Inicializa Docker Swarm
	@echo "🔧 Inicializando Docker Swarm..."
	@docker swarm init

networks: ## Lista las redes existentes
	@echo "🌐 Listando redes de Docker..."
	@docker network ls

create-network: ## Crea la red overlay si no existe
	@echo "🔍 Verificando si la red '$(NETWORK)' existe..."
	@if docker network inspect $(NETWORK) > /dev/null 2>&1; then \
		echo "✅ Red '$(NETWORK)' ya existe."; \
	else \
		echo "🌐 Red '$(NETWORK)' no existe. Creándola..."; \
		docker network create --driver overlay $(NETWORK); \
	fi

inspect: ## Inspecciona detalles de la red overlay
	@echo "🌐 Verificando red overlay llamada '$(NETWORK)'..."
	@docker network inspect '$(NETWORK)'

# ------------------------------------------------------------------------------
# Despliegue
# ------------------------------------------------------------------------------
deploy: ## Despliega el stack completo con espera
	@echo "🚀 Desplegando el stack '$(STACK_NAME)' con espera..."
	@docker stack deploy --detach=false -c $(COMPOSE_FILE) $(STACK_NAME)
	@echo "🔍 Servicios activos del stack '$(STACK_NAME)':"
	@docker service ls --filter label=com.docker.stack.namespace=$(STACK_NAME)

deploy-safe: create-network deploy ## Crea red si es necesario y despliega

status: ## Muestra estado de servicios y contenedores
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

ps: ## Lista servicios activos del stack
	@echo "📋 Listando servicios activos del stack '$(STACK_NAME)'..."
	@docker service ls --filter label=com.docker.stack.namespace=$(STACK_NAME)

# ------------------------------------------------------------------------------
# Eliminación y limpieza
# ------------------------------------------------------------------------------
rm: ## Elimina el stack desplegado
	@echo "🗑️ Eliminando el stack '$(STACK_NAME)'..."
	@docker stack rm $(STACK_NAME)

clean: ## Elimina contenedores detenidos
	@echo "🧹 Eliminando contenedores detenidos..."
	@docker ps -aq | xargs docker rm -f || true

prune: ## Elimina recursos no utilizados
	@echo "🔥 Eliminando recursos no utilizados (volúmenes incluidos)..."
	@docker system prune -af --volumes

up: build deploy ## Compila y despliega todo
down: rm clean prune ## Elimina todo (stack, contenedores, recursos)

# ------------------------------------------------------------------------------
# Logs
# ------------------------------------------------------------------------------
logs-admin: ## Logs de admin-django
	@docker service logs $(STACK_NAME)_admin-django

logs-orchestrator: ## Logs de orchestrator
	@docker service logs $(STACK_NAME)_orchestrator

logs-zoho: ## Logs de zoho-integration
	@docker service logs $(STACK_NAME)_zoho-integration

logs-odoo: ## Logs de odoo-integration
	@docker service logs $(STACK_NAME)_odoo-integration

logs-openai: ## Logs de openai-integration
	@docker service logs $(STACK_NAME)_openai-integration

logs-nginx: ## Logs de nginx
	@docker service logs $(STACK_NAME)_nginx

logs-claudeai: ## Logs de Claude AI
	@docker service logs $(STACK_NAME)_claudeai-integration

logs: logs-admin logs-orchestrator logs-zoho logs-openai logs-odoo logs-claudeai logs-nginx  ## Muestra todos los logs

logs-admin-follow: ## Logs en tiempo real de admin-django
	@docker service logs -f $(STACK_NAME)_admin-django

logs-orchestrator-follow: ## Logs en tiempo real de orchestrator
	@docker service logs -f $(STACK_NAME)_orchestrator

logs-zoho-follow: ## Logs en tiempo real de zoho-integration
	@docker service logs -f $(STACK_NAME)_zoho-integration

logs-odoo-follow: ## Logs en tiempo real de odoo-integration
	@docker service logs -f $(STACK_NAME)_odoo-integration

logs-openai-follow: ## Logs en tiempo real de openai-integration
	@docker service logs -f $(STACK_NAME)_openai-integration

logs-openai-follow: ## Logs en tiempo real de claudeai-integration
	@docker service logs -f $(STACK_NAME)_claudeai-integration

logs-nginx-follow: ## Logs en tiempo real de nginx
	@docker service logs -f $(STACK_NAME)_nginx

logs-error-%: ## Muestra logs del último contenedor con error por nombre
	@cid=$$(docker ps -a --filter "name=$(STACK_NAME)_$*" --filter "status=exited" -q | head -n 1); \
	if [ -z "$$cid" ]; then \
		echo "✅ No se encontraron contenedores con error para '$*'."; \
	else \
		docker logs $$cid; \
	fi

# ------------------------------------------------------------------------------
# Reload de servicios
# ------------------------------------------------------------------------------
reload-admin: ## Reinicia el servicio admin-django
	@docker service update --force $(STACK_NAME)_admin-django

reload-orchestrator: ## Reinicia el servicio orchestrator
	@docker service update --force $(STACK_NAME)_orchestrator

reload-zoho: ## Reinicia el servicio zoho-integration
	@docker service update --force $(STACK_NAME)_zoho-integration

reload-odoo: ## Reinicia el servicio odoo-integration
	@docker service update --force $(STACK_NAME)_odoo-integration

reload-openai: ## Reinicia el servicio openai-integration
	@docker service update --force $(STACK_NAME)_openai-integration

reload-claudeai: ## Reinicia el servicio claudeai-integration
	@docker service update --force $(STACK_NAME)_claudeai-integration

reload-nginx: ## Reinicia el servicio nginx
	@docker service update --force $(STACK_NAME)_nginx

reload: reload-admin reload-orchestrator reload-zoho reload-odoo reload-openai reload-claudeai reload-nginx ## Reinicia todos los servicios

# ------------------------------------------------------------------------------
# Shell en contenedores
# ------------------------------------------------------------------------------
shell-admin: ## Accede al contenedor admin-django
	@docker exec -it $$(docker ps --filter "name=$(STACK_NAME)_admin-django" --format "{{.ID}}") sh

shell-orchestrator: ## Accede al contenedor orchestrator
	@docker exec -it $$(docker ps --filter "name=$(STACK_NAME)_orchestrator" --format "{{.ID}}") sh

shell-zoho: ## Accede al contenedor zoho-integration
	@docker exec -it $$(docker ps --filter "name=$(STACK_NAME)_zoho-integration" --format "{{.ID}}") sh

shell-odoo: ## Accede al contenedor odoo-integration
	@docker exec -it $$(docker ps --filter "name=$(STACK_NAME)_odoo-integration" --format "{{.ID}}") sh

shell-openai: ## Accede al contenedor openai-integration
	@docker exec -it $$(docker ps --filter "name=$(STACK_NAME)_openai-integration" --format "{{.ID}}") sh

shell-claudeai: ## Accede al contenedor claudeai-integration
	@docker exec -it $$(docker ps --filter "name=$(STACK_NAME)_claudeai-integration" --format "{{.ID}}") sh

shell-nginx: ## Accede al contenedor nginx
	@docker exec -it $$(docker ps --filter "name=$(STACK_NAME)_nginx" --format "{{.ID}}") sh

# ------------------------------------------------------------------------------
# Subir imagen
# ------------------------------------------------------------------------------
build-admin: ## Construye imagen Docker de admin-django
	docker build -t $(REGISTRY)/admin-django:$(VERSION) ./backend/django

push-admin: ## Sube imagen Docker de admin-django
	docker push $(REGISTRY)/admin-django:$(VERSION)

publish-admin: build-admin push-admin ## Construye y sube imagen Docker de admin-django
	
  
build-orchestrator: ## Construye imagen Docker de orchestrator
	docker build -t $(REGISTRY)/orchestrator:$(VERSION) ./backend/services/orchestrator

push-orchestrator: ## Sube imagen Docker de orchestrator
	docker push $(REGISTRY)/orchestrator:$(VERSION)

publish-orchestrator: build-orchestrator push-orchestrator ## Construye y sube imagen Docker de orchestrator
	

build-odoo: ## Construye imagen Docker de odoo-integration
	docker build -t $(REGISTRY)/odoo-integration:$(VERSION) ./backend/services/odoo_integration

push-odoo: ## Sube imagen Docker de odoo-integration
	docker push $(REGISTRY)/odoo-integration:$(VERSION)

publish-odoo: build-odoo push-odoo ## Construye y sube imagen Docker de orchestrator


build-zoho: ## Construye imagen Docker de zoho-integration
	docker build -t $(REGISTRY)/zoho-integration:$(VERSION) ./backend/services/zoho_integration

push-zoho: ## Sube imagen Docker de zoho-integration
	docker push $(REGISTRY)/zoho-integration:$(VERSION)

publish-zoho: build-zoho push-zoho ## Construye y sube imagen Docker de zoho-integration


build-openai: ## Construye imagen Docker de openai-integration
	docker build -t $(REGISTRY)/openai-integration:$(VERSION) ./backend/services/openai_integration

push-openai: ## Sube imagen Docker de openai-integration
	docker push $(REGISTRY)/openai-integration:$(VERSION)

publish-openai: build-openai push-openai ## Construye y sube imagen Docker de build-openai

build-claudeai: ## Construye imagen Docker de claudeai-integration
	docker build -t $(REGISTRY)/claudeai-integration:$(VERSION) ./backend/services/claudeai_integration

push-claudeai: ## Sube imagen Docker de claudeai-integration
	docker push $(REGISTRY)/claudeai-integration:$(VERSION)

publish-claudeai: build-claudeai push-claudeai ## Construye y sube imagen Docker de build-claudeai

build-nginx: ## Construye imagen Docker de nginx
	docker build -t $(REGISTRY)/nginx:$(VERSION) ./nginx

push-nginx: ## Sube imagen Docker de nginx
	docker push $(REGISTRY)/nginx:$(VERSION)

publish-nginx: build-nginx push-nginx ## Construye y sube imagen Docker de build-nginx

build: build-admin build-orchestrator build-odoo build-zoho build-openai build-claudeai build-nginx ## Construye todas las imágenes
push: push-admin push-orchestrator push-odoo push-zoho push-openai push-claudeai push-nginx ## Sube todas las imágenes
publish: publish-admin publish-orchestrator publish-odoo publish-zoho publish-openai publish-claudeai publish-nginx ## Publica todas las imagenes

# ------------------------------------------------------------------------------
# Variables de entorno
# ------------------------------------------------------------------------------
env-admin: ## Muestra variables de entorno de admin-django
	@docker exec -it $$(docker ps --filter "name=$(STACK_NAME)_admin_django" --format "{{.ID}}") printenv

env-orchestrator: ## Muestra variables de entorno de orchestrator
	@docker exec -it $$(docker ps --filter "name=$(STACK_NAME)_orchestrator" --format "{{.ID}}") printenv

env-zoho: ## Muestra variables de entorno de zoho-integration
	@docker exec -it $$(docker ps --filter "name=$(STACK_NAME)_zoho_integration" --format "{{.ID}}") printenv

env-odoo: ## Muestra variables de entorno de odoo-integration
	@docker exec -it $$(docker ps --filter "name=$(STACK_NAME)_odoo_integration" --format "{{.ID}}") printenv

env-openai: ## Muestra variables de entorno de openai-integration
	@docker exec -it $$(docker ps --filter "name=$(STACK_NAME)_openai_integration" --format "{{.ID}}") printenv

env-claudeai: ## Muestra variables de entorno de claudeai-integration
	@docker exec -it $$(docker ps --filter "name=$(STACK_NAME)_openai_integration" --format "{{.ID}}") printenv


env-nginx: ## Muestra variables de entorno de nginx
	@docker exec -it $$(docker ps --filter "name=$(STACK_NAME)_nginx" --format "{{.ID}}") printenv

envs: env-admin env-orchestrator env-zoho env-openai env-odoo env-nginx ## Muestra todas las variables de entorno


# ------------------------------------------------------------------------------  
# Ayuda  
# ------------------------------------------------------------------------------  
help: ## Muestra esta ayuda  
	@echo "📖 Comandos disponibles:"  
	@grep -E '^[a-zA-Z0-9_-]+:.*?## ' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-30s\033[0m %s\n", $$1, $$2}'  
  
# ------------------------------------------------------------------------------  
# Reglas PHONY  
# ------------------------------------------------------------------------------  
.PHONY: \
  build build-admin build-nginx build-odoo build-openai build-claudeai build-orchestrator build-zoho \
  clean create-network \
  deploy deploy-safe down \
  env-admin env-nginx env-odoo env-openai env-orchestrator env-zoho env-claudeai envs \
  help \
  inspect \
  logs logs-admin logs-nginx logs-odoo logs-openai logs-orchestrator logs-zoho logs-claudeai \
  logs-admin-follow logs-nginx-follow logs-odoo-follow logs-openai-follow logs-orchestrator-follow logs-zoho-follow  logs-claudeai-follow\
  logs-error-% \
  networks \
  prune ps push push-admin push-nginx push-odoo push-openai push-orchestrator push-zoho push-claudeai \
  reload reload-admin reload-nginx reload-odoo reload-openai reload-orchestrator reload-zoho reload-claudeai \
  rm \
  shell-admin shell-nginx shell-odoo shell-openai shell-orchestrator shell-zoho shell-claudeai \
  status swarm-init up
