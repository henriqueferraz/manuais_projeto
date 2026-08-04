# Checklist de revisão visual (DoD)

> Usar em **toda** PR/tela com UI. Espelha o DoD de [`docs/plano-tarefas.md`](../../docs/plano-tarefas.md).

Marcar só o que se aplica; item N/A com nota.

## Marca e design system

- [ ] Parece TechParts AI (navy + Inter); **não** parece Bootstrap genérico
- [ ] AI Cyan aparece **somente** em features de IA / badges de assistência
- [ ] Ícones Material Symbols Outlined (sem misturar packs)

## Hierarquia e tipografia

- [ ] Ordem visual: título > preço/ação > specs (mono) > corpo
- [ ] JetBrains Mono em SKU/specs/fonte de manual
- [ ] Whitespace generoso entre seções (não “página cheia”)

## Componentes e estados

- [ ] Botões: Primary navy / AI cyan / Ghost conforme ação
- [ ] Loading com **skeleton** (não spinner genérico como padrão)
- [ ] Empty state com próximo passo claro
- [ ] Error state com ação de recuperação
- [ ] Hover/focus com transição ~200ms

## Mobile e a11y

- [ ] Usável em viewport estreito (grid 4 col / margins 16px)
- [ ] Chat (se houver): input acessível com teclado virtual
- [ ] Contraste AA em textos e badges
- [ ] Foco de teclado visível em todos os controles
- [ ] `alt` em imagens de produto; ícones decorativos com `aria-hidden`

## IA (quando a tela tiver assistente)

- [ ] Rótulo claro de interação com IA
- [ ] Fonte técnica citada (página/seção do manual)
- [ ] Fallback “não encontrei no manual” possível na copy/UX
- [ ] Indicador “IA digitando” / loading adequado
- [ ] Feedback 👍/👎 presente em respostas

## Confronto com protótipo

- [ ] Confrontado com `docs/design/` ou `docs/src/` quando existir tela equivalente

## Foto de produto (PDP/card)

- [ ] Fundo neutro / ângulo consistente com o guia [`BRAND.md`](BRAND.md)
