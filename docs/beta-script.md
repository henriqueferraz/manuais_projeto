# Script de testes — Beta humana (T-P.1 / pós-F8)

Objetivo: validar o MVP com usuários reais (ou proxies internos) e alimentar o loop de qualidade.  
Relatório vivo: [`beta-relatorio.md`](beta-relatorio.md).

## Pré-requisitos

```bash
# a partir de backend/, com .env local (DEBUG=true, mocks de pagamento/LLM)
python manage.py migrate
python manage.py seed_beta
python manage.py runserver
```

O `seed_beta` deixa pronto (idempotente):

| Artefato | Valor |
|---|---|
| Staff | `beta.staff@techparts.local` / `beta-local-only` |
| Tester | `beta.tester@techparts.local` / `beta-local-only` |
| Equipamento | SKU `VTE-02` (Mondial) publicado |
| Peça | SKU `CAP-35` com estoque + compatibilidade |
| RAG | Manual VTE-02 indexado (capacitor / diagnóstico) |

Modos esperados: `PAYMENT_PROVIDER=mock`, `CHAT_LLM_MODE=mock` (ou `openai` se quiser LLM real).  
**Não** rode `seed_beta` em produção (`DEBUG=false` bloqueia; `--force` só em staging controlado).

## Script (ordem)

| # | Fluxo | Passos | Critério de sucesso |
|---|---|---|---|
| 1 | Cadastro via manual | Staff: upload PDF → revisão HITL → publicar (ou usar VTE-02 já seedado) | Produto no catálogo com SKU |
| 2 | Compra | Tester: buscar CAP-35 → carrinho → checkout mock → confirmação e-mail | Pedido `paid` + e-mail |
| 3 | Chat/diagnóstico | Sintoma no `/assistente/chat/` (ex.: “capacitor VTE-02”) → card + fonte | Resposta com citação; SKU se aplicável |
| 4 | Foto | Upload JPEG da peça | Candidatos ranqueados ou empty/`tp-empty` + CTA |
| 5 | Chamado | Abrir chamado pelo site ou 👎×2 no chat | Ticket com histórico; e-mail de status |
| 6 | Dashboard | Staff abre `/dashboard/` e `/dashboard/monitoramento/` | Insights + alertas sem admin cru |

## Coleta por sessão

Para cada tester, preencher uma linha em [`beta-relatorio.md`](beta-relatorio.md) § Sessões e anotar:

1. Clareza da UI (Industrial Precision / DoD visual)
2. Qualidade da resposta RAG (citação correta? alucinação?)
3. Tempo percebido (streaming / skeleton)
4. Confiança no card de diagnóstico
5. Facilidade de abrir chamado sem repetir o relato
6. Issues novas (P0 bloqueia / P1 UX / P2 polish) com dono

## Loop de qualidade

1. Priorizar issues no relatório
2. Atualizar golden set (`make golden` / `make golden-rag`) e prompts se houver regressão
3. Revisar DoD visual nas telas tocadas
4. Fechar aceite T-P.1 quando houver ≥1 sessão real documentada

## Critérios specify (avaliar ao final)

Ver `docs/specify.md` § sucesso: operação acompanha vendas/chamados/custo/qualidade **sem** abrir admin cru ou Flower no dia a dia; cliente compra e é acompanhado; chat cita fonte e escala com histórico.
