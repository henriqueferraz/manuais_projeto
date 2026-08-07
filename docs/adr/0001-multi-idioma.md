# ADR 0001 — Multi-idioma no catálogo e chat

- **Status:** Aceito
- **Data:** 2026-08-06
- **Pilares:** P01, P10, P11

## Contexto

O schema já tem `ProductTranslation.locale`. O MVP só usa `pt-BR`. Na escala, técnicos e clientes podem perguntar em outros idiomas.

## Decisão

1. Resolver locale via query `?lang=`, cookie `tp_lang` ou `Accept-Language` (fallback `pt-BR`).
2. Catálogo e PDP leem tradução do locale; se ausente, fallback `pt-BR`.
3. Chat/diagnóstico: detectar idioma do relato (heurística) e instruir resposta no mesmo idioma; retrieval permanece no corpus indexado (manuais).
4. Conteúdo EN/ES no `seed_scale_catalog` (T-P.5); corpus RAG de manuais permanece majoritariamente pt-BR.

## Consequências

+ Sem quebrar schema F1.  
− Qualidade RAG em idioma ≠ manual depende de tradução futura do corpus.

## Atualização T-P.5 (2026-08-07)

Seed de escala cria traduções `en` e `es` para cada SKU novo (além de `pt-BR`).
