# Tech Spec

**Sistema da Biblioteca FAMETRO**

## Data Model (Diagram)

```mermaid
erDiagram
    direction TB

    usuarios {
        integer id PK
        varchar nome
        varchar email UK
        varchar password
        varchar perfil
        boolean is_active
        timestamp created_at
        integer created_by FK "nullable"
        timestamp updated_at
        integer updated_by FK "nullable"
    }

    obras {
        integer id PK
        varchar titulo
        varchar autor
        varchar isbn "nullable"
        varchar editora "nullable"
        integer ano_publicacao "nullable"
        varchar id_totvs UK "nullable"
        boolean is_active
        timestamp created_at
        integer created_by FK "nullable"
        timestamp updated_at
        integer updated_by FK "nullable"
    }

    exemplares {
        integer id PK
        integer obra_id FK
        varchar codigo UK
        varchar situacao
        varchar id_totvs UK "nullable"
        boolean is_active
        timestamp created_at
        integer created_by FK "nullable"
        timestamp updated_at
        integer updated_by FK "nullable"
    }

    reservas {
        integer id PK
        integer usuario_id FK
        integer obra_id FK
        timestamp data_reserva
        varchar situacao
        timestamp confirmada_em "nullable"
        timestamp data_limite "nullable"
        timestamp encerrada_em "nullable"
        boolean is_active
        timestamp created_at
        integer created_by FK "nullable"
        timestamp updated_at
        integer updated_by FK "nullable"
    }

    emprestimos {
        integer id PK
        integer usuario_id FK
        integer exemplar_id FK
        integer reserva_id FK,UK "nullable"
        timestamp data_retirada
        date data_prevista
        timestamp data_devolucao "nullable"
        boolean is_active
        timestamp created_at
        integer created_by FK "nullable"
        timestamp updated_at
        integer updated_by FK "nullable"
    }

    configuracao_biblioteca {
        integer id PK
        integer limite_reservas_ativas
        integer limite_emprestimos_ativos
        integer prazo_emprestimo_dias
        integer prazo_retirada_reserva_dias
        boolean is_active
        timestamp created_at
        integer created_by FK "nullable"
        timestamp updated_at
        integer updated_by FK "nullable"
    }

    usuarios ||--o{ reservas : solicita
    usuarios ||--o{ emprestimos : retira
    obras ||--o{ exemplares : possui
    obras ||--o{ reservas : recebe
    exemplares ||--o{ emprestimos : circula
    reservas |o--o| emprestimos : origina
```

**Notes**

- Os IDs são gerados pelo Django com `AutoField`. As chaves primárias e estrangeiras são representadas como `integer`. Definir `DEFAULT_AUTO_FIELD = "django.db.models.AutoField"` e alinhar o `default_auto_field` dos AppConfig que tiverem configuração própria.
- Todas as models de domínio herdam de `BaseModel`, localizada em `backend/core/base_model.py`. Ela é uma classe base abstrata, com `Meta.abstract = True`, que compartilha campos sem gerar tabela própria.
- Os campos herdados por todas as models são exatamente `is_active`, `created_at`, `created_by`, `updated_at` e `updated_by`.
- `created_at` e `updated_at` são preenchidos pelo backend. `created_by` e `updated_by` são referências ao usuário responsável pela operação, também preenchidas pelo backend. Os relacionamentos de auditoria apontam para `usuarios` e podem ser nulos no cadastro inicial do administrador ou em operações técnicas sem usuário autenticado.
- A criação mantém `created_by` e `created_at`. As alterações atualizam `updated_by` e `updated_at`. Os clientes recebem esses campos como somente leitura.
- `is_active` controla a desativação lógica. O backend preserva o histórico e impede desativar um empréstimo ativo para contornar a devolução.
- O usuário customizado herda os campos comuns e utiliza a autenticação do Django. `password` armazena o hash gerenciado pelo Django. `is_active` é um único campo compartilhado com essa autenticação.
- Somente `obras` e `exemplares` recebem dados do TOTVS e possuem `id_totvs`. O campo é opcional, nulo quando não existe vínculo e único quando preenchido.
- Usuários, reservas, empréstimos e configuração são mantidos pelo próprio sistema. A sincronização consulta a API TOTVS para cadastrar ou atualizar exclusivamente obras e exemplares.
- `obras` representa o cadastro bibliográfico. `exemplares` representa cada unidade física, com código único e situação própria.
- A reserva pertence à obra e pode ser solicitada mesmo sem exemplar disponível. O exemplar é identificado na retirada.
- Uma reserva ativa por aluno e obra e um empréstimo ativo por exemplar devem ser protegidos por restrições de unicidade e transações no backend.
- `reserva_id` no empréstimo é opcional e vincula a retirada ao pedido atendido. O backend valida a correspondência de aluno e obra.
- Os prazos e limites ficam em uma configuração ativa da biblioteca e são aplicados pelo backend. Seus valores devem ser definidos com a biblioteca.
- As datas utilizam o suporte de fuso horário do Django, com apresentação em `America/Manaus`. Os nomes distintos de auditoria para cada model são definidos na classe abstrata para evitar colisões de relacionamentos.

**Access profiles**

- `ALUNO` utiliza o aplicativo mobile para consultar o catálogo, solicitar reserva e acompanhar suas próprias reservas.
- `BIBLIOTECARIO` utiliza o web para gerenciar obras, exemplares, reservas, retiradas, devoluções e relatórios.
- `ADMINISTRADOR` utiliza o web para administrar usuários, parâmetros, sincronização TOTVS e as operações de gestão.

**Valores de `situacao`**

- Em `exemplares`, `DISPONIVEL` ou `EMPRESTADO`. A desativação utiliza `is_active`.
- Em `reservas`, os valores propostos são `SOLICITADA`, `CONFIRMADA`, `ATENDIDA` e `CANCELADA`. As transições são validadas e executadas pelo backend.

## Architecture

Monólito Django/DRF com um app separado para cada model de domínio. O backend é responsável por toda a lógica de negócio, validação de dados, autorização, consultas, filtros, cálculos e processamento.

O web Next.js e o mobile React Native coletam os dados informados pelo usuário, enviam requisições e apresentam os dados, as ações permitidas e as mensagens retornadas pela API. Toda validação e regra de negócio é executada no backend.

Cada app contém sua model em `models.py` e os arquivos correspondentes `serializers.py`, `views.py` e `services.py`. Os arquivos `apps.py`, `urls.py` e a pasta `migrations/` completam a estrutura do app. A organização das responsabilidades segue o padrão abaixo.

- **Models** contêm os campos, relacionamentos e restrições de integridade do ORM.
- **Serializers** definem os dados de entrada e saída e validam sua estrutura no backend.
- **Views/APIs** recebem as requisições, verificam a autenticação, acionam os serviços e retornam as respostas.
- **Services** aplicam regras e permissões de negócio, executam consultas e cálculos, controlam transações, processam os dados e realizam a sincronização TOTVS.

`BaseModel` é compartilhada por todas as models de domínio. A implementação usa a classe abstrata do Django para que os campos sejam herdados pelas tabelas concretas.

```text
biblioteca-fametro/
├── backend/                                           # Django e DRF
│   ├── core/                                          # Código compartilhado
│   │   └── base_model.py                              # BaseModel abstrata com os cinco campos comuns
│   ├── config/                                        # Settings e URLs do projeto
│   ├── apps/                                          # Um app para cada model
│   │   ├── usuarios/                                  # Usuario, autenticação e permissões
│   │   │   ├── apps.py                                # Configuração do app
│   │   │   ├── models.py                              # Model do domínio com herança de BaseModel
│   │   │   ├── serializers.py                         # Entrada e saída da API
│   │   │   ├── views.py                               # Requisições e respostas HTTP
│   │   │   ├── services.py                            # Lógica, validações e processamento
│   │   │   ├── urls.py                                # Rotas da API
│   │   │   └── migrations/                            # Migrações do app
│   │   ├── obras/                                     # Obra e dados TOTVS opcionais
│   │   │   ├── apps.py                                # Configuração do app
│   │   │   ├── models.py                              # Model do domínio com herança de BaseModel
│   │   │   ├── serializers.py                         # Entrada e saída da API
│   │   │   ├── views.py                               # Requisições e respostas HTTP
│   │   │   ├── services.py                            # Lógica, validações e processamento
│   │   │   ├── urls.py                                # Rotas da API
│   │   │   └── migrations/                            # Migrações do app
│   │   ├── exemplares/                                # Exemplar e dados TOTVS opcionais
│   │   │   ├── apps.py                                # Configuração do app
│   │   │   ├── models.py                              # Model do domínio com herança de BaseModel
│   │   │   ├── serializers.py                         # Entrada e saída da API
│   │   │   ├── views.py                               # Requisições e respostas HTTP
│   │   │   ├── services.py                            # Lógica, validações e processamento
│   │   │   ├── urls.py                                # Rotas da API
│   │   │   └── migrations/                            # Migrações do app
│   │   ├── reservas/                                  # Reserva
│   │   │   ├── apps.py                                # Configuração do app
│   │   │   ├── models.py                              # Model do domínio com herança de BaseModel
│   │   │   ├── serializers.py                         # Entrada e saída da API
│   │   │   ├── views.py                               # Requisições e respostas HTTP
│   │   │   ├── services.py                            # Lógica, validações e processamento
│   │   │   ├── urls.py                                # Rotas da API
│   │   │   └── migrations/                            # Migrações do app
│   │   ├── emprestimos/                               # Emprestimo
│   │   │   ├── apps.py                                # Configuração do app
│   │   │   ├── models.py                              # Model do domínio com herança de BaseModel
│   │   │   ├── serializers.py                         # Entrada e saída da API
│   │   │   ├── views.py                               # Requisições e respostas HTTP
│   │   │   ├── services.py                            # Lógica, validações e processamento
│   │   │   ├── urls.py                                # Rotas da API
│   │   │   └── migrations/                            # Migrações do app
│   │   └── configuracao_biblioteca/                   # ConfiguracaoBiblioteca
│   │       ├── apps.py                                # Configuração do app
│   │       ├── models.py                              # Model do domínio com herança de BaseModel
│   │       ├── serializers.py                         # Entrada e saída da API
│   │       ├── views.py                               # Requisições e respostas HTTP
│   │       ├── services.py                            # Lógica, validações e processamento
│   │       ├── urls.py                                # Rotas da API
│   │       └── migrations/                            # Migrações do app
│   ├── integracoes/                                   # Comunicação externa
│   │   └── totvs.py                                   # Cliente da API para obras e exemplares
│   └── manage.py
├── frontend/                                          # Next.js para bibliotecário e administrador
│   └── src/
│       ├── app/                                       # App Router
│       │   ├── (auth)/login/                          # Login da gestão
│       │   └── (app)/
│       │       ├── obras/                             # Cadastro de livros
│       │       ├── exemplares/                        # Cadastro e disponibilidade
│       │       ├── usuarios/                          # Administração de usuários
│       │       ├── reservas/                          # Gerenciamento de reservas
│       │       ├── circulacao/                        # Retiradas e devoluções
│       │       ├── relatorios/                        # Resultados calculados pelo backend
│       │       └── configuracoes/                     # Parâmetros e sincronização TOTVS
│       ├── components/                                # Componentes de apresentação
│       ├── lib/api/                                   # Clientes HTTP tipados
│       └── types/                                     # Tipos das respostas da API
├── infra/                                             # Dockerfiles, Docker Compose e configurações de ambiente
├── docs/                                              # SDD
│   ├── TechSpec_Biblioteca_FAMETRO.md
│   ├── especificacoes/                                # Regras, contratos e critérios de aceitação
│   ├── tarefas/                                       # Tarefas derivadas das especificações
│   └── decisoes/                                      # Decisões técnicas
├── mobile/                                            # React Native para o aluno, desenvolvido depois do web
│   └── src/
│       ├── screens/
│       │   ├── LoginScreen.tsx
│       │   ├── CatalogoScreen.tsx
│       │   ├── DetalheObraScreen.tsx
│       │   └── MinhasReservasScreen.tsx
│       ├── components/                                # Componentes de apresentação
│       ├── services/                                  # API e sessão
│       └── types/                                     # Tipos das respostas da API
└── README.md
```

```mermaid
flowchart TB
    WEB["Web Next.js"]
    MOBILE["Mobile React Native"]
    BACKEND["Backend Django e DRF"]
    DB["PostgreSQL"]
    TOTVS["API TOTVS"]

    WEB -->|"Requisições e respostas"| BACKEND
    MOBILE -->|"Requisições e respostas"| BACKEND
    BACKEND -->|"Consultas e persistência"| DB
    BACKEND -->|"Sincronização de obras e exemplares"| TOTVS
```

Na sincronização, o administrador aciona o backend pelo web. O serviço consulta a API TOTVS, valida o retorno, identifica obras e exemplares existentes, cria ou atualiza os cadastros e retorna o resultado. O cadastro manual e as operações locais funcionam independentemente dessa integração.

No fluxo de reserva, o backend identifica o aluno autenticado, verifica limite e duplicidade e registra a solicitação. Na retirada, valida aluno e exemplar, cria o empréstimo, atualiza a disponibilidade e encerra a reserva vinculada. Na devolução, encerra o empréstimo e libera o exemplar. O backend executa as alterações relacionadas dentro de uma transação.

Os formulários do web e do mobile enviam os dados para a API. O backend retorna os erros de campo, as mensagens e o resultado das operações. A disponibilidade, os prazos, os totais dos relatórios e as permissões apresentados nas interfaces são fornecidos pelo backend.

## Stack

### Frontend

- **Web** Next.js com App Router e TypeScript.
- **Mobile** React Native e TypeScript para Android e iOS.
- **Perfis do web** Bibliotecário e administrador.
- **Perfil do mobile** Aluno.
- **Responsabilidade** Coletar entradas, chamar a API e apresentar suas respostas. Regras, validações e processamento pertencem ao backend.

### Backend

- **Linguagem** Python.
- **Framework** Django e Django REST Framework.
- **Arquitetura** Monólito com um app por model e camada de serviço dentro de cada app.
- **Classe base** `BaseModel`, abstrata, com os campos herdados por todas as models de domínio.
- **IDs** `AutoField` do Django e relacionamentos inteiros.

### API & Communication

- **Protocolo** REST.
- **Formato** JSON.
- **Autenticação** JWT com Simple JWT.
- **Autorização** Verificada no backend em cada operação.
- **TOTVS** Consulta opcional pelo backend, exclusivamente para obras e exemplares.

### Data & Persistence

- **Banco** PostgreSQL.
- **ORM** Django ORM.
- **Migrações** Django migrations.
- **Persistência** Transações e restrições aplicadas pelo backend e pelo banco.

### Infrastructure

- **Containers** Docker.
- **Orquestração** Docker Compose para web, backend e PostgreSQL.
- **Repositório** Monorepo com `backend`, `frontend`, `infra`, `docs` e `mobile`.
- **Especificações** Markdown em `docs`, orientando o desenvolvimento com SDD.

## Risks & Mitigation

| Risco | Impacto | Mitigação |
|---|---|---|
| TOTVS indisponível ou integração desativada | A sincronização de obras e exemplares fica indisponível. | Manter cadastro manual e operação com a base própria. Informar a falha sem comprometer os registros locais. |
| Duplicidade na sincronização | Uma obra ou exemplar pode ser cadastrado novamente. | Identificar pelo `id_totvs`. Para exemplares, validar também o código único. Vincular explicitamente obras locais quando a correspondência for ambígua. |
| Falha durante a gravação de um lote | A importação pode produzir dados parciais. | Validar o retorno antes da gravação e aplicar as alterações do lote em uma transação. |
| Retiradas simultâneas | Um exemplar pode ser emprestado mais de uma vez. | Bloquear o exemplar durante a transação e manter restrição de um empréstimo ativo por exemplar. |
| Reservas simultâneas acima do limite | O aluno pode exceder o limite permitido. | Verificar limite e duplicidade no backend, com transação e bloqueio do registro do aluno. |
| Acesso indevido do aluno | Exposição de reservas de terceiros ou execução de gerenciamento. | Filtrar dados pela identidade autenticada e verificar o perfil e a propriedade no backend. |
| Divergência entre web e mobile | Regras e resultados podem variar entre interfaces. | Centralizar integralmente regras, validações, cálculos e processamento no backend. |
| Prazos e limites pendentes | O comportamento pode divergir da rotina da biblioteca. | Manter os parâmetros no banco e validá-los com a biblioteca antes de sua utilização operacional. |

## Implementation Plan

### Backend Implementation Plan

- [ ] **Phase 1 — Core & Infrastructure** Criar Django/DRF, PostgreSQL e Docker Compose. Configurar `AutoField` e implementar a classe abstrata `BaseModel` com `is_active`, `created_at`, `created_by`, `updated_at` e `updated_by`.
- [ ] **Phase 2 — Users & Authentication** Criar o app de usuários com sua model, serializers, views e services. Implementar usuário customizado com herança de BaseModel, autenticação JWT, perfis e administração local.
- [ ] **Phase 3 — Catalog** Criar apps separados para obras e exemplares, cada um com sua model, serializers, views e services. Implementar herança de BaseModel, cadastros locais, busca, disponibilidade e campos TOTVS opcionais.
- [ ] **Phase 4 — Reservations & Settings** Criar apps separados para reservas e configuração da biblioteca, cada um com sua model, serializers, views e services. Aplicar limite, duplicidade, propriedade e transições de situação nos serviços do backend.
- [ ] **Phase 5 — Circulation** Criar o app de empréstimos com sua model, serializers, views e services. Centralizar retirada, devolução, cálculo de prazo, vínculo com reserva e atualização da disponibilidade nos serviços do backend.
- [ ] **Phase 6 — Reports** Implementar consultas, filtros, agrupamentos e cálculos dos relatórios no backend.
- [ ] **Phase 7 — TOTVS Sync** Implementar a consulta à API e o processamento exclusivo de obras e exemplares, com identificação dos registros e gravação transacional.
- [ ] **Phase 8 — Verification** Verificar permissões, auditoria dos campos comuns, integridade das operações e funcionamento independente do TOTVS.

### Frontend Implementation Plan

Concluir o backend e o web antes de iniciar a implementação do mobile.

- [ ] **Phase 1 — Web Setup & Auth** Preparar Next.js com TypeScript, login e apresentação da navegação fornecida pelo perfil autenticado.
- [ ] **Phase 2 — Web Layout & API Clients** Criar componentes de apresentação e clientes HTTP para consumir o backend.
- [ ] **Phase 3 — Web Management** Criar telas de usuários, obras e exemplares. Enviar os formulários e apresentar resultados e erros da API.
- [ ] **Phase 4 — Web Reservations & Circulation** Criar telas de gerenciamento de reservas, retirada e devolução, consumindo as operações do backend.
- [ ] **Phase 5 — Web Reports & Settings** Exibir relatórios calculados pelo backend, editar os parâmetros e acionar a sincronização de obras e exemplares.
- [ ] **Phase 6 — Backend & Web Acceptance** Conferir os fluxos de gerenciamento e os contratos da API antes do mobile.
- [ ] **Phase 7 — Mobile Setup & Catalog** Preparar React Native para Android e iOS, login do aluno, catálogo e detalhes das obras consumindo a API.
- [ ] **Phase 8 — Mobile Reservations** Criar solicitação e acompanhamento das próprias reservas. Exibir as situações, mensagens e erros retornados pelo backend.
- [ ] **Phase 9 — Final Verification** Conferir os fluxos em web, Android e iOS e a correspondência das interfaces com os resultados do backend.

Antes de cada funcionalidade, registrar em `docs` a especificação e os critérios de aceitação, derivar as tarefas, implementar e verificar o resultado. Atualizar a especificação quando houver mudança.
