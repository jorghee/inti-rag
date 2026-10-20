# Inter-Agent Handoff Contracts

This document formalizes the communication protocol, data payloads, and control flow transitions between Orchestrator, Implementer, and Reviewer agents in the Inti Legal RAG project.

---

## 1. Implementer to Reviewer Handoff Contract

When an implementer (`backend-implementer`, `frontend-implementer`, or `docs-implementer`) completes a task, it generates a structured Handoff Payload persisted in `.agents/plans/issue-<id>-handoff.md`.

### Payload Schema

```markdown
## Implementation Handoff: Issue #<ID>

### Task Context
- **Target Issue**: #<ID> - <Issue Title>
- **Implementer**: <backend-implementer | frontend-implementer | docs-implementer>
- **Iteration**: <1 | 2 | 3>

### Modified and Created Files
- `src/rag/retriever.py`: Implemented pgvector cosine distance query with >=0.75 threshold
- `tests/unit/test_retriever.py`: Unit test suite covering threshold boundaries

### Acceptance Criteria Verification
- [x] Scenario 1: <Verified via test_valid_legal_query>
- [x] Scenario 2: <Verified via test_out_of_scope_query_suppression>
- [x] Zero Hallucinations: <Verified against statutory fixtures>

### Verification Results
- **Lint / Format**: `ruff check src/` (0 errors), `ruff format --check src/` (0 files modified)
- **Automated Tests**: `pytest tests/unit/ -v` (12 passed, 0 failed, coverage >= 80%)
- **Exit Status**: SUCCESS (0)

### Architectural Notes & Guardrails
- Adheres to ADR-001 (Supabase pgvector) and ADR-003 (LlamaIndex + Groq).
- Zero inline emojis used in code, comments, or docstrings.
```

---

## 2. Reviewer to Implementer Handoff Contract

The reviewer (`code-reviewer` or `docs-reviewer`) inspects the implementation against repository standards and produces a Review Report persisted in `.agents/plans/issue-<id>-review-<iteration>.md`.

### Review Report Schema

```markdown
## Review Report: Issue #<ID>

### Verdict: <APPROVED | CHANGES_REQUESTED | BLOCKED>
### Iteration: <1/3 | 2/3 | 3/3>

### Summary
<High-level assessment of code quality, test coverage, and acceptance criteria fulfillment>

### Findings

#### Critical (Must Fix - Blocks Approval)
- [`src/rag/retriever.py:45`]: Query threshold was set to 0.65 instead of the required 0.75 in ADR-003. Update parameter and test fixture.
- [`docs/...`]: Found relative link pointing to nonexistent file. Fix markdown link syntax.

#### Suggestions (Non-blocking Improvements)
- [`src/rag/retriever.py:72`]: Add type hint annotation to helper method.

#### Verified Aspects
- [x] All automated tests pass with >= 80% coverage on new code.
- [x] Clean technical content verified: zero emojis in code, commits, and comments.
- [x] Formal Spanish orthography verified in user-facing strings and documentation.
```

---

## 3. Orchestration Control Flow & Escalation Rules

The `orchestrator` manages the loop between Implementer and Reviewer:

```
                  [Implementer completes code/doc]
                                 |
                                 v
                     [Persist Handoff Payload]
                                 |
                                 v
                     [Invoke Reviewer Agent]
                                 |
                                 v
                     [Persist Review Report]
                                 |
                                 +-----------------------+
                                 |                       |
                     [Verdict: APPROVED]     [Verdict: CHANGES_REQUESTED]
                                 |                       |
                                 v                       v
                      [Proceed to Human Gate]    [Check Iteration Count]
                                                         |
                                       +-----------------+-----------------+
                                       |                                   |
                                [Iteration < 3]                     [Iteration == 3]
                                       |                                   |
                                       v                                   v
                             [Route findings back]             [Trigger Human Escalation]
                             [to Implementer Agent]            [via ask_question]
```

### Escalation Conditions (Immediate Stop)
1. **Deadlock**: Iteration reaches `3/3` with unresolved `CHANGES_REQUESTED`.
2. **Verdict BLOCKED**: Reviewer identifies architectural violation (e.g. attempting to scrape CEJ or introduce native mobile frameworks forbidden by ADR-005 / ADR-006) or contradictory specifications.
