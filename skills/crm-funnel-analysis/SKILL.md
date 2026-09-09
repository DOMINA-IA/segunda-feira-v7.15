---
name: crm-funnel-analysis
description: "Analisa funil e Tempo Médio de Vida de um CRM — extrai por API/DB, calcula conversão por etapa e gargalo. Use ao avaliar performance comercial. NOT for: mexer em lead individual no CRM."
tools: ["Read", "Write", "Edit", "Bash", "Glob", "Grep", "WebFetch"]
harnesses:
  - claude-code: full
  - codex: native
  - cursor: limited
  - aider: limited
---

# CRM Funnel Analysis — Método de leitura completa de pipeline

Validado em 06/05/2026 contra CLIENTE_EXEMPLO Pipeline (3.833 opps) e CRM próprio CLIENTE_EXEMPLO (171 contatos). Resultado: relatório de 12 KB + PDFs em ~30 minutos, com 6 heurísticas extraídas.

## Quando usar

- CEO pediu "ler o CRM" / "TMV" / "tempo no funil"
- Comparativo entre 2+ CRMs (ex: agência vs casa)
- Diagnóstico de gargalo de conversão
- Antes de mudança de processo comercial (SLA, scripts SDR, simplificação de etapas)
- Pesquisa de causa raiz de perdas

## Quando NÃO usar

- Pergunta pontual sobre 1 lead — usar query SQL direto
- Análise puramente quantitativa de receita/CAC — usar `campaign-report` ou `analyst`
- Relatório operacional de rotina — usar dashboards existentes

## Stack de ferramentas

| Ferramenta | Quando |
|-----------|--------|
| **API do CRM** (preferido) | Sempre tentar primeiro — checar painel `/api/` para token |
| **DB SQLite/Postgres direto** | Se for sistema próprio com acesso na VPS |
| **Export XLS/CSV via UI** | Se API não tem histórico granular de mudança de etapa |
| **Scraping DOM (Playwright)** | ÚLTIMO RECURSO — frágil, lento, propenso a estourar contexto |

## Protocolo de execução

### Fase 1 — Reconnaissance (5 min)

1. **Achar a fonte de dados certa**, em ordem:
   - Buscar página `/api/`, `/integrations/`, `/settings/api` no painel
   - Probing de header de auth: testar `Authorization`, `Token`, `X-Token`, `access-token`, `Authorization: Bearer` com curl `-w "%{http_code}"`
   - Se for sistema próprio: `ssh root@VPS "ls /opt/PROJECT/dashboard/*.db"` e `scp` o arquivo
2. **Mapear estrutura sem extrair tudo:**
   - Listar funis/pipes (`SELECT pipe_name, COUNT(*)` ou similar)
   - Listar stages (geralmente em `/v1/pipes` ou hard-coded no schema)
   - Verificar campos de timestamp: `created_at`, `updated_at`, `stage_last_change`, `close_in`, `consultation_date`
3. **Confirmar período coberto** antes de prometer comparação histórica

### Fase 2 — Extração (10-30 min)

**Via API REST** (padrão mais comum):
```bash
TOKEN="<uuid>"
mkdir -p /tmp/PROJECT/pages
PAGE=1
while true; do
  curl -s --max-time 60 -H "Authorization: $TOKEN" \
    "https://api.CRM.com/v1/opportunities?limit=200&page=$PAGE" \
    -o /tmp/PROJECT/pages/page_$PAGE.json
  COUNT=$(python3 -c "import json; d=json.load(open('/tmp/PROJECT/pages/page_$PAGE.json')); print(len(d.get('get_list',{}).get('itens',[])))")
  echo "Page $PAGE: $COUNT itens"
  [ "$COUNT" -lt "200" ] && break
  PAGE=$((PAGE+1))
done
```

**Via SQLite local** (sistema próprio):
```bash
scp root@VPS:/opt/PROJECT/dashboard/db.sqlite /tmp/PROJECT/db.sqlite
sqlite3 /tmp/PROJECT/db.sqlite ".tables"
sqlite3 /tmp/PROJECT/db.sqlite ".schema main_table"
```

⚠️ **Anti-pattern:** Rodar paginação em background com `&` — Bash em sandbox pode matar antes do `done`. Sempre rodar em foreground com timeout >60s.

### Fase 3 — Cálculo de métricas (15 min)

Para cada lead, calcular:

| Métrica | Fórmula |
|---------|---------|
| **Lead time → ganha** | `close_in - added_in` para opps com type='win' |
| **Lead time → perda** | `close_in - added_in` para opps com type='loss' |
| **Tempo na stage atual** | `now - stage_last_change` para opps em aberto |
| **Tempo de 1ª resposta** | `MIN(activities.created_at) - contact.created_at` |
| **Tempo POR etapa (histórico)** | reconstruir via `crm_activities WHERE type='status_change'`: para cada par consecutivo, calcular delta |

**Buckets recomendados** (lead time):
- `<1 dia` (quick-close — perfil indicação/cliente ativo)
- `1-7 dias` (rápido)
- `8-30 dias` (médio — coração da operação)
- `31-90 dias` (longo)
- `>90 dias` (resgate)

### Fase 4 — Análise por dimensões (10 min)

Para cada coluna importante, contar total + ganhas + perdidas + conv%:
- Origem (Mídia paga, Indicação, Cliente Ativo, Orgânico)
- Suborigem (Meta, Google, Indicação Cliente, Indicação Parceiro)
- Responsável (assigned_to)
- Score qualificativo (S/A/B/C)
- Mês de entrada (curva de captação + sazonalidade)

**Sempre destacar:**
- Pacientes/leads com 2+ vendas (recorrentes — público AA real)
- Suborigens com conv >50% (replicar)
- Suborigens com conv <1% (cortar ou recalibrar)

### Fase 5 — Cálculo de taxas com múltiplos denominadores

Quando o CEO perguntar "qual a taxa de fechamento?", responder com **TODAS as variações**:

| Denominador | Significado | Quando reportar |
|-------------|-------------|-----------------|
| Total de leads | Funil completo | Métrica de marketing |
| Qualificados | Filtrando lixo | Métrica de SDR |
| Score A+B (quentes) | Alta intenção | Métrica de closer |
| Que chegaram a Agendamento | Avaliando consulta | Diagnóstico operacional |
| Que chegaram a Pré-Consulta | Pós tomografia | Capacidade de fluxo |
| Em "Consulta + Pitch" | Imediatamente antes do pagamento | Métrica de fechamento real |

A taxa única perde informação. **Mostrar a queda em CADA passagem** revela onde mora o gargalo.

### Fase 6 — Comparativo entre CRMs (se aplicável)

⚠️ **Estabelecer equivalência por MARCO FINANCEIRO, não por nome de stage:**
- "Consulta paga" no CRM A = "Compareceu" no CRM B (se houver pagamento na consulta)
- "Fechado" em CRM A = "Procedimento confirmado" em CRM B (não basta nome igual)

Pipeline com nomes parecidos mas semânticas diferentes gera comparação enganosa.

### Fase 7 — Entrega

Estrutura padrão do relatório:
1. **Sumário executivo** com 8-10 achados em tabela (severidade 🔴🟠🟡🟢)
2. Estrutura do pipeline (mapa de etapas)
3. Receita & ticket médio
4. Lead time (entrada → desfecho) com buckets
5. Tempo POR etapa (atual + histórico reconstruído)
6. Tempo de 1ª resposta (segredo do high-ticket)
7. Origem e suborigem
8. Motivos de perda (humanizados — não usar IDs)
9. Produtividade por usuária responsável
10. Evolução mensal
11. Recomendações priorizadas (P0 / P1 / P2 — Hormozi style: maior alavancagem primeiro)

Salvar em `~/Downloads/`:
- `PROJECT_Analise_TMV_CRM.md` (markdown)
- `PROJECT_Analise_TMV_CRM.pdf` (Chrome headless)
- `PROJECT_CRM_dados_brutos/` (JSONs, scripts, DB)
- `PROJECT_Fechamentos.csv` (lista de ganhas — sep `;`, encoding utf-8-sig pra Excel pt-BR)

## Conversão MD → PDF

Quando WeasyPrint falhar por libs nativas (libgobject), fallback Chrome headless:
```bash
"/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" \
  --headless=new --disable-gpu --no-pdf-header-footer --print-to-pdf-no-header \
  --print-to-pdf="output.pdf" "file:///path/to/report.html"
```

CSS para PDF (tabelas grandes):
```css
@page { size: A4; margin: 1.6cm 1.4cm 2cm 1.4cm; }
table { border-collapse: collapse; width: 100%; font-size: 8.5pt; page-break-inside: avoid; }
thead { background: #1a1a2e; color: #fff; }
th, td { border: 1px solid #ccc; padding: 5px 7px; }
tbody tr:nth-child(even) { background: #fafafa; }
blockquote { border-left: 3px solid #c0392b; background: #fef6f5; page-break-inside: avoid; }
```

## Heurísticas validadas

### H1 — SLA de 1ª resposta é o maior preditor de perda
Quando `loss_reason = "tentativa de contato esgotadas"` representa >30% das perdas, parar TODA discussão sobre copy/oferta/preço e atacar SLA primeiro. Confidence: 0.95.

### H2 — Cliente Ativo + Indicação convertem 50× mais que Mídia Paga
Em high-ticket, 1-2% do volume vira 60-70% das ganhas. Programa formal de indicação tem ROI quase infinito. Confidence: 0.9.

### H3 — Funis com >15 etapas viram letra morta
Padrão saudável: 5-8 etapas. Se vê 27 com 8 vazias, é debt acumulado, não complexidade real. Confidence: 0.85.

### H4 — Schema sem stage de fechamento esconde estagnação
Em CRM novo, pré-criar stages e activity types correspondentes a CADA marco financeiro (consulta paga, sinal, contrato, primeira parcela). Caso contrário, vendas reais ficam fora do sistema. Confidence: 0.9.

### H5 — Score qualificativo no UI da LP > campo manual no CRM
Wizard de qualificação na LP captura 77% dos leads vs ~1-5% via campo manual. Confidence: 0.9.

### H6 — Pacientes com 2+ vendas = público AA absoluto
Em high-ticket consultivo (saúde, jurídico, B2B caro), 10-15% das ganhas vêm de clientes recorrentes que somam 25-30% da receita. Antes de captar mais, ligar pra esses primeiro. Confidence: 0.85.

## Anti-patterns

| Evitar | Por quê |
|--------|---------|
| Reportar 1 taxa única de conversão | Esconde onde mora o gargalo |
| Comparar nomes de stage sem checar semântica | "Agendado" pode significar 5 coisas diferentes |
| Tentar scrapear DOM antes de buscar API | API sempre é 100× mais rápida e estável |
| Usar IDs numéricos de motivo de perda no relatório | Humanizar com nome real (loss_reason_id=7 → "Tentativa de contato esgotadas") |
| Ignorar leads em "Descarte" / "Follow-up" antigos | É onde mora o estoque morto recuperável |
| Fazer comparativo sem normalizar período | 12 meses vs 1 mês precisa ser explicitado |
| Esquecer de salvar dados brutos junto com o relatório | Sem reprodutibilidade, próxima análise refaz tudo |

## Output esperado por execução

- 1 relatório MD + PDF (12-20 KB de texto, 4-8 páginas PDF)
- 1 CSV de fechamentos (separador `;`, encoding utf-8-sig)
- 1 pasta de dados brutos (JSONs ou DB + scripts Python reutilizáveis)
- 1 nota CORTEX em `~/cortex/vault/feedback/feedback-PROJECT-tmv-MES-ANO.md`
- 1 entrada na memória pessoal apontando pra nota CORTEX

## Fontes desta skill

- Sessão de validação: 06/05/2026 — análise dual CLIENTE_EXEMPLO CLIENTE_EXEMPLO (CLIENTE_EXEMPLO) + CLIENTE_EXEMPLO Casa
- Nota CORTEX: `~/cortex/vault/feedback/feedback-clienteexemplo-tmv-funil-mai-2026.md`
- Scripts de referência: `~/projetos/clientes/clienteexemplo/dados-brutos/analyze.py`, `~/projetos/clientes/clienteexemplo/dados-brutos/casa/analyze_casa.py`
