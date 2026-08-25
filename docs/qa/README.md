# QA com IA (Senac 4.7)

| Artefato | O quê |
|---|---|
| [`review-grounding-eebcc7e.md`](review-grounding-eebcc7e.md) | Review de **alteração real** (`eebcc7e`) — diff/commit no GitHub |
| Teste priorizado por risco | `test_diagnosis_adversarial_injection_does_not_leak_secrets` (peça/segredo errados) |
| Integração | `backend/apps/ai/tests/test_diagnosis.py`, `test_pipeline.py` |
| E2E | `e2e/test_chat.py`, `e2e/test_checkout.py`, `e2e/test_ticket.py` (nightly) |

A geração/refinamento dos testes de diagnóstico e sanitização acompanhou o commit de grounding (centenas de linhas em `test_diagnosis.py` / `test_pipeline.py`). O critério de prioridade está no review: **diagnóstico com evidência errada vende peça errada**.
