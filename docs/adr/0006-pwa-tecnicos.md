# ADR 0006 — PWA offline para técnicos

- **Status:** Aceito
- **Data:** 2026-08-06
- **Pilares:** P12, P21

## Contexto

Técnicos em campo com conectividade ruim precisam de shell offline (manual/chamado).

## Decisão

1. `manifest.webmanifest` + service worker que cacheia shell (HTML/CSS/JS estáticos) e `/health/`.
2. Registro do SW em `base.html` (somente se `PWA_ENABLED=true`).
3. Offline: página fallback estática; sync de chamados fica para iteração (Background Sync).

## Consequências

+ Instalável / shell offline.  
− Manuais PDF offline completos exigem cache seletivo e storage quota — não nesta entrega.
