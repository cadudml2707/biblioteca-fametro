COMPOSE_FILE := infra/compose.yaml
ENV_FILE ?= infra/.env
ENV_EXAMPLE := infra/.env.example
COMPOSE := docker compose --env-file $(ENV_FILE) -f $(COMPOSE_FILE)

.DEFAULT_GOAL := help

.PHONY: help env config up build down stop restart logs ps backend-shell db-shell migrate backend-check backend-test check-migrations

help: ## Exibir os comandos disponíveis
	@awk 'BEGIN {FS = ":.*##"; printf "Uso: make <comando>\n\n"} /^[a-zA-Z0-9_-]+:.*##/ {printf "  %-20s %s\n", $$1, $$2}' $(MAKEFILE_LIST)

env: ## Criar o arquivo de ambiente caso não exista
	@if [ ! -f "$(ENV_FILE)" ]; then \
		cp "$(ENV_EXAMPLE)" "$(ENV_FILE)"; \
		echo "Criado $(ENV_FILE). Substitua a chave e a senha de exemplo antes de iniciar."; \
	else \
		echo "$(ENV_FILE) já existe."; \
	fi

config: ## Validar a configuração do Docker Compose
	$(COMPOSE) config --quiet

up: ## Construir e iniciar os serviços em segundo plano
	$(COMPOSE) up --build -d

build: ## Construir as imagens dos serviços
	$(COMPOSE) build

down: ## Remover containers e rede, preservando o volume do banco
	$(COMPOSE) down

stop: ## Parar os serviços sem remover os containers
	$(COMPOSE) stop

restart: ## Reiniciar os serviços sem reconstruir as imagens
	$(COMPOSE) restart

logs: ## Acompanhar os logs dos serviços
	$(COMPOSE) logs -f

ps: ## Exibir o estado dos serviços
	$(COMPOSE) ps

backend-shell: ## Abrir um shell no container do backend
	$(COMPOSE) exec backend sh

db-shell: ## Abrir o cliente PostgreSQL no container do banco
	$(COMPOSE) exec db sh -c 'exec psql -U "$$POSTGRES_USER" -d "$$POSTGRES_DB"'

migrate: ## Aplicar as migrações do Django
	$(COMPOSE) exec backend python manage.py migrate

backend-check: ## Verificar o projeto Django e a conexão com o banco
	$(COMPOSE) exec backend python manage.py check --database default

backend-test: ## Executar os testes do backend
	$(COMPOSE) exec backend python manage.py test tests

check-migrations: ## Verificar se há migrações pendentes de criação
	$(COMPOSE) exec backend python manage.py makemigrations --check --dry-run
