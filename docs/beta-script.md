# Script de testes — Beta fechado (F7 / T-7.3)

Objetivo: validar o MVP com usuários reais (ou proxy internos) e alimentar o loop de qualidade.

## Pré-requisitos

- Conta staff + usuário convidado (beta)
- Manual indexado (ex. VTE-02) e ao menos 1 peça publicada com estoque
- `CHAT_LLM_MODE=mock` ou Anthropic configurado
- Pagamento `PAYMENT_PROVIDER=mock`

## Script (ordem)

| # | Fluxo | Passos | Critério de sucesso |
|---|---|---|---|
| 1 | Cadastro via manual | Upload PDF → revisão HITL → publicar produto | Produto no catálogo com SKU |
| 2 | Compra | Buscar peça → carrinho → checkout mock → confirmação e-mail | Pedido `paid` + e-mail |
| 3 | Chat/diagnóstico | Sintoma no `/assistente/chat/` → card + fonte | Resposta com citação; SKU se aplicável |
| 4 | Foto | Upload JPEG da peça | Candidatos ranqueados ou rejeição MIME |
| 5 | Chamado | Abrir chamado pelo site ou 👎×2 no chat | Ticket com histórico; e-mail de status |
| 6 | Dashboard | Staff abre `/dashboard/` e `/dashboard/monitoramento/` | 4 áreas de insights + alertas |

## Coleta de feedback

Para cada tester, anotar:

1. Clareza da UI (Industrial Precision / DoD visual)
2. Qualidade da resposta RAG (citação correta? alucinação?)
3. Tempo percebido (streaming / skeleton)
4. Confiança no card de diagnóstico
5. Facilidade de abrir chamado sem repetir o relato

## Loop de qualidade

1. Priorizar issues (P0 bloqueia beta / P1 UX / P2 polish)
2. Atualizar golden set (`make golden` / `make golden-rag`) e prompts
3. Revisar DoD visual nas telas: catálogo, PDP, chat, checkout, chamados, dashboard
4. Preencher [relatório de beta](beta-relatorio.md)

## Critérios specify (avaliar ao final)

Ver `docs/specify.md` § sucesso: operação acompanha vendas/chamados/custo/qualidade **sem** abrir admin cru ou Flower para o dia a dia.
