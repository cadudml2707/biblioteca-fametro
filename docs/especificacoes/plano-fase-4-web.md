# Plano de execução — Fase 4 do frontend

## Objetivo

Disponibilizar para bibliotecários e administradores a gestão de reservas, retiradas e devoluções pela web. O backend continua sendo a autoridade para permissões, disponibilidade, prazos e transições de estado. A criação de reservas permanece no aplicativo do aluno.

## Estado observado

Há implementação da fase já no workspace: consulta paginada de alunos, identificadores de aluno/obra/exemplar nas respostas, contratos e proxy autenticado, navegação para Reservas e Circulação, listagens com filtros e ações, diálogo de retirada e confirmação de devolução. Também há alterações de backend, documentação e um teste de integração em arquivos modificados ou não rastreados.

As entregas foram revisadas e validadas. O resumo de fases em `docs/tech-spec.md` agora marca a Fase 4 como concluída. A validação incluiu a suíte Django (50 testes), `npm run typecheck` e build de produção. O build padrão com Turbopack encontrou uma falha interna de criação de processo no ambiente; o build com `next build --webpack` concluiu com sucesso.

Na implementação atual, a retirada carrega todas as páginas de alunos e filtra a busca no navegador; as telas também carregam coleções completas para filtrar localmente. Isso mantém compatibilidade com os contratos existentes. Se o volume tornar a carga inicial lenta, a próxima melhoria é usar `search` remoto para alunos e definir paginação compatível para reservas e empréstimos antes de alterar essas respostas.

## Plano por entregas

### 1. Fechar os contratos necessários

- Confirmar `GET /api/v1/alunos` para equipe: pesquisa por nome/e-mail, paginação e campos mínimos (`id`, nome, e-mail e estado), incluindo inativos.
- Confirmar que a resposta de reservas fornece aluno e obra; a resposta de empréstimos fornece aluno, exemplar e título da obra, mantendo os campos anteriores e a resposta usada pelo mobile.
- Confirmar que filtros e ações web correspondem às rotas existentes. Não mudar o formato de paginação de reservas ou empréstimos nesta fase sem especificação compatível.
- Conferir que a consulta não introduz uma consulta por registro e que somente perfis da equipe têm acesso à busca administrativa.

**Pronto quando:** contratos, autorização e compatibilidade estão cobertos pela implementação e pela documentação técnica.

### 2. Fechar clientes e acesso autenticado

- Revisar tipos e clientes para alunos, obras, exemplares, reservas e empréstimos.
- Revisar o encaminhamento server-side: sessão existente, proteção de origem, renovação de sessão, allowlist de rotas e parâmetros; tokens não podem ser enviados ao navegador.
- Confirmar mensagens para erros da API e falhas de rede, sem sugerir repetição cega de ações que possam já ter sido processadas.

**Pronto quando:** chamadas permitidas chegam ao backend com autenticação, e respostas de erro preservam contexto utilizável pela interface.

### 3. Entregar a gestão de reservas

- Exibir aluno, obra, situação e datas relevantes, com filtros por aluno, obra e situação.
- Permitir confirmar reservas solicitadas e cancelar reservas solicitadas ou confirmadas, respeitando o estado atual retornado pelo backend.
- Após sucesso, atualizar os dados e apresentar feedback; cobrir carregamento, erro, lista vazia e falha de ação.

**Pronto quando:** a equipe consegue consultar e executar apenas as transições autorizadas, e a lista reflete o resultado persistido.

### 4. Entregar a circulação

- Exibir histórico de empréstimos com filtros por aluno, exemplar e situação, identificação legível e datas no fuso `America/Manaus`.
- Para retirada, pesquisar alunos por nome/e-mail e permitir selecionar apenas alunos ativos; listar somente exemplares disponíveis de obras ativas.
- Oferecer vínculo opcional somente com reserva ativa, confirmada e compatível com aluno e obra selecionados. O backend deve revalidar todas as condições.
- Confirmar devolução de empréstimos ativos, inclusive quando o aluno ficou inativo ou não há configuração ativa.
- Atualizar o histórico após sucesso e mostrar data prevista ou erros retornados pelo backend.

**Pronto quando:** retirada vinculada e sem reserva, além de devolução, funcionam sem depender de validação exclusivamente no cliente.

### 5. Validar a jornada e concluir a fase

- Percorrer a jornada ponta a ponta: aluno solicita reserva no fluxo já existente, equipe confirma, registra retirada vinculada e devolve; repetir retirada sem reserva.
- Cobrir autorização por perfil, pesquisa/paginação, aluno inativo, exemplar indisponível, reserva incompatível ou vencida, configuração ausente, ações duplicadas, renovação/falha de sessão e falha de rede.
- Verificar teclado e foco nos diálogos, estados de carregamento/erro/vazio, atualização das listas e apresentação de datas.
- Rodar os testes backend relacionados, verificação de tipos e build do frontend; corrigir falhas e registrar os resultados.
- Só então marcar a Fase 4 como concluída no resumo de fases do `docs/tech-spec.md`.

**Pronto quando:** todos os cenários críticos passam, a documentação corresponde ao comportamento entregue e não há pendências bloqueadoras.

## Dependências e limites

- Solicitações, confirmações e retiradas dependem de configuração ativa da biblioteca. A tela de administração da configuração é da Fase 5; devoluções continuam disponíveis sem configuração ativa.
- O backend permanece responsável pela autorização e pelas regras de negócio. Filtros locais podem ajudar a interface, mas não substituem filtros nem validações do servidor.
- Relatórios, sincronização TOTVS e tela de configuração não fazem parte desta fase.

## Encerramento

As operações repetidas foram incluídas na verificação da jornada: confirmar reserva repetidamente é rejeitado pelo backend e a devolução repetida permanece segura. Os filtros e coleções continuam locais na versão atual; acompanhar o volume em uso antes de ampliar os contratos da API.
