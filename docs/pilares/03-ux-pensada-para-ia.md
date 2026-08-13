# Pilar 03 — Experiência de usuário (UX) pensada para IA

> **Parte 1 — Pilares Gerais para Apps de IA** · Fonte-mestre: [`pilares-app-ia-vendas-pecas.md`](../pilares-app-ia-vendas-pecas.md)

## Definição do pilar

Streaming de respostas; estados de carregamento; design para incerteza; fallbacks graciosos.

## Requisitos consolidados

- **Streaming:** respostas via SSE (`StreamingHttpResponse` do Django) — não fazer o usuário esperar o texto inteiro.
- **Indicadores:** `hx-indicator` / skeleton / “IA está digitando”.
- **Incerteza e confiança:** baixa confiança escala para humano; card de diagnóstico mostra nível de confiança.
- **Fallback explícito:** dizer “não encontrei isso no manual” em vez de inventar — especialmente sobre segurança.
- **Correção pelo usuário:** feedback 👍/👎; regenerar/desfazer quando aplicável.
- **Escalonamento:** 👎 (ou dois seguidos) ou insistência do cliente → chamado técnico com histórico anexado.

## Fluxos de experiência ligados à IA

| Fluxo | Comportamento UX |
|---|---|
| Chat técnico / diagnóstico | Mensagens streamadas; fonte citada; feedback por resposta |
| Busca por sintoma (hero) | “minha geladeira não gela” → sugere peças |
| Busca por foto | Upload com loading; candidatos ranqueados |
| Revisão humana (admin) | Fila de rascunhos com confiança da extração |

## UI vigente

- Chat: `/assistente/chat/` → [`../pages/assistente-chat.md`](../pages/assistente-chat.md)
- Home / sintoma: `core/home.html`
- Foto: `/assistente/foto/`
- HITL: `/manuais/revisao/`
- Inventário: [`../pages/inventory.md`](../pages/inventory.md)
- Tokens: [`../design/DESIGN.md`](../design/DESIGN.md)

## Fontes

- `pilares-app-ia-vendas-pecas.md` — Pilar 3
- `specify.md` — §4.3
- `plano-ecommerce-ia-pecas.md` — Diagnóstico, Feedback do chat (histórico)
- `DESIGN.md` — AI Chat Interface
