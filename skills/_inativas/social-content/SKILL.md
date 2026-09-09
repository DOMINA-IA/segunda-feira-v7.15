---
name: social-content
description: "Criação de conteúdo para o Instagram @${CEO_INSTAGRAM} (DOMINA.IA) — posts, reels, carrosséis e stories nos pilares de autoridade, urgência e dados reais, com validação obrigatória de acentuação PT-BR e integração com o calendário do CLIENTE_EXEMPLO. Use quando precisar criar ou roteirizar conteúdo orgânico para o Instagram do CEO."
user-invocable: true
allowed-tools:
  - Read
  - Write
  - Edit
  - Bash
  - Grep
  - Glob
  - WebSearch
  - WebFetch
---

# Social Content — Skill de Criação de Conteúdo Instagram

## Contexto

Perfil: **@${CEO_INSTAGRAM}** — CEO da DOMINA.IA
Nicho: IA aplicada a negócios, ferramentas com IA, mentoria, eventos
Público: Empreendedores brasileiros 25-55 anos que querem usar IA para crescer

---

## Regras Invioláveis (atualizado 09-Mai-2026 — defesa estrutural)

1. **Acentuação validada por código (BLOQUEANTE):** rodar `python3 ~/cortex/scripts/validate-pt-accents.py` em todo script de geração. Validador detecta ~120 palavras PT-BR sem acento + 19 caracteres Unicode complexos + 10 nomes próprios proibidos. Sem aprovação do validador, NÃO renderizar.
2. **Glifos seguros por fonte:** apenas ASCII + acentos PT-BR + pontuação básica. Caracteres ☒ ⚠ 🚀 📊 emojis bandeira NÃO renderizam em Bebas Neue/Montserrat — viram quadrado X. Usar `>` `|` `+` `-` ASCII ou `draw.line()` primitiva.
3. **Agentes IA são funcionais, não personagens:** "AGENTE DE TRÁFEGO", "AGENTE DE FOLLOW-UP", "OS 4 SISTEMAS" — NUNCA Sobral/Atlas/Aurora/nomes próprios. Posicionamento DOMINA.IA "ferramenta > prompt" = sistema corporativo B2B.
4. **Auditoria visual pixel-a-pixel** em capas críticas — abrir PNG renderizado e verificar zero placeholder X. Não confiar em thumbnail.
5. **NUNCA mexer em posts já agendados no CLIENTE_EXEMPLO** — antes de criar qualquer conteúdo, verificar a agenda existente em `https://seudominio.com.br` ou no banco local.
6. **NUNCA repetir a mesma foto em todos os posts** — buscar imagens temáticas diferentes para cada publicação. Variedade visual é obrigatória.
7. **NUNCA recortar foto de dentro de outro criativo** — usar foto raw original ou estilo sem foto (tipografia pura, ícones, ilustrações).
8. **Formato padrão feed:** 1080x1080 (1:1) — só usar 1080x1920 (9:16) quando explicitamente solicitado para Stories/Reels.

**Pre-flight obrigatório no topo de TODO `gerar_*.py`:**

```python
import subprocess, sys
r = subprocess.run(
    ["python3", "$HOME/cortex/scripts/validate-pt-accents.py", __file__],
    capture_output=True, text=True
)
if r.returncode != 0:
    print(r.stdout, file=sys.stderr); sys.exit(1)
```

**Referências:** `~/cortex/vault/rules/visual-rendering-safety.md` + `~/.claude/skills/creative-validator.md` (9 checks bloqueantes).

---

## Pilares de Conteúdo

### Pilar 1: Autoridade (40% do conteúdo)
- Resultados reais com dados (CPL, leads, faturamento)
- Bastidores de operação (dashboard, métricas, processo)
- Opiniões fortes sobre o mercado de IA
- Cases de clientes e alunos
- **Tom:** Confiante, direto, sem enrolação

### Pilar 2: Educação (30% do conteúdo)
- Tutoriais rápidos de ferramentas IA
- Frameworks e métodos (tráfego, copy, automação)
- "Como eu fiz X usando IA"
- Desmistificação de conceitos técnicos
- **Tom:** Didático, acessível, prático

### Pilar 3: Urgência e Oportunidade (20% do conteúdo)
- "O mercado invisível" — oportunidades que ninguém vê
- Dados de mercado (crescimento IA, vagas, faturamento)
- Escassez real (vagas limitadas, prazos reais)
- Transformação: antes vs depois
- **Tom:** Provocativo, instigante, data-driven

### Pilar 4: Conexão e Bastidores (10% do conteúdo)
- Dia a dia do empreendedor
- Erros e aprendizados
- Motivação genuína (sem clichê)
- Interação direta com seguidores
- **Tom:** Humano, vulnerável, autêntico

---

## Estratégia de Reels

### Estrutura de Hook (primeiros 3 segundos)
Fórmulas que funcionam:
1. **Número + Promessa:** "3 ferramentas de IA que me geraram R$30K em 30 dias"
2. **Polêmica controlada:** "Quem ainda não usa IA para negócios vai ficar para trás em 2026"
3. **Pergunta direta:** "Você sabe quanto custa um lead qualificado hoje?"
4. **Revelação:** "Descobri um mercado que ninguém está olhando..."
5. **Prova social:** "218 pessoas já se inscreveram em 2 dias. Você ainda está de fora?"

### Formatos de Reels
| Formato | Duração | Quando Usar |
|---------|---------|-------------|
| Tutorial rápido | 30-60s | 2x/semana — ferramentas IA |
| Talking head | 15-30s | 3x/semana — opiniões, dados |
| Antes/Depois | 15-30s | 1x/semana — resultados |
| Trend + Nicho | 7-15s | 1x/semana — alcance |
| Bastidores | 30-90s | 1x/semana — humanização |

### CTAs para Reels
- **Engajamento:** "Comenta 'IA' que eu te mando o link"
- **Perfil:** "Segue para mais conteúdo como esse"
- **Link:** "Link na bio para se inscrever"
- **Salvar:** "Salva esse vídeo para consultar depois"
- **Compartilhar:** "Manda para aquele amigo que precisa ouvir isso"

---

## Framework de Carrossel (10 Slides)

### Estrutura Padrão
| Slide | Função | Exemplo |
|-------|--------|---------|
| 1 | **Capa com hook** | "5 formas de ganhar dinheiro com IA em 2026" |
| 2 | **Contexto/problema** | "97% dos empreendedores não sabem que esse mercado existe" |
| 3 | **Ponto 1** | Ferramenta/método/dado |
| 4 | **Ponto 2** | Ferramenta/método/dado |
| 5 | **Ponto 3** | Ferramenta/método/dado |
| 6 | **Ponto 4** | Ferramenta/método/dado |
| 7 | **Ponto 5** | Ferramenta/método/dado |
| 8 | **Resumo/consolidação** | Recap visual dos 5 pontos |
| 9 | **Prova social** | Resultado, depoimento, dado |
| 10 | **CTA forte** | "Quer aprender? Link na bio" |

### Regras de Design Carrossel
- Fundo escuro (#0D0D0D ou #1A1A1A) com texto branco
- Destaques em verde (#00FF88 ou #39FF14) — padrão da marca
- Fonte grande e legível (mínimo 24pt equivalente)
- Máximo 40 palavras por slide
- Ícones e elementos visuais em cada slide

---

## Estratégia de Stories

### Sequência Diária (5-8 stories)
1. **Bom dia com contexto** — O que vai acontecer hoje
2. **Bastidor** — Tela do computador, dashboard, processo
3. **Enquete ou caixinha** — Engajamento ativo
4. **Conteúdo educativo** — Dica rápida, ferramenta, insight
5. **Prova social** — Print de resultado, depoimento
6. **CTA** — Direcionamento para link, DM, ou ação

### Elementos de Engajamento
- **Enquetes:** "Você já usou IA no seu negócio? Sim / Ainda não"
- **Caixinha de perguntas:** "Me pergunta qualquer coisa sobre IA para negócios"
- **Quiz:** "Quanto você acha que custa um lead qualificado?"
- **Countdown:** Para eventos, lives, abertura de vagas
- **Slider de emoji:** "De 0 a 10, quanto você domina IA?"

---

## Calendário Semanal Template

| Dia | Formato | Pilar | Tema Exemplo |
|-----|---------|-------|--------------|
| Segunda | Reels talking head | Autoridade | Resultado da semana / dado de mercado |
| Terça | Carrossel 10 slides | Educação | Tutorial / framework / ferramentas |
| Quarta | Reels tutorial | Educação | Como usar ferramenta X com IA |
| Quinta | Reels trend + nicho | Urgência | Oportunidade / mercado invisível |
| Sexta | Carrossel ou static | Autoridade | Case / bastidores / dados |
| Sábado | Reels bastidores | Conexão | Dia a dia / reflexão |
| Domingo | Stories only | Conexão | Descanso + interação leve |

**Stories:** Todos os dias, 5-8 stories seguindo a sequência acima.

---

## Integração com CLIENTE_EXEMPLO

### Antes de Criar Conteúdo
```bash
# Verificar posts agendados no CLIENTE_EXEMPLO
# Endpoint: GET /api/content/scheduled
# Ou consultar banco PostgreSQL diretamente
```

### Ao Finalizar Conteúdo
- Subir criativo no CLIENTE_EXEMPLO (DB + diretório correto)
- Preencher: título, copy, hashtags, data/hora, plataforma
- Associar ao pilar de conteúdo correto
- Definir status: rascunho / aprovado / agendado

### Diretório de Assets
- Criativos: `/opt/CLIENTE_EXEMPLO/uploads/creatives/`
- Templates: `$HOME/projetos/dominaia/content-studio/`

---

## Hashtags Strategy

### Hashtags Fixas (usar em todo post)
`#dominaia #inteligenciaartificial #iaparanegócios`

### Hashtags por Pilar
- **Autoridade:** `#empreendedorismo #resultados #marketingdigital`
- **Educação:** `#dicadeia #ferramentasia #tutorial`
- **Urgência:** `#oportunidade #mercadoinvisível #futuro`
- **Conexão:** `#bastidores #vidadeempreendedor #rotina`

### Regras
- Máximo 15 hashtags por post (Instagram recomenda 3-5 em 2026)
- Misturar volume: 2 grandes (>1M), 3 médias (100K-1M), 5 pequenas (<100K)
- Nunca usar hashtags banidas ou irrelevantes

---

## Processo de Criação

1. **Verificar agenda** — Consultar CLIENTE_EXEMPLO para não conflitar
2. **Definir pilar e formato** — Usar calendário semanal como guia
3. **Escrever copy** — Hook forte, corpo conciso, CTA claro
4. **Selecionar/criar visual** — Imagem diferente para cada post, nunca repetir
5. **Revisar acentuação** — Checar TODOS os acentos antes de finalizar
6. **Subir no CLIENTE_EXEMPLO** — Criativo + metadados completos
7. **Agendar** — Data e horário otimizados (melhor horário: 12h, 18h, 20h)
