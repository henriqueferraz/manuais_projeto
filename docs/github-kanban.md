# Fase D — GitHub (Kanban, `develop`, colaborador)

Enunciado: [`senac.md`](senac.md) §§ 5.3–5.4.

## Branch `develop`

Criada a partir de `main` (SHA `1006553`, mesmo HEAD remoto de 2026-08-25):

https://github.com/henriqueferraz/manuais_projeto/tree/develop

Daí em diante:

```bash
git fetch origin
git checkout develop
git checkout -b feature/nome-curto
# PR: feature/* → develop → main (antes de 31/08 15h)
```

As mudanças locais das Fases A–C ainda **não** estão na `develop`/`main` até um commit + PR.

## Issues (cards)

Temas do enunciado, com objetivo / resultado / evidência no corpo:

| # | Tema | Coluna sugerida |
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
| [#48](https://github.com/henriqueferraz/manuais_projeto/issues/48) | README, vídeo e AVA | **Em Andamento** |

Lista: https://github.com/henriqueferraz/manuais_projeto/issues?q=is%3Aissue+%5BSenac%5D

## Project Kanban (você cria no browser)

O token `gh` atual **não tem** scope `project`. Um comando no PC (abre o login do GitHub):

```bash
gh auth refresh -s project,read:project
gh project create --owner henriqueferraz --title "TechParts Senac M2.2"
```

Ou: repositório → **Projects** → **New project** → Board.

Colunas pedidas: **Backlog**, **A Fazer**, **Em Andamento**, **Bloqueado**, **Em Revisão**, **Concluído**.

Depois: **…** no projeto → **Settings** → **Linked repositories** → `manuais_projeto` → adicionar as issues `#43`–`#53`. Arraste para as colunas da tabela acima. **Não** deixe tudo em Concluído no mesmo dia sem histórico — as issues fechadas já mostram data; o card `#48` deve andar até o vídeo.

Cole a URL do projeto no AVA e neste arquivo (substitua TBD).

**URL do quadro:** TBD

## Professor colaborador

Settings do repo → **Collaborators** → convite com o **GitHub do professor** (está no AVA, não neste repo).

## Segredos

`.env` está no `.gitignore` (padrão `.env*`). `.env.example` é a única fonte versionada de variáveis.

## Commits

Mensagens semânticas (`feat:`, `fix:`, `docs:`). Um PR por `feature/*` para `develop`.
