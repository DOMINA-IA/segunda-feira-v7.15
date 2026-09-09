---
id: playbook-israel-king-trafego
title: Playbook Israel King — Tráfego Pago High Ticket
type: playbook
domain:
- traffic
agents:
- traffic
tags:
- tráfego
- playbook
- sobral
status: active
created: '2026-04-12'
last_verified: '2026-04-12'
decay_rate: 0.02
links:
- target: 2026-05-07-high-ticket-capture-tracking
  type: auto-linked
- target: playbook-trafego
  type: auto-linked
- target: playbook-valter-pixel
  type: auto-linked
- target: specialists
  type: auto-linked
migrated_from: $HOME/.claude/projects/-HOME-/memory/playbook-israel-king-trafego.md
old_description: Conhecimento completo de tráfego pago do Israel King (King Ads) —
  pixel, CAPI, GTM, Andrômeda, estrutura de campanha, públicos, métricas, hacks. Fonte
  primária para @traffic e campanhas Meta Ads.
axis: ops
---

# Playbook Israel King — Tráfego Pago

> Fonte: 2 transcrições de aulas ao vivo na comunidade DOMINA.IA (07/04/2026)
> Israel King: gestor de tráfego, +40 clientes, agência, e-commerce de moda masculina R$1.1M/ano, certificação Meta

---

## 1. PIXEL — O Funcionário Dentro do Facebook

- Pixel = funcionário do Facebook. Quanto mais novo, mais burro. Quanto mais dados, mais inteligente.
- **Pixel novo precisa ser cuidado com carinho** — quando entender quem compra, qualquer criativo vende.
- O pixel coleta: quem clicou, quem viu página, quem interagiu, quem comprou.
- A cada compra, pixel absorve comportamento/interesse do comprador e busca pessoas similares.
- **50 conversões** é a meta para o pixel sair da fase de aprendizado.

### Nutrição do Pixel (CAPI + GTM)
- **Só pixel browser não basta** — cookie de terceiro não pega muitos dados (iOS 14+).
- **API de Conversões (CAPI):** cada lead/compra no CRM envia server-side para Meta com dados enriquecidos (nome, telefone, fbc, fbp, IP, user_agent).
- **Google Tag Manager (GTM):** captura dados do navegador que o pixel sozinho não consegue → melhora nota de correspondência.
- **Nota de correspondência** = quanto o Facebook consegue associar o evento a uma pessoa real. Sem CAPI/GTM, nota fica baixíssima.
- **CRM → Pixel:** lead que chamou = Lead event. Lead que fechou = Purchase event. Isso retroalimenta o pixel para achar mais pessoas daquele perfil.

### Confirmar Eventos no Gerenciador
- Gerenciador de Eventos → clicar no pixel → "Analisar eventos".
- Eventos com exclamação vermelha = não reconhecidos pela Meta.
- Se eventos mostram só "navegador" sem nota → tracking incompleto → CAPI necessário.
- **Obrigatório confirmar eventos** senão campanha fica burra — não absorve inteligência.

---

## 2. ESTRUTURA DE CAMPANHA — Uma Campanha, Muitos Criativos

### Hierarquia
```
CAMPANHA (estrutural — NÃO MEXER)
  └─ CONJUNTO DE ANÚNCIO (inteligência primária — NÃO MEXER)
       └─ ANÚNCIOS/CRIATIVOS (aqui pode mexer — rotatividade)
```

- **Campanha** = estrutural. Não alterar após criar.
- **Conjunto de anúncio** = inteligência primária. Consulta o pixel. Quanto mais tempo rodando, mais inteligente. **NUNCA alterar conjunto no meio do processo** — perde tudo.
- **Anúncios** = criativos. Aqui pode trocar, adicionar, remover.

### Regra de Ouro: Uma Campanha Principal
- **Não empilhar várias campanhas para o mesmo produto/público.**
- Causa **fragmentação/sobreposição de público** → CPM sobe, CPA sobe.
- Facebook quer **poucas campanhas e muitos criativos**.
- Israel: "Eu só tenho uma campanha de venda por cliente. Uma. Com 30 criativos dentro."

### Fluxo de Teste e Escala
1. Campanha principal rodando com budget alto (ex: R$200/dia)
2. Para testar criativo novo: criar campanha separada com R$33/dia
3. Se criativo validou → **duplicar para a campanha principal** (não criar campanha nova)
4. Desligar campanha de teste
5. Criativo se beneficia da inteligência acumulada no conjunto da campanha principal

### Quando Subir Nova Campanha
- Só subir campanha nova de teste quando a principal já estiver com pelo menos R$200/dia.
- Teste de criativo: R$33/dia mínimo, budget ímpar.
- Teste de página: 3 campanhas idênticas (mesmo criativo, mesmo público), páginas diferentes. Máximo 48h. R$50 cada.

---

## 3. PÚBLICOS — Original vs Advantage+

### Advantage+ (Público Amplo)
- Facebook expande a segmentação para públicos similares.
- "Compradores Envolvidos" no Advantage+ = **184 milhões** (inflado — inclui perfis similares).
- Bom quando: pixel já tem muitos dados, conta madura, muitas conversões.
- **Risco:** pixel novo + Advantage+ = público desqualificado, CPM alto, desperdício.

### Original (Público Segmentado)
- Facebook **respeita exatamente** a segmentação definida.
- "Compradores Envolvidos" no Original = **72 milhões** (real).
- **Usar quando:** conta nova, pixel novo, pouca verba, precisa de qualificação.
- Afunila o público → leads mais qualificados → pixel aprende mais rápido.

### Regra Prática
- **Público aberto** (sem segmentação): tanto faz Advantage+ ou Original.
- **Com segmentação específica**: usar **Original** senão Facebook não respeita.
- **Pixel maduro com conversões**: pode usar Advantage+ que já sabe quem buscar.

### Compradores Envolvidos
- Pessoas que compraram online nos últimos 90 dias.
- **Excelente para:** low ticket, infoproduto, e-commerce.
- Israel usa em praticamente todos os clientes de produto/info.
- Exemplo: batente de porta — R$18K investido, R$72K retorno, só com compradores envolvidos.

### High Ticket — Público de Alto Valor
- Comportamentos → Classificação do consumidor → **"Pessoas que preferem valor de produto alto no Brasil"**
- Reduz público de ~77M para ~10M (elimina 60M+ que não compram alto valor).
- **Obrigatório para high ticket** (consultoria, imobiliária, eventos caros).
- Facebook sabe nos últimos 90 dias quem comprou produtos de luxo/alto valor.
- Depois: testar marcas de luxo como interesse adicional.

---

## 4. CAMPANHA DE RECONHECIMENTO — Topo de Funil

### O que é
- Campanha para **ser visto**, não para vender.
- CPM extremamente barato (R$1,55 vs R$30+ de venda).
- R$10/dia alcança quase 10.000 pessoas.
- **Não oferece nada.** Só apresenta quem você é, o que resolve.

### Por que é essencial
- Pessoa precisa te ver **7 a 12 vezes** antes de comprar.
- Campanha de venda para público frio = caro (mostra 7x custa R$50).
- Reconhecimento mostra para muito mais gente, gastando R$10.
- Quando campanha de venda roda, faz remarketing automático em cima de quem já viu no reconhecimento.
- **Resultado:** CPA cai drasticamente porque público já está aquecido.

### Tipos de Reconhecimento
- Visita no perfil do Instagram
- Visualização de página de destino
- Visualização de conteúdo de vídeo (50%+ do vídeo = muito importante)
- Curtidas na página do Facebook (para aquecer conta nova)

### Quando usar
| Negócio | Reconhecimento? |
|---------|----------------|
| Negócio local | **Obrigatório** |
| Imobiliária | **Obrigatório** |
| Infoproduto | Muito bom |
| E-commerce | Bom |
| Criador de conteúdo | Extremamente importante |
| Palestra/evento | Fundamental |

### Aquecimento de Conta Nova
- Antes de anunciar venda: rodar **5 dias** campanha de engajamento para curtidas na **página do Facebook** (não Instagram).
- R$10/dia. Criativo genérico. Objetivo: aquecer conta no score do Facebook.
- Sem isso, Facebook vê que você só quer ganhar dinheiro → penaliza.

---

## 5. ANDRÔMEDA — Inteligência Artificial do Facebook

### O que é
- IA da Meta (parceria com NVIDIA/Manus) que distribui anúncios.
- Reconhece criativos e manda para a persona certa.
- **70% do sucesso = qualidade do criativo.** Segmentação perdeu importância.

### Regras da Andrômeda
- 70% da imagem deve seguir padrões da Andrômeda (proporções, elementos visuais).
- Não ter muitos dizeres na imagem.
- Fotos com ângulos específicos performam melhor.

### Princípio fundamental: Ângulos Diferentes, Mesmo Conteúdo
- Andrômeda quer o **mesmo conteúdo** por **ângulos diferentes**.
- Se criativos são muito similares → Andrômeda lê como um só → só distribui um → sobreposição de público.
- **Exemplo:** mesmo produto/mensagem, mas:
  - Um com selfie
  - Um sentada na cadeira
  - Um estático
  - Um com carro ao fundo
- Andrômeda sabe quem gosta de selfie, quem gosta de sentado, quem gosta de estático → distribui para cada persona.

### Teste de Criativo
- Pedir segunda-feira para "pautar criativo de acordo com Andrômeda, para que não haja entrega de um apenas".
- Mineração na biblioteca de anúncio via Perplexity para modelar criativos.
- Se criativo satura → trocar criativo, NÃO o produto. Rodízio de criativos mantém produto vendendo perpetuamente.

---

## 6. LEITURA DE MÉTRICAS

### CTR (Taxa de Cliques no Link)
- **Unidade de medida da qualidade do criativo.**
- Abaixo de 1% = criativo ruim.
- Acima de 2% = bom para Brasil.
- Acima de 3% = excelente.

### CPM (Custo por 1000 Impressões)
- **Valor do seu público.** Quanto custa mostrar para 1000 pessoas.
- Acima de R$70-80 = algo errado na conta. Mexer.
- Israel: CPM mais caro = R$30. Angélica = R$20. Imobiliária = R$15-16.

### Correlação CTR × CPM (Regra dos 5%)
- **CTR deve ser no mínimo 5% do valor do CPM.**
- CPM R$50 → CTR mínimo 2,5%.
- CPM R$30 → CTR mínimo 1,5%.
- Se correlação bate: clique mais barato, LP view mais barata, conversão mais barata.
- Se não bate: trocar criativo ou público.

### Connect Rate (Taxa de Conexão)
- % de pessoas que clicaram e realmente chegaram na página.
- **Mínimo 70%.** Ideal 90%+. Israel: 95%.
- Abaixo de 70% = perdendo 30% do dinheiro. Página lenta, hosting ruim.
- Pedir segunda-feira para otimizar connect rate **sem perder qualidade da imagem**.

### Finalização de Compra (Checkout Rate)
- % de pessoas que entraram no checkout e compraram.
- **Mínimo 50%.** Israel: 60-66%.
- Se CTR bom + CPM bom + NÃO converte → **problema é o negócio, não o tráfego.**
- Tráfego = demanda. Quem converte = seu negócio (página, copy, oferta, credibilidade).

### Amostragem do Facebook
- Facebook trabalha com **amostragem semanal** (3-7 dias).
- Precisa de **8.000-10.000 impressões** para precificar CPM.
- **NUNCA tomar decisão baseada em 1 dia.** Esperar 3 dias mínimo.
- Dia ruim seguido de dia bom é normal — Facebook otimiza na semana.
- Se já está convertendo e teve 1 dia ruim: NÃO mexer. Esperar 3 dias.

---

## 7. HACKS OPERACIONAIS

### Budget Ímpar (Hack do Leilão)
- **Nunca usar número redondo** (R$30, R$50, R$100).
- Usar R$33, R$51, R$43 — sair da gaveta de leilão das "sardinhas".
- A maioria bota número redondo → ficam no mesmo leilão → mais caro.
- Budget ímpar = gaveta de leilão diferente = CPM mais barato.

### Dark Post (Hack do CPM)
- Se CPM está caro: postar o criativo no **feed do Instagram** como post normal.
- Rodar campanha de **engajamento R$10** para o post (curtidas).
- Usar o post engajado como anúncio na campanha de venda.
- **CPM cai ~40%** porque post já tem engajamento → Facebook distribui melhor.
- Funciona especialmente bem para reconhecimento.
- **Não usar músicas licenciadas do Instagram** no post (senão não pode usar como anúncio).

### Subir Campanhas com Segurança
- **Não subir muitas campanhas de uma vez** (risco de bloqueio de BM).
- Subir uma, verificar, subir outra, verificar.
- Programar para rodar a partir de **00:05** do dia seguinte (24h para o Facebook otimizar).
- Pedir para IA **navegar de forma humana** ao subir campanhas (pausas, mouse lento).

### Não Lateralizar Contas
- Não rodar mesmo produto/público em múltiplas contas de anúncio.
- Facebook chama de **Shadow Ban** → pode punir todas as contas.
- Centralizar tudo em uma conta de anúncio por negócio.

### Remarketing em 2026
- **Não gastar dinheiro com campanha de remarketing separada.** Facebook já faz remarketing automático via pixel.
- Máximo: rodar criativo específico para quem visualizou página/Instagram nos últimos 90 dias.
- Fundo do funil real: cupom matador de desconto para quem viu e não comprou.

---

## 8. FUNIL TÉCNICO

```
RECONHECIMENTO (R$10/dia — branding, visibilidade)
    ↓ nutre pixel com dados baratos
TOPO DE FUNIL (criativo + público aberto/segmentado)
    ↓ clique → página → interesse
MEIO DE FUNIL (remarketing automático do Facebook)
    ↓ viu 7-12 vezes → confiança
FUNDO DE FUNIL (oferta + checkout)
    ↓ conversão → pixel fica mais inteligente
FUNDO DO FUNDO (cupom matador para quem não comprou)
```

### O que barateia o topo barateia tudo
- Segredo: **baratear o topo de funil.**
- Reconhecimento barato → público aquecido → campanha de venda mais barata.
- "O sucesso do fundo do funil é a qualidade do topo do funil."

---

## 9. POR TIPO DE NEGÓCIO

| Negócio | Público | Reconhecimento | Foco |
|---------|---------|---------------|------|
| Infoproduto | Compradores Envolvidos | Conteúdo de valor | Criativo + página |
| E-commerce | Compradores Envolvidos | Brand da loja | Criativo multi-ângulo |
| High ticket | Produtos alto valor + Original | Obrigatório | Qualificação + CRM |
| Negócio local | Geo + interesse | Obrigatório | Visibilidade + confiança |
| Imobiliária | Condomínio fechado | Obrigatório (CPM R$1,55) | Formulário + closer |
| Palestra/evento | Geo + interesse | Obrigatório | Reconhecimento + venda |
| Reunião/consultoria | Alto valor + Original | Bom ter | Calendly + closer |

---

## 10. INFRAESTRUTURA IMPLEMENTADA (07/04/2026)

| Componente | ID/Config | Status |
|-----------|-----------|--------|
| Meta Pixel | `${META_PIXEL_ID}` | Ativo |
| CAPI (server-side) | `/opt/CLIENTE_EXEMPLO/lib/meta-capi.ts` | Funcionando |
| GTM | `GTM-${GTM_ID}` | Publicado v2 |
| GA4 | `G-${GA4_ID}` | Ativo |
| LP → fbc, fbp, event_id | Todas 3 LPs | Deployed |
| Deduplicação browser↔server | event_id compartilhado | Funcionando |