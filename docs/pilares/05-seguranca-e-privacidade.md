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

- Django Auth + **sessão** (+ django-two-factor / 2FA staff); **sem JWT**
- Templates de login em `backend/templates/two_factor/` + `design-system/auth.css`
- Proteção brute-force no login (django-axes)
- Rate limiting em endpoints de IA
- Validação MIME/tamanho + antivírus (ClamAV) em uploads
- System prompt isolado do conteúdo do manual (anti prompt injection)
- CSRF, XSS, SQL via ORM, HTTPS/HSTS, cookies secure/HttpOnly/SameSite
- Sessão: `SESSION_COOKIE_AGE` (24h), `SESSION_SAVE_EVERY_REQUEST`, não expira ao fechar o browser (defaults em `.env.example`)
- CSP, X-Frame-Options, Referrer-Policy
- `form-action` inclui domínios do Mercado Pago (Checkout Pro redireciona fora do site)
- R2 privado + URLs assinadas com expiração curta
- Anonimização de e-mail/CPF/endereço em logs (structlog)

## Fontes

- `constitution.md` — Artigos 3 e 8
- `security-hardening.md` — checklist pré-go-live
- `plano-ecommerce-ia-pecas.md` — Segurança (histórico)
- `plan.md` — Segurança
- Ver também pilar **15** (segurança aplicada ao domínio)