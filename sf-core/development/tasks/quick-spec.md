# Quick Spec - Lean Technical Spec Creation

---
elicit: true
confirmation_required: false
execution_modes: [yolo, interactive]
---

**Goal:** Create an implementation-ready technical spec with minimum ceremony. Target 900-1600 tokens.

**Your Role:** You are an elite architect-developer creating a precise, actionable spec. No bureaucracy, no padding. Every word earns its place.

## EXECUTION

### Step 1: Understand Intent

- Ask the user what they want to build/fix/change
- Identify the single user-facing goal (reject specs with "and" splitting goals)
- Clarify scope boundaries: what's IN, what's OUT
- Identify affected files/components

### Step 2: Investigate Context

- Read relevant existing code to understand patterns and conventions
- Identify integration points and dependencies
- Check for existing tests and testing patterns
- Note any technical constraints or gotchas

### Step 3: Generate Spec

Create spec with this structure:

```markdown
# Tech Spec: [Title]

## Problem
[1-2 sentences describing the problem/need]

## Approach
- [Technical approach bullet points]
- [Key design decisions]
- [Integration points]

## Tasks
- [ ] Task 1: [description] — [testable criteria]
- [ ] Task 2: [description] — [testable criteria]
- [ ] Task 3: [description] — [testable criteria]

## Edge Cases
- [Edge case 1 and how to handle]
- [Edge case 2 and how to handle]

## Acceptance Criteria
- Given [context], When [action], Then [expected result]
- Given [context], When [action], Then [expected result]

## Files Affected
- [file path] — [what changes]
```

### Step 4: Review & Validate

- Verify spec is 900-1600 tokens (trim or expand as needed)
- Ensure each task has testable criteria
- Confirm no "and" conjunction splitting goals
- Present to user for approval

## QUALITY CHECKS

- Single user-facing goal (no split objectives)
- Each task has testable completion criteria
- Edge cases identified and handled
- Acceptance criteria in Given/When/Then format
- Files affected are listed
- No time estimates included
