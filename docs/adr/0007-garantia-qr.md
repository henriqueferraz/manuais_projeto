# ADR 0007 — Garantia digital com QR-code

- **Status:** Aceito
- **Data:** 2026-08-06
- **Pilares:** P08, P11

## Contexto

QR na peça/embalagem deve abrir chamado pré-contextualizado na mesma fila.

## Decisão

1. Model `WarrantyCode` (uuid, product opcional, SKU, ativo) em app `warranty`.
2. URL pública `/garantia/<uuid>/` renderiza formulário de chamado com origem `qr`.
3. PNG do QR gerado com lib `qrcode` (já no projeto) para staff/ops.
4. Extender `Ticket.Origin` com `qr` e `whatsapp`.

## Consequências

+ Um funil unificado de tickets.  
− Impressão física / packing slip fica operacional.
