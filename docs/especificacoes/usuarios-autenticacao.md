# Fase 2 — Usuários e autenticação

## Escopo e contratos

A API usa JSON e prefixo `/api/v1`. O campo `perfil` é numérico: `1` para `ALUNO` (Aluno), `2` para `BIBLIOTECARIO` (Bibliotecário) e `3` para `ADMINISTRADOR` (Administrador). As rotas não têm barra final. Todos os erros têm `codigo`, `mensagem` e, para erros de validação, `erros` com detalhes por campo. Senhas e tokens nunca são retornados em cadastros ou consultas de usuários.

- `POST /login`: recebe `email`, `password` e `plataforma` (`web` ou `mobile`); retorna `access`, `refresh` e `usuario` com `id`, `nome` e `perfil`. Mobile aceita somente `ALUNO`; web aceita `ALUNO`, `BIBLIOTECARIO` e `ADMINISTRADOR`, com permissões de acordo com o perfil.
- `POST /auth/refresh`: recebe `refresh` válido, retorna novos `access` e `refresh` e revoga o refresh anterior. Retentativas com token revogado são recusadas. A plataforma original e o perfil atual devem continuar compatíveis.
- `POST /logout`: recebe `refresh` pertencente ao usuário autenticado e o revoga; responde 204. A revogação de refresh não revoga access já emitido, que expira em até 15 minutos. Desativação ou alteração incompatível de perfil bloqueia access na próxima requisição.
- `GET /me`: com Bearer válido, retorna `id`, `nome`, `email` e `perfil` atuais.
- `GET/POST /usuarios` e `GET/PATCH /usuarios/{id}`: somente administrador. A criação recebe `nome`, `email`, `perfil` e `password`; alteração aceita esses campos e `is_active`. Auditoria e ID são somente leitura. Não há exclusão física.

O access dura 15 minutos e o refresh 7 dias, com rotação e blacklist. Esses valores são decisões iniciais de desenvolvimento. Usuários inativos não autenticam nem renovam tokens. O backend consulta a situação e perfil atuais em cada requisição autenticada. O primeiro administrador é criado por comando administrativo local interativo, apenas quando não existe administrador, sem senha em argumentos. Alterar o próprio perfil ou desativar a própria conta pela API é recusado.

E-mail é normalizado para minúsculas e único sem distinção de caixa; nome e senha são obrigatórios na criação e senhas devem respeitar os validadores do Django. Migração preserva usuários existentes preenchendo nome a partir do e-mail e perfil inicial `ALUNO`; colisões de e-mail sem distinção de caixa devem ser resolvidas antes da migração.

## Critérios de aceitação

- Login, refresh rotativo, logout, identidade e gestão respeitam as permissões e contratos acima.
- Senha é armazenada em hash e não aparece nas respostas; alterações de auditoria são atribuídas ao usuário autenticado, sem permitir sua alteração pelo cliente.
- Token expirado, inválido, revogado, de outra conta ou de usuário inativo é recusado; refresh concorrente não gera duas sessões sucessoras para um mesmo token.
- Migrações funcionam em banco limpo e banco da fase 1; testes cobrem autorização, plataforma, tokens, auditoria, validações e bootstrap.
