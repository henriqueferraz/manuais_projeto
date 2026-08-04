# Pilar 10 — RAG para dúvidas técnicas dos clientes

> **Parte 2 — Pilares Específicos do Projeto** · Fonte-mestre: [`pilares-app-ia-vendas-pecas.md`](../pilares-app-ia-vendas-pecas.md)

## Definição do pilar

Chunking de domínio; pgvector; metadados como filtro; LangGraph; citação de fonte; fallback explícito.

## Requisitos

- **Chunking:** por seção/parágrafo semântico; preservar tabelas; metadados (produto, seção, página)
- **Banco vetorial:** pgvector no PostgreSQL (sem vector DB externo no início)
- **Filtro por metadados:** produto/categoria antes da busca semântica
- **Fluxo LangGraph:** identificação do produto → retrieval → geração → verificação
- **Citação:** toda resposta técnica referencia página/seção do manual
- **Fallback:** “não encontrei no manual” — especialmente segurança

## Chat e diagnóstico

```
Pergunta → Embedding → Busca pgvector → Claude → Resposta (+ fonte) + stream SSE
```

Diagnóstico assistido (fase 6): entender relato → decidir busca (manual / pedidos / pedir detalhes) → sugerir causa e peça, sempre citando o manual.

## Canais futuros (mesma base RAG)

WhatsApp (fase 8), multi-idioma (detectar idioma da pergunta e responder no mesmo).

## UI de referência

- `code.html`, `code (cópia 9).html`
- `src/components/DiagnosticChatView.tsx`

## Fontes

- `pilares-app-ia-vendas-pecas.md` — Pilar 10
- `specify.md` — §4.3
- `plano-ecommerce-ia-pecas.md` — RAG, Diagnóstico, fases 5–6
- `plan.md` — Chat
