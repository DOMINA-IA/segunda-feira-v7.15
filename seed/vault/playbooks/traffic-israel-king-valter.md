---
id: traffic-israel-king-valter
title: "Tráfego Pago — Conhecimento de Curso Israel King + Valter (versão @traffic)"
type: playbook
domain:
- traffic
agents:
- traffic
axis: ops
tags:
- tráfego
- playbook
- pixel
- meta-ads
triggers:
- israel king
- valter
- pixel meta
- capi
- andrômeda
- gerenciador de eventos
- estrutura de campanha
status: active
created: '2026-07-07'
last_verified: '2026-07-07'
decay_rate: 0.02
links:
- target: playbook-israel-king-trafego
  type: related
- target: playbook-valter-pixel
  type: related
description: "Conhecimento de curso estático (Israel King — estratégia; Valter — operacional/pixel) extraído do agente @traffic (progressive disclosure, Sprint 2 A6). Versão condensada na voz do agente — para o conteúdo completo/fonte primária, ver playbook-israel-king-trafego.md e playbook-valter-pixel.md, que já cobrem o mesmo material com mais detalhe e citações diretas."
---

# Tráfego Pago — Conhecimento de Curso Israel King + Valter

> Nota de origem: este conteúdo vivia inline no agente `@traffic` (`$HOME/.claude/agents/ops/traffic.md`) e foi extraído em 07-Jul-2026 (Sprint 2, grupo A6 — progressive disclosure) para reduzir o tamanho do arquivo do agente. O agente mantém um ponteiro de 2-4 linhas apontando para esta nota.
>
> **Relação com as notas já existentes no vault:** `playbook-israel-king-trafego.md` e `playbook-valter-pixel.md` já documentam o mesmo material-fonte com mais profundidade (citações diretas, exemplos numéricos adicionais, seção comparativa King×Valter). Esta nota é a versão condensada na voz operacional do agente `@traffic` — útil como referência rápida sem abrir os dois arquivos-fonte.

## CONHECIMENTO ISRAEL KING — Estratégia

> Fonte: Gestor de tráfego com +40 clientes, agência, e-commerce R$1.1M/ano, certificação Meta.

### 1. PIXEL — O Funcionário Dentro do Facebook

- Pixel = funcionário do Facebook. Pixel novo é burro, pixel com dados é inteligente.
- **50 conversões** = meta para sair da fase de aprendizado.
- A cada compra: pixel absorve comportamento do comprador → busca similares.
- **Pixel browser sozinho não basta** (iOS 14+). Usar CAPI + GTM.

#### Nutrição do Pixel: CAPI + GTM
- **CAPI (API de Conversões):** envia dados server-side com dados enriquecidos (nome, fone, fbc, fbp, IP, user_agent).
- **GTM:** captura dados do navegador que o pixel sozinho perde → melhora nota de correspondência.
- **Nota de correspondência** = quanto o Meta associa evento a pessoa real. Sem CAPI = nota baixíssima.
- **CRM → Pixel:** lead chamou = Lead event. Lead fechou = Purchase event. Retroalimenta pixel.

#### Confirmar Eventos no Gerenciador
- Gerenciador de Eventos → pixel → "Analisar eventos"
- Eventos com exclamação vermelha = não reconhecidos pela Meta
- Se só mostra "navegador" sem nota → CAPI necessário
- **Obrigatório confirmar eventos** — campanha sem isso fica burra

### 2. ESTRUTURA DE CAMPANHA — Uma Campanha, Muitos Criativos

```
CAMPANHA (estrutural — NÃO MEXER)
  └─ CONJUNTO DE ANÚNCIO (inteligência — NÃO MEXER)
       └─ ANÚNCIOS/CRIATIVOS (aqui pode mexer)
```

**Regra de Ouro (King):** "Eu só tenho uma campanha de venda por cliente. Uma. Com 30 criativos dentro."

- **Nunca empilhar campanhas para o mesmo produto** → fragmentação de público → CPM sobe
- Facebook quer: **poucas campanhas, muitos criativos**
- Campanha e conjunto: não alterar após criar (perde inteligência acumulada)

#### Fluxo de Teste e Escala
1. Campanha principal rodando (ex: R$200/dia)
2. Testar criativo novo: campanha separada com R$33/dia (budget ímpar)
3. Se criativo validou → **duplicar para a campanha principal**
4. Desligar campanha de teste
5. Criativo herda inteligência do conjunto principal

### 3. PÚBLICOS — Original vs Advantage+

| Situação | Público Recomendado |
|----------|-------------------|
| Pixel novo / conta nova / pouca verba | **Original** — Facebook respeita segmentação |
| Pixel maduro com muitas conversões | **Advantage+** — Facebook sabe quem buscar |
| Público aberto (sem segmentação) | Tanto faz |
| Com segmentação específica | **Original** — Advantage+ ignora segmentação |

- **Compradores Envolvidos** (compraram online nos últimos 90 dias): excelente para low ticket, infoproduto, e-commerce
- **High Ticket:** Comportamentos → "Pessoas que preferem valor de produto alto no Brasil" → reduz 77M para ~10M qualificados

### 4. CAMPANHA DE RECONHECIMENTO — Topo de Funil

- **CPM:** R$1,55 (vs R$30+ de conversão) — extremamente barato
- **R$10/dia** alcança quase 10.000 pessoas
- **Não oferece nada.** Só apresenta quem você é, o que resolve
- Pessoa precisa ver **7 a 12 vezes** antes de comprar
- Quando campanha de venda roda: faz remarketing automático em cima de quem viu no reconhecimento
- **Resultado:** CPA cai drasticamente

| Negócio | Reconhecimento? |
|---------|----------------|
| Negócio local | Obrigatório |
| Imobiliária | Obrigatório |
| Palestra/evento | Fundamental |
| Infoproduto | Muito bom |
| E-commerce | Bom |

#### Aquecimento de Conta Nova
- Antes de anunciar venda: **5 dias** de engajamento na **página do Facebook** (não Instagram)
- R$10/dia, criativo genérico, objetivo: curtidas
- Sem isso, Facebook penaliza (vê que você só quer ganhar dinheiro)

### 5. ANDRÔMEDA — IA do Facebook para Distribuição de Anúncios

- IA da Meta que distribui anúncios para as personas certas
- **70% do sucesso = qualidade do criativo**. Segmentação perdeu importância.
- Reconhece criativos e manda para a persona certa automaticamente

#### Regras da Andrômeda
- Criativos muito similares → Andrômeda lê como um só → distribui apenas um → sobreposição
- **Ângulos diferentes, mesmo conteúdo:**
  - Um com selfie → persona A
  - Um sentada na cadeira → persona B
  - Um estático → persona C
  - Um com carro ao fundo → persona D
- Andrômeda sabe quem prefere cada formato e distribui para cada segmento

#### Estratégia de Criativo com Andrômeda
- Pedir ângulos que não se sobreponham (não apenas variações do mesmo)
- Mineração na Biblioteca de Anúncios via Perplexity para modelar criativos
- Criativo que satura → trocar criativo, **não o produto**. Rodízio de criativos mantém produto vendendo

### 6. MÉTRICAS — Leitura Correta

#### CTR (Taxa de Clique no Link)
- Unidade de medida da **qualidade do criativo**
- < 1% = criativo ruim
- > 2% = bom para Brasil
- > 3% = excelente

#### CPM (Custo por 1000 Impressões)
- Valor do público — quanto custa mostrar para 1000 pessoas
- > R$70-80 = algo errado na conta. Investigar.
- Referências King: próprio R$30, Angélica R$20, imobiliária R$15-16

#### Correlação CTR × CPM — Regra dos 5%
- **CTR deve ser no mínimo 5% do CPM**
- CPM R$50 → CTR mínimo 2,5%
- CPM R$30 → CTR mínimo 1,5%
- Se correlação bate: clique mais barato → LP view mais barata → conversão mais barata

#### Connect Rate (Taxa de Conexão)
- % de quem clicou e chegou na página
- **Mínimo 70%.** Ideal 90%+.
- Abaixo de 70% = perdendo dinheiro. Página lenta, hosting ruim.

#### Finalização de Compra (Checkout Rate)
- % de quem entrou no checkout e comprou
- **Mínimo 50%.** King: 60-66%.
- CTR bom + CPM bom + sem conversão = **problema no negócio, não no tráfego**

#### Amostragem
- Facebook trabalha com amostragem semanal (3-7 dias)
- Precisa de **8.000-10.000 impressões** para precificar CPM
- **NUNCA tomar decisão com 1 dia de dados.** Mínimo 3 dias.

### 7. HACKS OPERACIONAIS (King)

#### Budget Ímpar — Hack do Leilão
- **Nunca número redondo** (R$30, R$50, R$100)
- Usar R$33, R$51, R$43 — gaveta de leilão diferente das "sardinhas"
- Maioria usa número redondo → mesmo leilão → mais caro
- Budget ímpar = CPM mais barato

#### Dark Post — Hack do CPM (-40%)
1. Postar criativo no **feed do Instagram** como post normal (sem música licenciada)
2. Rodar campanha de **engajamento R$10** para o post (curtidas)
3. Usar o post engajado como anúncio na campanha de venda
4. **CPM cai ~40%** — post com engajamento tem distribuição melhor

#### Subir Campanhas com Segurança
- Não subir muitas campanhas de uma vez (risco de bloqueio BM)
- Subir uma → verificar → subir outra → verificar
- Programar para rodar a partir de **00:05** do dia seguinte (24h de otimização)

#### Não Lateralizar Contas
- Mesmo produto/público em múltiplas contas = Shadow Ban
- Centralizar tudo em **uma conta de anúncio por negócio**

#### Remarketing em 2026
- **Não gastar com campanha de remarketing separada** — Facebook já faz automaticamente via pixel
- Fundo do funil real: cupom matador para quem viu e não comprou (últimos 90 dias)

### 8. FUNIL TÉCNICO (King)

```
RECONHECIMENTO (R$10/dia — branding, visibilidade)
    ↓ nutre pixel com dados baratos
TOPO DE FUNIL (criativo + público segmentado/aberto)
    ↓ clique → página → interesse
MEIO DE FUNIL (remarketing automático do Facebook via pixel)
    ↓ pessoa vê 7-12 vezes → confiança
FUNDO DE FUNIL (oferta + checkout)
    ↓ conversão → pixel fica mais inteligente
FUNDO DO FUNDO (cupom matador para quem não comprou)
```

**Segredo:** Baratear o topo barateia tudo. Reconhecimento barato → público aquecido → campanha de venda mais barata.

---

## CONHECIMENTO VALTER — Operacional (Pixel e Setup)

> Fonte: Instrutor de tráfego para infoprodutores, comunidade MID (aula 08/04/2026).

### Pixel por Categoria de Produto

**Valter recomenda pixel separado por categoria** — diferente de King que usa um por cliente:

| Categoria | Pixel |
|-----------|-------|
| Low ticket | Separado |
| Médio ticket | Separado |
| High ticket | Separado |
| Evento online | Separado |
| Evento presencial | Separado |
| Mentoria | Separado |

**Por quê:** Cada categoria tem perfil de comprador diferente. Um pixel único misturado fica confuso — perde especificidade e assertividade.

### Setup de Pixel com CAPI — Passo a Passo

#### Criar Pixel no Meta
1. Gerenciador de Anúncios → Todas as ferramentas → **Configurações da empresa**
2. Lateral: **Conjunto de dados e pixel** → **Adicionar**
3. Nome descritivo (ex: `pixel_mentoria_abr2026`) — pixel criado não pode ser apagado
4. Selecionar conta de anúncio → Avançar → **Ir para gerenciador de eventos**

#### Configurar CAPI
1. Gerenciador de Eventos → **"Configurar API de conversões"**
2. **"Ver outras formas de configurar"** → Configurar manualmente → Avançar
3. **"Iniciar configurações de API"**
4. Categoria: **Educação**
5. Eventos a selecionar:
   - Adicionar informações de pagamento
   - Inicializar finalização de compra
   - **Comprar** (principal)
   - Pesquisar
   - **Lead** (principal)
   - Contato
   - Ver conteúdo
   - Concluir inscrição
6. **Selecionar TODOS os parâmetros** de detalhamento e informações do cliente → ficará verde "boas práticas"

#### Gerar e Salvar Token
- Clicar em **"Gerar token"** → copiar código
- **TOKEN É GERADO UMA ÚNICA VEZ** — salvar imediatamente em lugar seguro
- Salvar junto: ID do Pixel (na tela final)
- Formato sugerido:
  ```
  Pixel: [nome]
  ID Pixel: [número]
  Token API: [código grandão]
  ```

### Instalação em GreatPages (Landing Page)
1. Selecionar LP → não precisa entrar em edição de design
2. ⚙️ Engrenagem → **Integrações**
3. Habilitar **"Integração com Facebook API"**
4. Preencher: ID do Pixel + Token
5. **Salvar** → Publicar página

### Instalação em Eduzz (Checkout)
1. Produtos → **Links** → selecionar produto → Confirmar
2. **Pixel de conversão** → **Facebook**
3. ID de conversão = ID do Pixel
4. Chave/token = Token da API
5. **Salvar** → Fechar
6. Repetir para cada produto

### Validar se Pixel Está Funcionando
1. Gerenciador de Eventos → clicar no pixel → **"Evento teste"**
2. Selecionar canal **"Site"**
3. Colar URL da landing page → **"Eventos teste"**
4. Navegar na página aberta (clicar nos botões, descer, subir)
5. Voltar ao gerenciador: verificar **"Eventos recebidos"**
   - `PageView` = OK
   - Eventos aumentam conforme navega
6. Sinal positivo: **"Recebendo atividade"** em verde ✅
