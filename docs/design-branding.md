# Identidade visual — Biblioteca FAMETRO

## Direção

**Uma biblioteca contemporânea, clara e confiável.** A interface combina o azul institucional com superfícies luminosas, tipografia expressiva e detalhes discretos que remetem a livros e organização do conhecimento. A prioridade é facilitar o trabalho diário da equipe e a descoberta do acervo pelo aluno.

A proposta parte da observação do portal FAMETRO: marca azul e vermelha sobre branco, navegação lateral azul, atalhos em turquesa e áreas de consulta com filtros. O mural usa peças promocionais de cores intensas; para a biblioteca, a identidade mantém a ligação institucional e usa composição mais tranquila, com hierarquia e espaço para leitura. Os hexadecimais abaixo são **propostos**, não uma extração oficial da marca. Usar o arquivo oficial da FAMETRO, sem redesenhar ou alterar suas proporções, quando disponibilizado.

## Paleta proposta

### Marca

| Token | Uso | Hex |
|---|---|---|
| `brand-primary` | Azul institucional, ações principais | `#07549B` |
| `brand-primary-dark` | Sidebar e hover do botão principal | `#07386C` |
| `brand-primary-light` | Seleção e fundos suaves | `#E8F1FA` |
| `brand-accent` | Turquesa de destaque e elementos gráficos | `#087E8B` |
| `brand-accent-dark` | Texto de destaque e hover | `#06636D` |
| `brand-accent-light` | Fundos de destaque | `#E0F4F3` |
| `brand-red` | Referência pontual ao vermelho da marca | `#C82736` |

O azul domina a identidade. O turquesa orienta detalhes e descobertas; o vermelho institucional aparece pontualmente e não é o único indicador de erro. Não usar turquesa claro ou vermelho em grandes áreas decorativas.

### Neutros

| Token | Uso | Hex |
|---|---|---|
| `background` | Fundo geral | `#F5F8FC` |
| `surface` | Cards, tabelas e diálogos | `#FFFFFF` |
| `surface-soft` | Áreas secundárias | `#EDF3F8` |
| `border` | Divisores e contornos | `#D4DFEA` |
| `text-primary` | Texto principal | `#142C42` |
| `text-secondary` | Texto secundário e auxiliar | `#52697D` |
| `text-inverse` | Texto sobre azul escuro | `#FFFFFF` |

### Cores semânticas

| Token | Uso | Texto/ícone | Fundo suave |
|---|---|---|---|
| `success` | Disponível, concluído | `#176B45` | `#E4F4EB` |
| `warning` | Atenção, prazo próximo | `#805000` | `#FFF2D6` |
| `danger` | Erro, atraso, ação destrutiva | `#B42332` | `#FDEBED` |
| `info` | Informações e situação em andamento | `#07549B` | `#E8F1FA` |

Sempre apresentar status com texto e, quando útil, ícone; cor isolada não comunica significado. Texto semântico usa a cor escura sobre o fundo suave, nunca branco sobre amarelo.

## Hierarquia visual

1. **Estrutura institucional:** sidebar `#07386C`, marca oficial sobre fundo apropriado e indicadores de navegação claros.
2. **Ação principal:** fundo `#07549B`, texto branco e hover `#07386C`. Uma ação principal por região ou etapa.
3. **Destaque editorial:** turquesa `#087E8B` em detalhes, links e indicadores, com uso moderado.
4. **Conteúdo:** fundo `#F5F8FC`, superfícies brancas, divisores discretos e títulos `#142C42`.

### Tipografia

- **Títulos:** Plus Jakarta Sans, pesos 600–700; títulos de página em 28–32 px, seção em 20–24 px. Sua geometria dá personalidade sem competir com o acervo.
- **Interface e leitura:** Source Sans 3, 16 px e entrelinha de 1,5; rótulos e metadados em 14 px, com peso 600 quando necessário.
- **Alternativas:** `system-ui, sans-serif`; garantir carregamento com fallback e sem bloquear o conteúdo. No mobile, respeitar o tamanho de texto configurado pelo usuário.
- Usar números tabulares para prazos, códigos e contadores. Evitar textos longos em caixa alta.

### Ritmo e superfícies

- Escala de espaçamento: 4, 8, 12, 16, 24, 32 e 48 px; conteúdo de página com 24–32 px em desktop e 16 px em telas pequenas.
- Raio padrão de 10 px para campos e botões; 14 px para cards e diálogos; badges em formato de cápsula.
- Borda de 1 px e sombra leve `0 4px 16px rgba(20, 44, 66, 0.06)` em superfícies elevadas. Evitar sombras pesadas e excesso de cards.
- Ícones Lucide em traço consistente, 18–20 px na interface e 24 px em destaques; sempre rotular ações que dependam apenas de ícone.
- Movimento funcional de 150–200 ms para foco, hover e abertura; respeitar `prefers-reduced-motion` e as preferências nativas de redução de movimento.

## Aplicação prática

### Web de gestão

- **Sidebar:** fundo `#07386C`, texto branco, item ativo `#14558F` com indicador turquesa claro `#7FE2E3`; exibir ícone e nome. Recolher em telas menores sem esconder o acesso à navegação.
- **Header:** branco, borda inferior `#D4DFEA`, título escuro, identificação do usuário e ações contextuais. Em telas internas, priorizar título, descrição curta e ação principal.
- **Botão primário:** azul `#07549B`, texto branco, hover `#07386C`; altura mínima de 44 px. Secundário branco, texto azul e borda `#D4DFEA`; destrutivo com confirmação quando a operação exigir.
- **Campos e filtros:** rótulo permanente acima do campo, ajuda e erro ao lado do contexto; foco visível em azul, sem depender de placeholder. Filtros próximos à lista e opção clara de limpar.
- **Tabelas:** cabeçalho suave, linhas com bom espaçamento, alinhamento de datas e números, ações identificadas e paginação. Em telas estreitas, preservar acesso a todas as colunas com rolagem identificável ou apresentação adaptada.
- **Cards:** usar para resumos, não para embrulhar cada elemento. Indicadores mostram título, número e contexto; relatórios favorecem tabelas e gráficos legíveis.
- **Estados:** carregamento, vazio, erro e ausência de resultados devem explicar o que aconteceu e oferecer ação pertinente. Exibir confirmação somente após resposta da API.

### Mobile do aluno

- As abas **Catálogo** e **Minhas reservas** mantêm rótulos visíveis e indicam a aba ativa em azul. Respeitar áreas seguras e navegação nativa.
- Catálogo com busca evidente, lista de obras e disponibilidade textual fornecida pela API; capas são opcionais e têm substituto visual neutro.
- Detalhe da obra prioriza título, autor, disponibilidade e ação de reservar quando permitida. Durante o envio, mostrar progresso e impedir repetição.
- Reservas mostram obra, situação e datas da API, com atualização acessível. Feedback de rede e recuperação de sessão seguem o tech-spec.
- Alvos de toque de pelo menos 44 × 44 pt no iOS e 48 × 48 dp no Android, com espaçamento suficiente; suportar leitor de tela e ampliação do texto.

## Badges e situações da biblioteca

| Situação | Tratamento | Observação |
|---|---|---|
| Exemplar disponível | Sucesso | `DISPONIVEL` |
| Exemplar emprestado | Informação | `EMPRESTADO`; não implica atraso |
| Reserva solicitada | Informação | `SOLICITADA` |
| Reserva confirmada | Sucesso | `CONFIRMADA`; apresentar prazo quando fornecido |
| Reserva atendida | Neutro | `ATENDIDA` |
| Reserva cancelada | Neutro | `CANCELADA`; não presumir erro |
| Empréstimo em atraso | Erro | Indicador derivado e fornecido pelo backend; não cria novo status no modelo |
| Prazo próximo | Aviso | Exibir apenas se calculado e informado pelo backend |

## Acessibilidade e responsividade

- Texto normal: contraste mínimo 4,5:1; texto grande e indicadores gráficos relevantes: 3:1. Validar cada combinação real, inclusive hover, foco e estados desabilitados.
- Foco de teclado visível de pelo menos 2 px, ordem lógica, rótulos acessíveis, link para pular ao conteúdo e navegação completa por teclado na web.
- Não transmitir disponibilidade ou erro apenas por cor. Mensagens de erro devem identificar o campo e orientar a correção.
- Projetar a partir de 375 px, sem corte de conteúdo; aumentar margens e densidade gradualmente. Evitar rolagem horizontal da página.
- Tema claro é o escopo inicial; um tema escuro requer tokens próprios e verificação de contraste, sem inversão automática.

## Tokens CSS — shadcn/ui e Tailwind CSS v4

Os nomes semânticos seguem o modelo do shadcn/ui. `accent` representa uma superfície de interação suave, enquanto `brand-accent` é a cor turquesa da identidade. O exemplo usa `@theme inline` do Tailwind v4; se o projeto adotar outra versão, adaptar a integração ao formato correspondente.

```css
@import "tailwindcss";

:root {
  --brand-primary: #07549B;
  --brand-primary-dark: #07386C;
  --brand-primary-light: #E8F1FA;
  --brand-accent: #087E8B;
  --brand-accent-dark: #06636D;
  --brand-accent-light: #E0F4F3;
  --brand-red: #C82736;

  --background: #F5F8FC;
  --foreground: #142C42;
  --card: #FFFFFF;
  --card-foreground: #142C42;
  --popover: #FFFFFF;
  --popover-foreground: #142C42;
  --primary: #07549B;
  --primary-foreground: #FFFFFF;
  --secondary: #EDF3F8;
  --secondary-foreground: #142C42;
  --muted: #EDF3F8;
  --muted-foreground: #52697D;
  --accent: #E0F4F3;
  --accent-foreground: #06636D;
  --destructive: #B42332;
  --destructive-foreground: #FFFFFF;
  --border: #D4DFEA;
  --input: #D4DFEA;
  --ring: #07549B;
  --sidebar: #07386C;
  --sidebar-foreground: #FFFFFF;
  --sidebar-primary: #7FE2E3;
  --sidebar-primary-foreground: #07386C;
  --sidebar-accent: #14558F;
  --sidebar-accent-foreground: #FFFFFF;
  --sidebar-border: #37658F;
  --sidebar-ring: #7FE2E3;
  --success: #176B45;
  --success-light: #E4F4EB;
  --warning: #805000;
  --warning-light: #FFF2D6;
  --danger: #B42332;
  --danger-light: #FDEBED;
  --info: #07549B;
  --info-light: #E8F1FA;
  --radius: 0.625rem;
}

@theme inline {
  --color-brand-primary: var(--brand-primary);
  --color-brand-primary-dark: var(--brand-primary-dark);
  --color-brand-primary-light: var(--brand-primary-light);
  --color-brand-accent: var(--brand-accent);
  --color-brand-accent-dark: var(--brand-accent-dark);
  --color-brand-accent-light: var(--brand-accent-light);
  --color-brand-red: var(--brand-red);
  --color-background: var(--background);
  --color-foreground: var(--foreground);
  --color-card: var(--card);
  --color-card-foreground: var(--card-foreground);
  --color-popover: var(--popover);
  --color-popover-foreground: var(--popover-foreground);
  --color-primary: var(--primary);
  --color-primary-foreground: var(--primary-foreground);
  --color-secondary: var(--secondary);
  --color-secondary-foreground: var(--secondary-foreground);
  --color-muted: var(--muted);
  --color-muted-foreground: var(--muted-foreground);
  --color-accent: var(--accent);
  --color-accent-foreground: var(--accent-foreground);
  --color-destructive: var(--destructive);
  --color-destructive-foreground: var(--destructive-foreground);
  --color-border: var(--border);
  --color-input: var(--input);
  --color-ring: var(--ring);
  --color-sidebar: var(--sidebar);
  --color-sidebar-foreground: var(--sidebar-foreground);
  --color-sidebar-primary: var(--sidebar-primary);
  --color-sidebar-primary-foreground: var(--sidebar-primary-foreground);
  --color-sidebar-accent: var(--sidebar-accent);
  --color-sidebar-accent-foreground: var(--sidebar-accent-foreground);
  --color-sidebar-border: var(--sidebar-border);
  --color-sidebar-ring: var(--sidebar-ring);
  --color-success: var(--success);
  --color-success-light: var(--success-light);
  --color-warning: var(--warning);
  --color-warning-light: var(--warning-light);
  --color-danger: var(--danger);
  --color-danger-light: var(--danger-light);
  --color-info: var(--info);
  --color-info-light: var(--info-light);
  --radius-sm: calc(var(--radius) - 4px);
  --radius-md: calc(var(--radius) - 2px);
  --radius-lg: var(--radius);
  --radius-xl: calc(var(--radius) + 4px);
}
```

No React Native, reproduzir os mesmos valores em um objeto de tema TypeScript; as variáveis CSS e os componentes shadcn/ui se aplicam ao web. Os dados, permissões, situações e cálculos permanecem sob responsabilidade da API, conforme o tech-spec.

Referências técnicas: [temas do shadcn/ui](https://ui.shadcn.com/docs/theming) e [variáveis de tema do Tailwind CSS](https://tailwindcss.com/docs/theme).
