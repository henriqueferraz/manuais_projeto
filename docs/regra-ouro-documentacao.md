# Regra de ouro — documentação

> Obrigatória em **toda** mudança de código ou comportamento.  
> Complementa [`regra-ouro-campos-produto.md`](regra-ouro-campos-produto.md) (valores de catálogo).

## Princípio

Código e documentação caminham juntos. Uma mudança sem atualizar a doc correspondente
está **incompleta**.

---

## R-DOC.1 — Atualizar docs após cada mudança (obrigatório)

Depois de alterar comportamento, schema, rotas, env ou UI, **na mesma entrega**:

| Se mudou… | Atualize… |
|---|---|
| Tela / rota / template | [`pages/inventory.md`](pages/inventory.md) e doc da página em [`pages/`](pages/) se existir |
| Campo / form de produto | [`regra-ouro-campos-produto.md`](regra-ouro-campos-produto.md) + [`pages/dashboard-produto.md`](pages/dashboard-produto.md) |
| Model / relação | [`fase-1-schema-produto.md`](fase-1-schema-produto.md) (nota de evolução) ou pilar 11; docstring do model |
| Service / regra de domínio | Docstring da função/classe + MkDocs (gera da docstring) |
| Chat / RAG / confiança | [`pages/assistente-chat.md`](pages/assistente-chat.md) + pilar 10 + `.env.example` se nova env |
| Segurança / cookies / 2FA | [`security-hardening.md`](security-hardening.md) / [`deploy.md`](deploy.md) |
| Feature entregue | [`plano-tarefas.md`](plano-tarefas.md) (checkbox / pós T-P.6) |
| Decisão arquitetural | Novo ou update em [`adr/`](adr/) |

Agentes (Cursor) e humanos: **não encerrar a tarefa** só com o código; incluir o patch de docs.

## R-DOC.2 — O que documentar no código (docstring)

**Sim (API interna pública):**

- Módulos de domínio (`models.py`, `services*.py`, graphs)
- Classes e funções **públicas** (sem `_` no início)
- Comportamento não óbvio: filtros M2M, limiares, side-effects, formatos de retorno

**Não:**

- Helpers `_privados`
- Getters/`__str__` óbvios
- Testes (basta docstring de módulo do arquivo de teste, se útil)

## R-DOC.3 — Formato da docstring

Estilo curto, português, primeira linha no imperativo/resumo:

```python
def filter_catalog(*, category: str = "", ...) -> QuerySet[Product]:
    """Filtra o catálogo publicado.

    Args:
        category: slug ou nome; casa FK `category` ou M2M `categories`.

    Returns:
        QuerySet de produtos published, sem duplicar linhas do M2M.
    """
```

Módulo: uma linha no topo dizendo o papel do arquivo.

## R-DOC.4 — Site de API (MkDocs)

- Fonte: docstrings → `mkdocs build` / `mkdocs serve`
- Config: [`mkdocs.yml`](../mkdocs.yml) na raiz
- Escopo indexado: `apps/*/models.py`, `apps/*/services*.py`, services em subpastas

## R-DOC.5 — Gate de cobertura (interrogate)

- Escopo: `backend/apps/**/models.py` e `**/services*.py` (+ `services/`)
- Meta: ver `[tool.interrogate]` em `pyproject.toml`
- CI: job `interrogate` em `.github/workflows/ci.yml`

## Checklist rápido (fim de PR / commit)

- [ ] Docstring nos símbolos públicos novos/alterados (P0)
- [ ] `docs/pages/` ou inventário se UI/rota mudou
- [ ] `.env.example` se env nova
- [ ] `plano-tarefas` / ADR se feature ou decisão
- [ ] `interrogate` local ok no escopo de services/models
