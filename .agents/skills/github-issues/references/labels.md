# Project Labels Taxonomy (Simplified Architecture)

This reference defines the standardized, non-redundant label taxonomy used in the Inti Legal RAG repository.

---

## 1. Architectural Separation: Labels vs. Project Fields

To prevent visual clutter, badge saturation, and metadata desynchronization, the project enforces a strict boundary between issue labels and GitHub Projects planning fields:

| Dimension | Managed In | Values / Format | Rationale |
|---|---|---|---|
| **Artifact Nature** | **Issue Labels (`type:*`)** | `type: user-story`, `type: technical-task`, `type: epic` | Identifies whether the issue is an agile value story, an engineering task, or an architectural epic. |
| **Architectural Module** | **Issue Labels (`component:*`)** | `component: backend`, `component: frontend`, `component: ingestion`, `component: rag-engine`, `component: database` | Identifies the codebase subsystem impacted. Invariant across sprints. |
| **MoSCoW Priority** | **GitHub Projects Field (`MoSCoW`)** | `Must Have`, `Should Have`, `Could Have`, `Won't Have` | Product Owner release planning attribute. Managed in the project board to avoid label bloat. |
| **Effort Sizing** | **GitHub Projects Field (`Story Points`)** | Numeric Fibonacci (`3`, `5`, `8`, `13`) | Relative effort sizing strictly for User Stories. Supports column summing and board aggregation. |
| **Iteration Cadence** | **GitHub Projects Field (`Sprint`)** | `Sprint 1` through `Sprint 6`, `Product Backlog` | Timeboxed execution window. Updated via project board views. |
| **Execution Flow** | **GitHub Projects Fields (`Status` & `Kanban Column`)** | `Todo`, `In Progress`, `Review`, `Done` | Dynamic workflow states with WIP limits and automated PR transitions. |
| **Delivery Milestones** | **GitHub Milestones (`Milestone`)** | `M1` through `M4` | Contractual delivery gates mapped across 12 academic weeks. |

---

## 2. Active Repository Labels

### A. Issue Type Labels (`type:*`)
Categorizes the nature and granularity of the deliverable:

| Label | Color | Description | Usage |
|---|---|---|---|
| `type: user-story` | `#5319E7` | Functional User Story (`HU-XX`) delivering end-user legal value | Backlog user stories (sized in Story Points) |
| `type: technical-task` | `#1D76DB` | Atomic technical task (`TASK-XX.Y`) contributing to a story | Engineering implementation (sized in hours) |
| `type: epic` | `#3E4B9E` | High-level system module or cross-cutting scope container | Architectural and boundary specifications (e.g. #13) |

### B. Component Labels (`component:*`)
Identifies the technical subsystem impacted:

| Label | Color | Description | Architectural Scope |
|---|---|---|---|
| `component: backend` | `#1D76DB` | FastAPI API endpoints, JWT auth, business logic, pytest test suite | `backend/` |
| `component: frontend` | `#7057FF` | Responsive web UI, CSS layout, client-side session and stream reader | `frontend/`, web assets |
| `component: ingestion` | `#006B75` | Legal norm scraping, text normalization, regex hierarchical parser | `ingestion/` |
| `component: rag-engine` | `#B60205` | Vector retrieval, prompt synthesis, LlamaIndex, Groq Llama 3.3 | RAG orchestrator |
| `component: database` | `#008672` | PostgreSQL schema, Supabase DDL, pgvector HNSW indexes, RLS policies | Database migrations |

---

## 3. Label Usage Standards

1. **Max 2 labels per issue:** Every issue should carry exactly one `type:` label and one `component:` label (e.g., `type: user-story` + `component: rag-engine`).
2. **Zero duplicate planning labels:** Never create or re-introduce labels for priorities (`priority:*`), story points (`points:*`), or workflow states (`status:*`). These attributes are maintained exclusively in GitHub Projects fields.
3. **Repository Label List:** Standard repository maintenance labels (`bug`, `documentation`, `duplicate`, `enhancement`, `good first issue`, `help wanted`, `invalid`, `question`, `wontfix`) are reserved for ad-hoc repository maintenance and CI/triage.
