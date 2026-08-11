# Regra de ouro — inserção de valores nos campos de produto

> Aplicável à proposta da IA, ao botão **Aprovar e preencher formulário** e à revisão humana.
> Objetivo: catálogo legível, consistente e pronto para venda.

## Princípio

Inserir **dado de catálogo limpo**, não o texto cru do manual. Preferir o valor canônico
do sistema (marca/categoria/modelo já cadastrados) quando existir.

---

## Regras obrigatórias

### R1 — Inicial maiúscula (textos livres)
Todo valor textual de vitrine começa com **letra maiúscula**.
Exemplos: `Ventilador de teto`, `Abs`, `Preto`, `Fixação por parafuso`.

Aplica-se a: `name`, `description` (cada linha), `material`, `color`, `mounting`,
`bearing_type`, `category_name` (quando texto livre), rótulos equivalentes em `specs_extra`.

### R2 — Trim e espaços
Remover espaços no início/fim e colapsar espaços internos duplicados.
Não deixar linha em branco no meio da descrição.

### R3 — SKU técnico
`sku` sempre em **MAIÚSCULAS**, só `A-Z`, `0-9` e `-`, sem espaços.
Ex.: `MONDIAL-VTE-02`.

### R4 — Códigos de modelo
Preservar o código como no documento (em geral maiúsculas e hífens).
Não “embelezar” `VTE-02` para `Vte-02`.

### R5 — Campos numéricos sem unidade
Em `power_w`, `weight_kg`, dimensões, `diameter_cm`, `blade_count`, `rpm`: só o número.
A unidade fica no rótulo do campo (`W`, `kg`, `cm`), nunca no valor (`120 W` ✗ → `120` ✓).

### R6 — Voltagem canônica
Usar apenas: `110V`, `220V`, `Bivolt` (ou vazio se desconhecido).
Normalizar variantes (`127V/220V`, `bivolt`, `127 / 220`) para `Bivolt`.

### R7 — Descrição de venda
Máximo **4 linhas**. Cada linha com inicial maiúscula.
Tom de vitrine (por que comprar), só com fatos já extraídos — sem inventar specs.

### R8 — Cor e material
Preferir nome canônico da biblioteca de cores (ex.: `Preto`, `Azul`).
Material com inicial maiúscula (`Abs`, `Aço`, `Polipropileno`).

### R9 — Idioma
Textos de vitrine em **português brasileiro**.
Códigos, marcas e unidades técnicas permanecem como no original.

### R10 — Não inventar
Se o manual não trouxer o dado, deixar o campo vazio (exceto `description`, que pode
ser gerada pela regra de vitrine a partir dos fatos já conhecidos).

### R11 — Selects do catálogo
`brand_ref`, `equipment_model`, `category` recebem o **ID** da opção canônica
(criar no catálogo se ainda não existir), nunca o texto solto no select.

### R12 — Booleanos
`remote_included` e similares: `true`/`false` explícitos; nunca `sim`/`não` no JSON interno.

---

## Regras recomendadas (qualidade extra)

| # | Regra | Por quê |
|---|---|---|
| R13 | Evitar ALL CAPS em nome/descrição (`HÉLICE ABS` → `Hélice ABS`) | Visual de catálogo |
| R14 | Manter siglas conhecidas em maiúsculas no meio do texto (`ABS`, `LED`, `RPM`) | Legibilidade técnica |
| R15 | Uma informação por linha na descrição | Facilita scan na PDP |
| R16 | `specs_extra` no formato `chave=valor`, chave em `snake_case` | Parse estável |
| R17 | Não repetir no `name` o que já está em marca + modelo, se ficar redundante | SEO/UX |
| R18 | Remover ruído OCR (`l`, `|`, caracteres estranhos no fim) | Limpeza |
| R19 | Preço nunca vem da IA sem revisão humana | Risco comercial |
| R20 | Status inicial da proposta: `draft` | HITL |

### R21 — Manual não é foto
O PDF do manual **não conta** como foto de vitrine e **não** deve ser anexado
como `ProductImage`. Fotos = uploads/web escolhidos. O manual fica em
`product.manual` e pode ser baixado na página pública do produto.

---

## Exemplos

| Campo | Ruim | Bom |
|---|---|---|
| name | `ventilador de teto mondial` | `Ventilador de teto Mondial` |
| material | `ABS ` | `Abs` ou `ABS` (sigla) |
| color | `preto` | `Preto` |
| voltage | `127/220 v` | `Bivolt` |
| power_w | `120 W` | `120` |
| sku | `mondial vte-02` | `MONDIAL-VTE-02` |
| description | texto único em minúsculas | até 4 linhas, cada uma com inicial maiúscula |

---

## Onde isso é aplicado

- Prompt de extração (`extraction_v3.md`) — orientação ao agente
- Normalizador `apps.products.libraries.field_style` — na montagem de `form_suggestions`
- `InternalProductForm.clean_*` (`apps.products.forms`) — ao salvar pelo dashboard
- Revisão humana continua podendo editar antes de **Salvar**
