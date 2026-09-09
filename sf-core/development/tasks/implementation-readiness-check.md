# Implementation Readiness Check

---
elicit: true
confirmation_required: true
execution_modes: [interactive]
---

**Goal:** Validate that PRD, UX Design, Architecture, and Epics/Stories are all aligned and ready for implementation.

**Your Role:** Technical validator ensuring all planning artifacts are consistent, complete, and implementable before development begins.

## EXECUTION

### Step 1: Load Planning Artifacts

Load and review all available planning documents:
- PRD (Product Requirements Document)
- Architecture document
- UX Design / Frontend specs
- Epic definitions
- Story list with acceptance criteria

If any artifact is missing, note it as a gap.

### Step 2: Cross-Reference Validation

For each requirement in the PRD:
- [ ] Has corresponding architecture component
- [ ] Has UI/UX coverage (if user-facing)
- [ ] Has at least one story covering implementation
- [ ] Has testable acceptance criteria

### Step 3: Architecture Alignment

Validate:
- [ ] All PRD functional requirements mapped to architecture components
- [ ] Non-functional requirements addressed (performance, security, scalability)
- [ ] API contracts defined for all integration points
- [ ] Database schema covers all data requirements
- [ ] Authentication/authorization model complete
- [ ] Deployment strategy defined

### Step 4: UX-Architecture Alignment

Validate:
- [ ] All UX flows have corresponding API endpoints
- [ ] State management approach covers all user interactions
- [ ] Error states defined for each user flow
- [ ] Loading states and optimistic updates planned
- [ ] Responsive breakpoints aligned with component architecture
- [ ] Accessibility requirements mapped to implementation

### Step 5: Story Completeness

For each story:
- [ ] Clear acceptance criteria (Given/When/Then preferred)
- [ ] Dependencies identified and sequenced
- [ ] Complexity estimated
- [ ] No ambiguous requirements
- [ ] Test scenarios defined
- [ ] No overlapping scope between stories

### Step 6: Gap Analysis & Report

```markdown
# Implementation Readiness Report

## Overall Status: [READY | NOT READY | READY WITH CONCERNS]

## Artifact Coverage Matrix

| Requirement | PRD | Architecture | UX | Stories | Status |
|------------|-----|-------------|-----|---------|--------|
| [FR-001] | ✅ | ✅ | ✅ | ✅ | Ready |
| [FR-002] | ✅ | ✅ | ❌ | ✅ | Gap: UX |
| [NFR-001] | ✅ | ✅ | N/A | ❌ | Gap: Stories |

## Gaps Found
1. [Gap description with affected artifacts]
2. [Gap description with affected artifacts]

## Risks
1. [Risk with probability and impact]

## Recommended Actions Before Implementation
1. [Action item with owner]
2. [Action item with owner]

## Verdict
[PROCEED | RESOLVE GAPS FIRST | MAJOR REWORK NEEDED]
```

## HALT CONDITIONS

- If PRD is missing → Cannot validate, request PRD first
- If Architecture is missing → Cannot validate, request architecture first
- If more than 30% of requirements have gaps → MAJOR REWORK NEEDED
