# Technical Research Workflow

---
elicit: true
confirmation_required: false
execution_modes: [interactive]
---

**Goal:** Conduct technical feasibility research including architecture options, implementation approaches, technology evaluation, and integration patterns.

**Your Role:** Technical researcher evaluating options and providing data-driven technology recommendations.

## EXECUTION

### Step 1: Initialize Research

- Clarify technical question or challenge
- Identify constraints (performance, scale, budget, team skills)
- Define evaluation criteria
- Establish scope: library, framework, platform, or architecture

### Step 2: Technical Overview

Research and document:
- Current technology landscape for the domain
- Available solutions and their maturity
- Community health (GitHub stars, npm downloads, contributors)
- Documentation quality and learning curve
- License compatibility

### Step 3: Integration Patterns

Analyze:
- API design patterns (REST, GraphQL, gRPC, WebSocket)
- Data exchange formats and protocols
- Authentication and authorization patterns
- Event-driven vs request-response patterns
- Webhook and callback patterns

### Step 4: Architectural Patterns

Evaluate:
- Monolith vs microservices vs serverless
- State management approaches
- Caching strategies
- Database selection criteria
- Deployment and scaling patterns

### Step 5: Implementation Research

For each viable option:
- Proof of concept feasibility
- Performance benchmarks (if available)
- Migration path from current stack
- Team ramp-up requirements
- Long-term maintenance implications
- Vendor lock-in risk assessment

### Step 6: Research Synthesis

Compile findings with decision matrix:

```markdown
# Technical Research Report: [Topic]

## Executive Summary
[Overview, key findings, recommendation]

## Problem Statement
[Technical challenge to solve]

## Constraints
- Performance: [requirements]
- Scale: [requirements]
- Budget: [constraints]
- Team: [current skills]

## Options Evaluated

### Option A: [Name]
- **Pros:** [list]
- **Cons:** [list]
- **Maturity:** [emerging/stable/legacy]
- **Community:** [size/health]
- **Learning Curve:** [low/medium/high]

### Option B: [Name]
[Same structure]

## Decision Matrix

| Criteria | Weight | Option A | Option B | Option C |
|----------|--------|----------|----------|----------|
| Performance | 25% | 4/5 | 3/5 | 5/5 |
| Developer Experience | 20% | 5/5 | 4/5 | 3/5 |
| Community/Support | 15% | 5/5 | 3/5 | 4/5 |
| Scalability | 20% | 4/5 | 5/5 | 4/5 |
| Cost | 10% | 5/5 | 3/5 | 2/5 |
| Migration Effort | 10% | 3/5 | 4/5 | 2/5 |
| **Weighted Total** | | **X.X** | **X.X** | **X.X** |

## Recommendation
[Recommended option with rationale]

## Implementation Path
1. [Step with rationale]
2. [Step with rationale]

## Risks & Mitigations
| Risk | Probability | Impact | Mitigation |
|------|------------|--------|------------|
| [risk] | [H/M/L] | [H/M/L] | [action] |

## Sources
[Links and references]
```

## OUTPUT

Save report to: `docs/research/technical-research-{date}.md`
