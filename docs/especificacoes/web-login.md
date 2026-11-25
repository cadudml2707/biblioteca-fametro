# Web — Fase 1: acesso e navegação

## Escopo

A interface web permite que bibliotecários e administradores acessem a área de gestão usando a API de autenticação existente. A interface apresenta uma página inicial e a navegação correspondente ao perfil; módulos ainda não implementados são identificados como indisponíveis, sem dados fictícios ou links quebrados. Alunos não acessam a gestão web.

## Sessão e comportamento

- O login envia e-mail, senha e plataforma `web` para o backend e apresenta mensagens e erros retornados. Durante o envio, impede submissões repetidas.
- Os tokens ficam em cookies HttpOnly, com SameSite e Secure em produção, gerenciados pelo servidor Next.js. O navegador não acessa os tokens via JavaScript. O frontend encaminha as solicitações ao backend na rede interna, sem expor credenciais ou URL interna ao navegador.
- Ao abrir a área autenticada, o servidor consulta a identidade atual no backend. Quando necessário, renova a sessão pelo refresh rotativo; credenciais inválidas encerram a sessão. Uma falha temporária do backend apresenta opção de tentar novamente, preservando a sessão.
- O logout revoga o refresh no backend e limpa os cookies locais; o usuário retorna ao login. O acesso de usuário inativo ou com perfil incompatível é recusado pelo backend.
- A navegação de gestão mostra início, catálogo, circulação, reservas e relatórios. Usuários e configurações são apresentados somente ao administrador. Áreas futuras são indicadas como indisponíveis.
- Interface para computadores, acessível por teclado e fiel à identidade visual de `docs/design-branding.md`. O aplicativo para celulares é um projeto separado. O login e a navegação usam o logotipo do Portal da FAMETRO.

## Aceitação

- Login válido direciona à área de gestão com identidade e perfil retornados pela API; dados inválidos e perfil não autorizado apresentam erro.
- A sessão sobrevive à atualização de página e logout impede nova restauração com o refresh revogado.
- A indisponibilidade temporária do backend é comunicada, sem apagar a sessão durante a restauração.
- A aplicação e o backend executam via Compose; a configuração da API é definida em ambiente no servidor frontend. A tela funciona em resoluções de computador a partir de 1024 px.
