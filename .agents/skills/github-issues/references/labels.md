# Project Labels Taxonomy

This reference defines the standardized label taxonomy used in the Inti Legal RAG repository. Always inspect existing repository labels before creating new ones to maintain taxonomy integrity.

---

## 1. MoSCoW Priority Labels

Defines functional requirement importance as established in academic deliverables and agile planning.

| Label | Color | Description | Usage |
|---|---|---|---|
| `priority: must-have` | `B60205` | Non-negotiable scope for MVP delivery (39 SP total) | Mandatory for Core MVP stories |
| `priority: should-have` | `D93F0B` | High priority; to be incorporated if capacity allows (19 SP) | Sprint 2 candidates |
| `priority: could-have` | `FBCA04` | Desirable features; included only if time permits (16 SP) | Post-MVP backlog |
| `priority: wont-have` | `6A737D` | Explicitly excluded from MVP scope (e.g. mobile app, CEJ scraping) | Out of scope / ADR rejected |

---

## 2. Issue Type Labels

Categorizes the nature of the issue across personal and organizational repositories.

| Label | Color | Description | Usage |
|---|---|---|---|
| `type: story` | `0E8A16` | Functional User Story (`HU-XX`) delivering student value | Backlog user stories |
| `type: task` | `1D76DB` | Atomic technical task (`TASK-XX.Y`) contributing to a story | Engineering implementation |
| `type: bug` | `D73A4A` | Defect, unexpected behavior, or regression | Defect tracking |
| `type: chore` | `C5DEF5` | Maintenance, configuration, or operational updates | Tooling / repo maintenance |
| `type: spike` | `5319E7` | Timeboxed research or technical proof-of-concept | Architecture exploration |

---

## 3. Component Labels

Identifies the architectural tier or domain module impacted by the change.

| Label | Color | Description |
|---|---|---|
| `component: auth` | `BFD4F2` | Supabase Auth, JWT verification, institutional domain filter (`@unsa.edu.pe`) |
| `component: ingestion` | `D4C5F9` | Legal scrapers, SPIJ ingestion, structural hierarchy chunking |
| `component: rag` | `1D76DB` | Vector retrieval, cosine similarity, prompt augmentation, Groq LLM inference |
| `component: citations` | `006B75` | Hyperlinked statutory citations, official portal linking, grounding audit |
| `component: frontend` | `0E8A16` | Responsive web interface, chat stream rendering, citation modals |
| `component: docs` | `0075CA` | Technical documentation, architecture decisions, requirements matrix |
| `component: infra` | `F9D0C4` | Database migrations, pgvector configuration, CI/CD pipelines |

---

## 4. Status Labels (Scrumban Workflow)

Tracks progress across development lifecycle states with Kanban WIP limits.

| Label | Color | Description | WIP Policy |
|---|---|---|---|
| `status: backlog` | `E4E669` | Prioritized item awaiting sprint commitment | Uncapped |
| `status: in-progress` | `FEF2C0` | Active implementation currently underway | **Strict Limit: Max 4** |
| `status: in-review` | `BFDADC` | Pull Request open, peer review or CI verification active | **Strict Limit: Max 3** |
| `status: done` | `0E8A16` | Fully implemented, merged into main, DoD verified | Closed issues |
| `status: blocked` | `D93F0B` | Impediment preventing progress; requires escalation | Zero tolerance; resolve ASAP |

---

## 5. Story Points Estimation Labels

Fibonacci point values assigned to User Stories during agile planning.

| Label | Color | Estimated Effort / Complexity |
|---|---|---|
| `points: 1` | `C2E0C6` | Trivial change or minor parameter update |
| `points: 2` | `A2D4AB` | Small task, clear implementation pattern |
| `points: 3` | `70C180` | Moderate task, standard service endpoint |
| `points: 5` | `37A755` | Significant story, multiple components |
| `points: 8` | `1B8738` | Complex story, deep integration (e.g., RAG pipeline) |
| `points: 13` | `0C5922` | Maximum story size; recommend decomposing into sub-tasks |

---

## 6. GitHub CLI Commands for Label Management

### List Current Repository Labels
```bash
gh label list --limit 100
```

### Create or Update a Label
```bash
gh label create "priority: must-have" --color "B60205" --description "Must-have MVP feature" --force
```

### Apply Labels to an Issue
```bash
gh issue edit <issue-number> \
  --add-label "type: story" \
  --add-label "priority: must-have" \
  --add-label "component: rag" \
  --add-label "points: 8"
```

### Remove a Label from an Issue
```bash
gh issue edit <issue-number> --remove-label "status: in-progress"
```
