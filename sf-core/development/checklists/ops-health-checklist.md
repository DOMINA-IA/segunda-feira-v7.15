# Operations Health Checklist

> Used by @ops-monitor during health checks and weekly reviews

## Infrastructure (VPS ${VPS_HOST})

- [ ] All PM2 processes online (CLIENTE_EXEMPLO, CLIENTE_EXEMPLO-dashboard, pixel-bot, whatsapp-bot, CLIENTE_EXEMPLO_4)
- [ ] RAM usage normal (Node.js < 200MB, Python bots < 50MB idle)
- [ ] No process with > 50 restarts
- [ ] Disk usage < 80% on /opt
- [ ] Docker containers healthy (postgres, easypanel, traefik)
- [ ] SSL certificates valid (> 14 days until expiry)

## Databases

- [ ] ${USER} responsive (< 100ms query time)
- [ ] cliente_dashboard responsive
- [ ] Connection count normal (< 50 per DB)
- [ ] No long-running queries (> 30s)
- [ ] Database size reasonable (flag if > 1GB growth/week)

## Tokens & Credentials

- [ ] CLIENTE_EXEMPLO Meta token valid
- [ ] UTM Manager Meta token valid
- [ ] CLIENTE_EXEMPLO Dashboard Meta token valid (client responsibility — only verify)
- [ ] Claude API key valid
- [ ] Instagram publish capability confirmed
- [ ] Freepik API accessible

## Syncs (CLIENTE_EXEMPLO Dashboard)

- [ ] Eduzz sync completed in last 24h
- [ ] Asaas sync completed in last 24h
- [ ] No sync errors in SyncLog
- [ ] Eduzz record count consistent (no drops > 5%)
- [ ] Greenn status checked (currently offline — track)

## Bugs & SLAs

- [ ] No overdue bugs (past deadline)
- [ ] All critical bugs have owner assigned
- [ ] All high bugs have action plan defined
- [ ] Command Center data matches reality
- [ ] Health scores recalculated

## Cleanup

- [ ] /opt/video-pipeline/tmp/ < 50MB
- [ ] No orphan job directories
- [ ] PM2 logs rotated (< 100MB per log)
- [ ] Old deploy artifacts cleaned

## Scoring

| Check Category | Weight | Pass Criteria |
|---------------|--------|--------------|
| Infrastructure | 30% | All processes online, RAM normal |
| Databases | 20% | Responsive, connections normal |
| Tokens | 20% | All valid, no expiring < 7 days |
| Syncs | 15% | All syncs < 24h, no errors |
| Bugs & SLAs | 15% | No overdue, all assigned |

**Overall Score = weighted average (0-10)**
