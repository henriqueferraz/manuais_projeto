# ADR 0002 — WhatsApp reaproveitando RAG/diagnóstico

- **Status:** Aceito
- **Data:** 2026-08-06
- **Pilares:** P03, P05, P10, P15

## Contexto

Ampliar canal sem duplicar o motor de IA. Meta Cloud API / BSP exige webhook verificado.

## Decisão

1. App `channels` com endpoint webhook (GET verify + POST inbound).
2. Validar assinatura HMAC (`X-Hub-Signature-256`) quando `WHATSAPP_APP_SECRET` estiver setado.
3. Reusar `diagnose_question` / `answer_question` + abrir `Ticket` com `origin=whatsapp` se escalonar.
4. Modo `WHATSAPP_MODE=mock` no CI/local (sem chamar Meta).
5. Resposta outbound mockada (log + opcional HTTP se token presente).

## Consequências

+ Um único pipeline de qualidade (golden/RAG).  
− Produção exige BSP/Meta e compliance (opt-in); mock não substitui homologação Meta.
