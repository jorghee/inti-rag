# Sequence Diagrams

Sequence diagrams illustrate interactions and message exchanges between participants over time. They are ideal for documenting API authentication lifecycles, streaming retrieval pipelines, and multi-agent coordination flows.

## Core Syntax Rules for GitHub

1. Use `autonumber` at the top of the diagram to make steps easy to reference in text discussions and PR reviews.
2. Define all participants explicitly with `participant ID as Label` at the beginning of the block to control column order.
3. Use solid arrows with filled heads `->>` for synchronous calls and open dashed arrows `-->>` for return messages.
4. Use `alt / else / end` blocks for branching logic (e.g. success vs error scenarios).
5. Never use reserved syntax words (`loop`, `alt`, `opt`, `end`, `par`) as participant identifiers.
6. Do not include semicolons `;` in message labels.

---

## Example 1: Law Student Authentication & UNSA Verification

Documents how the Web UI signs in via Supabase Auth and enforces the `@unsa.edu.pe` institutional domain filter.

```mermaid
sequenceDiagram
    autonumber
    participant Student as Law Student (Web UI)
    participant Auth as Supabase Auth (GoTrue)
    participant API as FastAPI Backend
    participant DB as PostgreSQL Database

    Student->>Auth: signInWithPassword(email, password)
    activate Auth
    Auth->>DB: Query user profile & credentials
    DB-->>Auth: Password hash & metadata
    Auth->>Auth: Verify hash & sign JWT
    Auth-->>Student: Return Session(accessToken, refreshToken)
    deactivate Auth

    Student->>API: GET /api/v1/profile (Bearer accessToken)
    activate API
    API->>API: Decode JWT & inspect email claim
    alt Domain == @unsa.edu.pe
        API->>DB: SELECT * FROM profiles WHERE id = uid
        DB-->>API: Profile data (role, faculty)
        API-->>Student: 200 OK (UserProfileResponse)
    else External Domain
        API-->>Student: 403 Forbidden (InstitutionalDomainRequired)
    end
    deactivate API
```

---

## Example 2: Streaming Legal RAG Query Flow

Shows how natural language queries stream back synthesized statutory answers with bracketed official citations.

```mermaid
sequenceDiagram
    autonumber
    participant Student as Law Student (Web UI)
    participant API as FastAPI Router
    participant RAG as LlamaIndex Engine
    participant VectorDB as Supabase pgvector
    participant LLM as Groq Cloud (Llama 3.3)

    Student->>API: POST /api/v1/query (natural language question)
    activate API
    API->>RAG: Dispatch query with session context
    activate RAG
    RAG->>VectorDB: Query cosine nearest neighbors (threshold >= 0.75)
    VectorDB-->>RAG: Top-k legal chunks (Articles, Book, Title, SPIJ URL)
    
    RAG->>LLM: Stream completion (System Prompt + Legal Chunks + Question)
    activate LLM
    LLM-->>RAG: Stream token chunks with citations
    deactivate LLM

    RAG-->>API: Stream formatted Server-Sent Events (SSE)
    deactivate RAG
    API-->>Student: Render streaming tokens & interactive links [Código Civil, Art. 1969]
    deactivate API
```

---

## Example 3: Antigravity Multi-Agent Orchestration Flow

Illustrates how the project's AI subagents collaborate from requirement parsing to verified implementation.

```mermaid
sequenceDiagram
    autonumber
    actor Human as Developer / Evaluator
    participant Orch as Orchestrator Agent
    participant Implementer as Backend Implementer
    participant Reviewer as Code Reviewer

    Human->>Orch: Assign GitHub Issue (#16 Query Endpoint)
    activate Orch
    Orch->>Orch: Analyze Issue scope & acceptance criteria
    Orch->>Orch: Create decomposition & implementation plan

    Orch->>Implementer: Delegate FastAPI endpoint implementation
    activate Implementer
    Implementer->>Implementer: Consult AGENTS.md & requirements matrix
    Implementer->>Implementer: Write endpoint, Pydantic schemas, and unit tests
    Implementer->>Implementer: Run pytest and ruff linter locally
    Implementer-->>Orch: Implementation complete (code diff)
    deactivate Implementer

    Orch->>Reviewer: Request code review for changes
    activate Reviewer
    Reviewer->>Reviewer: Execute test suite & check architectural compliance
    Reviewer->>Reviewer: Verify zero-hallucination and citation invariants
    alt All Checks Pass
        Reviewer-->>Orch: Verdict: APPROVED
    else Lint, Test, or Scope Failure
        Reviewer-->>Orch: Verdict: CHANGES_REQUESTED (findings)
        Orch->>Implementer: Request fixes (iteration 1 of 3)
    end
    deactivate Reviewer

    Orch-->>Human: Present final solution & PR summary for approval
    deactivate Orch
```

---

## Best Practices for Sequence Diagrams

- **Focus**: Keep sequence diagrams strictly to one interaction flow or scenario. Do not combine disparate use cases into one diagram.
- **Activations**: Use `activate` and `deactivate` to explicitly show processing lifespans.
- **Notes**: Add explanatory context when necessary using `Note over Participant: Explanation`.
- **Clean Naming**: Ensure participant labels reflect accurate system roles (`FastAPI Backend`, `Supabase pgvector`, `Orchestrator Agent`).
