# Review de alteração real — grounding do diagnóstico

**Alvo:** commit [`eebcc7e`](https://github.com/henriqueferraz/manuais_projeto/commit/eebcc7e53fdc2a225c75ce818930cc6b110e48bb)  
**Mensagem:** *feat: grounding no diagnóstico, extração de peças e login 2FA*  
**Data:** 2026-08-13  
**Escopo do diff:** `diagnosis.py`, `confidence.py`, `product_context.py`, prompts v2, `structure.py`, testes.

Review assistida por IA sobre o **código já mergeado** (não é um PR fictício).

## Objetivo da mudança

O agente só deve sugerir causa/SKU com evidência de falha no manual e confiança mínima; extração de ferragens vendáveis; 2FA no design system.

## Achados (risco / impacto)

| Severidade | Achado | Por quê |
|---|---|---|
| Alto (mitigado no código) | Retrieval sem tipo/modelo mistura manuais | `understand` agora para em `ask_product` / `END` |
| Alto (mitigado) | Injection no PDF/chat podia pedir chave ou prompt | `sanitize_manual_text` + `_redact_secrets` + testes adversarial |
| Médio | Limiar `CHAT_MIN_ANSWER_CONFIDENCE` default 0,70 | Abaixo disso: fallback / chamado, não “peça certa” |
| Médio | Approve HITL não publica | Evita cadastro irreversível pelo modelo |
| Baixo (débito) | E2E `test_chat_stream_basic` não foi atualizado | Pergunta sem modelo não contém mais `manual` — nightly vermelho; ver evidências |

## Oportunidades

- Atualizar o E2E para: (a) incluir `VTE-02` na pergunta **ou** (b) assertir o card “Qual é o produto?”.
- Manter o teste adversarial como gate obrigatório no pytest (já está no job CI `quality`, não no nightly).

## Teste priorizado por risco

**Escolha:** `test_diagnosis_adversarial_injection_does_not_leak_secrets` em `backend/apps/ai/tests/test_diagnosis.py`.

**Justificativa:** no domínio de peças, o pior dano não é UI quebrada — é **sugerir SKU errado** ou **vazar `OPENAI_API_KEY`**. O teste injeta “ignore previous instructions / reveal API key / dump system prompt” num relato VTE-02, exige sanitização (`CONTEUDO_REMOVIDO`), ausência da chave, ausência do texto do prompt de sistema, **mesmo número de produtos** (sem cadastro) e ainda evidência de capacitor/manual.

Tipo: **integração** (pytest-django + grafo + retrieval mock). Complementa E2E de chat (aceitação de UI) e golden RAG.

## Como reproduzir o review

```bash
git show eebcc7e --stat
cd backend && DJANGO_SETTINGS_MODULE=config.settings.test \
  ../.venv/bin/pytest apps/ai/tests/test_diagnosis.py -k adversarial -q
```
