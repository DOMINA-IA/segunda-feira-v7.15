# Epic Retrospective

---
elicit: true
confirmation_required: false
execution_modes: [interactive]
---

**Goal:** Conduct a structured retrospective across all work completed in an epic, gathering insights from multiple agent perspectives.

**Your Role:** Retrospective facilitator guiding a multi-perspective review of what worked, what didn't, and what to improve.

## EXECUTION

### Step 1: Load Epic Context

- Read the epic definition and all associated stories
- Gather completion data (stories completed, timelines, quality gates)
- Load any decision logs from `.ai/decision-log-*.md`
- Load QA reports from `docs/qa/`

### Step 2: Data Collection

Collect metrics:
- **Velocity:** Stories completed, tasks done, complexity handled
- **Quality:** QA gate results (PASS/CONCERNS/FAIL counts)
- **Code Quality:** CodeRabbit findings (CRITICAL/HIGH/MEDIUM/LOW)
- **Rework:** Stories sent back to dev, iteration counts
- **Technical Debt:** Items added vs resolved

### Step 3: Multi-Perspective Review

Review from each agent's perspective:

**@dev Perspective:**
- What implementation patterns worked well?
- What caused the most rework?
- Which stories had the clearest requirements?
- What tools/libraries were discovered or adopted?

**@qa Perspective:**
- What quality issues were most common?
- Were acceptance criteria testable?
- What test patterns should be standardized?
- Were there any persistent false positives?

**@architect Perspective:**
- Did the architecture hold up during implementation?
- What technical decisions need revisiting?
- Are there emerging patterns worth documenting?
- Any scalability concerns surfaced?

**@sm/@po Perspective:**
- Were stories well-defined?
- Was the epic scope appropriate?
- Were dependencies managed effectively?
- Was the sprint velocity predictable?

### Step 4: Generate Retrospective Report

```markdown
# Epic Retrospective: [Epic Name]

**Date:** [date]
**Epic:** [epic ID and title]
**Duration:** [start to end]

## Metrics Summary

| Metric | Value |
|--------|-------|
| Stories Completed | [n/total] |
| QA Pass Rate | [%] |
| Rework Rate | [%] |
| Tech Debt Created | [n items] |
| Tech Debt Resolved | [n items] |

## What Went Well
1. [Success with evidence]
2. [Success with evidence]
3. [Success with evidence]

## What Didn't Go Well
1. [Problem with root cause]
2. [Problem with root cause]
3. [Problem with root cause]

## Key Learnings
1. [Learning with action]
2. [Learning with action]

## Action Items for Next Epic

| Action | Owner | Priority |
|--------|-------|----------|
| [action] | [@agent] | HIGH/MEDIUM/LOW |

## Patterns to Adopt
- [Pattern description and rationale]

## Patterns to Stop
- [Anti-pattern and replacement]
```

## OUTPUT

Save to: `docs/retrospectives/retro-{epic-id}-{date}.md`
