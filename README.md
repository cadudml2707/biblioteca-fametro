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

O `make up` inicia o frontend com atualização automática: mudanças em `frontend/src` e `frontend/public` aparecem no navegador sem reconstruir a imagem. Mudanças nas dependências (`package.json` ou `package-lock.json`) exigem executar `make up` novamente; mudanças em arquivos de configuração podem exigir reiniciar o frontend com o mesmo comando.

O frontend fica em `http://127.0.0.1:3000/` e a API em `http://127.0.0.1:8000/` por padrão; altere `FRONTEND_PORT` ou `BACKEND_PORT` se necessário. No acesso web, o Next.js se comunica com o backend pela rede interna do Compose. O Compose espera o PostgreSQL estar pronto. Migrações são executadas explicitamente, não automaticamente na inicialização.

Para acessar o site em um celular na mesma rede, configure `FRONTEND_BIND_ADDRESS=0.0.0.0` em `infra/.env` e recrie os serviços com `make up`. Abra `http://IP_DO_COMPUTADOR:3000` no celular, substituindo pelo IP da interface de rede do computador. A porta deve estar liberada no firewall; em WSL, a configuração de rede do Windows pode exigir encaminhamento adicional. Essa configuração expõe o frontend à rede local e destina-se ao desenvolvimento. Para voltar ao acesso local, use `127.0.0.1` e execute `make up` novamente.

```bash
make ps
make logs
make down
```

Use `make help` para listar todos os comandos. Os comandos Django usam os containers em execução. O código do backend é copiado para a imagem; execute `make up` novamente após alterá-lo. Para rodar testes de tipos do frontend localmente, execute `npm ci` e `npm run typecheck` dentro de `frontend/`. Para usar outro arquivo de ambiente, informe `ENV_FILE`, por exemplo: `make ENV_FILE=/caminho/ambiente.env up`.

O volume nomeado do PostgreSQL é preservado pelo `down` e pela recriação dos containers. Remover o volume apaga os dados. Se as credenciais do PostgreSQL forem alteradas após a inicialização do volume, a configuração existente do banco deve ser atualizada separadamente.

## Backend no Render com banco Neon

Crie um Web Service Python para este repositório e selecione a branch que contém as alterações de deploy. Configure:

- **Root Directory:** `backend`
- **Build Command:** `pip install -r requirements.txt`
- **Start Command:** `python manage.py migrate --noinput && gunicorn config.wsgi:application --bind 0.0.0.0:$PORT`

O comando de inicialização aplica as migrações antes de iniciar o servidor. Configure um único processo de implantação para aplicar migrações em ambientes com várias instâncias; para uso inicial em uma instância, o comando acima também funciona em planos sem acesso ao shell. Migrations alteram o banco apontado pelas variáveis do serviço.

Em **Environment**, defina `DJANGO_SECRET_KEY` com uma chave aleatória, `DJANGO_DEBUG=false` e `DJANGO_ALLOWED_HOSTS` com o domínio do serviço no Render, sem protocolo. Configure `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_HOST` e `POSTGRES_PORT` com os dados do Neon. Defina `PGSSLMODE=require` para exigir TLS na conexão PostgreSQL. Não compartilhe nem versione a senha do banco ou a chave Django.

Na Vercel, configure `BACKEND_API_URL` com a URL HTTPS do serviço Render, sem `/api/v1`, e `AUTH_COOKIE_SECURE=true`. Após alterar variáveis da Vercel, faça um novo deploy.

Para criar o primeiro administrador sem shell no Render, adicione temporariamente as variáveis `ADMIN_INICIAL_NOME`, `ADMIN_INICIAL_EMAIL` e `ADMIN_INICIAL_SENHA` ao serviço. Use uma senha forte e mantenha-a privada. Durante essa inicialização, configure o Start Command como:

```bash
python manage.py migrate --noinput && python manage.py criar_admin_inicial --ambiente && gunicorn config.wsgi:application --bind 0.0.0.0:$PORT
```

O comando cria a conta somente se não houver administrador. Após confirmar o acesso, remova as três variáveis e volte ao Start Command anterior; se não houver variáveis configuradas, o comando não cria conta. A senha é validada pelas regras do Django e não aparece nos logs. O comando também está disponível interativamente por `python manage.py criar_admin_inicial` em um ambiente autorizado conectado ao banco de produção.

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
