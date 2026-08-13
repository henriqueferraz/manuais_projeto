# API interna (gerada das docstrings)

Documentação automática dos módulos públicos de domínio via
[mkdocstrings](https://mkdocstrings.github.io/). Fonte: código em `backend/apps/`.

## Como gerar / ver

```bash
pip install -r requirements/docs.txt
mkdocs serve    # http://127.0.0.1:8000
mkdocs build    # pasta site/
```

## Escopo

Models e services (API interna). Views/templates: ver [Páginas](../pages/inventory.md).

## Regra

Toda mudança nesses módulos deve atualizar a docstring na mesma entrega —
[`regra-ouro-documentacao.md`](../regra-ouro-documentacao.md).
