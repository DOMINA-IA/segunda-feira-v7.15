# Quick Dev - Lean Implementation from Spec

---
elicit: false
confirmation_required: false
execution_modes: [yolo, interactive]
---

**Goal:** Implement a technical spec end-to-end using the 5-phase Quick Dev methodology.

**Your Role:** Elite developer executing with precision. Red-Green-Refactor cycle. No corners cut on quality, all ceremony cut from process.

## EXECUTION

### Phase 1: Clarify Intent

- Read the complete spec file
- Validate understanding of scope and goals
- Identify any ambiguities → resolve with user if interactive mode
- In yolo mode: make best judgment and log decisions

### Phase 2: Plan Implementation

- Map tasks to implementation order (respect dependencies)
- Identify which files need modification vs creation
- Plan test strategy for each task
- Estimate complexity per task (simple/moderate/complex)

### Phase 3: Implement (Red-Green-Refactor)

For each task in order:

1. **RED** - Write failing test(s) first
   - Define expected behavior via tests
   - Ensure tests actually fail (not false positives)

2. **GREEN** - Write minimal code to pass tests
   - Implement the simplest solution that works
   - All tests must pass (new AND existing)

3. **REFACTOR** - Improve without changing behavior
   - Clean up code while tests stay green
   - Follow existing patterns and conventions
   - Remove duplication, improve naming

4. **Verify** - Run full test suite
   - `npm test` or equivalent
   - `npm run lint` or equivalent
   - Fix any failures before proceeding

5. **Mark Complete** - Update spec checkbox `[x]`

### Phase 4: Self-Check (Adversarial Review)

After all tasks complete:

1. Review all changes as an adversary (see adversarial-review.md)
2. Check for:
   - Missing error handling
   - Security vulnerabilities
   - Performance issues
   - Edge cases not covered by tests
   - Inconsistent patterns
3. Fix any findings before proceeding

### Phase 5: Present Results

Provide summary:

```markdown
## Quick Dev Complete

**Spec:** [spec title]
**Tasks:** [X/Y completed]

### Changes Made
- [file] — [what changed]

### Tests Added
- [test file] — [what's tested]

### Evidence
- All tests pass: [yes/no]
- Lint passes: [yes/no]
- Self-review: [issues found and fixed]

### Notes
- [Any decisions made, gotchas found]
```

## BLOCKING CONDITIONS

- HALT if tests fail after 3 fix attempts
- HALT if spec is ambiguous and mode is interactive
- HALT if breaking changes detected in existing functionality
- HALT if security vulnerability discovered during self-review

## COMPLETION CRITERIA

- All spec tasks marked [x]
- All tests pass (new AND existing)
- Lint passes
- Self-adversarial review complete
- Summary presented to user
