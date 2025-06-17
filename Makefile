
REGISTRY = johnsantamaria
STACK_NAME = exponentialit_stack
COMPOSE_FILE = docker-compose.yml
VERSION ?= 1.0.0

build-admin:
	docker build -t admin_django:$(VERSION) ./backend/django

build-ocr:
	docker build -t ocr_integration:$(VERSION) ./backend/services/ocr_integration

build-zoho:
	docker build -t zoho_integration:$(VERSION) ./backend/services/zoho_integration

build-openai:
	docker build -t openai_integration:$(VERSION) ./backend/services/openai_integration

build-nginx:
	docker build -t nginx:$(VERSION) ./nginx

build:
	@echo "🛠️  Construyendo imágenes con la versión $(VERSION)..."
	make build-admin VERSION=$(VERSION)
	make build-ocr VERSION=$(VERSION)
	make build-zoho VERSION=$(VERSION)
	make build-openai VERSION=$(VERSION)
	make build-nginx VERSION=$(VERSION)

push-admin:
	docker tag admin_django:$(VERSION) $(REGISTRY)/admin_django:$(VERSION)
	docker push $(REGISTRY)/admin_django:$(VERSION)

push-ocr:
	docker tag ocr_integration:$(VERSION) $(REGISTRY)/ocr_integration:$(VERSION)
	docker push $(REGISTRY)/ocr_integration:$(VERSION)

push-zoho:
	docker tag zoho_integration:$(VERSION) $(REGISTRY)/zoho_integration:$(VERSION)
	docker push $(REGISTRY)/zoho_integration:$(VERSION)

push-openai:
	docker tag openai_integration:$(VERSION) $(REGISTRY)/openai_integration:$(VERSION)
	docker push $(REGISTRY)/openai_integration:$(VERSION)

push-nginx:
	docker tag nginx:$(VERSION) $(REGISTRY)/nginx:$(VERSION)
	docker push $(REGISTRY)/nginx:$(VERSION)

push:
	@echo "🚀 Subiendo imágenes con la versión $(VERSION)..."
	make push-admin VERSION=$(VERSION)
	make push-ocr VERSION=$(VERSION)
	make push-zoho VERSION=$(VERSION)
	make push-openai VERSION=$(VERSION)
	make push-nginx VERSION=$(VERSION)

deploy:
	docker stack deploy -c $(COMPOSE_FILE) $(STACK_NAME)

deploy-check:
	@echo "🚀 Desplegando el stack '$(STACK_NAME)' con espera..."
	docker stack deploy --detach=false -c $(COMPOSE_FILE) $(STACK_NAME)
	docker service ls --filter label=com.docker.stack.namespace=$(STACK_NAME)

rm:
	docker stack rm $(STACK_NAME)

ps:
	docker service ls --filter label=com.docker.stack.namespace=$(STACK_NAME)

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

check-env:
	@if [ ! -f ./backend/services/ocr_integration/.env.prod ]; then \
		echo "❌ ERROR: No se encontró .env.prod"; exit 1; \
	fi
	@if ! grep -q "^DATABASE_URL=" ./backend/services/ocr_integration/.env.prod; then \
		echo "❌ ERROR: Falta DATABASE_URL"; exit 1; \
	fi

clean:
	docker ps -aq | xargs docker rm -f || true

prune:
	docker system prune -af --volumes

up: build deploy

down: rm clean

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

prod-deploy:
	docker stack deploy -c docker-stack.yml $(STACK_NAME)

prod-rm:
	docker stack rm $(STACK_NAME)

prod-status:
	docker stack ls
	docker service ls --filter label=com.docker.stack.namespace=$(STACK_NAME)
	docker ps -a

prod-logs-nginx:
	docker service logs -f $(STACK_NAME)_nginx

prod-reload-nginx:
	docker service update --force $(STACK_NAME)_nginx

prod-shell-nginx:
	docker exec -it $$(docker ps --filter "name=$(STACK_NAME)_nginx" --format "{{.ID}}") sh

prod-info: prod-status

.PHONY: \
  build build-admin build-ocr build-zoho build-openai build-nginx \
  push push-admin push-ocr push-zoho push-openai push-nginx \
  deploy deploy-check rm ps \
  logs logs-admin logs-ocr logs-zoho logs-openai logs-nginx \
  status check-env clean prune \
  up down \
  reload reload-admin reload-ocr reload-zoho reload-openai reload-nginx \
  shell-admin shell-ocr shell-zoho shell-openai shell-nginx \
  prod-deploy prod-rm prod-status prod-logs-nginx prod-reload-nginx prod-shell-nginx prod-info
