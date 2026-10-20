---
name: github-issues
description: >-
  Create, query, update, and manage GitHub issues, milestones, and project backlog items using the GitHub CLI (gh)
  and GitHub API. Enforces the Inti project taxonomy for User Stories (HU-XX), Technical Tasks (TASK-XX.Y),
  Story Points estimation, MoSCoW priorities, and Scrumban WIP status labels. Use when creating issues, updating
  task status, tracking dependencies, or managing backlog items.
---

# GitHub Issues & Backlog Management

Manage GitHub issues and product backlog items for the Inti Legal RAG project using the GitHub CLI (`gh`) and the GitHub API.

## Core Responsibilities

1. **Issue Creation**: Create standardized User Stories (`[HU-XX]`), Technical Tasks (`[TASK-XX.Y]`), Bug Reports, and Chores using templates.
2. **Taxonomy Enforcement**: Apply MoSCoW priority, component, Story Points, and Scrumban status labels.
3. **Traceability**: Maintain bidirectional links between User Stories, atomic tasks, and Pull Requests.
4. **WIP Gatekeeping**: Enforce Scrumban WIP limits (**WIP = 4** in `In Progress`, **WIP = 3** in `In Review`).

---

## 1. Available Tools & Interfaces

### GitHub CLI (`gh`) — Primary Interface

The `gh` CLI is the standard, battle-tested tool for issue operations in this repository:

| Operation | Command |
|---|---|
| View issue details | `gh issue view <number> --json number,title,body,state,labels,assignees,milestone` |
| List open issues | `gh issue list --state open --limit 50` |
| Filter by label | `gh issue list --label "priority: must-have" --state open` |
| Create issue | `gh issue create --title "..." --body-file ... --label "..."` |
| Edit issue / labels | `gh issue edit <number> --add-label "..." --remove-label "..."` |
| Add comment | `gh issue comment <number> --body "..."` |
| Close issue | `gh issue close <number> --comment "Resolved in PR #..."` |

### GitHub REST API via `gh api` — Advanced Operations

Use `gh api` when programmatic JSON manipulation or specific REST endpoints are required:

```bash
# Query issue via REST
gh api repos/{owner}/{repo}/issues/{number} --jq '{number, title, state, labels: [.labels[].name]}'

# Replace entire label set
gh api repos/{owner}/{repo}/issues/{number}/labels -X PUT -f 'labels[]=type: story' -f 'labels[]=status: done'
```

---

## 2. Issue Taxonomy & Naming Conventions

### Title Conventions
- **User Story**: `[HU-XX] <Short descriptive title in Spanish>` (e.g., `[HU-01] Motor RAG con recuperación semántica`)
- **Technical Task**: `[TASK-XX.Y] <Technical task title>` (e.g., `[TASK-01.1] Implementar retriever de pgvector en FastAPI`)
- **Bug Report**: `fix: <Clear defect description>`
- **Documentation / Chore**: `docs: <Documentation deliverable>` or `chore: <Maintenance task>`

### Label Strategy
Maintain a clean, non-redundant label taxonomy. Issues carry strictly two label categories:
- **Type**: `type: user-story`, `type: technical-task`, `type: epic`
- **Component**: `component: backend`, `component: frontend`, `component: ingestion`, `component: rag-engine`, `component: database`

Planning, sizing, and execution metrics (`MoSCoW`, `Story Points`, `Sprint`, `Status`, `Kanban Column`) are managed exclusively in **GitHub Projects** fields, preventing metadata duplication and label clutter. Consult [`references/labels.md`](references/labels.md) for details.

---

## 3. Operational Workflows

### Creating a User Story
1. Gather story context and acceptance criteria from the target user story definition, backlog planning, or project requirements.
2. Populate the User Story template from [`references/templates.md`](references/templates.md).
3. Execute `gh issue create` and link to project:

```bash
gh issue create \
  --title "[HU-01] Consulta en lenguaje natural con respuesta contextualizada" \
  --body-file .agents/plans/hu-01-body.md \
  --label "type: user-story" \
  --label "component: rag-engine"

# Add to GitHub Projects and configure planning fields
gh project item-add 3 --owner jorghee --url "<issue-url>"
gh project item-edit 3 --owner jorghee --url "<issue-url>" --field "MoSCoW" --value "Must Have"
gh project item-edit 3 --owner jorghee --url "<issue-url>" --field "Story Points" --number 8
gh project item-edit 3 --owner jorghee --url "<issue-url>" --field "Sprint" --value "Sprint 3 (Weeks 5-6)"
```

### Creating an Atomic Technical Task
1. Verify the parent User Story number (e.g. `#5`).
2. Populate the Technical Task template with technical scope and hourly estimation ($\le 8$ hours).
3. Execute `gh issue create` and link to project:

```bash
gh issue create \
  --title "[TASK-05.2] Endpoints de Registro y Login con JWT en FastAPI" \
  --body-file .agents/plans/task-05.2-body.md \
  --label "type: technical-task" \
  --label "component: backend"

# Add to GitHub Projects and configure sprint
gh project item-add 3 --owner jorghee --url "<issue-url>"
gh project item-edit 3 --owner jorghee --url "<issue-url>" --field "Sprint" --value "Sprint 1 (Weeks 1-2)"
gh project item-edit 3 --owner jorghee --url "<issue-url>" --field "Kanban Column" --value "Sprint Backlog"
```

### Transitioning Task Status (WIP Policy)
Update item status directly in GitHub Projects (or via PR automation):
```bash
gh project item-edit 3 --owner jorghee --url "<issue-url>" --field "Status" --value "In Progress"
gh project item-edit 3 --owner jorghee --url "<issue-url>" --field "Kanban Column" --value "In Progress"
```

---

## 4. Reference Documentation Index

For detailed guidelines on advanced features, consult the dedicated references:
- [`references/templates.md`](references/templates.md): Full markdown templates for User Stories, Technical Tasks, Bugs, and Chores.
- [`references/labels.md`](references/labels.md): Hex colors, descriptions, and rules for repository labels.
- [`references/milestones.md`](references/milestones.md): Managing Project Delivery Milestones (`M1`, `M2`, `M3`, `M4`).
- [`references/dependencies.md`](references/dependencies.md): Tracking blocking and blocked-by relationships between tasks.
- [`references/sub-issues.md`](references/sub-issues.md): Linking atomic tasks to parent stories.
- [`references/projects.md`](references/projects.md): Syncing issues with GitHub Projects boards.
- [`references/search.md`](references/search.md): Advanced query syntax for backlog auditing.
