## Task Definition (AIOS Task Format V1.0)

```yaml
task: projectReview()
responsável: Sentinel (Guardian)
responsavel_type: Agente
trigger: '*project-review'
elicit: false
mode: autonomous
```

## Purpose

Weekly project review — analyze all 11 projects, update health scores, check bug SLAs, identify risks, and generate action items for the week.

## Execution Steps

### Step 1: Load Project Data
```bash
# From Command Center API
curl -s -b CLIENTE_EXEMPLO_auth=authenticated_session_v1 http://localhost:3000/api/projects | python3 -m json.tool
```

### Step 2: For Each Project, Evaluate

**Health Score Recalculation:**
- Start at 10
- -3 for each critical bug open
- -2 for each high bug open
- -1 for each medium bug open
- -1 if service is down
- -1 if RAM anomaly detected
- -1 if token expiring < 7 days

**SLA Compliance:**
- Check each bug's deadline against today
- Mark OVERDUE if past deadline
- Mark AT_RISK if < 2 days to deadline
- Calculate SLA compliance percentage

### Step 3: Generate Weekly Report

```
📋 WEEKLY PROJECT REVIEW — {date}
═══════════════════════════════════

📊 PORTFOLIO SUMMARY
  Total: 11 | Active: {n} | In Dev: {n} | Prospecting: {n}
  Avg Health: {score}/10
  Bugs: {open} open | {overdue} overdue | {fixed_this_week} fixed this week

🏥 HEALTH SCORES (changes from last week)
  Content Studio    9/10  (=)
  CLIENTE_EXEMPLO         9/10  (↑ from 8)
  CLIENTE_EXEMPLO_4         9/10  (=)
  ...

🐛 BUG SLA STATUS
  ✅ On track: {n}
  ⚠️ At risk: {n}
  🚨 Overdue: {n}

  Overdue:
    - {bug title} | {project} | {days overdue} days | Owner: {owner}

📈 IMPROVEMENTS PIPELINE
  Critical: {n}
  High: {n}
  Medium: {n}

🎯 RECOMMENDED FOCUS THIS WEEK
  1. {highest impact action}
  2. {second action}
  3. {third action}
```

### Step 4: Update Health Scores in DB

For any project whose health score changed:
```sql
UPDATE projects SET health_score = {new_score}, updated_at = NOW()
WHERE slug = '{slug}';
```

### Step 5: Send Summary via Telegram (optional)

Condensed version for mobile review.
