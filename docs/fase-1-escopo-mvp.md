# Fase 1 — Escopo comercial e de IA (MVP)

> Entrega da tarefa **T-1.1** · Pilar **P01** · Branch `fase/1-escopo-mvp`  
> Fontes: [`specify.md`](specify.md), [`constitution.md`](constitution.md), [`plano-tarefas.md`](plano-tarefas.md), [`plano-ecommerce-ia-pecas.md`](plano-ecommerce-ia-pecas.md)

**Status:** aprovado para MVP  
**Data:** 2026-08-04

---

## 1. Decisão de valor (P01)

A IA só entra no produto se transformar **dado de manual** em:

1. **venda** (cadastro de catálogo / diagnóstico → peça), ou  
2. **suporte melhor** (RAG com fonte no manual), ou  
3. **economia operacional** (menos digitação / menos atendimento repetitivo).

Recursos que não se conectam a essa cadeia ficam fora do MVP.

---

## 2. Categorias do MVP

| Prioridade | Categoria | Motivo |
|---|---|---|
| P0 | **Ventiladores de teto** (produto completo) | Manuais previsíveis; exemplo já citado no plano (Mondial VTE-02/VTE-04) |
| P0 | **Peças de reposição de ventiladores** (hélices, capacitores, controles, etc.) | Compatibilidade e venda assistida são o diferencial |
| P1 (mesmo MVP, escopo estreito) | **Circuladores / ventiladores de mesa-coluna** da mesma linha de fabricantes | Amplia volume de teste sem mudar o schema |

**Não entram no MVP de catálogo:** linha branca completa, TVs, adegas, etc. — mesmo que existam PDFs no acervo local.

---

## 3. Fabricantes e manuais de validação (mín. 3 layouts)

Objetivo: testar robustez da extração (F3) com **layouts diferentes**, não só volume.

| # | Fabricante | Arquivo (acervo local `manuais/`) | Layout / por que |
|---|---|---|---|
| 1 | Mondial | `mondial/Manual-VTE-02.pdf` | Manual clássico de ventilador de teto (referência do plano) |
| 2 | Mondial | `mondial/Manual-VT-40-NB.pdf` | Outro modelo/layout Mondial (mesa/coluna) |
| 3 | Britânia | `britania/Documento_para_o_produto_Circulador_de_Ar_C60_Turb_Manual_-_Circulador_de_Ar_C60_Turbo_068V200000aVNV6IAO.pdf` | Naming/layout Britânia (documento longo + ficha) |
| 4 | Electrolux | `eletrolux/2010_680_00498umPT.pdf` (ou outro `*umPT.pdf` de linha de ar/ventilação após triagem) | Layout industrial Electrolux (código numérico) |
| 5 | — | `Vista Explodida.pdf` (raiz de `manuais/`) | Lista/explodida de peças — útil para peças de reposição |

> Os PDFs **não** vão para o Git (ver `.gitignore`). O golden set da F3 aponta para esses caminhos locais/staging.

**Critério de diversidade:** ≥3 fabricantes **ou** ≥3 famílias de layout (Mondial VT*, Britânia “Documento_para_o_produto_*”, Electrolux código numérico).

---

## 4. O que entra no MVP (in / out)

### Dentro (entregar até F4b–F5)

- Pipeline de ingestão de manuais + revisão humana (rascunho → publicar)
- Catálogo, estoque com reserva, carrinho, checkout, frete, pagamento tokenizado, NF-e, e-mail transacional
- Verificador de compatibilidade (modelo × peça)
- Chat RAG com citação de fonte + feedback 👍/👎 + escalonamento para chamado
- Chamados técnicos básicos (“Meus chamados”)
- Design system Industrial Precision (F0) aplicado às telas

### Fora de escopo imediato (specify §6 + plano)

- Multi-idioma em produção (schema já prevê i18n)
- WhatsApp em produção
- Rede de assistências parceiras ativa
- Assinatura de manutenção preventiva como produto comercial
- App/PWA offline para técnicos
- Expansão para fabricantes/categorias além da validação acima
- Busca por foto e diagnóstico LangGraph avançado (F6 — pós-MVP core, mas planejado)

---

## 5. Critérios de sucesso (specify §7) — checklist MVP

O MVP cumpre o propósito quando:

- [ ] Novo produto pode ser cadastrado a partir do manual com esforço humano muito menor que digitar tudo, após revisão
- [ ] Chat resolve parcela relevante das dúvidas técnicas com fonte; ao escalar, histórico vai junto
- [ ] Cliente descobre a peça por **modelo** e/ou **sintoma** (foto fica para F6)
- [ ] Operação acompanha o essencial (pedidos, chamados, custo de IA quando houver chat) sem depender só de admin cru
- [ ] Loja vende no Brasil: NF-e, arrependimento (F4d), LGPD básica

---

## 6. Sequência após esta fase

Conforme [`plano-tarefas.md`](plano-tarefas.md) / R2: merge F1 → **F0** (design system) → **F2** (base Django/CI) → F3…
