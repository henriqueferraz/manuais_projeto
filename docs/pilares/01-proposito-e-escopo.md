# Pilar 01 — Propósito e escopo bem definidos

> **Parte 1 — Pilares Gerais para Apps de IA** · Fonte-mestre: [`pilares-app-ia-vendas-pecas.md`](../pilares-app-ia-vendas-pecas.md)

## Definição do pilar

Definir claramente qual problema a IA resolve, evitando tentar cobrir tudo de forma rasa. Melhor fazer poucas coisas muito bem do que muitas de forma mediana.

## O que o projeto existe para fazer

O projeto vende peças e produtos de reposição usando **IA como motor de automação e diferencial competitivo**, não como enfeite. As duas trilhas centrais devem permanecer o coração do produto:

1. **Extração automática de catálogo** a partir de manuais do fabricante
2. **Suporte técnico via RAG** com base nesses mesmos manuais

Todo novo recurso de IA deve responder: *isso transforma dado de manual em venda, em suporte melhor, ou em economia operacional?* Recursos que não se conectam a essa cadeia são candidatos a corte ou adiamento.

## Por que isso importa

Cadastrar um catálogo tecnicamente detalhado é trabalho manual lento; o suporte pós-venda depende de atendentes que precisam conhecer cada manual. Extrair estrutura e conhecimento do manual faz o mesmo documento alimentar venda e suporte.

## Para quem é

- Cliente final (muitas vezes resolvendo equipamento quebrado)
- Equipe interna de catálogo (revisar/aprovar extrações)
- Equipe de suporte/operação
- Técnicos de campo e assistências parceiras (fases posteriores)

## Critério de priorização

O núcleo comercial (estoque, checkout, pagamento, frete, NF-e) vem **antes** dos diferenciais de IA que dependem dele. Automação de catálogo e suporte via IA pousam sobre uma base comercial funcional.

## Fora de escopo imediato (visão longa, não bloquear MVP)

- Multi-idioma em produção
- WhatsApp em produção
- Rede de assistências e assinatura de manutenção como produtos completos
- App offline para técnicos
- Expansão além do escopo inicial de validação

## Fontes

- `constitution.md` — Artigos 1 e 6
- `specify.md` — §§1–3, 6–7
- `techparts_ai_project_brief.md` — Overview e objetivos
- `plano-ecommerce-ia-pecas.md` — Contexto e funcionalidades diferenciais
- `plan.md` — Objetivo
