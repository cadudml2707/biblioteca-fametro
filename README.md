# Biblioteca FAMETRO

Sistema com frontend Next.js e backend Django/DRF com PostgreSQL. O backend inclui infraestrutura, auditoria e autenticação JWT; catálogo, circulação e integração TOTVS pertencem às próximas fases.

## Desenvolvimento local

Pré-requisitos: Docker com Compose, Make e portas locais disponíveis para o frontend (3000) e o backend (8000). Na raiz do repositório:

```bash
make env
```

Edite `infra/.env`: substitua a chave e a senha de exemplo. Para gerar uma chave aleatória, use `python3 -c 'import secrets; print(secrets.token_urlsafe(50))'`. Os valores do arquivo são apenas para desenvolvimento. Não versione credenciais.

```bash
make up
make migrate
make backend-check
make backend-test
make check-migrations
```

O frontend fica em `http://127.0.0.1:3000/` e a API em `http://127.0.0.1:8000/` por padrão; altere `FRONTEND_PORT` ou `BACKEND_PORT` se necessário. No acesso web, o Next.js se comunica com o backend pela rede interna do Compose. O Compose espera o PostgreSQL estar pronto. Migrações são executadas explicitamente, não automaticamente na inicialização.

```bash
make ps
make logs
make down
```

Use `make help` para listar todos os comandos. Os comandos Django usam os containers em execução. Como o código é copiado para as imagens, execute `make up` novamente após alterações no backend ou frontend. Para rodar testes de tipos do frontend localmente, execute `npm ci` e `npm run typecheck` dentro de `frontend/`. Para usar outro arquivo de ambiente, informe `ENV_FILE`, por exemplo: `make ENV_FILE=/caminho/ambiente.env up`.

O volume nomeado do PostgreSQL é preservado pelo `down` e pela recriação dos containers. Remover o volume apaga os dados. Se as credenciais do PostgreSQL forem alteradas após a inicialização do volume, a configuração existente do banco deve ser atualizada separadamente.

## Continuidade

`AUTH_USER_MODEL` aponta para `usuarios.Usuario` desde a primeira migração. A configuração Compose é destinada ao desenvolvimento. Os campos de auditoria são atribuídos pelo backend nas operações de gestão.


## Usuários e autenticação

Após reconstruir a imagem (`make up`) e aplicar as migrações (`make migrate`), crie o primeiro administrador interativamente:

```bash
docker compose --env-file infra/.env -f infra/compose.yaml exec backend python manage.py criar_admin_inicial
```

O comando solicita nome, e-mail e senha; não coloque a senha na linha de comando. Ele só funciona enquanto não houver administrador. A gestão posterior é feita pela API. Se um banco da fase 1 já contiver usuários, a migração preserva os registros, usa o e-mail como nome inicial e atribui o perfil `ALUNO` (`1`). E-mails duplicados sem distinção de maiúsculas precisam ser corrigidos antes da migração.

A API usa `/api/v1`, sem barra final. Envie JSON e, nas rotas autenticadas, `Authorization: Bearer <access>`. Exemplos de chamadas:

```bash
curl -X POST http://127.0.0.1:8000/api/v1/login \
  -H 'Content-Type: application/json' \
  -d '{"email":"admin@example.org","password":"SENHA","plataforma":"web"}'

curl http://127.0.0.1:8000/api/v1/me -H 'Authorization: Bearer ACCESS_TOKEN'
```

`POST /auth/refresh` recebe `refresh` e retorna novos tokens; `POST /logout` recebe `refresh` e exige Bearer. A administração utiliza `GET/POST /usuarios` e `GET/PATCH /usuarios/{id}`. O contrato completo, as permissões e a política inicial de duração dos tokens estão em [usuários e autenticação](docs/especificacoes/usuarios-autenticacao.md). Para a limpeza periódica de tokens expirados, execute `python manage.py flushexpiredtokens` no container.

## Acesso web

Acesse `http://127.0.0.1:3000` com uma conta de bibliotecário ou administrador. A navegação apresenta as áreas futuras como indisponíveis. Os tokens permanecem em cookies HttpOnly. O Compose é para desenvolvimento local: `AUTH_COOKIE_SECURE=false` permite acesso por HTTP no localhost; em produção, use HTTPS e configure `AUTH_COOKIE_SECURE=true`.
