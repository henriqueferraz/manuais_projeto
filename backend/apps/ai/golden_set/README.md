# Golden set RAG (F6 / T-6.4)

Perguntas de regressão + fixtures de texto. Roda em mock embeddings (CI).

```bash
make golden-rag
# ou
cd backend && DJANGO_SETTINGS_MODULE=config.settings.test \
  ../.venv/bin/python manage.py run_rag_golden_set
```
