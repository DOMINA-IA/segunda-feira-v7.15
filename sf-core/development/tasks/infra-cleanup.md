## Task Definition (AIOS Task Format V1.0)

```yaml
task: infraCleanup()
responsável: Sentinel (Guardian)
responsavel_type: Agente
trigger: '*cleanup'
elicit: false
mode: autonomous
```

## Purpose

Clean tmp files, old logs, zombie processes, and orphan data across the VPS.

## Execution Steps

### Step 1: Video Pipeline tmp
```bash
# Check size
du -sh /opt/video-pipeline/tmp/

# List directories older than 3 days (not active jobs)
find /opt/video-pipeline/tmp/ -maxdepth 1 -type d -mtime +3 -not -name tmp

# Get active jobs from jobs.json
cat /opt/video-pipeline/tmp/jobs.json

# Delete orphan dirs (not in active jobs)
# CONFIRM before deleting if > 100MB
```

### Step 2: PM2 Logs
```bash
# Check log sizes
ls -lh ~/.pm2/logs/

# Rotate if > 50MB
pm2 flush  # Clear all logs
# OR selective:
# > ~/.pm2/logs/CLIENTE_EXEMPLO-error.log
```

### Step 3: Next.js Build Cache
```bash
# Check .next sizes
du -sh /opt/CLIENTE_EXEMPLO/.next/cache/
du -sh /opt/CLIENTE_EXEMPLO-dashboard/.next/cache/

# Clean if > 500MB (rebuild will regenerate)
```

### Step 4: Docker Cleanup
```bash
docker system df  # Check usage
docker system prune -f  # Remove unused images/containers
```

### Step 5: Zombie Processes
```bash
# Check for orphan node/python processes
ps aux | grep -E "node|python" | grep -v grep | grep -v pm2

# Check for high-memory processes
ps aux --sort=-%mem | head -10
```

## Safety Rules

- NEVER delete active job directories
- NEVER delete .env files
- NEVER delete node_modules (takes too long to reinstall)
- NEVER flush logs without checking for recent errors first
- Always show what will be deleted BEFORE deleting
- Keep at least 1 day of logs for debugging

## Output

```
🧹 CLEANUP REPORT — {date}
═══════════════════════════

Cleaned:
  /opt/video-pipeline/tmp/: -{size}MB
  PM2 logs: -{size}MB
  Docker: -{size}MB

Total freed: {total}MB
```
