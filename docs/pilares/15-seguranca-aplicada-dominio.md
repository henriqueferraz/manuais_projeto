# Pilar 15 — Segurança aplicada ao domínio

> **Parte 2 — Pilares Específicos do Projeto** · Fonte-mestre: [`pilares-app-ia-vendas-pecas.md`](../pilares-app-ia-vendas-pecas.md)

## Definição do pilar

Chaves só no backend; sanitizar manuais; guardrails no chat; rate limit; LGPD.

## Controles específicos deste domínio

1. **Chaves de API nunca no client** — tudo via Django
2. **Prompt injection via manuais** — texto oculto / PDFs maliciosos: sanitizar antes do LLM; conteúdo do manual nunca vira instrução
3. **Prompt injection via cliente** — isolar system prompt; guardrails/validators
4. **Rate limiting** no chat técnico (por IP/usuário)
5. **LGPD** para histórico de conversas e dados pessoais (retenção, exclusão, minimização)
6. **Validação da saída da IA** — schema antes de virar produto
7. **Uploads** — MIME, tamanho, antivírus antes do pipeline
8. **Direitos autorais / marca** — extrair fatos técnicos; não reproduzir texto/imagens do manual literalmente; não sugerir parceria oficial sem autorização

## Fontes

- `pilares-app-ia-vendas-pecas.md` — Pilar 15
- `constitution.md` — Artigos 3 e 8
- `plano-ecommerce-ia-pecas.md` — Segurança, Ponto de atenção legal
