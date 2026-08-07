# Relatório de beta — TechParts AI (F7 / T-7.3)

**Status:** template pronto para preenchimento pós-sessões de beta.  
**Data:** _YYYY-MM-DD_  
**Participantes:** _N testers_

## Resumo executivo

- Escopo testado: cadastro via manual, compra, chat/diagnóstico, foto, chamado, dashboard.
- Resultado geral: _aprovado com ressalvas / precisa iteração_.

## Issues priorizadas

| ID | Severidade | Área | Descrição | Ação |
|---|---|---|---|---|
| B-001 | P0 | _|_ | _|_ |
| B-002 | P1 | _|_ | _|_ |
| B-003 | P2 | _|_ | _|_ |

## Qualidade das respostas (RAG / diagnóstico)

- Taxa percebida de citação correta: _%_
- Casos de alucinação / fallback: _
- Golden set atualizado? [ ] sim [ ] não (`make golden` / `make golden-rag`)

## DoD visual (telas críticas)

| Tela | Passou checklist? | Notas |
|---|---|---|
| Catálogo / PDP | [ ] | |
| Chat / diagnóstico | [ ] | |
| Checkout | [ ] | |
| Chamados | [ ] | |
| Dashboard insights/monitoramento | [ ] | |

## Critérios de sucesso (specify)

| Critério | Met? | Evidência |
|---|---|---|
| Operação vê chat/chamados/vendas IA/custo no dashboard | [ ] | `/dashboard/` |
| Incidente aparece no monitoramento + alerta | [ ] | `/dashboard/monitoramento/` |
| Cliente compra e acompanha sem “ficar no escuro” | [ ] | e-mails / status |
| HITL impede publicação automática | [ ] | fila de revisão |

## Próximos passos

1. _
2. _
3. Entrar na Fase 8 apenas com ADRs por item (WhatsApp, assinatura, etc.)
