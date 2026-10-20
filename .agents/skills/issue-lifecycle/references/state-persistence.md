# State Persistence and Session Recovery Guide

This reference defines how agent execution state is persisted on disk to guarantee resilience against CLI restarts, context compaction, process terminations, or multi-turn sessions in the Inti Legal RAG project.

---

## 1. Directory Structure

All persistent agent plans, handoffs, and review reports are stored under:
`.agents/plans/`

Files follow deterministic naming keyed by the Issue ID:
```
.agents/plans/
├── issue-<id>-plan.md           # Master execution plan and phase state
├── issue-<id>-handoff.md        # Latest implementer handoff payload
└── issue-<id>-review-<n>.md     # Review report for iteration <n>
```

---

## 2. Master Plan Schema (`issue-<id>-plan.md`)

```markdown
# Execution Plan: Issue #<ID> - <Title>

## Metadata
- **Branch**: `<type>/<id>-<short-description>`
- **Phase**: `<DISCOVERY | WORKTREE | PLANNING | EXECUTION | REVIEW | HUMAN_GATE | PR_PREP | COMPLETED>`
- **Assigned Agents**: `<orchestrator, backend-implementer, code-reviewer>`
- **Iteration Count**: `<0 | 1 | 2 | 3>`
- **Last Updated**: `<ISO-8601 Timestamp>`

## Acceptance Criteria Checklist
- [ ] Criteria 1: <Description from issue acceptance criteria>
- [ ] Criteria 2: <Description from issue acceptance criteria>

## Task Breakdown
- [ ] Task 1: <Description of change> (`src/path/to/target/file.py`)
- [ ] Task 2: <Description of test> (`tests/unit/test_target.py`)

## Local Verification Gates
- [ ] Lint Gate: `ruff check src/`
- [ ] Format Gate: `ruff format --check src/`
- [ ] Test Gate: `pytest tests/unit/ -v`
- [ ] Content Gate: clean technical content check (zero emojis, formal Spanish orthography)

## Review History
- Iteration 1: <APPROVED | CHANGES_REQUESTED | PENDING> (`.agents/plans/issue-<id>-review-1.md`)
- Iteration 2: <APPROVED | CHANGES_REQUESTED | PENDING> (`.agents/plans/issue-<id>-review-2.md`)

## Pull Request Draft
- **Title**: `feat(<component>): <English descriptive title>`
- **Closure Keyword**: `Closes #<ID>`
- **Status**: `<DRAFT | READY_FOR_REVIEW | SUBMITTED>`
```

---

## 3. Session Recovery Algorithm

When an agent is invoked to resume or resolve an Issue, it executes this recovery routine:

1. **Detect Current Branch**:
   ```bash
   git branch --show-current
   ```
2. **Extract Issue ID**:
   If the branch matches `^(feature|feat|fix|refactor|docs|test|chore)/([0-9]+)-([a-z0-9-]+)$`, extract the numeric ID.
3. **Locate Plan File**:
   Check if `.agents/plans/issue-<id>-plan.md` exists.
4. **Inspect Phase State**:
   - If `Phase == EXECUTION`: Inspect `git status` and `git diff` to determine edited files; continue with the next pending checklist item in the plan.
   - If `Phase == REVIEW`: Inspect the latest review report `.agents/plans/issue-<id>-review-<n>.md`. If `CHANGES_REQUESTED`, proceed with remediation. If `APPROVED`, transition to `HUMAN_GATE`.
   - If `Phase == HUMAN_GATE`: Present summary to user and request approval before creating a PR or pushing to remote.
5. **No Existing Plan**:
   If on `main` or no plan exists, initialize Phase 1 (Dynamic Discovery) using `gh issue view`.
