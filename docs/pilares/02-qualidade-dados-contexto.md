# Pilar 02 — Qualidade dos dados e do contexto

> **Parte 1 — Pilares Gerais para Apps de IA** · Fonte-mestre: [`pilares-app-ia-vendas-pecas.md`](../pilares-app-ia-vendas-pecas.md)

## Definição do pilar

RAG bem implementado; prompts engenheirados; gerenciamento de memória/histórico quando relevante.

## Requisitos consolidados

- **Rastreabilidade:** toda extração e toda resposta de chat deve apontar para o trecho do manual (ou dado) que a originou.
- **Saída como dado, nunca como código:** JSON de extração validado contra schema (Pydantic) antes de virar produto. Conteúdo de manuais nunca é interpretado como instrução de sistema — só como contexto.
- **Prompts versionados:** templates LangChain para extração estruturada e para o chat, com parsers de saída.
- **Histórico de conversa:** quando relevante (diagnóstico, escalonamento), anexar histórico ao chamado humano para o cliente não repetir o que já disse.
- **Golden set:** conjunto fixo de manuais reais com JSON esperado; regressão no CI a cada mudança de prompt/lógica.
- **Feedback 👍/👎:** sinal direto de qualidade; alimenta dashboard e golden set.

## Extração de contexto do PDF

- pdfplumber / unstructured.io para texto e tabelas antes de enviar ao modelo
- Evitar gastar tokens processando imagens quando não necessário
- OCR quando o manual for escaneado

## Fontes

- `constitution.md` — Artigo 2
- `specify.md` — §§4.2–4.3, 5
- `plano-ecommerce-ia-pecas.md` — IA (RAG e extração), Qualidade de dados
- `plan.md` — Seção IA
