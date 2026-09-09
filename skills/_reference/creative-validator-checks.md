# Creative Validator — Checks 6-9 (Referência Detalhada)

> Extraído de `$HOME/.claude/skills/creative-validator.md` (progressive disclosure, Sprint 2 A6). O arquivo principal mantém o fluxo e os checks 1-5 inline; aqui ficam as regras detalhadas dos checks 6-9. Mantenha os dois sincronizados se o pipeline mudar.

### CHECK 6: PADRÃO VISUAL APROVADO (MÉDIO)

**Severidade:** MÉDIO
**Ação em falha:** Alertar. Não bloqueia, mas documenta desvio.

#### Estilo visual campeão (Dark/Green Minimalista) — CPL R$3.61:

| Elemento | Especificação |
|----------|--------------|
| Fundo | Gradiente escuro dark navy/black (#0a0a0a a #1a1a1a) |
| Números grandes | Verde neon (#2ECC71 / #00ff88 / #39ff14) |
| Headlines | Texto branco bold |
| Subtexto | Cinza (#888888) |
| Botão CTA | Verde arredondado |
| Pill de data | Verde escuro (#1a6b3a) |
| Foto | SEM foto — text-only performa melhor |
| Estilo geral | Minimalista, limpo, muito espaço |
| Fonte títulos | Bebas Neue ou Impact, 80-200px |

#### Ângulos que funcionam (dados reais de performance):

| Ângulo | CPL | Exemplo |
|--------|-----|---------|
| Ganância/dinheiro | R$3.61-R$4.26 | "R$ X.XXX na mesa", "R$3K a R$30K por projeto" |
| Pergunta provocativa | R$5.00 | "E se você pudesse cobrar R$30K?" |
| Comparação CLT vs IA | A testar | Salário riscado vs valor por projeto |
| FOMO empresarial | A testar | "Seu concorrente já usa IA. E você?" |
| Dor do empresário | A testar | "IA faz o trabalho de 3 funcionários" |

#### Ângulos que NÃO funcionam (evitar):

| Ângulo | CPL | Motivo |
|--------|-----|--------|
| Urgência sozinha ("FALTAM X DIAS") | 0 leads | Falta benefício/oportunidade |
| Profissão do futuro | 0 leads | Muito genérico |
| Bold Numbers sem contexto | 0 leads | Número sem história |
| Case de terceiro (aluno R$9K) | R$9.48 | Case de terceiro não converte frio |
| Autoridade/método | R$7.63 | Oportunidade financeira > autoridade |

#### Estrutura de copy para Meta Ads:

```
Headline (name): Frase curta e impactante (< 40 chars)
Texto (message):
  - Linha 1: Hook (gancho forte)
  - Linha 2-3: Proposta de valor com números
  - Linha 4: Barreira removida ("sem programar")
  - Linha 5: CTA + data + gratuito
  - Emoji: apenas emoji de calendário para data
Description: Frase curta reforçando gratuidade
CTA: SIGN_UP
```

#### Segmentação por público (criativos diferentes):

| Público | Ângulo ideal | Dor |
|---------|-------------|-----|
| Aberto (geral) | Ganância + oportunidade | Não sabe que mercado existe |
| Empresários | IA substitui funcionário | Faz tudo sozinho, sobrecarregado |
| CLT renda alta | Comparação salário vs projeto | Insatisfeito com salário fixo |

#### Regra dos 20% (Meta):

- Texto não pode ocupar mais de 20% da área da imagem
- Se o criativo tem muito texto → redistribuir em mais linhas menores ou reduzir copy

#### Validação:

- Verificar que background usa tons escuros (#0a0a0a a #1a1a1a)
- Verificar que cor de destaque é verde (aceitar variações: #2ECC71, #00ff88, #39ff14)
- Se o criativo usa cores completamente fora do padrão → alertar (não bloquear)
- Desvios do padrão são aceitos APENAS se o usuário pediu explicitamente outro estilo

**Origem:** feedback_criativos_ads_regras.md — "O padrão com MELHOR CPL (R$3.61) é fundo escuro gradiente + números grandes em verde + texto branco bold."

---

### CHECK 7: UPLOAD CLIENTE_EXEMPLO (OBRIGATÓRIO — BLOQUEANTE)

**Severidade:** CRÍTICO
**Ação em falha:** BLOQUEAR entrega até upload completo.

**Regra:** Criativo NÃO existe até estar no CLIENTE_EXEMPLO. NUNCA declarar criativo "pronto" sem estar no CLIENTE_EXEMPLO.

#### Fluxo obrigatório (sem exceção):

```
1. Gerar imagens (PIL/Pillow)
2. SCP para VPS → /opt/CLIENTE_EXEMPLO/public/traffic-creatives/{slug}/
3. INSERT no banco → status = 'pending'
4. Informar ao usuário que estão no CLIENTE_EXEMPLO para aprovação
5. ESPERAR aprovação do usuário
6. SOMENTE DEPOIS de aprovado → subir na Meta API / criar campanha
```

#### Detalhes técnicos:

| Parâmetro | Valor |
|-----------|-------|
| VPS | `root@${VPS_HOST}` |
| Senha | ver 1Password sob "${REDIGIDO}" (nunca texto plano — ver `~/cortex/vault/infra/vps-principal.md`) |
| DB | `postgresql://${USER}:$${USER}_PASSWORD@localhost:5432/${USER}` (senha via .env do VPS — nunca hardcode) |
| Tabela | `traffic_creatives` |
| Status válidos | `pending`, `approved`, `rejected` (NUNCA outro valor) |
| image_path | `/traffic-creatives/{slug}/{arquivo}.png` (relativo ao public/) |

#### Campos da tabela traffic_creatives:

- `campaign_name` — Nome da campanha
- `piece_name` — Nome da peça
- `format` — Ex: '9:16'
- `variation` — Variação (A, B, C...)
- `image_path` — Path relativo ao public/
- `status` — SEMPRE 'pending' no upload inicial
- `notes` — Observações
- `uploaded_by` — 'claude-code'
- `uploaded_at` — timestamp

#### Comando de upload SCP:

```bash
# Senha via 1Password/.env — NUNCA hardcode. Ex: export VPS_ROOT_PASSWORD=$(op read "${REDIGIDO}/${REDIGIDO}/password")
sshpass -p "$VPS_ROOT_PASSWORD" scp -o StrictHostKeyChecking=no \
  {arquivo_local}.png \
  root@${VPS_HOST}:/opt/CLIENTE_EXEMPLO/public/traffic-creatives/{slug}/
```

#### Comando de INSERT no banco:

```bash
sshpass -p "$VPS_ROOT_PASSWORD" ssh root@${VPS_HOST} \
  "PGPASSWORD=$${USER}_PASSWORD psql -U ${USER} -d ${USER} -h localhost -c \
  \"INSERT INTO traffic_creatives (campaign_name, piece_name, format, variation, image_path, status, notes, uploaded_by, uploaded_at) \
  VALUES ('{campaign}', '{piece}', '9:16', '{var}', '/traffic-creatives/{slug}/{arquivo}.png', 'pending', '{notes}', 'claude-code', NOW());\""
```

#### NUNCA fazer:

- Subir criativos na Meta API ANTES de aprovação no CLIENTE_EXEMPLO
- Criar campanhas ANTES de confirmar o destino (LP? DM? Grupo?)
- Usar status diferente de `pending`, `approved`, `rejected`
- Copiar arquivos sem inserir no banco
- Esperar o usuário pedir upload — fazer AUTOMATICAMENTE
- Declarar criativos "prontos" sem estarem no CLIENTE_EXEMPLO
- Assumir que destino é LP — PERGUNTAR se não for óbvio

**Origem:** feedback_CLIENTE_EXEMPLO_criativos.md — "O ${CEO_NAME} precisa aprovar criativos visualmente no CLIENTE_EXEMPLO E definir a estratégia de destino ANTES de criar campanhas."

---

### CHECK 8: GLIFOS UNICODE (CRÍTICO — BLOQUEANTE)

**Severidade:** CRÍTICO
**Ação em falha:** Substituir por equivalente ASCII ou primitiva visual. Se impossível → BLOQUEAR.
**Origem:** sessão 09-Mai-2026 — placeholder X visível em capas que usavam ☒, ⚠, emojis. Bebas Neue só renderiza ASCII básico + acentos PT-BR; Montserrat tem `→` mas falha em emojis e box drawings.

#### Caracteres Unicode PROIBIDOS em strings que viram PNG:

| Caractere | Sai como | Substituir por |
|-----------|----------|----------------|
| ☒ ☑ ☐ | quadrado X | `→` (ASCII) ou `>` ou texto |
| ⚠ ⚡ 🔒 | quadrado X | "AVISO:", "ATENÇÃO:", "RÁPIDO", "SEGURO" texto |
| 📊 📈 📉 ⭐ | quadrado X | tipografia ou primitiva `draw.line()` |
| ✅ ❌ ⚙️ 💎 🚀 | quadrado X | ✓ ✗ ou texto: "OK", "NÃO", "CONFIG", "PREMIUM", "ESCALAR" |
| 🎯 🔥 💰 🤖 | quadrado X | texto: "FOCO", "HOT", "R$", "AGENTE", "IA" |
| ─ ━ ┃ ┗ ┓ (box drawing) | quadrado X em Bebas | use `draw.line()` para desenhar primitiva |
| 🇺🇸 🇨🇳 🇧🇷 (bandeiras) | quadrado X | texto: "EUA", "CHINA", "BRASIL" |

#### Dicionário oficial: `UNICODE_FORBIDDEN` em `~/cortex/scripts/validate-pt-accents.py` (~19 caracteres). Validador detecta automaticamente.

#### Caracteres Unicode SEGUROS em fontes Bebas Neue / Montserrat / Georgia:

- Letras ASCII (A-Z, a-z) e dígitos (0-9)
- Acentos PT-BR: á à â ã é ê í ó ô õ ú ç (e maiúsculas)
- Pontuação: . , ; : ? ! ' " ( ) [ ] { } -- — ...
- Símbolos básicos: → (Montserrat OK, Bebas FAIL) | + - = * / # @ R$ %
- Setas via texto: > < ^ v
- Asteriscos: *

**Regra de ouro:** se NÃO está nessa lista → BLOQUEAR e exigir alternativa textual ou primitiva visual.

#### Auditoria pós-render:

```python
# após Image.save()
from PIL import Image
img = Image.open(path)
# detectar zonas com quadrados pretos vazios (placeholder PIL)
# se detectar → marcar como falho e regenerar sem o glifo problemático
```

---

### CHECK 9: NOMENCLATURA FUNCIONAL DE AGENTES (CRÍTICO — BLOQUEANTE)

**Severidade:** CRÍTICO
**Ação em falha:** Substituir nome próprio por descrição funcional. NUNCA usar nome próprio para agente em conteúdo de marketing.
**Origem:** sessão 09-Mai-2026 — "Sobral" colidiu com Pedro Sobral (2M seguidores, concorrente). CEO esclareceu: nenhum nome próprio para agentes em posts.

#### Princípio

Agentes IA da DOMINA.IA são **sistemas funcionais**, não personagens. Posicionamento de "ferramenta > prompt" pede tom corporativo B2B, não persona-coach.

#### Nomenclatura PROIBIDA em conteúdo:

- Sobral, Atlas, Aurora, Íris, Sentinela, Alfa, Mestre — qualquer nome próprio para agente IA
- "O agente {Nome}" — sempre tirar o nome próprio
- Nome próprio em logs renderizados (ex: `--name 'X'`) — usar identificador de função em snake_case

#### Nomenclatura OBRIGATÓRIA em conteúdo:

| Categoria | Forma correta |
|-----------|---------------|
| Função | "AGENTE DE TRÁFEGO", "AGENTE DE TRACKING", "AGENTE DE PROGRAMAÇÃO" |
| Genérico | "AGENTE COMERCIAL", "AGENTE DE FOLLOW-UP", "AGENTE FINANCEIRO" |
| Coletivo | "OS 4 SISTEMAS", "AS 3 AUTOMAÇÕES", "O AGENTE EM AÇÃO" |

#### Detecção automática:

Adicionar ao validador `WORDS_FORBIDDEN` os nomes próprios listados como rejeitados (Sobral, Atlas, etc.) — qualquer aparição em string de script de geração = falha bloqueante.

**Origem completa:** `~/cortex/vault/feedback/feedback-sem-nome-agente-posts.md` e `~/.claude/projects/-HOME-/memory/feedback-sem-nome-agente-posts.md`.
