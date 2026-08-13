# Pilares para Construção do App de IA — Venda de Peças e Produtos

Stack: Python + Django + htmx + Bootstrap + PostgreSQL + Cloudflare R2 + LangChain/LangGraph

> **Nota:** este arquivo é o índice conceitual dos 24 pilares. Stack LLM vigente = **OpenAI** (`*_LLM_MODE`); telas = [`pages/inventory.md`](pages/inventory.md). Detalhe por pilar em [`pilares/`](pilares/).

---

## Parte 1 — Pilares Gerais para Apps de IA

### 1. Propósito e escopo bem definidos
Definir claramente qual problema a IA resolve, evitando tentar cobrir tudo de forma rasa. Melhor fazer poucas coisas muito bem do que muitas de forma mediana.

### 2. Qualidade dos dados e do contexto
- RAG (Retrieval-Augmented Generation) bem implementado
- Prompts bem engenheirados (instruções claras, exemplos, formato de saída esperado)
- Gerenciamento de memória/histórico de conversa quando relevante

### 3. Experiência de usuário (UX) pensada para IA
- Streaming de respostas (não fazer o usuário esperar o texto inteiro)
- Estados de carregamento e feedback visual claros
- Design para incerteza (deixar claro quando a IA pode errar, permitir correções)
- Fallbacks graciosos quando a IA falha ou não sabe responder

### 4. Arquitetura técnica sólida
- Separação clara entre frontend, backend e camada de IA (chaves de API nunca no cliente)
- Cache de respostas quando fizer sentido
- Rate limiting e controle de custos
- Tratamento de erros robusto (timeouts, respostas malformadas)

### 5. Segurança e privacidade
- Validação e sanitização de inputs do usuário
- Cuidado com dados sensíveis (evitar logs desnecessários de informações pessoais)
- Proteção contra prompt injection

### 6. Avaliação e testes contínuos
- Testes com casos reais e extremos (edge cases)
- Métricas de qualidade, não só "funciona"
- Loop de feedback do usuário para melhorar prompts/modelo

### 7. Custo e performance
- Escolha do modelo certo para cada tarefa
- Monitoramento de latência
- Otimização de tamanho de prompts (menos tokens = mais rápido e barato)

### 8. Transparência com o usuário
- Deixar claro quando o usuário interage com IA
- Explicar limitações quando relevante
- Dar controle ao usuário (editar, regenerar, desfazer respostas)

---

## Parte 2 — Pilares Específicos do Projeto (Peças e Produtos)

### 9. Pipeline de ingestão de manuais
Fluxo: `Manual (PDF/imagem) → Extração → Estruturação → Validação humana → Catálogo`

- **Extração**: OCR para manuais escaneados; parsing direto de texto/tabelas para PDFs nativos
- **Estruturação via LangChain/LangGraph**: grafo com nós especializados (specs técnicas, SKU, descrição comercial, categoria/compatibilidade)
- **Saída estruturada**: JSON com schema fixo (Pydantic + `with_structured_output`)
- **Human-in-the-loop obrigatório**: nunca publicar automaticamente sem revisão humana
- **Versionamento do manual original**: guardar o PDF fonte no R2, vinculado ao produto, para auditoria

### 10. RAG para dúvidas técnicas dos clientes
- **Chunking pensado no domínio**: por seção/parágrafo semântico, preservando tabelas e mantendo metadados (produto, seção, página)
- **Banco vetorial**: pgvector no próprio PostgreSQL (evita serviço externo adicional)
- **Metadados como filtro**: filtrar por produto/categoria antes da busca semântica
- **LangGraph para o fluxo de resposta**: identificação do produto → retrieval → geração → verificação
- **Citação de fonte**: toda resposta técnica deve referenciar a página/seção do manual original
- **Fallback explícito**: dizer "não encontrei isso no manual" em vez de inventar respostas, especialmente sobre segurança

### 11. Modelagem de dados (Django + PostgreSQL)
- `Product` — dados do produto
- `Manual` — FK para o PDF no R2
- `ManualChunk` — trechos do manual com embedding (pgvector)
- `ExtractionLog` — histórico de execuções da IA, revisão humana, timestamps

### 12. Frontend com htmx
- Streaming de respostas via SSE (`StreamingHttpResponse` do Django)
- Indicadores de carregamento (`hx-indicator`)
- Feedback do usuário (👍/👎) em respostas técnicas
- Bootstrap para componentes visuais padrão

### 13. Observabilidade
- **LangSmith** para tracing de cada execução do grafo (LangChain/LangGraph)
- Logs estruturados (ex: `structlog`) correlacionando `request_id` do Django com `trace_id` do LangSmith
- Métricas de negócio: taxa de aprovação humana das extrações, taxa de "não encontrei resposta", tempo médio de resposta
- Alertas de custo (gasto em tokens por dia/produto processado)

### 14. CI/CD
- Testes automatizados para prompts/grafos, com dataset de manuais de teste e gabarito conhecido
- Migrations do Postgres + pgvector no pipeline padrão do Django
- Ambientes separados (staging com projeto LangSmith próprio, isolado da produção)

### 15. Segurança aplicada ao domínio
- Chaves de API nunca expostas no client — tudo via backend Django
- Proteção contra prompt injection via manuais (texto oculto, PDFs maliciosos) — sanitizar antes de enviar ao LLM
- Proteção contra prompt injection via cliente no chat técnico — isolar system prompt, usar guardrails/validators
- Rate limiting no chat técnico (por IP/usuário)
- Conformidade com LGPD para histórico de conversas e dados pessoais

---

## Parte 3 — Pilares de Experiência Visual e Qualidade de Design

### 16. Sistema de design consistente (Design System)
- Paleta de cores, tipografia e espaçamento próprios (customizar variáveis do Bootstrap para fugir do visual genérico)
- Componentes reutilizáveis e documentados (cards de produto, badges de especificação técnica, botões)
- Um único set de ícones consistente em todo o site

### 17. Hierarquia visual e tipografia
- Contraste claro entre títulos, specs técnicas e texto corrido
- Uso de peso e tamanho de fonte para guiar o olho (nome do produto > preço > specs principais > descrição)
- Espaço em branco generoso, evitando páginas de produto muito "cheias"

### 18. Fotografia e apresentação de produto
- Padrão consistente de imagens (fundo neutro, mesmo ângulo, mesma iluminação)
- Zoom e múltiplos ângulos na página de produto
- Imagens otimizadas via Cloudflare R2 (WebP/AVIF) com lazy loading

### 19. Estados de interface (loading, vazio, erro)
- Skeleton screens em vez de spinners genéricos
- Empty states bem desenhados (ex: "nenhum produto encontrado" com sugestão de busca)
- Estados de erro amigáveis com ação clara de recuperação, inclusive no chat técnico

### 20. Microinterações e feedback visual
- Transições suaves em hover, filtros e envio de mensagens (htmx + `hx-swap` + CSS transitions)
- Feedback visual imediato em ações (carrinho, favoritos, envio de pergunta)
- Indicador visual de "IA está digitando/pensando" no chat técnico

### 21. Responsividade e mobile-first
- Priorizar design para telas pequenas (grande parte da busca por peças vem de mobile)
- Chat técnico funcional em mobile (teclado não cobrir input, mensagens legíveis sem zoom)

### 22. Acessibilidade (a11y)
- Contraste adequado (WCAG AA), especialmente em badges de status e specs técnicas
- Navegação por teclado funcional em todo o site, incluindo o chat
- Textos alternativos (`alt`) em imagens e ícones (também bom para SEO)

### 23. Design da experiência de busca e filtros
- Filtros técnicos claros e rápidos (compatibilidade, modelo, voltagem, categoria)
- Busca com autocomplete/sugestões visuais (miniatura do produto na lista de sugestões)
- Diferencial visual de "busca por sintoma" (ex: "minha geladeira não gela" → IA sugere peças)

### 24. Identidade visual da marca
- Definir tom visual: técnico/industrial vs. consumer-friendly — guia cor, fonte e fotografia
- Consistência visual entre página de produto e widget de chat técnico (chat não deve parecer elemento "colado")

---

## Resumo Visual do Fluxo Central

```
┌─────────────────┐      ┌──────────────────┐      ┌─────────────────┐
│  Manual (PDF)    │ ───▶ │  LangGraph:       │ ───▶ │  Revisão Humana │
│  upload → R2     │      │  Extração/        │      │  (Django Admin) │
└─────────────────┘      │  Estruturação     │      └────────┬────────┘
                          └──────────────────┘               │
                                                               ▼
                                                      ┌─────────────────┐
                                                      │  Catálogo        │
                                                      │  (Product)       │
                                                      └─────────────────┘

┌─────────────────┐      ┌──────────────────┐      ┌─────────────────┐
│  Cliente         │ ───▶ │  LangGraph RAG:   │ ───▶ │  Resposta com    │
│  pergunta (htmx) │      │  Retrieval →      │      │  fonte + stream  │
│                  │      │  Geração →        │      │  (SSE)           │
│                  │      │  Verificação       │      │                  │
└─────────────────┘      └──────────────────┘      └─────────────────┘
```
