# Pilar 09 — Pipeline de ingestão de manuais

> **Parte 2 — Pilares Específicos do Projeto** · Fonte-mestre: [`pilares-app-ia-vendas-pecas.md`](../pilares-app-ia-vendas-pecas.md)

## Definição do pilar

Fluxo: Manual (PDF/imagem) → Extração → Estruturação → Validação humana → Catálogo.

## Fluxo

```
Manual (PDF) → upload R2 → Extração (OCR/texto) → LangGraph/LangChain
→ JSON (Pydantic) → Revisão humana (rascunho) → Publicação no catálogo
```

## Detalhamento

| Etapa | Como |
|---|---|
| Extração | OCR se escaneado; parsing texto/tabelas se PDF nativo (pdfplumber/unstructured) |
| Estruturação | Grafo com nós: specs, SKU, descrição comercial, categoria/compatibilidade |
| Saída | JSON com schema fixo (`with_structured_output` + Pydantic) |
| Human-in-the-loop | **Obrigatório** — nunca publicar sem revisão |
| Versionamento | PDF fonte no R2, vinculado ao produto, para auditoria |

## Implementação

- Task Celery; orquestração LangChain; interrupção LangGraph até aprovação no Django admin (ou tela amigável de revisão)
- Produto nasce como **rascunho**; humano aprova/corrige
- Fase 3 do roadmap — coração do diferencial; testar com vários manuais reais

## UI vigente

- Fila HITL: `/manuais/revisao/` → `manuals/review_queue.html`
- Detalhe: `/manuais/revisao/<id>/` → `manuals/review_detail.html`
- Cadastro assistido: `/dashboard/produtos/…` → [`../pages/dashboard-produto.md`](../pages/dashboard-produto.md)

## Fontes

- `pilares-app-ia-vendas-pecas.md` — Pilar 9
- `constitution.md` — Artigo 2.2
- `specify.md` — §4.2
- `plano-ecommerce-ia-pecas.md` — Revisão humana, fase 3 (histórico)
- `plan.md` — Pipeline
