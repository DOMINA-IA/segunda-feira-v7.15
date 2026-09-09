---
name: cortex
description: "Interface de linha de comando do CORTEX Knowledge System — busca por termo, briefing de agente, saúde do vault, estatísticas, ingest e rebuild de índices. Use quando precisar consultar ou administrar o CORTEX manualmente, além do que o hook injeta automaticamente."
tools: ["Read", "Write", "Edit", "Bash", "Glob", "Grep"]
---

# /cortex — Knowledge System Interface

> **Tipo:** Skill de gestão de conhecimento | **Sistema:** CORTEX v1.0
> **Localização:** `~/cortex/`

## Objetivo

Interface unificada para operar o CORTEX — buscar conhecimento, verificar saúde do vault, gerar briefings, adicionar notas.

## Comandos

O usuário pode invocar `/cortex` seguido de um subcomando:

| Subcomando | Ação |
|-----------|------|
| `/cortex` (sem args) | Status geral: stats + health resumido |
| `/cortex query TERMO` | Buscar conhecimento por termo |
| `/cortex agent NOME` | Mostrar briefing completo do agente |
| `/cortex health` | Relatório de saúde completo do vault |
| `/cortex stats` | Estatísticas do vault |
| `/cortex rebuild` | Reconstruir índices + briefings |
| `/cortex ingest` | Adicionar nova nota (interativo) |
| `/cortex stale` | Listar notas que precisam verificação |
| `/cortex links ID` | Mostrar links de/para uma nota |

## Execução

### Sem argumentos — Status geral
```bash
python3 ~/cortex/scripts/cortex_engine.py stats
python3 ~/cortex/scripts/cortex_engine.py health
```
Mostrar resultado formatado ao usuário.

### query TERMO
```bash
python3 ~/cortex/scripts/cortex_engine.py query "TERMO"
```
Mostrar resultados ranqueados. Se o usuário quiser mais detalhes, ler a nota indicada.

### agent NOME
```bash
cat ~/cortex/briefings/NOME.md
```
Se briefing não existir, gerar com:
```bash
python3 ~/cortex/scripts/cortex_engine.py build-briefings
cat ~/cortex/briefings/NOME.md
```

### health
```bash
python3 ~/cortex/scripts/cortex_engine.py build-index
python3 ~/cortex/scripts/cortex_engine.py health
```

### rebuild
```bash
python3 ~/cortex/scripts/cortex_engine.py build-index
python3 ~/cortex/scripts/cortex_engine.py build-briefings
```
Confirmar quantidade de notas indexadas e briefings gerados.

### ingest
Perguntar ao usuário:
1. Título da nota
2. Tipo (project, infra, pattern, playbook, feedback, rule, agent, meta)
3. Domínios relevantes
4. Agentes que precisam dessa informação
5. Tags
6. Corpo da nota

Executar:
```bash
~/cortex/scripts/ingest.sh --title "TITULO" --type TIPO --domain D1 D2 --agents A1 A2 --tags T1 T2
```
Depois editar a nota para adicionar o corpo completo.

### stale
```bash
python3 ~/cortex/scripts/cortex_engine.py build-index 2>/dev/null
python3 -c "
import json
from pathlib import Path
h = json.loads((Path.home() / 'cortex/index/health.json').read_text())
for n in h.get('stale_notes', []):
    print(f'  🔴 {n[\"id\"]} (freshness: {n[\"score\"]})')
for n in h.get('review_notes', []):
    print(f'  ⚠️  {n[\"id\"]} (freshness: {n[\"score\"]})')
if not h.get('stale_notes') and not h.get('review_notes'):
    print('  ✅ Nenhuma nota stale ou pendente de revisão')
"
```

### links ID
```bash
python3 -c "
import json
from pathlib import Path
graph = json.loads((Path.home() / 'cortex/index/graph.json').read_text())
note_id = 'ID'
outgoing = [e for e in graph['edges'] if e['source'] == note_id]
incoming = [e for e in graph['edges'] if e['target'] == note_id]
if outgoing:
    print(f'  → Saída ({len(outgoing)}):')
    for e in outgoing:
        print(f'    --[{e[\"type\"]}]--> {e[\"target\"]}')
if incoming:
    print(f'  ← Entrada ({len(incoming)}):')
    for e in incoming:
        print(f'    <--[{e[\"type\"]}]-- {e[\"source\"]}')
if not outgoing and not incoming:
    print(f'  👻 Nota orphan — sem links')
"
```
