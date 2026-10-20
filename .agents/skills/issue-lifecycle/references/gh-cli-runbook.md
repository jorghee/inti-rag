# GitHub CLI (`gh`) Operational Runbook

This reference defines the exact commands, error-handling routines, and verification standards for interacting dynamically with GitHub through the `gh` CLI during the Inti Issue lifecycle.

---

## 1. Authentication and Scope Verification

Before executing remote GitHub operations, verify that `gh` is authenticated and has required scopes:

```bash
gh auth status
```

### Required Token Scopes
| Scope | Purpose | Minimum Required |
|---|---|---|
| `repo` | Read/write issues, pull requests, create branches, push code | Yes |
| `project` | Read and update GitHub Projects v2 boards | Optional |
| `workflow` | Inspect GitHub Actions CI workflows | Optional |

### Error Handling
If `gh auth status` indicates an unauthenticated state:
1. Halt autonomous remote execution.
2. Inform the developer:
   ```text
   GitHub CLI is not authenticated. Please run 'gh auth login' or run 'gh auth setup-git'.
   ```
3. If issue content is provided in prompt context, proceed locally with implementation and defer remote synchronization until authenticated.

---

## 2. Dynamic Issue Discovery

### Query Complete Issue Context
Fetch issue metadata, body, and labels without interactive terminal paging:
```bash
gh issue view <issue-id> --json number,title,body,state,labels,assignees,milestone
```

### Query Issue Discussion Comments
```bash
gh issue view <issue-id> --comments
```

### Inspect Dependencies
When an issue indicates dependencies (e.g., `Depends on #14`):
```bash
gh issue view <dependent-id> --json number,title,state
```
- If `state == "CLOSED"`: Dependency satisfied. Proceed.
- If `state == "OPEN"`: Dependency active. Inspect existing code/artifacts to determine if mock interfaces can be used, or escalate to developer.

---

## 3. Pull Request Creation and CI Gating

### Pre-PR Verification Checklist
Before creating a Pull Request, verify:
1. Current branch matches: `^(feature|feat|fix|refactor|docs|test|chore)/([0-9]+)-([a-z0-9-]+)$`
2. Remote branch is pushed: `git push -u origin <branch-name>`
3. PR body contains closure keyword: `Closes #<issue-id>` or `Cierra #<issue-id>`
4. PR title adheres to Conventional Commits and clean technical content (zero emojis):
   - Example: `feat(rag): implement pgvector cosine retrieval endpoint`
5. Local verification gates passed (`pytest`, `ruff check`, `ruff format --check`).

### Pull Request Creation Command
Prepare the PR body in `.agents/plans/issue-<issue-id>-pr-body.md` and execute:

```bash
gh pr create \
  --title "feat(component): descriptive summary" \
  --body-file .agents/plans/issue-<issue-id>-pr-body.md \
  --base main \
  --head <branch-name>
```

### Inspecting CI Check Status
```bash
gh pr checks <pr-number>
```

If checks fail:
```bash
gh run list --limit 3
gh run view --log-failed
```

### PR Integration via Squash and Merge
Once automated tests and linters pass and explicit human approval is received:

```bash
gh pr merge <pr-number> --squash --delete-branch
```

---

## 4. Security & Least-Privilege Guardrails

1. **Read Operations Autonomy**: The agent can autonomously run `gh issue view`, `gh pr view`, `gh label list`.
2. **Local Write Autonomy**: The agent can autonomously create branches, write code, run linters, and generate persistent plan files.
3. **Restricted Remote Write Operations**:
   - `git push` requires developer sign-off.
   - `gh pr create` requires developer review of title and body.
   - `gh pr merge` requires human approval gate confirmation.
4. **Credential Safety**: Never run commands that expose `GH_TOKEN` or print secrets to console logs.
