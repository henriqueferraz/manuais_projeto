# ADR 0006 — PWA offline para técnicos

- **Status:** Aceito
- **Data:** 2026-08-06
- **Pilares:** P12, P21

## Contexto

Técnicos em campo com conectividade ruim precisam de shell offline (manual/chamado).

## Decisão

1. `manifest.webmanifest` + service worker que cacheia shell (HTML/CSS/JS estáticos) e `/health/`.
2. Registro do SW em `base.html` (somente se `PWA_ENABLED=true`).
3. Offline: página fallback estática; **Background Sync** de chamados (`tp-ticket-sync`) + cache seletivo de manuais (`tp-manuals-v1`).

## Consequências

+ Instalável / shell offline + fila de chamados.  
− Quota de storage do browser limita PDF grandes; política de evicção futura.

## Atualização T-P.5 (2026-08-07)

SW `tp-shell-v2`: outbox offline para POST `/chamados/` e cache-first de `/manuais/` e `/media/manuals/`.
