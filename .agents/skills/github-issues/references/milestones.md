# Milestones

Use milestones to group related issues into a deliverable unit of work.

Milestones can be read and managed through the GitHub REST API.

## List Milestones

```bash
gh api "repos/{owner}/{repo}/milestones?state=all&per_page=100" \
  --paginate \
  --jq '.[] | {number, title, state, open_issues, closed_issues, due_on}'
```

## Get Milestone

```bash
gh api repos/{owner}/{repo}/milestones/{milestone_number}
```

## Create Milestone

```bash
gh api repos/{owner}/{repo}/milestones \
  -X POST \
  -f title="Milestone title" \
  -f description="Milestone description"
```

Optional due date:

```bash
gh api repos/{owner}/{repo}/milestones \
  -X POST \
  -f title="Milestone title" \
  -f description="Milestone description" \
  -f due_on="2026-09-01T00:00:00Z"
```

## Update Milestone

```bash
gh api repos/{owner}/{repo}/milestones/{milestone_number} \
  -X PATCH \
  -f title="Updated title" \
  -f description="Updated description"
```

## Close Milestone

```bash
gh api repos/{owner}/{repo}/milestones/{milestone_number} \
  -X PATCH \
  -f state=closed
```

## Reopen Milestone

```bash
gh api repos/{owner}/{repo}/milestones/{milestone_number} \
  -X PATCH \
  -f state=open
```

## List Issues in Milestone

Use the milestone number, not the milestone title.

```bash
gh api "repos/{owner}/{repo}/issues?milestone={milestone_number}&state=all&per_page=100" \
  --paginate \
  --jq '.[] | select(.pull_request == null) | {number, title, state}'
```

The Issues REST endpoint can also return pull requests, so exclude entries
containing `pull_request` when the caller specifically requests milestone issues.

## Assign Issue to Milestone

```bash
gh api repos/{owner}/{repo}/issues/{issue_number} \
  -X PATCH \
  -F milestone={milestone_number}
```

## Remove Issue from Milestone

```bash
gh api repos/{owner}/{repo}/issues/{issue_number} \
  -X PATCH \
  -F milestone=null
```

## Delete Milestone

Delete a milestone only when explicitly requested.

```bash
gh api repos/{owner}/{repo}/milestones/{milestone_number} \
  -X DELETE
```

## Usage Rules

- Use milestone numbers for API operations.
- A milestone groups work into delivery stages; it does not define individual issue execution order.
- Use native issue dependencies for execution ordering.
- Do not infer dependencies merely because issues belong to the same milestone.
- Listing a milestone for an automated workflow should include all open and
  closed issues unless the caller explicitly requests otherwise.

## Conceptual Distinction: Milestones vs. Sprints (8-Week Horizon)

- **Milestones (PMBOK / Product Delivery Gates):** Represent contractual delivery stages across the 8-week course lifecycle:
  - `M1: Ingestion & Auth Foundation (Semanas 1-2)` (Due: 2026-10-17)
  - `M2: Vector Storage & Session History (Semanas 3-4)` (Due: 2026-10-31)
  - `M3: Core RAG Engine & Responsive UI (Semanas 5-6)` (Due: 2026-11-14)
  - `M4: Traceable Citations & Final Academic MVP (Semanas 7-8)` (Due: 2026-11-28)
- **Sprints (Scrum Iterations):** Represent 2-week execution timeboxes (`Sprint 1` to `Sprint 4` plus `Product Backlog`). Sprints are tracked and managed in **GitHub Projects** using the `Sprint` field, not as GitHub Milestones.
