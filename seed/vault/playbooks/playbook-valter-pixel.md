---
id: playbook-valter-pixel
title: Playbook Valter — Pixel Meta com CAPI (Passo a Passo Operacional)
type: playbook
domain:
- traffic
agents:
- traffic
tags:
- playbook
status: active
created: '2026-04-12'
last_verified: '2026-04-12'
decay_rate: 0.02
links:
- target: tagueamento-audit-framework
  type: auto-linked
- target: playbook-israel-king-trafego
  type: auto-linked
- target: specialists
  type: auto-linked
- target: empresa
  type: auto-linked
migrated_from: $HOME/.claude/projects/-HOME-/memory/playbook-valter-pixel.md
old_description: Aula do Valter (comunidade MID) sobre criar pixel Meta com API de
  Conversão, instalar em GreatPages e Eduzz. Complementa Israel King com visão operacional
  e segmentação de pixel por categoria de produto.
axis: ops
---

# Playbook Valter — Pixel Meta + CAPI: Passo a Passo Completo

> Fonte: Aula no YouTube (watch?v=5hsHsAFW66o) — comunidade MID
> Valter: instrutor de tráfego pago para infoprodutores (plataformas Eduzz/GreatPages)
> Data de estudo: 08/04/2026

---

## PRINCÍPIO CENTRAL: Pixel por Categoria de Produto

**Valter recomenda criar pixels separados, um por categoria:**

| Categoria | Pixel Separado |
|-----------|---------------|
| Low ticket | Sim |
| Médio ticket | Sim |
| High ticket | Sim |
| Evento online | Sim |
| Evento presencial | Sim |
| Mentoria | Sim |

**Por quê:** Cada categoria tem perfil de público diferente. Um único pixel misturado com todos os perfis (low a high ticket) fica "confuso" — perde especificidade e assertividade. O pixel deve funcionar como um vendedor experiente que sabe exatamente com quem falar.

> Compare com Israel King: King foca em "uma campanha por cliente". Valter refina para "um pixel por categoria de produto do infoprodutor" — especialmente relevante para quem vende múltiplas ofertas.

---

## PASSO A PASSO: Criação do Pixel com CAPI

### Etapa 1 — Criar o Pixel no Meta Business Manager

1. Gerenciador de Anúncios → **Todas as ferramentas** → **Configurações da empresa**
2. Lateral esquerda: **Conjunto de dados e pixel**
3. Clicar em **Adicionar** (topo direito)
4. Dar um nome ao pixel (ex: `pixel_mentoria_abr2026`) — nome é só para organização
5. **IMPORTANTE:** Um pixel criado nunca pode ser apagado — nomear com cuidado
6. Selecionar a conta de anúncio que vai usar esse pixel
7. Clicar em **Avançar** → **Ir para o gerenciador de eventos**

### Etapa 2 — Configurar a API de Conversão (CAPI)

1. No Gerenciador de Eventos, clicar em **"Configurar API de conversões"**
2. Clicar em **"Ver outras formas de configurar"** → **Configurar manualmente**
3. Clicar em **Avançar** → **Iniciar configurações de API**

#### Configuração de Categoria e Eventos
- Selecionar categoria: **Educação** (para infoprodutos/cursos)
- Selecionar eventos (Valter seleciona todos esses):
  - Adicionar informações de pagamento
  - Inicializar a finalização de compra
  - **Comprar** (principal)
  - Pesquisar
  - **Lead** (principal para captação)
  - Contato
  - Ver conteúdo
  - Concluir a inscrição

#### Parâmetros de Detalhamento
- **Selecionar TODOS os parâmetros** de detalhamento de evento E informações do cliente
- Quando tudo estiver selecionado, aparece "boas práticas" em verde — sinal positivo
- Clicar em Continuar → Continuar → Enviar instruções → Continuar

### Etapa 3 — Gerar e Salvar o Token da API

> **ATENÇÃO CRÍTICA:** O token é gerado uma ÚNICA VEZ. Se perder, precisa gerar outro.

1. Na tela final do gerenciador de eventos, clicar em **"Gerar token"**
2. Passar o mouse sobre o código gerado → clicar para copiar
3. **Salvar imediatamente** em Word/bloco de notas com estrutura:
   ```
   Pixel: [nome do pixel]
   ID do Pixel: [número do pixel — copiar da tela final]
   Token API: [código grandão gerado — colar aqui]
   ```
4. Clicar em **Concluir**

---

## INSTALAÇÃO: GreatPages (Landing Page)

1. Abrir a LP na GreatPages (não precisa entrar em modo de edição do design)
2. Clicar na **engrenagem** (⚙️) → **Integrações**
3. Habilitar **"Integração com Facebook API"**
4. Preencher:
   - **ID de rastreamento do Facebook Pixel:** colar o ID do pixel
   - **Token:** colar o token da API de conversão
5. Clicar em **Salvar**
6. Publicar a página

---

## INSTALAÇÃO: Eduzz (Checkout)

1. No Eduzz: **Produtos** → **Links**
2. Clicar no produto desejado → **Confirmar**
3. Na tela do produto: **Pixel de conversão** → **Facebook**
4. Preencher:
   - **ID de conversão:** colar o ID do pixel
   - **Token (chave de API de conversão):** colar o token grandão
5. Clicar em **Salvar** → **Fechar**

> Fazer esse processo para CADA produto que queira rastrear.

---

## VALIDAÇÃO: Testar se o Pixel Está Funcionando

1. Gerenciador de Eventos → clicar no pixel criado
2. Clicar em **"Evento teste"**
3. Selecionar canal **"Site"**
4. Confirme a configuração → colar a URL da landing page
5. Clicar em **"Eventos teste"** — abre a página no browser
6. Navegar na página: descer, subir, clicar nos botões (simular comportamento de visitante)
7. Voltar ao gerenciador → verificar se aparecem **"Eventos recebidos"**:
   - `PageView` = visualização da página — OK
   - Mais eventos conforme clica nos CTAs
8. Se aparecer **"Recebendo atividade"** em verde = configuração correta ✅

> Sinal visual no browser: o **Meta Pixel Helper** (extensão Chrome) deve mostrar número > 0 na aba onde a página foi aberta.

---

## REGRAS OPERACIONAIS DO VALTER

| Regra | Detalhe |
|-------|---------|
| Pixel por categoria | Nunca misturar low ticket com high ticket no mesmo pixel |
| Token = único | Gerar uma vez, salvar antes de fechar a tela |
| Pixel = funcionário | Quanto mais dados, mais inteligente e assertivo |
| CAPI obrigatório | Pixel de browser sozinho é insuficiente (iOS 14+, cookies) |
| Instalar em TUDO | LP + checkout = mínimo. Ideal: todas as páginas do funil |
| Selecionar todos parâmetros | Maximiza a inteligência do pixel e o ROI |

---

## ANALOGIA DO VALTER (para explicar ao cliente)

> "O pixel é como um carimbinho que vai carimbando cada etapa que a sua lead percorre dentro do seu anúncio, dentro da sua página, dentro do seu checkout."

> "Quanto mais informações [o pixel] tem, mais assertivo ele é. Como nós, seres humanos, quanto mais informações nós temos, mais assertivos nós somos."

---

## COMO SE RELACIONA COM ISRAEL KING

| Tema | Israel King | Valter |
|------|------------|--------|
| Estratégia de pixel | Um pixel por cliente/negócio | Um pixel por categoria de produto |
| CAPI | Explica por que é necessário (iOS 14, nota de correspondência) | Mostra como configurar passo a passo |
| GTM | Recomenda GTM junto com CAPI | Não menciona GTM |
| Eventos | Foca em Lead + Purchase | Detalha todos os 8 eventos para educação |
| Instalação | Conceitual | Operacional (GreatPages + Eduzz) |
| Validação | "Confirmar eventos no gerenciador" | Mostra passo a passo do teste |
| Plataformas | Agnóstico | Específico para GreatPages + Eduzz |

**Usar King para estratégia + Valter para execução.**