# Sprint Status Tracking

---
elicit: false
confirmation_required: false
execution_modes: [yolo, interactive]
---

**Goal:** Generate or update sprint status by scanning epic and story files to detect current progress.

**Your Role:** Sprint tracker that automatically detects story statuses and generates progress reports.

## EXECUTION

### Step 1: Scan Stories

- Read all story files from `docs/stories/`
- For each story, extract:
  - Story ID and title
  - Current status (Draft, Ready, InProgress, InReview, Done)
  - Epic association
  - Completion percentage (checkboxes completed / total)
  - Assigned agent (if any)

### Step 2: Aggregate by Epic

Group stories by epic and calculate:
- Total stories per epic
- Stories completed
- Stories in progress
- Stories blocked
- Epic completion percentage

### Step 3: Sprint Summary

Generate sprint status report:

```markdown
# Sprint Status Report

**Date:** [current date]
**Sprint:** [sprint number/name if available]

## Overall Progress

| Metric | Value |
|--------|-------|
| Total Stories | [count] |
| Done | [count] ([%]) |
| In Progress | [count] ([%]) |
| Ready | [count] ([%]) |
| Draft | [count] ([%]) |
| Blocked | [count] ([%]) |

## Epic Progress

| Epic | Total | Done | In Progress | Ready | % Complete |
|------|-------|------|-------------|-------|------------|
| [epic name] | [n] | [n] | [n] | [n] | [%] |

## Stories In Progress
| Story | Status | % Tasks | Assigned |
|-------|--------|---------|----------|
| [id] | [status] | [%] | [agent] |

## Blockers & Risks
- [Any blocked stories with reasons]

## Next Up (Ready for Dev)
1. [Story ready for development]
2. [Story ready for development]
```

### Step 4: Status Preservation

- NEVER downgrade a story status (Done → InProgress is invalid)
- Only update status forward in the lifecycle
- Flag any status inconsistencies found

## OUTPUT

Save to: `docs/sprint/sprint-status.md` (overwrite with latest)
