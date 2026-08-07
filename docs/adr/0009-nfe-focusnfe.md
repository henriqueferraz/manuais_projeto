# ADR 0009 — NF-e via Focus NFe (sandbox → produção)

- **Status:** Aceito
- **Data:** 2026-08-07
- **Pilares:** P05, P11, P15
- **Fase:** T-P.4

## Contexto

Emissão fiscal era só mock. Go-live BR exige provedor real com homologação.

## Decisão

1. `NFE_PROVIDER=mock` permanece default (CI/local).
2. `NFE_PROVIDER=focusnfe` + `FOCUSNFE_TOKEN` chama Focus NFe (`FOCUSNFE_BASE_URL` homologação por default).
3. Payload mínimo em `apps/checkout/nfe.py`; CNPJ emitente via `NFE_EMITTER_CNPJ`.
4. Falhas não bloqueiam o pagamento já capturado (retry Celery).

## Consequências

+ Caminho live testável em staging.  
− Requer contrato Focus e cadastro fiscal; CI nunca chama a API.
