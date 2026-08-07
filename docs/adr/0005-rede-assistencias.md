# ADR 0005 — Rede de assistências parceiras

- **Status:** Aceito
- **Data:** 2026-08-06
- **Pilares:** P01, P11

## Contexto

Clientes precisam achar assistência credenciada próxima.

## Decisão

1. App `partners` com `PartnerService` (nome, cidade, UF, CEP, geo lat/lng opcional, ativo).
2. Página pública `/assistencias/` com filtro por UF/cidade.
3. Seed mínimo via `seed_scale_catalog`.

## Consequências

+ Canal de campo sem app nativo.  
− Busca por raio/geo real exige geocoding (fora do stub).
