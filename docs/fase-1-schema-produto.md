# Fase 1 — Schema mínimo de produto (MVP)

> Entrega da tarefa **T-1.2** · Pilares **P01, P11** · Branch `fase/1-escopo-mvp`  
> Alinhado a F3 (extração) e F4a (catálogo). Implementação Django na F2/F4a.

**Status:** schema F1 aprovado; **evoluído** com multi-categoria (`categories` M2M) — ver seção abaixo.  
**Data:** 2026-08-04 · atualização categorias: 2026-08-13

---

## 1. Princípios

- Schema **mínimo para vender** + campos que a extração do manual consegue preencher.
- Preparado para **i18n** (campos traduzíveis separados), sem exigir conteúdo multi-idioma no MVP.
- Produto nasce como **rascunho** até revisão humana (`status`).
- Manual PDF fica no R2; produto guarda referência (`Manual`), não o binário no Git.

---

## 2. Entidades mínimas

```text
Category
Product (+ ProductTranslation)
ProductImage
Stock
Compatibility (equipment_model × part Product)
Manual
ManualChunk          # F5 — previsto, não obrigatório no schema de venda
ExtractionLog        # F3
```

---

## 3. `Product` — campos mínimos

| Campo | Tipo | Obrig. MVP | Origem típica | Notas |
|---|---|---|---|---|
| `sku` | string único | sim | manual / interno | índice |
| `slug` | string único | sim | gerado | URL |
| `status` | enum | sim | workflow | `draft` \| `published` \| `archived` |
| `product_kind` | enum | sim | classificação | `finished_good` \| `spare_part` |
| `category_id` | FK nullable | sim* | revisão humana | *Schema F1: FK única. **Evolução atual:** ver nota abaixo |
| `brand` | string | sim | manual | Mondial, Britânia… |
| `model_code` | string | sim | manual | VTE-02, VT-40-NB… |
| `name` | string | sim* | manual | *via translation `pt` no MVP |
| `description` | text | não | manual / edição | translation |
| `price` | decimal | sim | humano / regra | venda |
| `currency` | string | sim | default `BRL` | |
| `voltage` | enum/string | cond. | manual | `110V` \| `220V` \| `Bivolt` \| n/a |
| `power_w` | decimal | não | manual | potência |
| `weight_kg` | decimal | não | manual | frete |
| `dimensions` | JSON/texto | não | manual | A×L×P |
| `specs` | JSON | não | manual | chave→valor livres (pás, diâmetro, material…) |
| `manual_id` | FK nullable | não | pipeline | PDF fonte |
| `extraction_confidence` | float | não | IA | UI de revisão |
| `published_at` | datetime | não | publicação | |
| `created_at` / `updated_at` | datetime | sim | sistema | |

### Evolução pós-F1 — múltiplas categorias (2026-08)

O schema F1 acima previa **uma** categoria (`category` FK). O código vigente também tem:

| Campo | Tipo | Papel |
|---|---|---|
| `categories` | M2M → `catalog.Category` | Todas as categorias (ex.: Peça de reposição + Móveis) |
| `category` | FK nullable | Categoria **principal** (sync: primeira marcada no form) |

Formulário dashboard: checkboxes `categories` — ver [`pages/dashboard-produto.md`](pages/dashboard-produto.md).  
Migration: `products.0009_product_categories_m2m`.

### `ProductTranslation` (i18n desde o início)

| Campo | Notas |
|---|---|
| `product_id` + `locale` | PK composta; MVP usa só `pt-BR` |
| `name`, `description`, `slug` opcional por locale | |

No MVP, a UI pode ler só `pt-BR`; a tabela já existe para não remodelar na F8.

### Specs sugeridas para ventiladores / peças (dentro de `specs`)

`blade_count`, `diameter_cm`, `material`, `color`, `rpm`, `mounting`, `bearing_type`, `remote_included` — preenchidas quando o manual tiver.

---

## 4. Estoque e compatibilidade

### `Stock`

| Campo | Notas |
|---|---|
| `product_id` | 1:1 |
| `quantity_available` | |
| `quantity_reserved` | checkout |
| `minimum_alert` | alerta reposição |

### `Compatibility`

| Campo | Notas |
|---|---|
| `equipment_brand` | ex.: Mondial |
| `equipment_model` | ex.: VTE-02 |
| `part_product_id` | FK peça |
| `notes` | opcional |

Populada pela extração + revisão; consulta do verificador = ORM, sem LLM.

---

## 5. Manual e extração (contrato com F3)

### `Manual`

| Campo | Notas |
|---|---|
| `r2_key` / URL assinada | PDF no Cloudflare R2 |
| `filename`, `sha256`, `mime`, `size` | auditoria |
| `manufacturer`, `source_locale` | |
| `product_id` | nullable até vincular |

### `ExtractionLog`

| Campo | Notas |
|---|---|
| `manual_id` | |
| `started_at`, `finished_at` | |
| `status` | `running` \| `awaiting_review` \| `approved` \| `rejected` \| `failed` |
| `raw_json` | saída estruturada (validada Pydantic) |
| `model_name`, `tokens_in`, `tokens_out`, `cost_estimate` | P07 |
| `reviewed_by`, `reviewed_at` | HITL |
| `langsmith_trace_id` | quando houver |

---

## 6. Mapeamento manual → schema (extração)

| Trecho típico do manual | Campo destino |
|---|---|
| Nome / título do produto | `ProductTranslation.name` |
| Modelo / referência | `model_code`, parte do `sku` |
| Marca / fabricante | `brand` |
| Voltagem | `voltage` |
| Potência (W) | `power_w` |
| Dimensões / peso | `dimensions`, `weight_kg` |
| Características numeradas | `specs` (+ descrição) |
| EAN / NCM / freq. / capacidade / garantia / variantes | `Product.specs` (merge no approve; sem colunas dedicadas) |
| Lista de peças/acessórios vendáveis (`sellable_separately` + `code`) | novos `Product` (`spare_part`, status `draft`) + `Compatibility` |
| Itens só de composição (sem código / `sellable_separately=false`) | permanecem no `ExtractionLog` JSON (BOM); **não** viram produto de venda |
| BOM (`ref_number`, `qty_per_unit`) | `Compatibility.notes` (ex.: `ref=11; qty=2`) |
| Divergências entre trechos/documentos | `document_conflicts` → merge em `Product.specs` (HITL; não escolher em silêncio) |
| Esquemas / segurança | resumos podem ir a `specs`; texto completo segue nos chunks RAG (F5) |

Saída da IA: JSON validado contra schema Pydantic (`ExtractedProduct` / prompt `extraction_v3`) **antes** de gravar rascunho.

### Status da materialização no approve (HITL)

- [x] Produto principal → `Product` draft + `ProductTranslation`
- [x] Campos órfãos do prompt v3 → merge em `Product.specs` (incl. `document_conflicts`)
- [x] Peças/acessórios vendáveis → `Product(spare_part)` draft + `Compatibility`
- [x] Itens sem código → composição apenas (JSON do log)
- [x] Prompt de extração `v3` (Parte 0: escopo produto/peça/uso/conserto; sem alteração de código; só sugestões)
- [x] Chat/diagnóstico alinhados aos guardrails da Parte 0 (`chat_system_v2`, `diagnosis_system_v2`)
- [ ] Modelo BOM dedicado / estoque automático — fora do escopo atual
- [ ] Publicação automática de peças — **proibida** (P02/P09)

---

## 7. Fora do schema mínimo (vem depois, sem bloquear F4a)

- `Ticket`, `ChatFeedback`, `Coupon`, `ReturnRequest` — F4c/F4d/F5  
- `SubscriptionPlan`, `PartnerService` — F8  
- `ManualChunk` + embedding — F5  
- Carrinho/pedido — models de `cart` / `orders` na F4a–F4b  
- Modelo BOM dedicado (qty/ref fora de `Compatibility.notes`)  

---

## 8. Aceite T-1.2

- [x] Campos mínimos para vender documentados  
- [x] i18n previsto via `ProductTranslation`  
- [x] Mapeamento manual → schema explícito para F3/F4a  
- [x] Materialização de peças no approve alinhada ao prompt v3  
- [x] Campo `document_conflicts` + guardrails Parte 0  
