# Pilar 04 — Arquitetura técnica sólida

> **Parte 1 — Pilares Gerais para Apps de IA** · Fonte-mestre: [`pilares-app-ia-vendas-pecas.md`](../pilares-app-ia-vendas-pecas.md)

## Definição do pilar

Separação frontend/backend/IA; cache; rate limiting e custos; tratamento de erros robusto.

## Decisão de arquitetura

**Monólito modular** (Django) — deploy único, menor custo, sem microserviços no MVP.

```
                Cloudflare
                     │
             Django + htmx
                     │
      ┌──────────────┴──────────────┐
      │                             │
 Django Views                 Django REST API
      │                             │
      └──────────────┬──────────────┘
                     │
                Services
                     │
      ┌──────────────┼───────────────┐
      │              │               │
 Produtos        Checkout        Chat IA
      │              │               │
 PostgreSQL      Gateway      LangGraph
      │              │               │
      └──────────────┼───────────────┘
                     │
                  Celery
                     │
        Anthropic / Claude API
                     │
               Cloudflare R2
```

> **Stack vigente:** LLM = **OpenAI** via `*_LLM_MODE=mock|openai` (CI em mock).
> O diagrama acima é o esboço histórico do plano; ver nota em [`../plan.md`](../plan.md).

## Stack oficial

| Camada | Tecnologia |
|---|---|
| Backend | Python 3.13+, Django, DRF, Celery, Redis |
| Frontend | Django Templates, htmx, Bootstrap 5, Alpine.js, design-system |
| Banco | PostgreSQL + pgvector |
| Storage | Cloudflare R2 |
| IA | OpenAI (`*_LLM_MODE`), LangChain, LangGraph |
| PDFs | pdfplumber, Unstructured |
| Cache | Redis (broker Celery + django-redis) |
| Auth | Django session + django-two-factor (2FA staff); sem JWT |

## Organização de apps

`accounts`, `catalog`, `products`, `cart`, `checkout`, `orders`, `tickets`, `ai`, `manuals`, `compatibility`, `dashboard`, `notifications`, `subscriptions`, `partners`, `channels`, `warranty`, `core`

## Princípios de separação

- Chaves de API **nunca** no cliente — tudo via backend Django
- LangChain/LangGraph rodam **dentro** das tasks Celery (não é serviço novo)
- Django é dono do estado de negócio; LangGraph cuida do estado transitório da conversa/agente
- Cache de catálogo e consultas de compatibilidade no Redis
- Timeouts e tratamento de respostas malformadas em toda chamada a modelo

## Critério de complexidade

Para “pergunta → busca → resposta”, chamada direta basta. LangGraph entra quando há múltiplas ferramentas, decisões condicionais ou estado entre etapas.

## Fontes

- `plan.md` — Arquitetura e decisão final
- `plano-ecommerce-ia-pecas.md` — Stack tecnológico (histórico)
- Telas: [`../pages/inventory.md`](../pages/inventory.md)