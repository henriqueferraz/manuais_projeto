# Guia de marca — TechParts AI (Industrial Precision)

> Fase 0 · T-0.4 · Pilares **P18, P24**

## Posicionamento

**Brand concept:** Efficiency through Automation  
**Tom visual:** técnico / industrial — confiável, preciso, eficiente. **Não** consumer “fofo”, playful ou lifestyle genérico.

Público dual: técnicos (precisam de specs claras) e consumidores resolvendo equipamento quebrado.

## Sinais de marca no primeiro viewport

- Nome **TechParts AI** como sinal forte (não só texto de nav)
- Industrial Navy como cor dominante de marca
- AI Cyan **somente** onde há inteligência (chat, diagnóstico, badges de IA/compatibilidade assistida)

Teste: se remover a nav e a página puder ser de outra marca genérica Bootstrap, a marca está fraca.

## Tipografia

| Uso | Fonte |
|---|---|
| UI, títulos, corpo | Inter |
| SKU, specs, fonte de manual | JetBrains Mono |
| Ícones | Material Symbols Outlined |

## Fotografia de produto (P18)

- Fundo **neutro** (cinza claro / branco técnico)
- Ângulo e iluminação **consistentes** entre SKUs da mesma categoria
- Preferir um produto por frame; evitar collages no hero
- Entregar WebP/AVIF via R2 (F4a) com `alt` descritivo
- Zoom / múltiplos ângulos na PDP quando houver assets

## O que evitar

- Tema Bootstrap “cru” sem tokens
- Cyan em botões de checkout / nav principal
- Cards com sombra pesada ou radius pill
- Parallax / motion decorativo sem função
- Reproduzir texto/imagens de manuais de fabricantes literalmente no site (constitution Art. 8)

## Referências de protótipo

Meta visual (não stack de produção):

- [`docs/design/`](../../docs/design/) — HTML e screens
- [`docs/design/DESIGN.md`](../../docs/design/DESIGN.md) — tokens fonte
- [`docs/design/PROTOTYPE-CONFRONTATION.md`](../../docs/design/PROTOTYPE-CONFRONTATION.md) — confronto tela × protótipo (T-P.3 / B-006)

Produção alvo: **Django Templates + htmx + este design system**.
