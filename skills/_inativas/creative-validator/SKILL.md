---
name: creative-validator
description: "Valida automaticamente qualquer criativo gerado (ads, posts, banners) com 7 checagens bloqueantes — acentos, espaçamento, foto, variedade, formato, visual, upload. Use sempre antes de entregar um criativo produzido por /ad-creative, /social-content, /paid-ads ou fluxo equivalente — não depende de invocação manual do CEO."
---

# /creative-validator — Pipeline de Validação de Criativos

## Propósito

Validar AUTOMATICAMENTE todo criativo gerado antes de entregar ao usuário. Este pipeline elimina os erros repetitivos que custam 3-5h/semana de retrabalho. NENHUM criativo pode ser entregue sem passar pelos 7 checks.

## Quando Usar

Este pipeline é AUTOMÁTICO — deve ser executado SEMPRE que qualquer agente ou skill gerar criativos (ads, posts, banners). Não depende de invocação manual.

Skills que DEVEM chamar este validador antes de entregar:
- `/ad-creative`
- `/social-content`
- `/paid-ads` (quando gera criativos)
- Qualquer fluxo que produza imagens PNG/JPG para Meta Ads ou Instagram

---

## Pipeline de Validação (7 Checks)

```
Gerar criativo → Check 1-6 → Se falhar: corrigir auto → Re-check → Se OK: Check 7 (upload) → Entregar
```

**Regra de ouro:** Se QUALQUER check CRÍTICO falhar e não puder ser corrigido automaticamente → BLOQUEAR e informar o problema específico. NUNCA entregar criativo com erro.

---

### CHECK 1: ACENTUAÇÃO (CRÍTICO — BLOQUEANTE AUTOMATIZADO)

**Severidade:** CRÍTICO
**Ação em falha:** O validador retorna exit 1 e a renderização NÃO acontece.
**Origem:** 4 incidentes (sessão 05-Abr-2026, sessão 09-Mai-2026 ×3) — regra advisory falhou consistentemente; convertida em código bloqueante.

#### Implementação canônica — VALIDADOR EXTERNO

Use o script Python oficial: `~/cortex/scripts/validate-pt-accents.py`
- Dicionário de ~120 palavras conhecidas sem acento (você, não, ações, automação, relatório, gestão, começar, etc.)
- Varre strings literais Python (`"..."` e `'...'`) em arquivos `.py` e `.md`
- Ignora linhas com `# noqa` ou que contenham `BLOQUEADO`/`corrija acentos` (meta-strings do próprio validador)
- Exit 0 se zero ocorrências, exit 1 com lista detalhada (linha + palavra + sugestão + contexto)

#### Pre-flight obrigatório no topo de TODO script gerador:

```python
# topo de gerar_*.py
import subprocess, sys
r = subprocess.run(
    ["python3", "$HOME/cortex/scripts/validate-pt-accents.py", __file__],
    capture_output=True, text=True
)
if r.returncode != 0:
    print(r.stdout, file=sys.stderr)
    print("\nBLOQUEADO: corrija acentos antes de renderizar.", file=sys.stderr)
    sys.exit(1)
```

#### Comandos de uso direto:

```bash
# Validar pasta inteira
python3 ~/cortex/scripts/validate-pt-accents.py --dir /tmp/posts/

# Validar arquivos específicos
python3 ~/cortex/scripts/validate-pt-accents.py script1.py script2.py
```

#### Manutenção do dicionário:

Quando uma palavra nova sem acento aparecer em produção:
1. Adicionar ao `WORDS_FORBIDDEN` em `~/cortex/scripts/validate-pt-accents.py`
2. Re-rodar validador para confirmar que pega a palavra
3. Re-render dos PNGs afetados

#### Regra complementar (auditoria visual):

Validador valida CÓDIGO. Para validar PNG renderizado:
- Após `Image.save()`, abrir o PNG via Pillow
- Inspecionar pixel-a-pixel zonas de texto críticas (capa, headlines, CTAs)
- Procurar por quadrado X / tofu □ — indica glifo faltante
- Se houver → ver Check 8

**Migração de scripts antigos:** Adicionar pre-flight em todos os scripts de `/tmp/posts/*.py` e equivalentes. Documentado em `~/cortex/vault/patterns/rules-instagram-posts.md` Seção 1.

---

### CHECK 2: ESPAÇAMENTO 9:16 (CRÍTICO — BLOQUEANTE)

**Severidade:** CRÍTICO
**Ação em falha:** Ajustar automaticamente. Se impossível → BLOQUEAR.

Para criativos no formato Story 1080x1920 (9:16), o conteúdo DEVE preencher >= 75% da altura do canvas.

#### Regras de distribuição vertical (1080x1920):

| Zona | Posição Y | Conteúdo |
|------|-----------|----------|
| Topo | y=120-220 | Badge inicial, tag de evento |
| Corpo principal | y=220-1300 | Headline, body, números, benefícios |
| CTA + info evento | y=1300-1600 | Botão CTA, data, local |
| Rodapé fixo | y=1780-1920 | Swipe up indicator, logo |

#### Critérios de validação:

- **y_final >= 1440** (75% de 1920) — conteúdo deve terminar em ou após esta linha
- **y_final >= 1500** (78% de 1920) — META IDEAL
- **y_final < 1200** — CRÍTICO, NUNCA entregar
- **y_final < 1400** — AUMENTAR espaçamentos antes de salvar

#### Margens mínimas:

- **Bordas laterais:** mínimo 40px (x >= 40, x <= 1040)
- **Topo:** conteúdo não começa antes de y=100
- **Base:** swipe up/logo em y >= 1780

#### Correção automática (quando y_final < 1440):

1. Aumentar font size dos títulos (incrementar 10-20px)
2. Aumentar spacing entre blocos (incrementar 20-40px entre seções)
3. Adicionar espaçamento após glow_line separador (+40px)
4. Se ainda insuficiente: aumentar tamanho do botão CTA
5. Re-calcular y_final após ajustes

#### Fontes recomendadas para preencher canvas:

- Bebas Neue headline: 80-200px
- Body text: 30-36px
- CTA button: 80px de altura
- Espaçamento entre blocos: mínimo 40-80px

**Origem:** feedback_criativos_espacamento.md — "gerei 7 criativos com conteúdo terminando em y=915 de 1920px (48% do canvas). O ${CEO_NAME} teve que pedir correção."

---

### CHECK 3: FOTO NÃO RECORTADA (CRÍTICO — BLOQUEANTE)

**Severidade:** CRÍTICO
**Ação em falha:** BLOQUEAR. Não há correção automática — requer decisão.

#### Regras absolutas:

1. **NUNCA usar foto extraída/recortada de dentro de outro criativo**
   - Fundo baked-in cria degradê feio e corte na cabeça
   - Transição visível entre fundo original e novo background

2. **NUNCA aplicar gradient fade em cima de foto recortada**
   - Sempre fica com corte na cabeça
   - Resultado amador

3. **Se a instrução mencionar "usar foto do criativo X"** → BLOQUEAR
   - Informar: "Não é possível recortar foto de outro criativo. Opções: (a) fornecer foto raw/limpa, (b) usar estilo dark/green sem foto"

4. **Fontes válidas de foto:**
   - Foto raw/original (sem texto, sem fundo de criativo)
   - Diretório de assets do projeto
   - Banco de imagens (Unsplash, Pexels, Pixabay)

5. **Se não tiver foto limpa disponível:**
   - Usar estilo dark/green SEM foto (melhor CPL: R$3.61)
   - Text-only performa MELHOR nos dados reais
   - Não forçar foto quando não tem asset limpo

#### Detecção automática:

- Verificar se o path da imagem fonte referencia outro criativo (ex: `*_criativo_*.png`, `*_v6_*.png`)
- Verificar se a instrução do usuário contém "recortar de", "usar foto do", "pegar de"
- Se detectar qualquer indicativo → BLOQUEAR com opções

**Origem:** feedback_foto_criativos.md — "Tentativas repetidas falharam 3 vezes — degradê em cima da cabeça, texto sobreposto, e transição feia. O ${CEO_NAME} ficou frustrado."

---

### CHECK 4: VARIEDADE VISUAL (ALTO)

**Severidade:** ALTO
**Ação em falha:** Alertar e sugerir correção. Não bloqueia, mas exige justificativa para prosseguir.

#### Regras:

1. **Em batch de múltiplos criativos: nenhuma foto pode repetir**
   - Cada peça deve ter identidade visual própria
   - Verificar hash ou path de cada imagem usada
   - Se detectar repetição → alertar e sugerir alternativa

2. **Cada peça deve ter visual distinto:**
   - Cores de destaque diferentes (verde, azul, dourado)
   - Layout variado (hero left vs center vs right)
   - Tipografia variada quando possível

3. **Se batch > 3 peças: exigir pelo menos 2 estilos diferentes**
   - Ex: 2 dark/green + 2 com foto + 1 bold numbers
   - Não gerar 5 peças idênticas só mudando texto

4. **Buscar variedade de imagens:**
   - Para cada post/criativo, buscar imagem temática relacionada ao assunto
   - Usar bancos de imagem gratuitos (Unsplash, Pexels, Pixabay) via Fetch/Playwright
   - Variar layouts entre posts — não usar o mesmo template visual em sequência
   - Fotos pessoais do ${CEO_NAME} podem ser usadas, mas alternadas com imagens temáticas

5. **Testar overflow de texto ANTES de subir**
   - Garantir que nenhum texto está cortado
   - NUNCA subir criativo sem verificar visualmente

**Origem:** feedback_criativos_variedade.md — "O usuário reclamou que todos os reels tinham a mesma foto, sem variedade. Isso torna o feed repetitivo e amador."

---

### CHECK 5: FORMATO CORRETO (ALTO)

**Severidade:** ALTO
**Ação em falha:** Corrigir automaticamente.

#### Formatos válidos:

| Contexto | Formato | Dimensões |
|----------|---------|-----------|
| Meta Ads (padrão) | 9:16 Story | 1080x1920 |
| Feed Instagram | 1:1 Feed | 1080x1080 |

#### Regras:

1. **Formato padrão para Meta Ads: SEMPRE 1080x1920 (9:16)**
   - Se nenhum formato foi especificado → usar 9:16
   - Não gerar 1080x1080 a menos que explicitamente solicitado

2. **Formato feed (1080x1080): APENAS quando o usuário pedir explicitamente**
   - Termos que ativam: "feed", "quadrado", "1:1", "1080x1080"
   - Se ambíguo → usar 9:16 (padrão mais seguro para ads)

3. **Verificação:**
   - Checar `Image.new()` ou equivalente — dimensões devem ser (1080, 1920) ou (1080, 1080)
   - Se detectar dimensões diferentes → corrigir automaticamente
   - Alertar se proporção está invertida (1920x1080 → horizontal, errado)

**Origem:** feedback_criativos_ads_regras.md — "Story: 1080x1920 (9:16) — formato padrão para Meta Ads. Feed: 1080x1080 apenas quando explicitamente solicitado."

---

### CHECKS 6-9: Padrão Visual, Upload CLIENTE_EXEMPLO, Glifos Unicode, Nomenclatura de Agentes

Regras detalhadas (paleta/ângulos aprovados, comandos de upload CLIENTE_EXEMPLO, dicionário de glifos Unicode proibidos, nomenclatura funcional de agentes) vivem em:

**`$HOME/.claude/skills/_reference/creative-validator-checks.md`**

Severidade e ação-em-falha de cada check estão resumidas na tabela "Resumo do Pipeline" abaixo — consulte o arquivo de referência antes de gerar criativo com foto/estilo, antes do upload no CLIENTE_EXEMPLO, ou se houver dúvida sobre glifo ou nome de agente na copy.

---

## Resumo do Pipeline

| Check | Nome | Severidade | Ação em Falha |
|-------|------|-----------|---------------|
| 1 | Acentuação (validador externo) | CRÍTICO | Pre-flight script bloqueia render → corrigir → re-rodar |
| 2 | Espaçamento 9:16 | CRÍTICO | Ajustar auto (font/spacing) → Re-check → Bloquear |
| 3 | Foto não recortada | CRÍTICO | BLOQUEAR → Informar opções ao usuário |
| 4 | Variedade visual | ALTO | Alertar → Sugerir alternativa → Exigir justificativa |
| 5 | Formato correto | ALTO | Corrigir auto para 1080x1920 |
| 6 | Padrão visual | MÉDIO | Alertar desvio → Documentar → Não bloqueia |
| 7 | Upload CLIENTE_EXEMPLO | CRÍTICO | BLOQUEAR → Upload obrigatório antes de entregar |
| 8 | Glifos Unicode | CRÍTICO | Substituir por ASCII/primitiva → re-render |
| 9 | Nomenclatura funcional agente | CRÍTICO | Substituir nome próprio por descrição funcional |

## Relatório de Validação

Após executar os 7 checks, gerar relatório inline:

```
CREATIVE VALIDATOR — Resultado
================================
Check 1 (Acentuação):    PASS / FIXED (N correções) / BLOCKED
Check 2 (Espaçamento):   PASS / FIXED (y_final: Npx) / BLOCKED
Check 3 (Foto):          PASS / BLOCKED (motivo)
Check 4 (Variedade):     PASS / ALERTA (detalhe)
Check 5 (Formato):       PASS / FIXED (de NxN para NxN)
Check 6 (Visual):        PASS / ALERTA (desvios)
Check 7 (Upload):        PASS (CLIENTE_EXEMPLO ID: N) / BLOCKED
================================
Veredicto: APROVADO / BLOQUEADO (checks N, N)
```

## Integração com Outros Fluxos

- **`/ad-creative`**: Chamar creative-validator ANTES de entregar qualquer peça
- **`/paid-ads`**: Se gerar criativos, passar pelo validator antes de subir na Meta API
- **`/social-content`**: Validar criativos de posts antes de agendar
- **Qualquer agente**: Se produzir imagem para Meta/Instagram → validar

## Regra Final

**Se eu IDENTIFICAR um problema durante a geração, CORRIGIR ANTES de entregar. Não apontar o problema e gerar com o mesmo erro. Fix primeiro, entrega depois.**
