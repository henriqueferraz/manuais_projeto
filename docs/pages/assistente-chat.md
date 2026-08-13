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
2. Sem tipo/modelo resolvido → agente **pede o produto** (`product_context`) antes de buscar.
3. Retrieval com filtro de produto/categoria → trechos do manual.
4. Geração (LLM `mock` \| `openai`) + checagem de groundedness / confiança (`confidence.py`).
5. Se confiança &lt; `CHAT_MIN_ANSWER_CONFIDENCE` (default **0.70**) → não trata como resposta firme; sugere chamado.
6. Feedback 👍/👎 em `/assistente/chat/feedback/`; 👎 / baixa confiança pode abrir `Ticket`.

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
