---
name: issue-lifecycle
description: >-
  Autonomous end-to-end Issue resolution and Pull Request lifecycle guide for Antigravity CLI agents in the Inti Legal RAG project.
  Covers dynamic context retrieval via GitHub CLI (gh), ephemeral git branch lifecycle, progressive context isolation,
  agent role orchestration, implementer-reviewer handoff contracts, persistent plan management, human-in-the-loop gating,
  and local CI verification (pytest, ruff). Use when resolving an assigned GitHub issue, preparing a Pull Request,
  or coordinating multi-agent implementation tasks.
---

# Issue Resolution and PR Lifecycle

This skill governs the end-to-end operational lifecycle for resolving an assigned GitHub Issue in the Inti Legal RAG repository. It guarantees traceability, context isolation, quality gating, and full compliance with project architecture and verification standards.

---

## 1. Lifecycle State Machine

The complete lifecycle follows an 8-phase sequence:

```
[Issue Assigned / Input]
         |
         v
(Phase 1: Dynamic Discovery)
  - Verify gh authentication (gh auth status)
  - Fetch Issue details via gh CLI (gh issue view <id>)
  - Audit existing context in docs/ and repository codebase
  - Check dependencies and sprint status
         |
         v
(Phase 2: Worktree Preparation)
  - Sync origin/main
  - Create compliant ephemeral branch: <type>/<id>-<short-description>
         |
         v
(Phase 3: Implementation Planning)
  - Perform gap analysis against issue acceptance criteria and architectural decisions (docs/architecture/decisions.md)
  - Identify modified components and architectural constraints
  - Generate persistent plan: .agents/plans/issue-<id>-plan.md
         |
         v
(Phase 4: Agent Role & Skill Orchestration)
  - Route task to specialized implementer role
  - Load domain-specific skills on demand
  - Execute code or documentation modifications
         |
         v
(Phase 5: Automated Verification & Review Gate)
  - Execute local verification: ruff check, ruff format --check, pytest
  - Invoke reviewer role (code-reviewer or docs-reviewer)
  - Loopback remediation (max 3 iterations)
         |
         v
(Phase 6: Human Approval Gate)
  - Present consolidated diff summary to developer
  - Request explicit developer sign-off before commit/push
         |
         v
(Phase 7: Commit & Pull Request Preparation)
  - Conventional Commit in English (feat, fix, docs, refactor, test, chore)
  - Push branch with upstream tracking
  - Create PR with closure keyword: "Closes #<id>"
         |
         v
(Phase 8: Post-Merge Cleanup)
  - Clean local branch after remote squash and merge
```

---

## 2. Core Operational Rules

1. **Human-in-the-Loop Gate**: Agents must never push code to remote or open a Pull Request without explicit developer approval.
2. **Ephemeral Branches**: Every task must run in an isolated branch created from `origin/main` matching:
   `^(feature|feat|fix|refactor|docs|test|chore)/([0-9]+)-([a-z0-9-]+)$`
3. **Traceability**: All code changes, commits, and Pull Requests must strictly reference their parent Issue (`Closes #<id>`).
4. **Clean Technical Content**: Emojis, visual ornaments, and non-semantic characters are strictly prohibited in code, commits, PR titles, PR bodies, and diagrams (see `clean-technical-content`).
5. **Context Isolation**: Agents must load technical context on demand from `docs/` and relevant source code to prevent context-window saturation.
6. **Architectural Guardrails**: Must respect decisions in [`docs/architecture/decisions.md`](../../../docs/architecture/decisions.md) (e.g. no native mobile frameworks, no CEJ scraping, pgvector cosine distance threshold $\ge 0.75$).
7. **Autonomous PR Review & Integration**: Pull Requests do not require external collaborator approval. Self-review, CI passing, and developer sign-off authorize squash-and-merge.

---

## 3. Dynamic Agent Selection Matrix

Tasks are routed based on Issue labels, components, and target files:

| Issue Characteristics | Primary Implementer | Primary Reviewer | On-Demand Skills |
|---|---|---|---|
| `backend`, `rag`, `ingestion`, FastAPI | `backend-implementer` | `code-reviewer` | `clean-technical-content` |
| `frontend`, `responsive`, Web UI | `frontend-implementer` | `code-reviewer` | `clean-technical-content` |
| `docs`, `análisis`, `documentación` | `docs-implementer` | `docs-reviewer` | `mermaid-diagrams`, `clean-technical-content` |
| Hybrid (Code + Documentation) | Sequential: `backend-implementer` -> `docs-implementer` | Sequential: `code-reviewer` -> `docs-reviewer` | `mermaid-diagrams`, `clean-technical-content` |

---

## 4. Reference Documentation Index

For technical procedures and execution schemas, consult the reference modules:
- [`references/gh-cli-runbook.md`](references/gh-cli-runbook.md): Detailed `gh` CLI commands for issue inspection, PR creation, error recovery, and CI monitoring.
- [`references/handoff-contracts.md`](references/handoff-contracts.md): Structured schemas for implementer-to-reviewer handoffs, review reports, and the 3-iteration escalation loop.
- [`references/state-persistence.md`](references/state-persistence.md): Specification for `.agents/plans/issue-<id>-plan.md` to guarantee state recovery across sessions.
