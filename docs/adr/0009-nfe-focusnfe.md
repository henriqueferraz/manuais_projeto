# ADR 0009 — NF-e via NotaAS (preferencial) / Focus NFe

- **Status:** Aceito (atualizado)
- **Data:** 2026-08-07 · atualizado 2026-08-08
- **Pilares:** P05, P11, P15
- **Fase:** T-P.4

## Contexto

Emissão fiscal era só mock. Go-live BR exige provedor real. O projeto usa **NotaAS** (`API_KEY_NOTAAS`); Focus NFe permanece como alternativa.

## Decisão

1. `NFE_PROVIDER=mock` permanece default (CI/local).
2. Staging/prod preferencial: `NFE_PROVIDER=notaas` + `API_KEY_NOTAAS` (`x-api-key`), base `NOTAAS_BASE_URL` (default `https://platform.notaas.com.br/api/v1`).
3. Emissão NotaAS é assíncrona (`POST /nfe/emitir` → poll `GET /nfe/invoices/{id}/status` até `issued`/`error`).
4. Destinatário: CPF/CNPJ via `NFE_DEFAULT_DEST_DOCUMENT` (até o checkout coletar documento); IBGE via cidade/UF ou `NFE_DEFAULT_IBGE_CODE`; NCM via `NFE_DEFAULT_NCM` ou `product.specs.ncm`.
5. Alternativa: `NFE_PROVIDER=focusnfe` + `FOCUSNFE_TOKEN` (ADR histórico).
6. Falhas não bloqueiam o pagamento já capturado (retry Celery).

## Consequências

+ Caminho live alinhado à chave já presente no `.env`.  
− Checkout ainda não coleta CPF/CNPJ do cliente (fallback por env em staging).
