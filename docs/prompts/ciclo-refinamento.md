# Ciclo de refinamento — grounding e contexto de produto

**Critério Senac 4.10 / 15:** problema observado → alteração → resultado.

## Problema observado

O chat/diagnóstico respondia com trechos de **segurança preventiva** (“antes de ligar, trave a tampa”) como se fossem causa de “não liga”, ou extraía specs **inventadas**. Sem tipo/modelo, o RAG misturava manuais. Extração v1 era só ventilador; v2 ampliou o schema mas ainda **executava cadastro** na cabeça do modelo (sem Parte 0 de guardrails).

Commit âncora: `eebcc7e` (*feat: grounding no diagnóstico, extração de peças e login 2FA*, 2026-08-13). Extração v3: `f723af5`.

## Alteração

1. **Prompts**
   - Chat `v1` → `v2`: escopo produtos/peças/uso/conserto; proibir código; não usar aviso preventivo como diagnóstico.
   - Diagnóstico `v1` → `v2`: mesmo alinhamento + pedir tipo **ou** modelo **antes** de diagnosticar.
   - Extração `v1` → `v2` → `v3`: Parte 0 (papel, sem alteração de código, só sugestão para HITL); `model_variants`; potência só em `power_w`.
2. **Código**
   - `apps.ai.services.confidence` + `CHAT_MIN_ANSWER_CONFIDENCE` (default 0,70).
   - `product_context`: sem contexto → `ask_product` → `END` (sem retrieval).
   - Sanitização extra de leak de chave/prompt em `sanitize_manual_text`.
   - Extração: ferragens vendáveis só com identificador; approve HITL **não** publica sozinho.

## Resultado

- Testes: `test_diagnosis_adversarial_injection_does_not_leak_secrets`, `test_chat_injection_only_does_not_reveal_prompt`, `test_sanitize_strips_injection`, golden set extração/RAG no CI.
- Comportamento: pergunta “Qual a voltagem do capacitor…?” **sem** modelo agora pede o produto (`found=False`, `confidence=0.2` no log `diagnosis_done`) em vez de inventar spec.
- Efeito colateral documentado: o E2E nightly ainda espera a palavra `manual` nessa pergunta — ver [`../evidencias/anomalia-e2e-chat.md`](../evidencias/anomalia-e2e-chat.md). O produto está coerente com o prompt; o teste E2E ficou desatualizado (risco de falso negativo no nightly, não de peça errada no cliente).
