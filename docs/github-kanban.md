# Fase D — GitHub (Kanban, `develop`, colaborador)

Enunciado: [`senac.md`](senac.md) §§ 5.3–5.4. Fechada em 2026-08-25.

## Quadro Kanban

**URL (colar no AVA):** https://github.com/users/henriqueferraz/projects/2

Project **TechParts Senac M2.2** (público, nº 2), ligado ao repositório `henriqueferraz/manuais_projeto`. Colunas: Backlog, A Fazer, Em Andamento, Bloqueado, Em Revisão, Concluído.

## Branch `develop`

https://github.com/henriqueferraz/manuais_projeto/tree/develop

Fluxo:

```bash
git fetch origin
git checkout develop
git checkout -b feature/nome-curto
# PR: feature/* → develop → main (antes de 31/08 15h)
```

Evidência do fluxo nesta entrega:

| Passo | Artefato |
|---|---|
| Feature | `feature/senac-m22-entrega` |
| PR → `develop` | [#54](https://github.com/henriqueferraz/manuais_projeto/pull/54) (`cc2c4df`) |
| PR → `main` | [#55](https://github.com/henriqueferraz/manuais_projeto/pull/55) (`945b17f`) |
| `develop` alinhada à `main` | fast-forward após o merge da `#55` |

## Issues (cards)

Temas do enunciado, com objetivo / resultado / evidência no corpo:

| # | Tema | Coluna |
|---|---|---|
| [#44](https://github.com/henriqueferraz/manuais_projeto/issues/44) | Escopo e arquitetura | Concluído |
| [#43](https://github.com/henriqueferraz/manuais_projeto/issues/43) | LangGraph | Concluído |
| [#45](https://github.com/henriqueferraz/manuais_projeto/issues/45) | Tools | Concluído |
| [#46](https://github.com/henriqueferraz/manuais_projeto/issues/46) | Memória / RAG | Concluído |
| [#47](https://github.com/henriqueferraz/manuais_projeto/issues/47) | Segurança / adversarial | Concluído |
| [#49](https://github.com/henriqueferraz/manuais_projeto/issues/49) | Observabilidade | Concluído |
| [#50](https://github.com/henriqueferraz/manuais_projeto/issues/50) | QA com IA | Concluído |
| [#51](https://github.com/henriqueferraz/manuais_projeto/issues/51) | Pipeline / logs | Concluído |
| [#52](https://github.com/henriqueferraz/manuais_projeto/issues/52) | Anomalias / tendência | Concluído |
| [#53](https://github.com/henriqueferraz/manuais_projeto/issues/53) | Low-code n8n | Concluído |
| [#48](https://github.com/henriqueferraz/manuais_projeto/issues/48) | README, vídeo e AVA | **Em Andamento** (Fase E) |

Lista: https://github.com/henriqueferraz/manuais_projeto/issues?q=is%3Aissue+%5BSenac%5D

As issues fechadas `#43`–`#47` e `#49`–`#53` carregam a data de fechamento; o card `#48` permanece em andamento até o vídeo e o AVA.

## Professor colaborador

Convite concluído em 2026-08-25. A confirmação do colaborador é uma evidência externa ao repositório.

## Segredos

`.env` está no `.gitignore` (padrão `.env*`). `.env.example` é a única fonte versionada de variáveis.

## Commits

Mensagens semânticas (`feat:`, `fix:`, `docs:`). Um PR por `feature/*` para `develop`.
