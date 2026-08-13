**E-commerce de peças com IA**

*Plano de arquitetura, tecnologias e diferenciais*

> **Documento histórico** (roadmap longo original). Para status atual use [`plano-tarefas.md`](plano-tarefas.md); stack LLM vigente = OpenAI (`*_LLM_MODE`); telas = [`pages/inventory.md`](pages/inventory.md).

**Versão atualizada com stack: Python + Django + htmx + Bootstrap +
PostgreSQL + Cloudflare R2 — agora com LangChain/LangGraph,
observabilidade, CI/CD e segurança**

Contexto

A proposta é construir um site de venda de peças e produtos (inspirado
no modelo da Britânia e Philco) com um diferencial central: uso de IA
para automatizar o cadastro de produtos a partir dos manuais e para
responder dúvidas técnicas dos clientes com base nesses mesmos manuais.

Manuais de fabricante — como o de exemplo analisado (ventilador de teto
Mondial VTE-02/VTE-04) — seguem padrões razoavelmente previsíveis:
características numeradas, especificações técnicas, esquemas elétricos,
lista de peças de reposição. Isso torna a automação via IA bastante
viável.

Arquitetura geral

O manual alimenta duas trilhas de IA em paralelo:

- Uma trilha extrai dados estruturados do produto (nome, modelo,
  voltagem, potência, peças de reposição, etc.), que alimentam o
  catálogo e a loja online.

- Outra trilha gera embeddings a partir do conteúdo do manual, que
  alimentam uma base vetorial usada pelo chat de suporte técnico (RAG —
  Retrieval-Augmented Generation).

Ambos os caminhos convergem no cliente: ele compra produtos no catálogo
gerado automaticamente e tira dúvidas técnicas no chat, que responde com
base no manual real do produto.

Funcionalidades diferenciais do projeto

As funcionalidades abaixo fazem parte do escopo do projeto — não são
apenas ideias soltas para o futuro. Cada uma já nasce amarrada a uma
peça concreta do stack tecnológico detalhado na sequência e a uma fase
específica do roadmap:

Diagnóstico assistido por IA

O cliente descreve o problema (por exemplo, "meu ventilador não liga") e
o chat, usando o manual, sugere causas prováveis e indica a peça correta
para comprar — transformando suporte em venda.

- **Implementação:** modelado como um grafo no LangGraph, com nós para
  entender o relato do cliente, decidir se busca no manual (pgvector) ou
  no histórico de pedidos, e só então sugerir causa/peça; roda como task
  Celery acionada pelo endpoint DRF do chat.

- **Onde entra no roadmap:** fase 6 do planejamento, depois que o chat
  básico com RAG (fase 5) já estiver estável.

- **Ponto de atenção:** cada sugestão de causa/peça deve citar o trecho
  do manual usado, para o cliente confiar na recomendação e para
  facilitar auditoria via LangSmith.

Feedback do chat (👍/👎)

Um jeito simples do cliente avaliar cada resposta do chat, gerando um
sinal direto de qualidade em vez de depender só de reclamação ou
silêncio.

- **Implementação:** botão de 👍/👎 (e campo opcional de motivo) em cada
  resposta, salvo junto da pergunta, da resposta e dos trechos do manual
  usados; alimenta tanto o dashboard de insights quanto um "golden set"
  de exemplos reais para comparar antes/depois de qualquer mudança de
  prompt.

- **Gatilho automático:** um 👎 (ou dois seguidos na mesma conversa)
  pode disparar a abertura automática de um chamado técnico com o
  histórico anexado, em vez de deixar o cliente insistindo sozinho com a
  IA.

- **Onde entra no roadmap:** junto da fase 5 (chat com RAG), já que é
  praticamente gratuito de adicionar assim que o chat existe e passa a
  gerar dado de qualidade desde o primeiro dia.

Busca de peça por foto

O cliente tira foto da peça quebrada e a IA tenta identificar o item e
mostrar produtos compatíveis, usando o Claude com input de imagem.

- **Implementação:** endpoint DRF que recebe a imagem, envia para o
  Claude junto com os metadados do catálogo (categoria, fabricante
  informado, se houver) e retorna candidatos ranqueados; a chamada roda
  em task Celery para não travar o upload no frontend htmx.

- **Onde entra no roadmap:** pode ser desenvolvido em paralelo à fase 6,
  reaproveitando a mesma infraestrutura de upload para Cloudflare R2 já
  usada para os manuais.

- **Ponto de atenção:** mesma preocupação de segurança dos uploads de
  manual: validar tipo/tamanho de arquivo e aplicar rate limiting no
  endpoint, já que cada chamada tem custo de API.

Verificador de compatibilidade

O cliente informa o modelo do produto que já possui e o sistema lista
automaticamente todas as peças compatíveis, evitando compras erradas —
um problema clássico em e-commerce de peças.

- **Implementação:** tabela de compatibilidade no PostgreSQL (modelo ×
  peça), populada pela própria extração estruturada da IA a partir do
  manual; a checagem em si é uma consulta simples via Django ORM, sem
  precisar chamar o modelo em tempo real — o widget interativo no
  frontend é só htmx/Alpine.js consultando esse endpoint.

- **Onde entra no roadmap:** fase 4a (catálogo, estoque e carrinho), já
  que depende só do schema de produto e não de nenhum fluxo de IA em
  tempo real.

Cross-sell por compatibilidade

A mesma tabela de compatibilidade que evita compra errada também serve
para sugerir peças de desgaste relacionadas — capacitor, hélice,
controle remoto — no momento certo, transformando manutenção em venda
recorrente.

- **Implementação:** regra simples sobre o mesmo model de
  compatibilidade ("quem compra o modelo X costuma trocar a peça Y"),
  exibida na página do produto e no e-mail pós-compra; pode evoluir
  depois para usar o histórico agregado de pedidos em vez de regra fixa.

- **Onde entra no roadmap:** iteração da fase 4c, logo depois do
  verificador de compatibilidade básico estar pronto.

Assinatura de manutenção preventiva

Para peças de desgaste previsível (filtros, capacitores, correias), um
plano recorrente que já envia a peça certa antes de quebrar, em vez de
esperar o cliente perceber o defeito.

- **Implementação:** model de plano de assinatura (produto,
  periodicidade, peças incluídas), com o envio recorrente dos itens
  acionado por Celery beat e ligado ao histórico de compra do cliente; a
  periodicidade pode partir da vida útil informada no próprio manual,
  quando existir.

- **Onde entra no roadmap:** iteração da fase 8 (escala), depois que
  catálogo e cross-sell já estiverem validados — é um produto novo em
  cima de dados que o projeto já vai ter.

Integração com WhatsApp

No Brasil isso é praticamente indispensável para suporte pós-venda; um
bot de WhatsApp ligado à mesma base de RAG dos manuais amplia bastante o
alcance.

- **Implementação:** mais um endpoint DRF consumido pelo webhook do
  provedor de WhatsApp (ex.: API oficial da Meta ou um BSP como
  Twilio/Zenvia), reaproveitando o mesmo pipeline de RAG e, se fizer
  sentido, o mesmo grafo de diagnóstico do LangGraph — o canal muda, a
  lógica de negócio não.

- **Onde entra no roadmap:** depois da fase 5 (chat com RAG já validado
  no site), como uma iteração da fase 8 (escala).

Multi-idioma no catálogo e no chat

Suporte a mais de um idioma no catálogo e nas respostas do chat, para
quando o e-commerce quiser atender outros países ou público não-nativo
em português.

- **Implementação:** como o schema de produto já nasce preparado para
  i18n (detalhado na seção de Frontend, a seguir), a tradução do
  catálogo é um trabalho de conteúdo, não de remodelagem; no chat, o
  mesmo pipeline de RAG detecta o idioma da pergunta e instrui o Claude
  a responder no mesmo idioma, buscando os trechos do manual
  independente do idioma original do PDF.

- **Onde entra no roadmap:** fase 8 (escala), como parte natural de
  "adicionar mais fabricantes, categorias e idiomas".

Revisão humana no loop

Mesmo com extração automática, manter uma etapa de aprovação humana
antes de publicar evita erros de especificação técnica indo ao ar.

- **Implementação:** o Django admin resolve boa parte da UI dessa
  necessidade sem trabalho extra; quando o fluxo passar a rodar em
  LangGraph, o mesmo grafo pode ter um nó de interrupção que pausa a
  execução até a aprovação e retoma exatamente de onde parou, em vez de
  reiniciar o processo.

- **Onde entra no roadmap:** já nasce na fase 3 (pipeline de ingestão de
  manuais), como parte do desenho inicial — não é algo para adicionar
  depois.

Área de chamados técnicos

Um canal formal para o cliente abrir e acompanhar um chamado de
assistência técnica quando o chat/diagnóstico automático não resolve —
seja para acionar uma assistência autorizada, seja para acompanhar
reparo ou troca.

- **Implementação:** baseada no model Ticket detalhado mais adiante na
  seção de Dados, com um painel próprio no Django admin para a equipe de
  suporte (fila de chamados, filtros por status/produto/SLA) e uma área
  do cliente no site ("Meus chamados", em views + htmx) para abrir um
  chamado, anexar fotos/descrição do problema e acompanhar o histórico.

- **Escalonamento automático:** quando o grafo do LangGraph que atende o
  chat identificar baixa confiança na resposta (pergunta fora do que
  consta no manual, ou o cliente insistir que o problema não foi
  resolvido), ele mesmo abre o chamado e anexa o histórico da conversa,
  para o cliente não ter que repetir tudo para um atendente humano.

- **Múltiplas origens:** o chamado pode nascer do site, do chat, do
  WhatsApp ou do QR-code da garantia digital — todos caem na mesma fila
  e no mesmo model, o que evita retrabalho de manter fluxos de
  atendimento separados por canal.

- **Notificações e SLA:** tasks Celery (beat) notificam o cliente por
  e-mail a cada mudança de status e alertam a equipe interna quando um
  chamado é aberto ou fica parado sem atualização além de um prazo
  definido.

- **Onde entra no roadmap:** a estrutura básica (model, admin, abertura
  pelo site) já pode entrar na fase 4c/5, junto do catálogo e do chat; o
  escalonamento automático via LangGraph e a integração com
  WhatsApp/QR-code evoluem nas fases 6 a 8, conforme esses canais forem
  ficando prontos.

Rede de assistências técnicas parceiras

Em vez de todo chamado cair só na loja, o cliente pode escolher uma
assistência autorizada perto dele para o reparo — reduzindo o volume que
precisa ser resolvido internamente.

- **Implementação:** cadastro de assistências parceiras (endereço,
  especialidade por categoria de produto, avaliação) usando um model
  equivalente ao detalhado na seção de Dados; ao abrir um chamado, o
  cliente pode escolher entre resolver com a loja ou encaminhar para uma
  assistência credenciada próxima.

- **Onde entra no roadmap:** iteração da fase 8 (escala), depois que a
  área de chamados técnicos já estiver validada com atendimento direto
  pela loja.

App/PWA offline para técnicos de campo

Quem vai até a casa do cliente consertar precisa do manual mesmo sem
internet no local — um problema comum de assistência técnica presencial.

- **Implementação:** um PWA simples (service worker + cache) que permite
  ao técnico baixar o manual do produto (do Cloudflare R2) antes de sair
  para o atendimento, além dos dados básicos do chamado; sincroniza o
  resultado do atendimento quando a conexão voltar.

- **Onde entra no roadmap:** depois da rede de assistências estar
  funcionando, já na fase 8 (escala), como uma melhoria de um fluxo que
  já existe.

Área de garantia digital

Histórico de compra vinculado ao produto, com lembretes automáticos e
QR-code para acessar o manual e abrir um chamado técnico na área
descrita acima.

- **Implementação:** lembretes agendados via Celery beat, QR-code gerado
  a partir do id do produto/pedido apontando para uma página que serve o
  PDF do manual (Cloudflare R2, com URL assinada) e um botão que já abre
  um chamado pré-preenchido (produto e pedido identificados
  automaticamente) na área de chamados técnicos.

- **Onde entra no roadmap:** iteração da fase 8 (escala), depois que
  catálogo, chat, pedidos e a área de chamados já estiverem rodando em
  produção.

Funcionalidades essenciais de e-commerce (escopo base)

As funcionalidades diferenciais acima dependem de uma base comercial que
toda loja de peças precisa ter, mesmo sem IA. Elas ficaram implícitas em
“carrinho e checkout” no plano original e agora entram explicitamente,
porque sem isso o site não vende, não fatura e não opera dentro da lei
no Brasil.

Estoque e controle de disponibilidade

Sem controle de estoque o site pode vender peça que não existe
fisicamente, gerando cancelamento e cliente insatisfeito — um problema
clássico de e-commerce de peças com catálogo grande.

- **Implementação:** model de Estoque vinculado ao produto (quantidade
  disponível, quantidade reservada, mínimo para alerta), com baixa
  automática na confirmação do pedido e reserva temporária durante o
  checkout para evitar overselling em picos de tráfego; alerta de
  reposição no Django admin/dashboard quando o saldo ficar abaixo do
  mínimo.

- **Onde entra no roadmap:** fase 4a (catálogo, estoque e carrinho) — é
  pré-requisito para vender, não um adicional.

Pagamento e frete

Checkout completo depende de processar pagamento e calcular frete de
forma confiável, sem que a loja precise lidar diretamente com dado
sensível de cartão.

- **Implementação:** gateway de pagamento (Stripe, Mercado Pago ou
  PagSeguro) via checkout hospedado ou tokenização client-side — o
  backend nunca recebe nem armazena número de cartão, apenas o token e o
  status da transação; cálculo de frete integrado à API dos Correios ou
  de um agregador (ex.: Melhor Envio), com frete fixo como fallback caso
  a API do provedor falhe.

- **Ponto de atenção:** todo webhook de confirmação de pagamento deve
  validar a assinatura/segredo do provedor antes de atualizar o pedido,
  e o projeto fica fora do escopo pesado do PCI-DSS justamente por nunca
  tocar no número do cartão diretamente.

- **Onde entra no roadmap:** fase 4b (checkout, pagamento, frete e
  NF-e), como parte do checkout básico.

Nota fiscal eletrônica (NF-e)

Emissão de NF-e é obrigatória para vender no Brasil e não pode ficar
para depois do lançamento, diferente de vários diferenciais de IA que
podem esperar.

- **Implementação:** integração com um serviço de emissão fiscal (ex.:
  NFe.io, Focus NFe ou Tecnospeed) acionada por task Celery após a
  confirmação do pagamento, com o PDF/XML da nota anexado ao pedido e
  enviado ao cliente por e-mail; reprocessamento automático em caso de
  falha da API do provedor fiscal, para não travar a confirmação do
  pedido por um problema externo.

- **Onde entra no roadmap:** fase 4b, junto do checkout — sem isso a
  loja não pode operar legalmente.

Trocas, devoluções e direito de arrependimento

Diferente da área de chamados técnicos (suporte pós-venda), o cliente
também precisa de um fluxo comercial para desistir da compra em até 7
dias (Código de Defesa do Consumidor) ou solicitar troca/devolução por
defeito.

- **Implementação:** model de Solicitação de troca/devolução (pedido,
  motivo, status, reembolso ou peça nova), com prazo de 7 dias calculado
  a partir da data de entrega e painel próprio no Django admin para a
  equipe processar; reembolso disparado via API do gateway de pagamento
  quando aplicável.

- **Onde entra no roadmap:** fase 4d/5, logo depois do checkout básico
  (4b) estar validado.

Cupons e promoções

Preço promocional e cupom são parte básica de qualquer loja e sustentam
campanhas de marketing e recuperação de carrinho abandonado.

- **Implementação:** model de Cupom (código, tipo de desconto, validade,
  uso mínimo/máximo por cliente) aplicado no carrinho via htmx, e preço
  promocional por produto/categoria com data de início e fim controlada
  pelo Django admin.

- **Onde entra no roadmap:** iteração da fase 4d, logo depois do
  checkout básico (4b).

E-mail transacional

Confirmação de pedido, nota fiscal, status de troca e atualização de
chamado dependem de e-mail entregue de forma confiável, não apenas de um
SMTP genérico.

- **Implementação:** provedor dedicado (Amazon SES ou SendGrid) com
  templates transacionais versionados (confirmação de pedido, nota
  fiscal, atualização de chamado, lembrete de garantia), disparados por
  task Celery, com log de entrega/bounce para detectar e-mail não
  entregue.

- **Onde entra no roadmap:** fase 4b, junto do checkout, evoluindo
  depois para cada funcionalidade que dependa de notificação (chamados,
  garantia, assinatura).

Stack tecnológico (atualizado para Django)

Frontend (loja)

- Django Templates + htmx — em vez de um frontend separado em React, as
  páginas são renderizadas no servidor pelo próprio Django, e o htmx
  adiciona interatividade (busca em tempo real, filtros, adicionar ao
  carrinho, etc.) sem exigir uma SPA. Isso simplifica bastante o
  projeto: um único deploy, sem API separada para o catálogo.

- Bootstrap para estilização rápida e responsiva, com componentes
  prontos (cards de produto, modais, formulários).

- SEO: como as páginas são renderizadas no servidor (SSR nativo do
  Django), o SEO de produtos continua bom — não é preciso Next.js para
  isso.

- Quando for necessário algo mais dinâmico que o htmx não resolve bem
  (ex.: verificador de compatibilidade interativo, chat), pequenos
  trechos de Alpine.js ou JavaScript puro complementam sem quebrar a
  abordagem server-driven.

- Internacionalização (i18n) prevista desde o schema: mesmo lançando só
  em português, os models de produto e os templates já usam o framework
  de tradução do Django (django.utils.translation), para não precisar
  remodelar o catálogo quando o multi-idioma entrar.

Backend

- Python + Django como framework principal — cobre autenticação, admin
  (útil para a revisão humana do catálogo extraído por IA), ORM e
  roteamento em um único lugar.

- Django REST Framework (DRF) apenas onde fizer sentido expor uma API
  real (ex.: endpoint que o chat de suporte consome via JavaScript, ou
  uma futura integração com WhatsApp/app mobile). O restante do site
  pode continuar em views tradicionais + htmx.

- Celery + Redis como fila de processamento assíncrono — roda a extração
  de manuais, geração de embeddings e chamadas à API da Anthropic em
  background, sem travar a requisição do usuário. É a escolha natural no
  ecossistema Django (equivalente ao BullMQ/Celery mencionados no plano
  original).

- Django admin customizado como painel de revisão humana: o produto
  extraído pela IA entra como rascunho e um humano aprova antes de
  publicar.

Dados

- PostgreSQL como banco principal (produtos, pedidos, usuários, peças,
  compatibilidade entre produtos), acessado via Django ORM.

- pgvector (extensão do Postgres) para os embeddings usados na busca
  semântica do chat — integra bem com Django via pacotes como
  django-pgvector ou uma migration customizada, evitando a necessidade
  de um vector DB dedicado (Pinecone, Qdrant, Weaviate) na fase inicial.

- Cloudflare R2 (via django-storages, com API compatível com S3) para
  guardar os PDFs originais dos manuais e as imagens dos produtos, com
  URLs assinadas para os PDFs quando o acesso precisar ser controlado —
  sem custo de egress, o que pesa menos no orçamento à medida que o
  catálogo de manuais e imagens cresce.

- Model de chamado técnico (Ticket) — cliente, produto/pedido
  relacionado, status (aberto, em andamento, resolvido, fechado), origem
  (site, chat, WhatsApp, QR-code de garantia) e histórico de mensagens,
  já apresentado na área de chamados técnicos (seção de funcionalidades
  diferenciais).

- Models de apoio aos novos diferenciais: feedback do chat (mensagem,
  nota 👍/👎, motivo opcional), plano de assinatura de manutenção
  preventiva (produto, periodicidade, peças incluídas) e assistência
  técnica parceira (dados, área de atendimento, especialidade) — todos
  simples o bastante para viverem no mesmo Postgres, sem necessidade de
  outro banco.

- Cache: Redis (já usado como broker do Celery) também usado como cache
  de páginas do catálogo e de consultas de compatibilidade mais
  acessadas (django-redis), reduzindo carga no Postgres em picos de
  tráfego.

- Índices e plano de escala: índices dedicados nas colunas mais
  consultadas (SKU, compatibilidade modelo × peça) e no pgvector (ex.:
  HNSW/IVFFlat) definidos já na fase 4, com plano de read
  replica/particionamento revisado na fase 8 quando o volume justificar.

IA (RAG e extração)

Essa parte do plano original não muda com a troca de stack — apenas
passa a ser orquestrada por views/tasks Django em vez de rotas
Node/FastAPI:

- Extração estruturada: o PDF (ou o texto extraído dele) é enviado à API
  da Anthropic (Claude) pedindo retorno em JSON no formato do catálogo
  (nome, modelo, voltagem, potência, número de pás, peso, dimensões,
  peças de reposição, etc.). A tarefa roda como um job Celery, e o
  resultado é salvo como um produto em rascunho para revisão humana no
  Django admin.

- RAG para o chat: os manuais são divididos em trechos (chunks),
  transformados em embeddings e armazenados no pgvector. Quando o
  cliente pergunta algo (via view Django ou endpoint DRF chamado pelo
  htmx/JS), o sistema busca os trechos mais relevantes no Postgres e os
  envia junto com a pergunta para o Claude gerar a resposta.

- Para extração de texto e tabelas do PDF antes de enviar ao modelo,
  bibliotecas como pdfplumber ou unstructured.io continuam sendo a
  escolha recomendada, evitando gastar recursos processando imagens
  quando não é necessário.

- Regressão automática da extração ("golden set"): um conjunto fixo de
  manuais reais de teste, com o JSON esperado de cada um, rodado no CI
  sempre que o prompt ou a lógica de extração mudar — evita que um
  ajuste feito para melhorar um fabricante quebre silenciosamente a
  extração de outro.

Orquestração de IA: LangChain e LangGraph

Com a extração e o RAG ficando mais ricos (múltiplas fontes, múltiplas
ferramentas, fluxos com etapas condicionais), faz sentido introduzir uma
camada de orquestração em vez de chamar a API da Anthropic diretamente
em cada task:

- **LangChain** como camada de abstração sobre os prompts e o pipeline
  de RAG: prompt templates versionados para extração estruturada e para
  o chat de suporte, parsers de saída (ex.: com Pydantic) para validar o
  JSON retornado pelo Claude antes de salvar no banco, e um vector store
  adapter para o pgvector (via langchain-postgres), o que evita
  reescrever a lógica de busca semântica na mão em cada endpoint que
  precisar dela.

- **LangGraph** para os fluxos que têm estado e múltiplos passos
  condicionais, difíceis de manter como uma sequência simples de
  chamadas: o diagnóstico assistido (entender o problema relatado →
  decidir se precisa buscar no manual, no histórico de compras ou pedir
  mais detalhes ao cliente → sugerir causa e peça), a revisão humana no
  loop (o grafo pode ter um nó de interrupção que pausa a extração até a
  aprovação no Django admin e retoma de onde parou) e a busca de peça
  por foto (identificar a peça → verificar compatibilidade → sugerir
  substitutos se não houver estoque exato).

- Integração com o stack: LangChain/LangGraph rodam dentro das mesmas
  tasks Celery já previstas — não é um serviço novo, é uma biblioteca
  Python a mais no worker. O Django continua sendo o dono do estado "de
  negócio" (produto, pedido, aprovação); o LangGraph cuida apenas do
  estado transitório de uma conversa ou execução de agente.

- Vale usar com critério: para o caso simples de "pergunta → busca no
  pgvector → resposta", uma chamada direta à API já resolve bem.
  LangGraph compensa a partir do momento em que o chat ou a extração
  ganham múltiplas ferramentas, decisões condicionais ou precisam manter
  estado entre etapas — não é necessário desde o dia 1.

Observabilidade e monitoramento

Sem monitoramento, problemas em produção — principalmente os
relacionados a IA, que falham de forma silenciosa (resposta ruim, custo
alto, latência) — só aparecem quando o cliente reclama. Camadas
recomendadas:

- **Erros de aplicação:** Sentry integrado ao Django e ao Celery,
  capturando exceptions das views, das tasks assíncronas e do worker,
  com contexto (usuário, produto, task) para facilitar o diagnóstico.

- **Logs estruturados:** structlog (ou o logging padrão do Django
  configurado em JSON) para que os logs de extração, RAG e chat sejam
  pesquisáveis e correlacionáveis por request/task id, em vez de texto
  solto.

- **Observabilidade específica de IA:** LangSmith (da própria LangChain)
  para rastrear cada execução de chain/agente — prompts enviados,
  respostas, latência, tokens consumidos e custo por chamada — o que é
  essencial para depurar por que uma extração ou resposta do chat saiu
  ruim, e para acompanhar o custo da API da Anthropic por
  produto/cliente.

- **Infraestrutura e filas:** Flower para visualizar as tasks do Celery
  (fila, falhas, tempo de execução) e métricas de aplicação
  (Prometheus + Grafana, ou uma alternativa gerenciada como Better
  Stack/Datadog) para tempo de resposta, taxa de erro e uso de recursos.

- **Disponibilidade:** checagem de uptime (UptimeRobot, Healthchecks.io
  ou equivalente) na loja e nos endpoints críticos (chat, checkout), com
  alerta antes que o cliente perceba o problema.

- **Alertas de custo:** acompanhamento do gasto com a API da Anthropic
  (via LangSmith ou métricas próprias), com limites de alerta —
  importante porque um bug em loop no chat ou na extração pode gerar
  custo inesperado rapidamente.

CI/CD, qualidade de código e Conventional Commits

Para manter a velocidade de desenvolvimento sem sacrificar estabilidade,
especialmente com uma equipe pequena mexendo em extração de IA, catálogo
e loja ao mesmo tempo:

- **Padrão de commits (Conventional Commits):** mensagens no formato
  feat:, fix:, docs:, refactor:, chore:, test:, etc., validadas
  automaticamente (commitlint via pre-commit/husky, ou o hook
  equivalente em Python). Isso permite gerar changelog automaticamente e
  versionar o projeto de forma semântica (ex.: com commitizen ou
  semantic-release), além de deixar o histórico do Git legível para quem
  entrar no projeto depois.

- **Pipeline de CI (ex.: GitHub Actions):** em cada push/PR, rodar lint
  (ruff/flake8 + black no modo check), checagem de tipos se for adotado
  mypy, testes automatizados (pytest, incluindo testes das tasks Celery
  com mocks para a API da Anthropic e a regressão do "golden set" de
  manuais) e verificação de migrations pendentes do Django antes de
  permitir o merge.

- **Pre-commit hooks:** black, ruff/isort e detecção de segredos (ex.:
  detect-secrets) rodando localmente antes do commit, para pegar
  problemas antes mesmo de chegar ao CI.

- **CD (deploy contínuo):** build de imagem Docker da aplicação Django +
  worker Celery, com deploy automático para ambiente de staging a cada
  merge na branch principal e promoção manual (ou automática após smoke
  tests) para produção — seja em Railway/Render (mais simples) ou AWS
  (Elastic Beanstalk/ECS, para quando o projeto crescer).

- **Migrations e rollback:** migrations do Django aplicadas como etapa
  explícita do deploy (não automaticamente no boot da aplicação), com
  plano de rollback documentado para o caso de uma migration quebrar
  produção.

- **Dependabot/pip-audit:** checagem automática de dependências
  desatualizadas ou com vulnerabilidades conhecidas, rodando
  periodicamente no CI.

- **Análise estática de segurança (SAST):** bandit rodando no CI para
  detectar padrões inseguros no código Python (uso de eval, segredo
  hardcoded, SQL não parametrizado), complementando lint e pip-audit.

- **Cobertura de testes e testes de ponta a ponta:** meta mínima de
  cobertura (ex.: 80% em checkout, pagamento e extração de IA)
  verificada no CI via pytest-cov, complementada por testes de
  integração/e2e (ex.: Playwright) cobrindo os fluxos críticos: checkout
  completo, abertura de chamado e chat de suporte.

- **Documentação de API:** endpoints DRF documentados automaticamente
  (drf-spectacular gerando OpenAPI/Swagger), para facilitar integração
  futura com app mobile, parceiros ou WhatsApp sem depender de
  documentação manual desatualizada.

- **Registro de decisões de arquitetura (ADR):** decisões técnicas
  relevantes (troca de stack, escolha de gateway de pagamento, adoção de
  LangGraph, etc.) documentadas em ADRs curtos versionados no
  repositório, preservando o motivo da decisão além do código.

Segurança

Pontos de segurança que merecem atenção específica neste projeto, além
das boas práticas gerais de qualquer aplicação Django:

- **Autenticação e autorização:** Django auth para o site e
  djangorestframework-simplejwt (ou sessions, se o consumo da API for só
  do próprio frontend) para os endpoints DRF; permissões claras
  separando o que é público (catálogo, chat) do que exige login
  (pedidos, garantia, admin).

- **RBAC configurável:** além dos grupos padrão do Django, um modelo de
  papéis e permissões configurável (models de Role/Permission próprios,
  ou django-guardian/rules quando permissão por objeto for necessária)
  que permite à equipe criar e ajustar papéis --- suporte, revisão de
  catálogo, gestor de chamados, admin geral --- e o que cada um pode ver
  ou fazer, sem precisar alterar código a cada mudança de política de
  acesso; usado tanto no Django admin quanto nas telas internas
  (dashboard, cadastros, chamados).

- **Proteção de conta e 2FA:** contas de staff/admin protegidas por
  autenticação de dois fatores (django-otp ou allauth-2fa), obrigatória
  para quem acessa o Django admin ou qualquer papel do RBAC com
  permissão de escrita.

- **Proteção contra brute-force:** limite de tentativas de login
  (django-axes ou rate limit dedicado no endpoint de autenticação),
  separado do rate limit das APIs de IA, bloqueando temporariamente
  IP/conta após tentativas repetidas.

- **Rate limiting no chat e nas APIs de IA:** django-ratelimit (ou
  equivalente) nos endpoints que chamam o Claude, para evitar abuso
  (bots gerando custo alto na API da Anthropic) e limitar o impacto de
  um cliente mal-intencionado ou de um loop de erro no frontend.

- **Validação da saída da IA:** todo JSON retornado pela extração é
  validado contra um schema (Pydantic/DRF serializers) antes de virar
  produto em rascunho, e nunca é executado ou interpretado como código —
  trata-se sempre como dado.

- **Validação de uploads de terceiros:** PDFs de manuais enviados por
  fornecedores/equipe são validados por tipo MIME e tamanho antes de
  entrar no pipeline de extração, e passam por varredura antivírus
  (ClamAV ou serviço equivalente) antes de serem processados ou expostos
  por URL assinada.

- **Prompt injection:** como o conteúdo indexado no RAG vem de manuais
  de terceiros, as instruções de sistema do chat ficam separadas do
  conteúdo recuperado, e o conteúdo do manual nunca é tratado como
  instrução — apenas como contexto de referência para a resposta.

- **Segredos e credenciais:** chaves da API da Anthropic, credenciais do
  banco e do Cloudflare R2 nunca commitadas — variáveis de ambiente
  geridas por um serviço de secrets (AWS Secrets Manager, Doppler, ou os
  secrets nativos de Railway/Render), com rotação periódica.

- **Trilha de auditoria:** toda ação sensível (mudança de
  papel/permissão no RBAC, aprovação de produto, alteração de pedido ou
  reembolso) fica registrada em um log de auditoria
  (django-simple-history ou equivalente), com quem fez, quando e o que
  mudou — necessário tanto para segurança quanto para rastreabilidade em
  disputas com cliente.

- **R2 e arquivos:** bucket privado por padrão, URLs assinadas com
  expiração curta para os PDFs dos manuais, e API tokens do Cloudflare
  R2 com escopo mínimo (só o bucket da aplicação, sem acesso amplo à
  conta Cloudflare).

- **Proteções web padrão:** CSRF (nativo do Django), proteção contra SQL
  injection via ORM (evitar SQL cru sem parametrização), sanitização de
  HTML nos templates para evitar XSS, HTTPS obrigatório com HSTS em
  produção.

- **Segurança de sessão e cabeçalhos:** cookies de sessão marcados como
  secure/HttpOnly/SameSite e com expiração configurada, além de
  cabeçalhos de segurança adicionais (Content-Security-Policy,
  X-Frame-Options, Referrer-Policy) via django-csp ou middleware
  equivalente.

- **Dados pessoais e LGPD:** como o projeto guarda dados de clientes
  (pedidos, garantia, histórico de compras), vale mapear desde já quais
  dados são coletados, por quanto tempo são retidos e como um cliente
  pode solicitar exclusão, para já nascer alinhado com a LGPD.

- **Backups:** backup automático e testado do PostgreSQL (dados de
  produtos, pedidos e usuários), com um plano de restauração validado —
  não só o backup rodando, mas a restauração testada periodicamente.

- **Anonimização em logs:** logs estruturados (structlog) mascaram ou
  omitem dados pessoais (e-mail, CPF, endereço) por padrão, para não
  vazar dado sensível em ferramenta de observabilidade e para ficar
  alinhado com a LGPD.

- **Dados de pagamento:** nunca armazenados diretamente pela aplicação —
  o gateway de pagamento (ver seção de Funcionalidades essenciais de
  e-commerce) faz a tokenização do cartão, e o backend guarda apenas o
  token e o status da transação.

Dashboard interno, monitoramento e cadastros no site

Além das ferramentas técnicas (Sentry, LangSmith, Flower, Django admin),
a equipe de operação — que nem sempre é técnica — precisa de uma área
própria dentro do site para acompanhar o negócio e cadastrar o dia a dia
sem depender de abrir várias ferramentas separadas ou mexer direto no
admin cru.

Dashboard de insights

- **Métricas do chat/RAG:** perguntas mais frequentes, taxa de resolução
  sem intervenção humana e nota média do feedback 👍/👎, agregadas
  periodicamente (task Celery) a partir dos dados salvos no Postgres e
  complementadas pelo LangSmith, exibidas em views Django com
  Chart.js/Recharts.

- **Métricas de chamados:** volume por status, tempo médio de resolução,
  SLA estourado e distribuição por origem (chat, WhatsApp, site,
  garantia, assistência parceira).

- **Métricas de vendas influenciadas por IA:** quantos pedidos vieram do
  diagnóstico assistido, da busca de peça por foto, do cross-sell de
  compatibilidade ou da assinatura de manutenção — o dado que mostra o
  retorno concreto do investimento em IA.

- **Custo de IA:** total gasto na API da Anthropic no período (via
  LangSmith), com comparação entre extração de catálogo e chat de
  suporte, para a equipe acompanhar sem precisar abrir uma ferramenta
  externa.

Monitoramento consolidado no site

- **Painel resumido:** em vez de a equipe abrir Flower, Sentry e Grafana
  separadamente, uma página interna consolida o essencial — falhas
  recentes de task, filas atrasadas, uptime dos serviços — com links
  diretos para a ferramenta completa quando for preciso investigar a
  fundo.

- **Alertas visíveis:** o mesmo alerta que dispara por Slack/e-mail
  (erro recorrente, custo de IA acima do esperado, chamado sem SLA)
  também aparece destacado nesse painel, para quem está de olho no site
  durante o dia.

Cadastros no site (além do Django admin)

- **Revisão e cadastro de produtos:** interface própria (views + htmx),
  mais amigável que o admin cru, para quem revisa no dia a dia o
  rascunho gerado pela extração de IA, edita campos e aprova a
  publicação, ou cadastra manualmente um produto sem manual em PDF.

- **Cadastro de categorias e compatibilidade:** gestão das relações
  entre modelo e peça (usadas pelo verificador de compatibilidade e pelo
  cross-sell) sem precisar editar direto no banco.

- **Cadastro de planos de assinatura e de assistências parceiras:**
  telas simples para criar/editar planos de manutenção preventiva e
  cadastrar a rede de assistências credenciadas (área de atendimento,
  especialidade, contato).

- **Gestão de conteúdo multi-idioma:** quando essa fase entrar, edição
  das traduções do catálogo pela mesma interface, sem depender de acesso
  técnico ao banco.

- **Controle de acesso:** baseado no RBAC configurável descrito na seção
  de Segurança, definindo por papel quem só visualiza o dashboard, quem
  edita cadastro e quem tem acesso total — evita que qualquer pessoa da
  operação mexa em configurações sensíveis, e permite ajustar essas
  regras conforme a operação cresce, sem depender de deploy.

- **Onde entra no roadmap:** a base de cadastro (produtos, categorias,
  compatibilidade) já nasce na fase 3/4 como evolução natural do Django
  admin; o dashboard de insights e o monitoramento consolidado entram na
  fase 7, quando já existe dado suficiente de chat, chamados e custo
  para mostrar; os cadastros de assinatura, assistências parceiras e
  multi-idioma acompanham cada diferencial correspondente na fase 8.

Planejamento do projeto (fases)

- 1\. Descoberta e escopo do MVP — definir quais categorias de produto
  entram primeiro (ex.: ventiladores de teto e peças de reposição) e
  qual o schema mínimo de produto (models Django) necessário para
  vender.

- 2\. Base do projeto — repositório com CI configurado desde o início
  (lint, testes, pre-commit e Conventional Commits), Docker e ambiente
  de staging, para que toda a construção seguinte já nasça com esse
  cinto de segurança.

- 3\. Pipeline de ingestão de manuais — construir essa parte primeiro,
  isoladamente, sem interface bonita: upload de PDF (para Cloudflare R2)
  → task Celery de extração (orquestrada com LangChain) → JSON revisável
  no Django admin antes de publicar. É o coração do diferencial do
  projeto, então vale testar com vários manuais reais (de fabricantes e
  layouts diferentes) para garantir robustez.

- 4\. Catálogo e loja básica — escopo grande o bastante para valer a
  pena entregar em sub-etapas, reduzindo o risco de uma equipe pequena
  tentar tudo de uma vez:

- 4a. Catálogo, estoque e carrinho — models e views Django para
  produtos, categorias e estoque (com reserva), templates com htmx para
  navegação, filtros e carrinho, e a tela de cadastro/revisão de
  produtos no site.

- 4b. Checkout, pagamento, frete e NF-e — fecha o ciclo de compra de
  ponta a ponta: gateway de pagamento, cálculo de frete e emissão de
  nota fiscal eletrônica. É o núcleo que faz a loja vender de fato, e
  por isso vem antes dos itens de conveniência abaixo.

- 4c. Suporte e cross-sell básicos — estrutura inicial de chamados
  técnicos (model Ticket e painel no admin) e cross-sell por
  compatibilidade, já usando o catálogo de 4a.

- 4d. Cupons, trocas e devoluções — iteração comercial
  (cupons/promoções, fluxo de troca/devolução e direito de
  arrependimento) feita depois que 4a–4c já estiverem validados em
  produção, evitando adicionar regra de negócio em cima de um checkout
  ainda instável.

- 5\. Chat de suporte com RAG — depois que o catálogo estiver rodando,
  ligar o chat (view/endpoint Django) aos manuais já indexados no
  pgvector, com feedback 👍/👎 em cada resposta e observabilidade via
  LangSmith desde o primeiro dia.

- 6\. Diagnóstico assistido e fluxos com LangGraph — depois que o chat
  básico estiver estável, evoluir para os fluxos com estado
  (diagnóstico, aprovação humana, busca por foto), incluindo o golden
  set de regressão da extração no CI.

- 7\. Testes com usuários reais / beta fechado, dashboard e
  monitoramento no site — validar se a extração automática está gerando
  cadastros de qualidade e se o chat responde bem, com o dashboard de
  insights e o painel de monitoramento consolidado já ativos para a
  equipe acompanhar.

- 8\. Iteração e escala — adicionar mais fabricantes, categorias e
  idiomas, integração com WhatsApp, assinatura de manutenção preventiva,
  rede de assistências parceiras e PWA offline para técnicos, com
  hardening de segurança revisado antes de abrir tráfego maior.

Custo estimado dos novos serviços externos

Os valores abaixo são uma ordem de grandeza para ajudar no planejamento
inicial, não uma cotação — cada fornecedor tem tabela própria, e o custo
real varia com volume de vendas, número de manuais processados e região.
Vale validar diretamente com cada provedor antes de fechar o orçamento
do projeto.

| **Serviço** | **Fornecedores sugeridos** | **Modelo de cobrança** | **Estimativa MVP (baixo volume)** |
|---|---|---|---|
| API Anthropic (Claude)              | API oficial da Anthropic                   | por token, extração + chat                              | R$ 300–1.500/mês, variando com nº de manuais processados e volume de conversas |
| Hospedagem (app + Postgres + Redis) | Railway ou Render                          | plano mensal por recurso                                | R$ 150–600/mês para staging + produção inicial                                 |
| Armazenamento de arquivos           | Cloudflare R2                              | por GB armazenado, sem cobrança de egress               | R$ 10–50/mês no início (poucos GB de PDFs e imagens)                           |
| Gateway de pagamento                | Stripe, Mercado Pago ou PagSeguro          | taxa percentual por transação (~2–5%)                   | sem custo fixo; escala com o volume de vendas                                   |
| Emissão de NF-e                     | NFe.io, Focus NFe ou Tecnospeed            | plano mensal com franquia de notas ou por nota emitida  | R$ 50–200/mês nos planos de entrada                                            |
| Cálculo de frete                    | Melhor Envio ou API dos Correios           | cotação geralmente gratuita; frete repassado ao cliente | sem custo direto relevante para a operação                                      |
| E-mail transacional                 | Amazon SES ou SendGrid                     | por e-mail enviado                                      | R$ 20–80/mês em volume baixo (SES costuma sair mais barato)                    |
| Antivírus para upload               | ClamAV (self-hosted) ou serviço gerenciado | gratuito (self-hosted) ou plano mensal                  | R$ 0 em container próprio; R$ 50–150/mês se optar por serviço gerenciado      |
| Observabilidade                     | Sentry, LangSmith, Flower                  | planos free/starter cobrem o início                     | R$ 0–150/mês nos planos de entrada                                             |
| WhatsApp Business API (fase 8)      | API oficial da Meta ou BSP (Twilio/Zenvia) | por conversa iniciada                                   | não essencial no MVP; orçar quando o canal entrar no roadmap                    |

De forma geral, os custos variáveis (API da Anthropic e gateway de
pagamento) tendem a pesar mais que os custos fixos (hospedagem, e-mail,
observabilidade) à medida que o volume de vendas cresce — vale
acompanhar isso pelo dashboard de custo de IA já previsto no plano, e
por um relatório equivalente do lado financeiro/pagamento.

Ponto de atenção importante (não técnico)

Ao revender peças e usar manuais de fabricantes (como a Mondial) para
cadastrar produtos, vale cuidado com dois pontos legais:

- 1\. Direitos autorais — é possível extrair dados técnicos (fatos não
  são protegidos por direitos autorais), mas deve-se evitar reproduzir o
  texto e as imagens do manual literalmente no site.

- 2\. Uso de marca — não usar o nome ou logo do fabricante de forma que
  sugira parceria oficial, a menos que exista essa autorização.

Esses pontos não mudam com a troca de stack técnico, mas é recomendável
defini-los antes de escalar o catálogo.

Resumo das mudanças em relação ao plano original

| **Área** | **Mudança** |
|---|---|
| Frontend                       | Next.js + Tailwind → Django Templates + htmx + Bootstrap (server-rendered, um único deploy)                                                                                                                                                                                                                                                                                                                                                                 |
| Backend                        | NestJS/Express ou FastAPI → Django (+ DRF onde necessário)                                                                                                                                                                                                                                                                                                                                                                                                  |
| Fila                           | BullMQ/Celery → Celery + Redis (padrão do ecossistema Django)                                                                                                                                                                                                                                                                                                                                                                                               |
| Banco                          | PostgreSQL + pgvector — mantido, agora com cache de catálogo/consultas via Redis (django-redis) e plano de índices/escala definido desde a fase 4                                                                                                                                                                                                                                                                                                           |
| Storage                        | Amazon S3 → Cloudflare R2 (via django-storages, API compatível com S3, sem custo de egress)                                                                                                                                                                                                                                                                                                                                                                 |
| IA (extração + RAG com Claude) | mantido, agora orquestrado com LangChain (pipeline/prompts) e LangGraph (fluxos com estado, ex.: diagnóstico e aprovação humana)                                                                                                                                                                                                                                                                                                                            |
| Busca                          | Meilisearch/Algolia → busca full-text nativa do Postgres no início, com upgrade opcional                                                                                                                                                                                                                                                                                                                                                                    |
| Observabilidade                | novo — Sentry (erros), structlog (logs), LangSmith (rastreio de chains/agentes e custo de IA), Flower/Prometheus+Grafana (infra e filas)                                                                                                                                                                                                                                                                                                                    |
| CI/CD                          | novo — GitHub Actions (lint, testes, migrations), pre-commit, Docker, deploy automático para staging, SAST (bandit), meta de cobertura de testes com e2e, documentação de API (drf-spectacular) e ADRs                                                                                                                                                                                                                                                      |
| Padrão de commits              | novo — Conventional Commits validados por commitlint, changelog e versionamento semântico automáticos                                                                                                                                                                                                                                                                                                                                                       |
| Segurança                      | novo — RBAC configurável (papéis e permissões ajustáveis, sem depender de deploy), 2FA e proteção contra brute-force no login, trilha de auditoria, validação/antivírus em uploads de manual, cabeçalhos de segurança e cookies seguros, anonimização de dados pessoais em log, tokenização de pagamento, rate limiting no chat/API de IA, validação de saída da IA, defesa contra prompt injection, gestão de segredos, revisão de LGPD e backups testados |
| Suporte                        | novo — área de chamados técnicos (model Ticket, painel no Django admin, "Meus chamados" no site), com escalonamento automático do chat via LangGraph e abertura pelo site, WhatsApp ou QR-code da garantia digital                                                                                                                                                                                                                                          |
| Dashboard e cadastros no site  | novo — dashboard de insights (chat, chamados, vendas influenciadas por IA, custo de IA), painel de monitoramento consolidado e telas de cadastro (produtos, compatibilidade, assinatura, assistências parceiras) além do Django admin                                                                                                                                                                                                                       |
| Qualidade de dados             | novo — feedback 👍/👎 em cada resposta do chat e golden set de manuais para regressão automática da extração no CI                                                                                                                                                                                                                                                                                                                                          |
| Novos diferenciais comerciais  | novo — cross-sell por compatibilidade, assinatura de manutenção preventiva, rede de assistências técnicas parceiras e app/PWA offline para técnicos de campo                                                                                                                                                                                                                                                                                                |
| Internacionalização            | novo — schema de produto e templates já preparados para i18n, com multi-idioma no catálogo e no chat previsto para a fase de escala                                                                                                                                                                                                                                                                                                                         |
| Escopo essencial de e-commerce | novo — estoque com reserva no checkout, gateway de pagamento e frete, emissão de NF-e, trocas/devoluções (direito de arrependimento), cupons/promoções e e-mail transacional; tudo já na fase 4, junto do catálogo e checkout                                                                                                                                                                                                                               |
