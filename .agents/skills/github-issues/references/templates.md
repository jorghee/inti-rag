# GitHub Issue Templates

Standardized issue templates for the Inti Legal RAG project. Use these templates to ensure traceability between User Stories, Technical Tasks, bug reports, and project backlog tracking.

---

## 1. User Story Template (`HU-XX`)

Use when creating or updating functional requirements in the product backlog.

```markdown
## Narrative
Como **[rol de usuario: estudiante de Derecho / docente de Derecho]**,
quiero **[funcionalidad o capacidad solicitada]**,
para **[beneficio, impacto académico o reducción de tiempo]**.

## Scope & MoSCoW Priority
- **Identifier**: `HU-XX`
- **MoSCoW**: `Must Have` | `Should Have` | `Could Have` | `Won't Have`
- **Story Points**: `[1 | 2 | 3 | 5 | 8 | 13]` (Fibonacci)
- **Target Sprint**: `[Sprint 1 | Sprint 2 | Backlog]`
- **Module / Component**: `[auth | ingestion | rag | citations | frontend]`

## Acceptance Criteria (Given-When-Then)

### Scenario 1: [Descriptive Scenario Name]
- **Dado que** [contexto o precondición verificable],
- **cuando** [acción realizada por el usuario o evento del sistema],
- **entonces** [resultado esperado, respuesta de la API o cambio de estado].

### Scenario 2: [Alternative or Error Scenario Name]
- **Dado que** [contexto o precondición],
- **cuando** [acción],
- **entonces** [resultado].

## Technical Dependencies
- Dependent on: `[None | Issue #ID]`
- Blocks: `[None | Issue #ID]`

## Definition of Done (DoD)
- [ ] Backend API endpoints implemented and documented in OpenAPI schema.
- [ ] Automated unit and integration tests passing (`pytest`) with >= 80% coverage.
- [ ] Code formatted and linted without warnings (`ruff check`, `ruff format`).
- [ ] Traceability verified against `docs/context/requirements_traceability_matrix.md`.
```

---

## 2. Technical Task Template (`TASK-XX.Y`)

Use when breaking down an accepted User Story into atomic developer tasks ($\le 8$ hours).

```markdown
## Objective
[Clear, concise description of the technical implementation task]

## Context & Parent Story
- **Parent User Story**: Closes or contributes to #`[Parent Issue ID]` (`HU-XX`)
- **Estimated Effort**: `[X] horas` (Within single-developer capacity)
- **Component**: `[backend | frontend | database | scraper | infra]`

## Technical Scope
1. [Component or file to create/modify]
2. [Data schema or migration to execute]
3. [API router, Pydantic model, or service logic to implement]

## Implementation Checklist
- [ ] Step 1: [Concrete implementation step]
- [ ] Step 2: [Concrete implementation step]
- [ ] Step 3: [Concrete implementation step]

## Local Verification Commands
```bash
# Linting and formatting
ruff check src/
ruff format --check src/

# Automated test execution
pytest tests/unit/ -v
```

## Related Architectural Decisions
- References: `[ADR-001 | ADR-002 | ADR-003 | ADR-004 | ADR-005 | ADR-006]`
```

---

## 3. Bug Report Template

Use when logging unexpected defects or regression errors.

```markdown
## Defect Summary
[Concise description of the observed defect or regression]

## Severity & Priority
- **Severity**: `[Critical | Major | Minor]`
- **Component**: `[auth | ingestion | rag | citations | frontend]`

## Steps to Reproduce
1. [First operational step]
2. [Second operational step]
3. [Execute query or submit payload]

## Expected Behavior
[What the system should return according to requirements]

## Actual Behavior
[What actually occurred, including HTTP status code or traceback]

## Error Logs / Stacktrace
```text
[Paste error log or traceback here]
```

## Environment
- Runtime: Python 3.11+ / FastAPI
- Database: Supabase PostgreSQL + pgvector
- Browser / Client: Chrome / Firefox / Responsive Web
```

---

## 4. Minimal Chore / Documentation Template

Use for operational updates, documentation refactoring, or dependency updates.

```markdown
## Description
[Clear statement of what needs to be updated and why]

## Impacted Files
- `docs/context/...`
- `.agents/skills/...`

## Tasks
- [ ] Task 1
- [ ] Task 2

## Verification
- [ ] All cross-references and relative links verified.
- [ ] Clean technical content rules satisfied (zero emojis, formal Spanish orthography).
```
