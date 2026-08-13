# Pilar 10 — RAG para dúvidas técnicas dos clientes

> **Parte 2 — Pilares Específicos do Projeto** · Fonte-mestre: [`pilares-app-ia-vendas-pecas.md`](../pilares-app-ia-vendas-pecas.md)

## Definição do pilar

Chunking de domínio; pgvector; metadados como filtro; LangGraph; citação de fonte; fallback explícito.

## Requisitos

- **Chunking:** por seção/parágrafo semântico; preservar tabelas; metadados (produto, seção, página)
- **Banco vetorial:** pgvector no PostgreSQL (sem vector DB externo no início)
- **Filtro por metadados:** produto / categoria (FK principal ou contexto resolvido) antes da busca semântica
- **Fluxo LangGraph:** identificação do produto → retrieval → geração → verificação
- **Citação:** toda resposta técnica referencia página/seção do manual
- **Fallback:** “não encontrei no manual” — especialmente segurança
- **Confiança mínima:** `CHAT_MIN_ANSWER_CONFIDENCE` (default `0.70`) — abaixo disso a resposta não é exibida como resposta do agente; abre caminho para chamado (`apps.ai.services.confidence`)
- **Contexto de produto:** sem tipo/modelo resolvido, o diagnóstico **pergunta** antes de buscar (`apps.ai.services.product_context`)

## Chat e diagnóstico

```
Pergunta → (contexto produto?) → Embedding → Busca pgvector
  → LLM OpenAI (ou mock) → groundedness/confiança → Resposta (+ fonte) + stream SSE
```

Diagnóstico assistido: entender relato → decidir busca (`ask_product` / `ask_details` / manual / pedidos) → sugerir causa e peça só com evidência de falha no trecho, sempre citando o manual.

## Canais futuros (mesma base RAG)

WhatsApp (fase 8), multi-idioma (detectar idioma da pergunta e responder no mesmo).

## UI vigente

- `/assistente/chat/` → `backend/templates/ai/chat.html`
- Doc de página: [`../pages/assistente-chat.md`](../pages/assistente-chat.md)
- Inventário: [`../pages/inventory.md`](../pages/inventory.md)

## Fontes

- `pilares-app-ia-vendas-pecas.md` — Pilar 10
- `specify.md` — §4.3
- `plano-ecommerce-ia-pecas.md` — RAG, Diagnóstico (histórico)
- `plan.md` — Chat
- `.env.example` — `CHAT_MIN_ANSWER_CONFIDENCE`, `*_LLM_MODE`
