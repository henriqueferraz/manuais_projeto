# Fase 1 — Schema mínimo de produto (MVP)

> Entrega da tarefa **T-1.2** · Pilares **P01, P11** · Branch `fase/1-escopo-mvp`  
> Alinhado a F3 (extração) e F4a (catálogo). Implementação Django na F2/F4a.

**Status:** aprovado para modelagem inicial  
**Data:** 2026-08-04

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
| `category_id` | FK | sim | revisão humana | ex.: ventiladores / hélices |
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
| Lista de peças de reposição | novos `Product` (`spare_part`) + `Compatibility` |
| Esquemas / segurança | **não** viram spec de venda; vão para chunks RAG (F5) |

Saída da IA: JSON validado contra schema Pydantic espelhando esta tabela **antes** de gravar rascunho.

---

## 7. Fora do schema mínimo (vem depois, sem bloquear F4a)

- `Ticket`, `ChatFeedback`, `Coupon`, `ReturnRequest` — F4c/F4d/F5  
- `SubscriptionPlan`, `PartnerService` — F8  
- `ManualChunk` + embedding — F5  
- Carrinho/pedido — models de `cart` / `orders` na F4a–F4b  

---

## 8. Aceite T-1.2

- [x] Campos mínimos para vender documentados  
- [x] i18n previsto via `ProductTranslation`  
- [x] Mapeamento manual → schema explícito para F3/F4a  
