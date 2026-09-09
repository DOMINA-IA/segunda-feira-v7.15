## Task Definition (AIOS Task Format V1.0)

```yaml
task: riskBoard()
responsável: Sentinel (Guardian)
responsavel_type: Agente
trigger: '*risk-board'
elicit: false
mode: autonomous
```

## Purpose

Display current risk board — all open bugs sorted by severity with SLA status, overdue flags, and recommended actions.

## Execution Steps

### Step 1: Query Command Center
```bash
curl -s -b CLIENTE_EXEMPLO_auth=authenticated_session_v1 \
  http://localhost:3000/api/projects | \
  python3 -c "
import sys, json
from datetime import datetime

data = json.load(sys.stdin)
today = datetime.now().strftime('%Y-%m-%d')

bugs = []
for p in data['projects']:
    for b in (p.get('bugs') or []):
        b['project'] = p['name']
        b['project_health'] = p['health_score']
        if b.get('deadline'):
            b['overdue'] = b['deadline'] < today
            days = (datetime.strptime(b['deadline'], '%Y-%m-%d') - datetime.now()).days
            b['days_to_deadline'] = days
        else:
            b['overdue'] = False
            b['days_to_deadline'] = None
        bugs.append(b)

# Sort: overdue first, then by severity
order = {'critical': 0, 'high': 1, 'medium': 2, 'low': 3}
bugs.sort(key=lambda x: (not x['overdue'], order.get(x.get('severity','low'), 4)))

print(json.dumps(bugs, indent=2, ensure_ascii=False))
"
```

### Step 2: Format Output

```
🚨 RISK BOARD — {date}
═══════════════════════

OVERDUE ({count}):
  🔴 {title} | {project} | {days} days overdue | Owner: {owner}

CRITICAL ({count}):
  {title} | {project} | {days_to_deadline}d left | Owner: {owner}

HIGH ({count}):
  {title} | {project} | {days_to_deadline}d left | Owner: {owner}

MEDIUM ({count}):
  {title} | {project} | {days_to_deadline}d left | Owner: {owner}

FIXED RECENTLY ({count}):
  ✅ {title} | {project} | fixed {fixedAt}

SUMMARY:
  Open: {open_count} | Fixed: {fixed_count} | Overdue: {overdue_count}
  SLA Compliance: {compliance}%
```

### Step 3: Recommendations

For each overdue or critical bug, generate specific recommendation:
- **Immediate action** needed (who does what)
- **Escalation** if blocked
- **Impact** if not resolved

## SLA Compliance Calculation

```
compliance = (bugs_within_sla / total_bugs_with_sla) * 100
```

Targets:
- Critical: 100% on-time (0 tolerance)
- High: 90% on-time
- Medium: 80% on-time
- Low: no target (backlog)
