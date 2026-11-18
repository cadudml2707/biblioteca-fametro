# Biblioteca FAMETRO

Fundação do backend em Django e Django REST Framework com PostgreSQL. Esta etapa prepara a infraestrutura e a auditoria; não inclui API de negócio, autenticação JWT ou integração TOTVS.

## Desenvolvimento local

Pré-requisitos: Docker com Compose e uma porta local disponível (8000 por padrão). Na raiz do repositório:

```bash
cp infra/.env.example infra/.env
```

Edite `infra/.env`: substitua a chave e a senha de exemplo. Para gerar uma chave aleatória, use `python3 -c 'import secrets; print(secrets.token_urlsafe(50))'`. Os valores do arquivo são apenas para desenvolvimento. Não versione credenciais.

```bash
docker compose --env-file infra/.env -f infra/compose.yaml up -d --build
docker compose --env-file infra/.env -f infra/compose.yaml exec backend python manage.py migrate
docker compose --env-file infra/.env -f infra/compose.yaml exec backend python manage.py check --database default
docker compose --env-file infra/.env -f infra/compose.yaml exec backend python manage.py test tests
docker compose --env-file infra/.env -f infra/compose.yaml exec backend python manage.py makemigrations --check --dry-run
```

O serviço de desenvolvimento escuta em `http://127.0.0.1:8000/` por padrão; altere `BACKEND_PORT` se necessário. Ainda não há rotas de negócio, portanto uma resposta 404 na raiz é esperada. O Compose espera o PostgreSQL estar pronto. Migrações são executadas explicitamente, não automaticamente na inicialização.

```bash
docker compose --env-file infra/.env -f infra/compose.yaml ps
docker compose --env-file infra/.env -f infra/compose.yaml logs backend
docker compose --env-file infra/.env -f infra/compose.yaml down
```

O volume nomeado do PostgreSQL é preservado pelo `down` e pela recriação dos containers. Remover o volume apaga os dados. Se as credenciais do PostgreSQL forem alteradas após a inicialização do volume, a configuração existente do banco deve ser atualizada separadamente.

## Continuidade

`AUTH_USER_MODEL` aponta para `usuarios.Usuario` desde a primeira migração. O modelo mínimo herda `BaseModel` e `AbstractBaseUser`, com e-mail único, senha gerenciada pelo Django e um único `is_active`. A fase 2 deve completar nome, perfil, gerenciador de usuários, permissões, autenticação, serviços e APIs; esses fluxos ainda não estão disponíveis. Os responsáveis da auditoria são opcionais e sua atribuição nas operações será feita pelos serviços futuros. A configuração Compose é para desenvolvimento, não uma configuração de produção.
