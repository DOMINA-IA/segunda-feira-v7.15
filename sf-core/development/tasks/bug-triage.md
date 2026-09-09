## Task Definition (AIOS Task Format V1.0)

```yaml
task: bugTriage()
responsável: Sentinel (Guardian)
responsavel_type: Agente
trigger: '*bug-triage'
elicit: true
mode: interactive
```

## Purpose

Triage a new bug — classify severity, assign owner, set SLA deadline, define action plan, and register in Command Center.

## Execution Steps

### Step 1: Gather Bug Info (elicit)

Ask user:
1. **Qual projeto?** (auto-suggest from project list)
2. **Descreva o bug** (o que acontece vs o que deveria acontecer)
3. **Impacto** — Alguma funcionalidade core está bloqueada? Há perda financeira?
4. **Workaround existe?**

### Step 2: Classify Severity

Based on answers:

| Criteria | Severity |
|----------|----------|
| Core functionality blocked OR financial loss | **Critical** — SLA 48h |
| Daily operation impacted, workaround exists | **High** — SLA 7 days |
| Annoying but doesn't block operation | **Medium** — SLA 30 days |
| Quality improvement only | **Low** — Backlog |

### Step 3: Assign Owner

Decision matrix:
- Code fix needed → **@dev**
- Infrastructure/deploy issue → **@devops**
- Client action needed → **${CEO_NAME}** (contact client)
- Traffic/ads optimization → **${CEO_NAME} + @traffic**
- Design/UX issue → **@ux-design-expert**

### Step 4: Define Action Plan

Write specific, actionable steps:
- What exactly needs to be done
- Which files/systems are affected
- How to verify the fix
- Rollback plan if fix fails

### Step 5: Calculate Deadline

```
deadline = today + SLA_days
if weekend falls within:
  deadline += weekend_days
```

### Step 6: Register in Command Center

```sql
-- Get current bugs for project
SELECT bugs FROM projects WHERE slug = '{project_slug}';

-- Append new bug to JSONB array
UPDATE projects SET bugs = bugs || '[{
  "title": "{bug_title}",
  "severity": "{severity}",
  "status": "open",
  "owner": "{owner}",
  "sla": "{sla}",
  "deadline": "{deadline}",
  "action": "{action_plan}"
}]'::jsonb, updated_at = NOW()
WHERE slug = '{project_slug}';
```

### Step 7: Notify

If severity is Critical or High:
- Send Telegram alert immediately
- Tag owner in notification

## Output Format

```
🐛 BUG REGISTERED
═══════════════════

Projeto:     {project_name}
Título:      {bug_title}
Severidade:  {severity} 🔴/🟡/🟢
Responsável: {owner}
SLA:         {sla}
Prazo:       {deadline}
Status:      open

Ação:
  {action_plan}
```
