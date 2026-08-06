# Golden set de extração (F3 / T-3.4)

Conjunto fixo de **textos** de manuais + JSON esperado para regressão local do extrator.

Os PDFs reais ficam em `manuais/` (gitignored). Aqui versionamos fixtures de texto
representativas dos layouts Mondial / Britânia / lista de peças.

```bash
cd backend
DJANGO_SETTINGS_MODULE=config.settings.test ../.venv/bin/python manage.py run_golden_set
```

Critério mínimo padrão: ≥ 66% dos casos OK (ajustável com `--min-score`).
No CI (F6): step `Golden set (extração + RAG)` em `.github/workflows/ci.yml`.
