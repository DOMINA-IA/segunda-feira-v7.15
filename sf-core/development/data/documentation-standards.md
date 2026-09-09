# Documentation Standards — AIOS Framework

CommonMark standards, technical writing best practices, and style guide compliance.

## User Specified CRITICAL Rules - Supersedes General Rules

- Documentar sempre em **Portugues Brasileiro** (exceto termos tecnicos)
- Usar acentos e cedilha corretamente (ã, é, ç, ô)

## General CRITICAL RULES

### Rule 1: CommonMark Strict Compliance

ALL documentation MUST follow CommonMark specification exactly. No exceptions.

### Rule 2: NO TIME ESTIMATES

NEVER document time estimates, durations, level of effort or completion times unless EXPLICITLY asked.

### CommonMark Essentials

**Headers:**
- Use ATX-style ONLY: `#` `##` `###` (NOT Setext underlines)
- Single space after `#`: `# Title` (NOT `#Title`)
- No trailing `#`: `# Title` (NOT `# Title #`)
- Hierarchical order: Don't skip levels (h1→h2→h3, not h1→h3)

**Code Blocks:**
- Use fenced blocks with language identifier
- NOT indented code blocks (ambiguous)

**Lists:**
- Consistent markers within list: all `-` or all `*` or all `+`
- Proper indentation for nested items
- Blank line before/after list for clarity

**Links:**
- Inline: `[text](url)`
- Reference: `[text][ref]` then `[ref]: url` at bottom
- NO bare URLs without `<>` brackets

**Emphasis:**
- Italic: `*text*` or `_text_`
- Bold: `**text**` or `__text__`
- Consistent style within document

## Mermaid Diagrams

**Critical Rules:**
1. Always specify diagram type first line
2. Use valid Mermaid v10+ syntax
3. Keep focused: 5-10 nodes ideal, max 15

**Diagram Type Selection:**
- **flowchart** - Process flows, decision trees, workflows
- **sequenceDiagram** - API interactions, message flows
- **classDiagram** - Object models, class relationships
- **erDiagram** - Database schemas, entity relationships
- **stateDiagram-v2** - State machines, lifecycle stages
- **gitGraph** - Branch strategies, version control flows

## Style Guide Principles

**Task-Oriented Focus:**
- Write for user GOALS, not feature lists
- Start with WHY, then HOW
- Every doc answers: "What can I accomplish?"

**Clarity Principles:**
- Active voice: "Click the button" NOT "The button should be clicked"
- Present tense: "The function returns" NOT "The function will return"
- Direct language: "Use X for Y" NOT "X can be used for Y"
- Second person: "You configure" NOT "Users configure"

**Structure:**
- One idea per sentence
- One topic per paragraph
- Headings describe content accurately
- Examples follow explanations

**Accessibility:**
- Descriptive link text: "See the API reference" NOT "Click here"
- Alt text for diagrams
- Semantic heading hierarchy
- Tables have headers

## Documentation Types: Quick Reference

| Type | Focus | Max Lines |
|------|-------|-----------|
| README | What, Why, How (quick start) | 500 |
| API Reference | Endpoints, schemas, examples | N/A |
| User Guide | Task-based sections | N/A |
| Architecture | System overview with diagrams | N/A |
| Developer Guide | Setup, workflow, testing | N/A |

## Quality Checklist

Before finalizing ANY documentation:

- [ ] CommonMark compliant
- [ ] NO time estimates
- [ ] Headers in proper hierarchy
- [ ] All code blocks have language tags
- [ ] Links work and have descriptive text
- [ ] Mermaid diagrams render correctly
- [ ] Active voice, present tense
- [ ] Task-oriented
- [ ] Examples are concrete and working
- [ ] Accessibility standards met
- [ ] Spelling/grammar checked
- [ ] Reads clearly at target skill level
