# Design System — Industrial Precision

Fundação visual da **Fase 0** para o e-commerce TechParts AI.

| Item | Valor |
|---|---|
| Bootstrap | **5.3.8** (maior estável em 2026-08-04 — R1) |
| Fontes | Inter + JetBrains Mono |
| Ícones | Material Symbols Outlined |
| Consumo futuro | copiar `css/` para `static/` do Django (F2) |

## Estrutura

```
design-system/
  css/
    tokens.css          # variáveis + mapa Bootstrap
    typography.css
    layout.css
    components.css
    states.css
    theme.css           # entry — importar após bootstrap.min.css
  preview/
    index.html          # story de tokens/componentes
  docs/
    BRAND.md
    VISUAL-REVIEW-CHECKLIST.md
  README.md
```

## Como visualizar

Abrir no navegador:

```bash
# a partir da raiz do repo
xdg-open design-system/preview/index.html
# ou servir localmente
python3 -m http.server 8765 --directory design-system
# http://127.0.0.1:8765/preview/
```

## Uso em templates (F2+)

```html
<link href="{% static 'vendor/bootstrap/bootstrap.min.css' %}" rel="stylesheet" />
<link href="{% static 'design-system/theme.css' %}" rel="stylesheet" />
```

Ou manter os partials (`tokens.css` …) se o pipeline de static files preferir.

## Regras rápidas

1. **Cyan só em IA** (`btn-ai`, header do chat, badges `tp-badge--ai` / compat assistida).
2. Primário de compra/nav = **Industrial Navy**.
3. Toda tela nova passa pelo [checklist visual](docs/VISUAL-REVIEW-CHECKLIST.md).

## Pilares cobertos

P16, P17, P18, P19, P20, P21, P22, P24.
