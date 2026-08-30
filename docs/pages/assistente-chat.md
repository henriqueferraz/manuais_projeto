# Assistente — chat / diagnóstico

| | |
|---|---|
| **URL** | `/assistente/chat/` |
| **Name** | `ai:chat` |
| **Template** | `backend/templates/ai/chat.html` |
| **Auth** | sessão anônima ou login (`tp_chat_key` / sessão) |

## Objetivo

Responder dúvidas técnicas com RAG sobre manuais e, em relatos de falha, sugerir diagnóstico e peças — sempre com citação de fonte.

## Fluxo

1. Cliente envia mensagem → `POST /assistente/chat/stream/` (SSE).
2. Sem tipo/modelo resolvido → agente **pede o produto** (`product_context`) e o grafo **para** (`END`).
3. Com contexto: `search_context` chama as tools RAG e pedidos (mesma thread). Depois o grafo **ramifica em paralelo** `emit_trace` ∥ `emit_done` e encerra.
4. `run_diagnosis` usa `recursion_limit=8` (evita loop). Extração HITL pausa em `interrupt()` até revisão humana (`recursion_limit=12`).
5. Retrieval com filtro de produto/categoria → trechos do manual (payload validado na tool). Se o `product_id` da sessão **não tem chunks** (manual não indexado ou não vinculado), o RAG **relaxa** o filtro e busca por modelo/categoria — senão o diagnóstico devolve confiança 0 e a mesma recusa + chamado. Query de falha expande sinônimos (`barulho`→`ruído`); o diagnóstico pede `top_k=12` para não perder a tabela de problemas no OCR.
6. Geração (LLM `mock` \| `openai`) + groundedness / confiança (`confidence.py`). Injection no relato é sanitizada (`sanitize_manual_text`); chaves de env não entram na resposta. Trecho já validado por `evidence_supports_answer` **não é descartado** se o LLM responder `NO_EVIDENCE` (cai no excerpt do manual; confiança no mínimo do limiar).
7. Se confiança &lt; `CHAT_MIN_ANSWER_CONFIDENCE` (default **0.70**) **e** não houver trecho grounded → não trata como resposta firme; sugere chamado. Sem chunks no produto (ex.: extração skipped, RAG nunca rodou) o sintoma típico é sempre a mesma frase de recusa + `CH-…`.
8. Feedback 👍/👎 em `/assistente/chat/feedback/`; 👎 / baixa confiança pode abrir `Ticket`.

## Endpoints relacionados

| URL | Função |
|---|---|
| `/assistente/chat/stream/` | Stream SSE da resposta |
| `/assistente/chat/feedback/` | Feedback da mensagem |
| `/assistente/foto/` | Upload para busca por foto |
| `/assistente/foto/<uuid>/` | Status / candidatos da busca |

## Config

Ver `.env.example`: `CHAT_LLM_MODE`, `DIAGNOSIS_LLM_MODE`, `EMBEDDING_MODE`, `CHAT_MIN_ANSWER_CONFIDENCE`, `RAG_*`.

## Ver também

- Pilar 10: [`../pilares/10-rag-duvidas-tecnicas.md`](../pilares/10-rag-duvidas-tecnicas.md)
- Inventário: [`inventory.md`](inventory.md)
