# Pilar 05 — Segurança e privacidade

> **Parte 1 — Pilares Gerais para Apps de IA** · Fonte-mestre: [`pilares-app-ia-vendas-pecas.md`](../pilares-app-ia-vendas-pecas.md)

## Definição do pilar

Validação/sanitização de inputs; cuidado com dados sensíveis; proteção contra prompt injection.

## Princípios (Constitution Art. 3 e 8)

- Segurança atravessa todas as fases — não é uma fase do roadmap
- Dados de pagamento **nunca** tocam a aplicação (tokenização)
- Uploads de terceiros são **hostis por padrão**
- Permissões configuráveis (RBAC), não fixas no código
- Ações sensíveis auditáveis
- Dados pessoais minimizados, mascarados em logs, alinhados à LGPD
- Segredos fora do repositório, com rotação
- Backup com restauração testada

## Controles técnicos

- Django Auth + JWT/sessions no DRF; 2FA para staff
- Proteção brute-force no login (django-axes)
- Rate limiting em endpoints de IA
- Validação MIME/tamanho + antivírus (ClamAV) em uploads
- System prompt isolado do conteúdo do manual (anti prompt injection)
- CSRF, XSS, SQL via ORM, HTTPS/HSTS, cookies secure/HttpOnly/SameSite
- CSP, X-Frame-Options, Referrer-Policy
- R2 privado + URLs assinadas com expiração curta
- Anonimização de e-mail/CPF/endereço em logs (structlog)

## Fontes

- `constitution.md` — Artigos 3 e 8
- `plano-ecommerce-ia-pecas.md` — Segurança
- `plan.md` — Segurança
- Ver também pilar **15** (segurança aplicada ao domínio)
