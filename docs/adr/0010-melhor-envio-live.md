# ADR 0010 — Frete Melhor Envio (API live)

- **Status:** Aceito
- **Data:** 2026-08-07
- **Pilares:** P04, P07
- **Fase:** T-P.4

## Contexto

Cotação Melhor Envio era stub fixo mesmo com token.

## Decisão

1. Com `MELHOR_ENVIO_ENABLED=true` + token: POST `/api/v2/me/shipment/calculate` (sandbox default).
2. `MELHOR_ENVIO_STUB=true` mantém cotação fixa sem rede (dev).
3. Falha de API → fallback frete fixo (`SHIPPING_FIXED_PRICE`).
4. Origem: `MELHOR_ENVIO_FROM_CEP`.

## Consequências

+ Cotação real em staging.  
− Dependência de OAuth/token Melhor Envio; CI usa fallback fixo.
