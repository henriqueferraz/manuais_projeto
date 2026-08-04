# Specify — E-commerce de Peças com IA

> Este documento descreve **o que** este produto deve fazer e **por que** cada parte dele existe. Ele não prescreve tecnologias, frameworks, bibliotecas ou fornecedores — essas são decisões de implementação, tratadas em outro momento. O objetivo aqui é fixar a intenção do produto de forma clara o bastante para que qualquer stack escolhida depois possa ser avaliada em relação a ela.

---

## 1. Visão geral

Estamos construindo um site de venda de peças e produtos de reposição (no molde de lojas como Britânia e Philco), com um diferencial central: **usar IA para transformar o manual do fabricante em duas coisas ao mesmo tempo — um cadastro de produto pronto para vender e uma base de conhecimento que responde dúvidas técnicas do cliente.**

Manuais de fabricante seguem um padrão razoavelmente previsível (características numeradas, especificações técnicas, esquemas elétricos, lista de peças de reposição). Isso torna viável automatizar tanto o cadastro quanto o suporte a partir da mesma fonte de informação, em vez de tratá-los como dois trabalhos manuais separados.

### Por que isso importa

Hoje, cadastrar um catálogo de peças tecnicamente detalhado é trabalho manual lento, e o suporte técnico pós-venda depende de atendentes que precisam conhecer cada manual de cada fabricante. Isso limita a velocidade de expansão do catálogo e a qualidade do suporte. Ao extrair estrutura e conhecimento diretamente do manual, o mesmo documento que hoje só serve para consulta interna passa a alimentar venda e suporte automaticamente.

---

## 2. Como as duas trilhas convergem no cliente

O manual do produto alimenta duas trilhas de IA em paralelo:

- **Trilha de catálogo:** extrai dados estruturados do produto (nome, modelo, voltagem, potência, peças de reposição, dimensões etc.) para alimentar a loja online.
- **Trilha de suporte:** transforma o conteúdo do manual em uma base de conhecimento consultável, usada para responder dúvidas técnicas do cliente com base no manual real daquele produto específico.

O cliente vive a experiência de ambas as trilhas de forma unificada: ele compra um produto cujo cadastro veio do manual, e quando tem dúvida sobre esse mesmo produto, o suporte responde com base no mesmo manual — não com respostas genéricas.

---

## 3. Para quem é este produto

- **Cliente final**, comprando peças de reposição ou produtos completos, muitas vezes tentando resolver um problema técnico (equipamento quebrado) e decidir sozinho qual peça comprar.
- **Equipe interna de catálogo**, que precisa revisar e aprovar o que a IA extraiu antes de publicar, sem precisar digitar tudo do zero.
- **Equipe de suporte/operação**, que acompanha chamados, chat e métricas de negócio no dia a dia, sem necessariamente ter conhecimento técnico profundo de sistemas.
- **Técnicos de campo**, que eventualmente precisam consultar o manual e o histórico de um chamado mesmo sem conexão estável no local do atendimento.
- **Assistências técnicas parceiras**, que podem receber chamados encaminhados pelo cliente.

---

## 4. O que o produto precisa fazer

### 4.1 Base comercial (sem isso, não existe loja)

- **Catálogo navegável de produtos e peças**, com busca e filtros, que o cliente consegue explorar e entender o que está comprando.
- **Controle de estoque confiável**, para nunca vender uma peça que não existe fisicamente — evitando cancelamento e frustração do cliente. Isso inclui reservar o item durante o checkout para não vender a mesma unidade duas vezes em picos de tráfego.
- **Checkout completo**, incluindo pagamento processado com segurança (sem a loja jamais lidar diretamente com dado sensível de cartão) e cálculo de frete confiável.
- **Emissão de nota fiscal eletrônica**, porque vender no Brasil sem isso não é uma opção — é requisito legal desde o primeiro pedido.
- **Trocas, devoluções e direito de arrependimento**, cobrindo tanto o prazo legal de desistência quanto defeito de produto — como um fluxo comercial, distinto do suporte técnico.
- **Cupons e promoções**, como ferramenta básica de marketing e recuperação de carrinho abandonado.
- **Comunicação por e-mail confiável** para cada evento importante do pedido (confirmação, nota fiscal, status de troca, atualização de chamado) — o cliente nunca deve ficar no escuro sobre o que está acontecendo com a compra dele.

### 4.2 Catálogo alimentado por IA

- **Extração automática de dados do produto a partir do manual em PDF**, reduzindo drasticamente o esforço manual de cadastro por item.
- **Revisão humana antes da publicação**: o que a IA extrai nasce como rascunho, e uma pessoa aprova (ou corrige) antes de ir ao ar. Isso protege contra erro de especificação técnica indo ao cliente final.
- **Verificador de compatibilidade**: o cliente informa o modelo do produto que já possui e o sistema mostra as peças compatíveis, evitando o erro clássico de comprar a peça errada.
- **Cross-sell por compatibilidade**: a mesma informação de compatibilidade também sugere peças de desgaste relacionadas (capacitor, hélice, controle remoto) no momento certo, transformando manutenção em venda recorrente.

### 4.3 Suporte técnico alimentado por IA

- **Chat de suporte que responde com base no manual real do produto**, não com respostas genéricas — e que sempre pode apontar de qual trecho do manual tirou a resposta, para o cliente confiar na informação.
- **Feedback simples do cliente sobre cada resposta (👍/👎)**, gerando sinal direto de qualidade em vez de depender só de reclamação ou silêncio. Um feedback muito negativo (ou repetido) pode abrir automaticamente um chamado técnico com o histórico anexado, para o cliente não ficar insistindo sozinho com a IA.
- **Diagnóstico assistido**: o cliente descreve o problema (ex.: "meu ventilador não liga") e o sistema sugere causas prováveis e a peça correta para resolver — transformando um atendimento de suporte em uma oportunidade de venda.
- **Busca de peça por foto**: o cliente fotografa a peça quebrada e o sistema tenta identificá-la e sugerir produtos compatíveis, para os casos em que o cliente não sabe o nome técnico do que precisa.
- **Escalonamento automático para atendimento humano** quando a IA identificar baixa confiança na própria resposta ou o cliente insistir que o problema não foi resolvido — sempre levando o histórico da conversa junto, para o cliente não repetir tudo para uma pessoa.

### 4.4 Atendimento e pós-venda

- **Área de chamados técnicos**, unificando em um único lugar pedidos de assistência vindos do site, do chat, do WhatsApp ou de um QR-code de garantia — o cliente abre e acompanha, a equipe gerencia fila, status e prazo de atendimento (SLA) em um painel próprio.
- **Notificação automática de mudança de status** de cada chamado, para o cliente e para a equipe interna quando um chamado fica parado além do prazo esperado.
- **Rede de assistências técnicas parceiras**, para que o cliente possa optar por um reparo presencial perto dele em vez de depender só do atendimento interno da loja.
- **Área de garantia digital**, vinculando o histórico de compra ao produto, com lembretes automáticos e um QR-code que leva direto ao manual e à abertura de um chamado já pré-preenchido com os dados do produto e do pedido.
- **App/uso offline para técnicos de campo**, permitindo baixar o manual e os dados do chamado antes de ir a um atendimento presencial sem internet garantida no local, sincronizando o resultado depois.

### 4.5 Expansão de alcance

- **Atendimento por WhatsApp**, canal praticamente indispensável no Brasil para suporte pós-venda, usando a mesma base de conhecimento dos manuais.
- **Suporte a múltiplos idiomas no catálogo e no chat**, para viabilizar expansão a outros países ou público não-nativo em português, sem precisar remodelar o catálogo depois — a estrutura de dados já nasce preparada para isso, mesmo que o lançamento inicial seja só em português.

### 4.6 Novo modelo de receita recorrente

- **Assinatura de manutenção preventiva**: para peças de desgaste previsível (filtros, capacitores, correias), um plano recorrente que envia a peça certa antes de ela quebrar, em vez de esperar o cliente perceber o defeito — transformando reposição reativa em receita recorrente previsível.

### 4.7 Visibilidade do negócio para quem opera

- **Dashboard de insights**, mostrando o que realmente importa para quem toca o negócio no dia a dia: perguntas mais frequentes do chat, taxa de resolução sem intervenção humana, volume e tempo de resolução de chamados, quantos pedidos foram influenciados por cada recurso de IA (diagnóstico, busca por foto, cross-sell, assinatura) e quanto está sendo gasto com IA no período.
- **Painel de monitoramento consolidado**, para a equipe acompanhar falhas, filas atrasadas e disponibilidade sem precisar abrir várias ferramentas técnicas separadas.
- **Telas de cadastro amigáveis** para produtos, categorias, compatibilidade, planos de assinatura e assistências parceiras — pensadas para uma equipe de operação que nem sempre é tecnicamente treinada, evitando que o dia a dia dependa de mexer direto em uma ferramenta administrativa crua.

---

## 5. O que o produto precisa ser (qualidades, não features)

- **Confiável tecnicamente**: uma recomendação de peça errada, uma resposta de suporte incorreta, ou uma venda de item sem estoque real corroem a confiança do cliente de forma desproporcional ao tamanho do erro. O produto deve tratar precisão como requisito, não como bônus.
- **Transparente sobre a origem da informação**: toda resposta técnica deve poder ser rastreada até o manual que a originou, tanto para o cliente confiar quanto para a equipe auditar.
- **Seguro por padrão** com dados de cliente, pagamento e manuais de terceiros — sem depender de reforço manual posterior.
- **Legal para operar no Brasil desde o primeiro pedido**: nota fiscal, direito de arrependimento e proteção de dados pessoais não são metas futuras, são pré-condições de lançamento.
- **Cauteloso com propriedade intelectual de terceiros**: dados técnicos extraídos de um manual podem ser usados (fatos não são protegidos por direitos autorais), mas o texto e as imagens do manual não devem ser reproduzidos literalmente, e o nome/logo do fabricante não deve sugerir uma parceria oficial inexistente.
- **Operável por gente não-técnica no dia a dia**: quem cuida do negócio (suporte, cadastro, gestão de chamados) precisa de telas pensadas para o trabalho dela, não apenas acesso a ferramentas técnicas cruas.

---

## 6. Fora de escopo (por enquanto)

Estes itens fazem parte da visão de longo prazo mas não são prioridade imediata — valem ser lembrados para não distorcer o desenho inicial dos dados e fluxos, mas não devem atrasar o que é essencial agora:

- Atendimento multi-idioma em produção (a estrutura de dados deve prever, mas o conteúdo e o lançamento vêm depois).
- Integração com WhatsApp em produção.
- Rede de assistências parceiras ativa e assinatura de manutenção preventiva como produtos comerciais completos.
- App offline para técnicos de campo.
- Expansão para novos fabricantes e categorias além do escopo inicial de validação.

---

## 7. Critérios de sucesso

O produto está cumprindo seu propósito quando:

- Um novo produto pode ser cadastrado a partir do manual do fabricante com esforço humano muito menor do que digitar tudo manualmente, mantendo qualidade suficiente para publicar após revisão.
- O chat de suporte resolve uma parcela relevante das dúvidas técnicas sem precisar escalar para um humano, e quando escala, o histórico já vai junto.
- O cliente consegue, sozinho, descobrir qual peça precisa comprar para resolver o problema que tem — seja descrevendo o sintoma, seja informando o modelo do produto, seja fotografando a peça quebrada.
- A equipe de operação consegue acompanhar o negócio (vendas, chamados, custo de IA, qualidade do suporte) sem depender de ferramentas técnicas cruas ou de pedir relatório para outra pessoa.
- A loja vende de forma legal e confiável no Brasil desde o primeiro dia: nota fiscal emitida, direito de arrependimento respeitado, dado pessoal protegido.
