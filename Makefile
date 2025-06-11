# =========================
# 🔧 Variables
# =========================
REGISTRY = johnsantamaria
STACK_NAME = exponentialit_stack
COMPOSE_FILE = docker-compose.yml

# =========================
# 🛠️ Build de imágenes
# =========================
build-admin:
	docker build -t admin_django ./backend/django

build-ocr:
	docker build -t ocr_integration ./backend/services/ocr_integration

build-zoho:
	docker build -t zoho_integration ./backend/services/zoho_integration

build-openai:
	docker build -t openai_integration ./backend/services/openai_integration

build-nginx:
	docker build -t nginx -f ./nginx/Dockerfile ./nginx



build: build-admin build-ocr build-zoho build-openai build-nginx

# =========================
# 🚀 Push a Docker Hub
# =========================
push-admin:
	docker tag admin_django $(REGISTRY)/admin_django:latest
	docker push $(REGISTRY)/admin_django:latest

push-ocr:
	docker tag ocr_integration $(REGISTRY)/ocr_integration:latest
	docker push $(REGISTRY)/ocr_integration:latest

push-zoho:
	docker tag zoho_integration $(REGISTRY)/zoho_integration:latest
	docker push $(REGISTRY)/zoho_integration:latest

push-openai:
	docker tag openai_integration $(REGISTRY)/openai_integration:latest
	docker push $(REGISTRY)/openai_integration:latest

push-nginx:
	docker tag nginx $(REGISTRY)/nginx:latest
	docker push $(REGISTRY)/nginx:latest

push: push-admin push-ocr push-zoho push-openai push-nginx

# =========================
# 🐳 Despliegue en Swarm
# =========================
deploy:
	docker stack deploy -c $(COMPOSE_FILE) $(STACK_NAME)

deploy-prod:
	docker stack deploy -c docker-compose.prod.yml $(STACK_NAME)

# Despliegue con espera y chequeo de estado
deploy-check:
	@echo "🚀 Desplegando el stack '$(STACK_NAME)' con espera (modo bloqueante)..."
	docker stack deploy --detach=false -c $(COMPOSE_FILE) $(STACK_NAME)
	@echo "✅ Estado de los servicios tras el despliegue:"
	docker service ls --filter label=com.docker.stack.namespace=$(STACK_NAME)


rm:
	docker stack rm $(STACK_NAME)

ps:
	docker service ls --filter label=com.docker.stack.namespace=$(STACK_NAME)

# =========================
# 🔍 logs 
# =========================

logs-admin:
	docker service logs $(STACK_NAME)_admin-django

logs-ocr:
	docker service logs $(STACK_NAME)_ocr-integration

logs-zoho:
	docker service logs $(STACK_NAME)_zoho-integration

logs-openai:
	docker service logs $(STACK_NAME)_openai-integration

logs-nginx:
	docker service logs $(STACK_NAME)_nginx

logs: logs-admin logs-ocr logs-zoho logs-openai logs-nginx

status:
	docker stack ls
	docker service ls --filter label=com.docker.stack.namespace=$(STACK_NAME)
	docker ps -a
	docker network ls


# =========================
# 🔍 Validación de .env
# =========================
check-env:
	@echo "🔍 Validando archivo .env.prod para ocr_integration..."
	@if [ ! -f ./backend/services/ocr_integration/.env.prod ]; then \
		echo "❌ ERROR: No se encontró ./backend/services/ocr_integration/.env.prod"; exit 1; \
	fi
	@if ! grep -q "^DATABASE_URL=" ./backend/services/ocr_integration/.env.prod; then \
		echo "❌ ERROR: Falta la variable DATABASE_URL en .env.prod"; exit 1; \
	fi
	@if grep -E '^DATABASE_URL="?postgresql:\/\/.+"?' ./backend/services/ocr_integration/.env.prod | grep -q '=""\|=""\|="postgresql://"' ; then \
		echo "❌ ERROR: DATABASE_URL está vacía o mal formada"; exit 1; \
	fi
	@echo "✅ .env.prod válido"

# =========================
# 🧹 Limpieza
# =========================
clean:
	docker ps -aq | xargs docker rm -f || true

prune:
	docker system prune -af --volumes

# =========================
# 📦 Atajos agrupados
# =========================
up: build deploy
down: rm clean

.PHONY: build push deploy rm ps logs clean prune status up down


# =========================
# 🔄 Reload de servicios Swarm
# =========================
reload-admin:
	docker service update --force $(STACK_NAME)_admin-django

reload-ocr:
	docker service update --force $(STACK_NAME)_ocr-integration

reload-zoho:
	docker service update --force $(STACK_NAME)_zoho-integration

reload-openai:
	docker service update --force $(STACK_NAME)_openai-integration

reload-nginx:
	docker service update --force $(STACK_NAME)_nginx

reload: reload-admin reload-ocr reload-zoho reload-openai reload-nginx


# =========================
# 💻 Acceso a contenedores en ejecución
# =========================
shell-admin:
	docker exec -it $$(docker ps --filter "name=$(STACK_NAME)_admin-django" --format "{{.ID}}") sh

shell-ocr:
	docker exec -it $$(docker ps --filter "name=$(STACK_NAME)_ocr-integration" --format "{{.ID}}") sh

shell-zoho:
	docker exec -it $$(docker ps --filter "name=$(STACK_NAME)_zoho-integration" --format "{{.ID}}") sh

shell-openai:
	docker exec -it $$(docker ps --filter "name=$(STACK_NAME)_openai-integration" --format "{{.ID}}") sh

shell-nginx:
	docker exec -it $$(docker ps --filter "name=$(STACK_NAME)_nginx" --format "{{.ID}}") sh

# ===========================================================
#
# 🛠️ Cómo usar el Makefile
#
# make build           # Construye todas las imágenes (incluye nginx)
# make push            # Sube todas las imágenes al registry (incluye nginx)
# make deploy          # Despliega el stack en Docker Swarm
# make deploy-check    # Despliega con espera y verifica estado
# make rm              # Elimina el stack del Swarm
# make up              # Ejecuta build + deploy
# make down            # Elimina el stack y contenedores residuales
# make logs            # Muestra logs de todos los servicios
# make status          # Estado del stack, servicios, contenedores y redes
# make reload          # Fuerza la recarga (rolling update) de todos los servicios
# make reload-nginx    # Recarga solo el servicio nginx
# make check-env       # Verifica archivo .env.prod del OCR
# make prune           # Limpia imágenes, volúmenes y redes no utilizadas
#
# 👀 Individual:
# make build-nginx     # Construye solo la imagen de nginx
# make push-nginx      # Sube solo la imagen de nginx
# make reload-ocr      # Recarga solo el servicio OCR
#
# 🔁 Repite para admin_django, zoho, openai según sea necesario.
# ===========================================================
