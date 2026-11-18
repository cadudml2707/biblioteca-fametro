# Biblioteca FAMETRO

Fundação do backend em Django e Django REST Framework com PostgreSQL. Esta etapa prepara a infraestrutura e a auditoria; não inclui API de negócio, autenticação JWT ou integração TOTVS.

## Desenvolvimento local

Pré-requisitos: Docker com Compose, Make e uma porta local disponível (8000 por padrão). Na raiz do repositório:

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

O serviço de desenvolvimento escuta em `http://127.0.0.1:8000/` por padrão; altere `BACKEND_PORT` se necessário. Ainda não há rotas de negócio, portanto uma resposta 404 na raiz é esperada. O Compose espera o PostgreSQL estar pronto. Migrações são executadas explicitamente, não automaticamente na inicialização.

```bash
make ps
make logs
make down
```

Use `make help` para listar todos os comandos. Os comandos Django usam os containers em execução. Como o código é copiado para a imagem, execute `make up` novamente após alterações no backend. Para usar outro arquivo de ambiente, informe `ENV_FILE`, por exemplo: `make ENV_FILE=/caminho/ambiente.env up`.

O volume nomeado do PostgreSQL é preservado pelo `down` e pela recriação dos containers. Remover o volume apaga os dados. Se as credenciais do PostgreSQL forem alteradas após a inicialização do volume, a configuração existente do banco deve ser atualizada separadamente.

## Continuidade

`AUTH_USER_MODEL` aponta para `usuarios.Usuario` desde a primeira migração. O modelo mínimo herda `BaseModel` e `AbstractBaseUser`, com e-mail único, senha gerenciada pelo Django e um único `is_active`. A fase 2 deve completar nome, perfil, gerenciador de usuários, permissões, autenticação, serviços e APIs; esses fluxos ainda não estão disponíveis. Os responsáveis da auditoria são opcionais e sua atribuição nas operações será feita pelos serviços futuros. A configuração Compose é para desenvolvimento, não uma configuração de produção.
