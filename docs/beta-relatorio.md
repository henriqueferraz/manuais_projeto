# Relatório de beta — TechParts AI (T-P.1 / pós-F8)

**Status:** infraestrutura de sessão pronta (`seed_beta`); sessões com usuários reais **pendentes**.  
**Data:** 2026-08-07  
**Participantes:** 0 testers externos · auditoria DoD visual já feita (T-P.3 / PR `#19`)  
**Branch/base:** `main` @ T-P.3 + branch `fase/pos-f8-tp1-beta-humana`

## Resumo executivo

- Escopo a validar com humanos: compra mock, chat/diagnóstico com citação, foto, chamado, dashboard ops.
- DoD visual das superfícies críticas: **aprovado** em T-P.3 (ver § DoD abaixo).
- Débito consciente: home marketing (HOME); integrações live (T-P.4); Playwright (T-P.6).

## Sessões

| ID | Data | Tester | Papel | Ambiente | Fluxos (# script) | Notas |
|---|---|---|---|---|---|---|
| — | — | — | — | — | — | Nenhuma sessão ainda — rodar `seed_beta` + [`beta-script.md`](beta-script.md) |

### Template de sessão (copiar)

```
### S-00X — AAAA-MM-DD — <nome>
- Papel: cliente | staff ops
- Ambiente: local mock | staging
- Fluxos: 1☐ 2☐ 3☐ 4☐ 5☐ 6☐
- UI (1–5): _
- RAG citação ok?: sim / parcial / não — evidência: _
- Alucinação / fallback: _
- Tempo percebido: _
- Confiança no diagnóstico (1–5): _
- Chamado sem repetir relato?: _
- Issues: (IDs novos ou N/A)
```

## Issues priorizadas

| ID | Severidade | Área | Descrição | Dono | Ação |
|---|---|---|---|---|---|
| HOME | P2 | Home | Hero loja vs shell técnico | — | Adiado (fora T-P.1) |
| B-001…B-006 | — | — | Fechados em T-P.3 | — | Ver histórico abaixo |

### Histórico (auditoria código/UI — não substituem beta humana)

| ID | Severidade | Área | Descrição | Ação |
|---|---|---|---|---|
| B-001 | P1 | Dashboard | ~~Widgets genéricos~~ | **Corrigido** — `tp-stat` / `tp-panel` |
| B-002 | P2 | Catálogo | ~~Specs acima do preço~~ | **Corrigido** |
| B-003 | P2 | Checkout | ~~Sem skeleton~~ | **Corrigido** |
| B-004 | P2 | Chat | ~~Empty foto~~ | **Corrigido** |
| B-005 | P2 | F8 | ~~Cards genéricos~~ | **Corrigido** |
| B-006 | P2 | Geral | ~~Confronto informal~~ | **Corrigido** |

~~B-000 P0~~ Cyan em chamados/monitoramento — **corrigido**.

## Qualidade das respostas (RAG / diagnóstico)

Preencher após ≥1 sessão real:

| Métrica | Valor |
|---|---|
| Taxa percebida de citação correta | _n/d_ |
| Casos de alucinação / fallback | _n/d_ |
| Golden set atualizado? | [x] base F8 verde — atualizar se beta revelar regressão |

Perguntas-guia do seed: “Qual o capacitor de partida do VTE-02?” · “Ventilador faz barulho e não gira”.

## DoD visual (telas críticas)

Critério: [VISUAL-REVIEW-CHECKLIST.md](../design-system/docs/VISUAL-REVIEW-CHECKLIST.md) · confronto: [`PROTOTYPE-CONFRONTATION.md`](design/PROTOTYPE-CONFRONTATION.md)

| Tela | Checklist código | Validação humana |
|---|---|---|
| Catálogo / PDP | [x] | [ ] |
| Chat / diagnóstico | [x] | [ ] |
| Checkout | [x] | [ ] |
| Chamados | [x] | [ ] |
| Dashboard | [x] | [ ] |
| Assinaturas / Assistências / Garantia | [x] | [ ] |

## Critérios de sucesso (specify)

| Critério | Código | Humano |
|---|---|---|
| Operação vê chat/chamados/vendas IA/custo no dashboard | [x] | [ ] |
| Incidente aparece no monitoramento + alerta | [x] | [ ] |
| Cliente compra e acompanha sem “ficar no escuro” | [x] parcial | [ ] |
| HITL impede publicação automática | [x] | [ ] |
| Chat cita fonte; ao escalar, histórico vai junto | [x] | [ ] |
| Descoberta por sintoma / modelo / foto | [x] | [ ] |

## Aceite T-P.1

- [ ] ≥1 sessão real documentada na tabela Sessões
- [ ] Taxa RAG / alucinação preenchida (mesmo que qualitativa)
- [ ] Issues P0/P1 com dono (ou “nenhuma”)
- [ ] Golden/prompts atualizados se houver regressão

## Próximos passos

1. Rodar `python manage.py seed_beta` e a primeira sessão pelo [`beta-script.md`](beta-script.md).
2. Após aceite T-P.1 → T-P.2 (hardening/staging).
3. Opcional em paralelo: HOME, T-P.6 Playwright.
