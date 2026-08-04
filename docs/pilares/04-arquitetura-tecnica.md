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

## Stack oficial

| Camada | Tecnologia |
|---|---|
| Backend | Python 3.13+, Django, DRF, Celery, Redis |
| Frontend | Django Templates, htmx, Bootstrap 5, Alpine.js |
| Banco | PostgreSQL + pgvector |
| Storage | Cloudflare R2 |
| IA | Claude (Anthropic), LangChain, LangGraph |
| PDFs | pdfplumber, Unstructured |
| Cache | Redis (broker Celery + django-redis) |

## Organização de apps

`accounts`, `catalog`, `products`, `cart`, `checkout`, `orders`, `tickets`, `ai`, `manuals`, `compatibility`, `dashboard`, `notifications`

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
- `plano-ecommerce-ia-pecas.md` — Stack tecnológico, Orquestração
- `src/components/ArchitectureView.tsx`
