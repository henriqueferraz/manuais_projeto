# Constitution — E-commerce de Peças com IA

> Este documento estabelece os princípios fundamentais e as diretrizes de desenvolvimento que regem este projeto. Ele não define stacks, frameworks ou fornecedores específicos — isso é decisão de implementação, revisável a qualquer momento. O que está aqui é o que **não muda** conforme a stack evolui: por que o projeto existe, como ele deve se comportar e quais linhas não podem ser cruzadas.
>
> Qualquer decisão técnica futura (escolha de stack, biblioteca, fornecedor, arquitetura) deve poder ser justificada em relação a estes princípios. Quando uma decisão de curto prazo conflitar com um princípio aqui descrito, o princípio prevalece — ou a mudança de princípio precisa ser explícita e registrada.

---

## Artigo 1 — Propósito e diferencial central

1.1. O projeto existe para vender peças e produtos, usando **IA como motor de automação e diferencial competitivo**, não como enfeite. As duas trilhas centrais — extração automática de catálogo a partir de manuais e suporte técnico via RAG — devem permanecer o coração do produto em todas as fases.

1.2. Todo novo recurso de IA proposto deve responder a uma pergunta simples: *isso transforma dado de manual em venda, em suporte melhor, ou em economia operacional?* Recursos que não se conectam a essa cadeia de valor são candidatos a serem cortados ou adiados.

1.3. Suporte técnico e venda não são áreas separadas: o diagnóstico assistido, o cross-sell por compatibilidade e a assinatura de manutenção existem porque, neste negócio, resolver o problema do cliente e vender a peça certa são a mesma ação.

---

## Artigo 2 — IA responsável e confiável

2.1. **Nenhuma resposta de IA é publicada ou entregue ao cliente sem rastreabilidade.** Toda extração de catálogo e toda resposta de chat deve poder apontar para o trecho do manual (ou dado) que a originou.

2.2. **Revisão humana no loop não é opcional nem tardia.** Produtos extraídos automaticamente nascem como rascunho; um humano aprova antes da publicação. Isso é parte do desenho inicial do pipeline, não um recurso a acrescentar depois.

2.3. **Toda saída de IA é tratada como dado, nunca como código ou instrução.** JSON de extração é validado contra schema antes de virar produto. Conteúdo de manuais de terceiros nunca é interpretado como instrução de sistema — apenas como contexto de referência.

2.4. **Custo de IA é uma métrica de primeira classe**, não um efeito colateral a descobrir na fatura. Todo fluxo que chama um modelo precisa de visibilidade de custo e limites de alerta, porque loops de erro ou abuso podem gerar custo inesperado rapidamente.

2.5. **Qualidade da IA é medida, não presumida.** Feedback do cliente (👍/👎) e um conjunto fixo de casos reais ("golden set") com resultado esperado alimentam uma regressão contínua: nenhuma mudança de prompt ou lógica de extração é aceita sem confirmar que não piorou casos que já funcionavam.

2.6. **IA sem confiança suficiente escala para humano, não insiste sozinha com o cliente.** Baixa confiança na resposta, feedback negativo repetido, ou o cliente insistindo que o problema não foi resolvido devem abrir caminho para atendimento humano automaticamente, com o histórico anexado — o cliente nunca deve repetir o que já disse.

---

## Artigo 3 — Segurança e dados por padrão

3.1. Segurança não é uma fase do roadmap; é uma propriedade que atravessa todas as fases. Cada novo recurso é avaliado quanto a autenticação, autorização, validação de entrada e superfície de exposição de dados antes de ser considerado pronto.

3.2. **Dados sensíveis de pagamento nunca tocam a aplicação.** Tokenização é obrigatória; a aplicação armazena apenas token e status de transação.

3.3. **Uploads de terceiros são hostis por padrão.** Todo arquivo enviado por fornecedor, equipe ou cliente (manuais, fotos de peças) é validado por tipo e tamanho, varrido antes de entrar em qualquer pipeline de processamento, e nunca exposto publicamente sem controle de acesso.

3.4. **Permissões são configuráveis, não fixas no código.** A capacidade de criar e ajustar papéis de acesso deve existir para que mudanças de política não dependam de deploy.

3.5. **Toda ação sensível é auditável**: quem fez, quando, o que mudou. Isso vale para aprovação de produto, mudança de papel/permissão, alteração de pedido ou reembolso.

3.6. **Dados pessoais são minimizados e protegidos por padrão**: mascarados em logs, com retenção e exclusão pensadas desde o início, alinhadas à LGPD — não como adendo posterior.

3.7. **Segredos nunca vivem no código.** Credenciais e chaves de API são geridas fora do repositório, com rotação periódica.

3.8. **Backup sem restauração testada não é backup.** A capacidade de restaurar dados é validada periodicamente, não apenas assumida.

---

## Artigo 4 — Observabilidade obrigatória

4.1. Nenhum fluxo crítico — extração, RAG, chat, checkout, pagamento — opera sem visibilidade de erro, latência e custo. Problemas de IA falham silenciosamente por natureza (resposta ruim, custo alto); o projeto compensa isso com instrumentação, não com sorte.

4.2. Logs são estruturados e correlacionáveis por requisição/tarefa, e nunca carregam dado pessoal em texto aberto.

4.3. Toda execução de IA (chain, agente, chamada de modelo) é rastreável individualmente: o que foi enviado, o que voltou, quanto custou, quanto demorou.

4.4. Alertas de indisponibilidade, custo anômalo e chamados sem resposta dentro do prazo existem **antes** que o cliente precise reclamar.

---

## Artigo 5 — Qualidade, entrega e governança técnica

5.1. **Nenhum código chega à branch principal sem passar por lint, testes automatizados e verificação de migrations pendentes.** Isso vale desde o primeiro commit do projeto, não a partir de uma fase intermediária.

5.2. **Commits seguem um padrão semântico e legível** (tipo de mudança explícito no início da mensagem), permitindo histórico rastreável e geração automática de changelog.

5.3. **Fluxos críticos de negócio (checkout, pagamento, extração de IA) têm cobertura de teste mínima obrigatória**, incluindo testes de ponta a ponta para os caminhos que envolvem dinheiro ou dado do cliente.

5.4. **Decisões técnicas relevantes são registradas com o motivo, não só o resultado.** Trocar uma peça do stack, escolher um fornecedor, adotar uma nova ferramenta de orquestração — tudo isso é documentado em decisões curtas e versionadas, para que quem chegar depois entenda o "porquê", não só o "o quê".

5.5. **Rollback é planejado antes de precisar dele.** Mudanças de schema de dados em produção têm plano de reversão documentado antes do deploy, não improvisado durante o incidente.

5.6. **Dependências são vigiadas continuamente** quanto a vulnerabilidades e desatualização — isso é parte do pipeline, não uma checagem manual esporádica.

---

## Artigo 6 — Entrega incremental e priorização

6.1. **O núcleo comercial vem antes dos diferenciais de IA que dependem dele.** Estoque, checkout, pagamento, frete e nota fiscal não são "adicionais depois do MVP de IA" — sem eles, a loja não vende nem opera dentro da lei. A automação de catálogo e o suporte via IA são o diferencial, mas pousam sobre uma base comercial funcional.

6.2. **Cada funcionalidade nova é amarrada a uma fase concreta do roadmap e a uma dependência real**, não tratada como ideia solta para "algum dia". Se uma funcionalidade não tem fase e dependência claras, ela não está pronta para entrar no escopo.

6.3. **Fluxos com estado e múltiplos passos condicionais (diagnóstico, aprovação humana, busca por foto) só ganham orquestração dedicada quando a complexidade justificar.** Para o caso simples de pergunta-busca-resposta, uma chamada direta já resolve; a complexidade adicional entra quando o problema exigir.

6.4. **Escala (mais fabricantes, mais idiomas, novos canais) é tratada como iteração sobre uma base validada**, nunca como pressuposto de design inicial que trava a entrega do essencial.

6.5. **Toda decisão de arquitetura de dados considera desde o início necessidades que chegarão depois** (como internacionalização), evitando remodelagens custosas — sem, no entanto, atrasar a entrega do que é essencial agora.

---

## Artigo 7 — Confiabilidade operacional e experiência de suporte

7.1. Suporte técnico, chamados e garantia convergem em um único modelo de dados e uma única fila, independentemente do canal de origem (site, chat, WhatsApp, QR-code). Múltiplos canais não podem significar múltiplos fluxos de atendimento paralelos e divergentes.

7.2. Notificação de status (pedido, chamado, troca, garantia) é tratada como parte do fluxo, não como funcionalidade extra — o cliente nunca deve precisar perguntar "e agora, o que aconteceu com meu pedido/chamado?".

7.3. A equipe de operação (que nem sempre é tecnicamente treinada) precisa de ferramentas internas amigáveis para revisar, cadastrar e acompanhar o negócio — depender exclusivamente de ferramentas técnicas cruas (admin bruto, painéis de infraestrutura) para o dia a dia operacional é uma falha de produto, não um detalhe menor.

---

## Artigo 8 — Conformidade legal e ética comercial

8.1. **Direitos autorais de terceiros são respeitados.** Dados técnicos e fatos extraídos de manuais podem ser usados; texto e imagens do manual não são reproduzidos literalmente no site.

8.2. **Uso de marca de fabricantes é cauteloso.** Nome e logo de fabricantes não sugerem parceria oficial sem autorização explícita para tal.

8.3. **Direitos do consumidor são tratados como requisito de lançamento, não como extra.** Direito de arrependimento, trocas e devoluções, emissão de nota fiscal eletrônica — nada disso é opcional para operar legalmente no Brasil.

8.4. **Dados pessoais são tratados sob a ótica da LGPD desde o desenho inicial** — o que é coletado, por quanto tempo é retido, e como o cliente solicita exclusão são perguntas respondidas antes de o dado começar a ser coletado, não depois de um incidente.

---

## Artigo 9 — Consciência de custo

9.1. Custos variáveis (chamadas de IA, taxas de gateway de pagamento) crescem com o volume de vendas e são monitorados continuamente, não apenas estimados uma vez no planejamento.

9.2. Toda nova funcionalidade que envolve chamada a modelo de IA ou serviço de terceiros pago por uso entra no roadmap acompanhada de uma estimativa de custo e de um mecanismo de limitar abuso (rate limiting), para que a inovação não se torne um risco financeiro silencioso.

---

## Como usar esta constituição

- Ao propor uma nova funcionalidade, verifique se ela fere algum artigo acima antes de detalhar a implementação.
- Ao escolher uma stack, biblioteca ou fornecedor, a escolha deve **servir** estes princípios — a stack é descartável, os princípios não são.
- Alterações a este documento devem ser explícitas, justificadas e versionadas — assim como as decisões de arquitetura que ele governa.
