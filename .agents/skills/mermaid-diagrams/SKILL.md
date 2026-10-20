---
name: mermaid-diagrams
description: >-
  Comprehensive guide for creating professional software diagrams using Mermaid syntax.
  Optimized specifically for native rendering in GitHub Markdown, Issues, Pull Requests,
  and documentation. Covers software architecture (C4 via subgraphs), sequence diagrams,
  flowcharts, entity-relationship diagrams (ERD), state diagrams, and class diagrams.
  Use when creating technical documentation, visualizing system architecture,
  documenting database schemas, or modeling query and ingestion workflows.
---

# Mermaid Diagramming for Software Engineering

Create professional, version-controlled software diagrams using Mermaid's text-based syntax. All diagrams render natively inside GitHub Markdown without external build steps, headless browsers, or binary image artifacts.

## Core Principles

1. **Text as Code**: Diagrams live directly inside Markdown files enclosed in ````mermaid```` code blocks. They are diffable, reviewable in Pull Requests, and easily maintained.
2. **Native GitHub Rendering**: Use only constructs supported natively by GitHub's Mermaid parser. Avoid non-standard extensions that require third-party renderers.
3. **Purposeful Visualization**: Every diagram must clarify architecture, workflows, or states. Never insert diagrams solely as decorative visual filler.
4. **Clean Technical Content**: Adhere strictly to the project policy prohibiting emojis, visual ornaments, or non-semantic symbols in diagram nodes and labels.
5. **Progressive Disclosure**: Keep diagrams focused and concise. Break complex architectures into multiple views rather than producing one unreadable mega-diagram.

## Diagram Selection Guide

| Need / Purpose | Recommended Type | Reference Guide |
|---|---|---|
| System architecture, component layers, cloud services | `flowchart TD` / `flowchart LR` with `subgraph` | [`references/architecture-diagrams.md`](references/architecture-diagrams.md) |
| API call flow, authentication, inter-service messaging | `sequenceDiagram` | [`references/sequence-diagrams.md`](references/sequence-diagrams.md) |
| Business processes, decision trees, workflow pipelines | `flowchart TD` | [`references/flowcharts.md`](references/flowcharts.md) |
| Database schema, PostgreSQL & pgvector tables | `erDiagram` | [`references/erd-diagrams.md`](references/erd-diagrams.md) |
| Lifecycle transitions, status progression, FSM | `stateDiagram-v2` | [`references/state-diagrams.md`](references/state-diagrams.md) |
| Domain model, class hierarchies, contracts | `classDiagram` | [`references/class-diagrams.md`](references/class-diagrams.md) |

## Quick Syntax Cheat Sheet (Inti Architecture Examples)

### 1. Architecture Flowchart (GitHub-Compatible)
```mermaid
flowchart TD
    subgraph ClientTier["Client Presentation Layer"]
        WebUI["Responsive Web UI\n(HTML5 / CSS / Vanilla JS)"]
    end

    subgraph APITier["Application API Layer (FastAPI)"]
        AuthRouter["Auth Router\n(JWT + @unsa.edu.pe filter)"]
        QueryRouter["Query Router\n(Streaming SSE / REST)"]
        RAGOrchestrator["RAG Engine\n(LlamaIndex Pipeline)"]
        QueryRouter --> RAGOrchestrator
    end

    subgraph DataTier["Persistence Layer (Supabase)"]
        PostgresDB[("PostgreSQL\n(User Profiles, Query History)")]
        VectorStore[("pgvector Extension\n(1536d Chunks Embeddings)")]
    end

    subgraph ExternalServices["External LLM & Scraping Services"]
        GroqAPI["Groq Cloud API\n(Llama 3.3 70B - Primary)"]
        OpenRouterAPI["OpenRouter Fallback\n(DeepSeek-V4.1 / GPT-6 Luna)"]
        SPIJScraper["SPIJ Scraper Pipeline\n(Civil Code Extraction)"]
    end

    WebUI -->|HTTPS / REST| AuthRouter
    WebUI -->|HTTPS / Streaming SSE| QueryRouter
    AuthRouter -->|SQL / RLS| PostgresDB
    RAGOrchestrator -->|Vector Cosine Search| VectorStore
    RAGOrchestrator -->|Inference Call| GroqAPI
    GroqAPI -.->|Failover on Rate Limit| OpenRouterAPI
    SPIJScraper -->|Insert Chunks & Vectors| VectorStore
```

### 2. Sequence Diagram (RAG Legal Query Flow)
```mermaid
sequenceDiagram
    autonumber
    participant Student as Law Student (Web UI)
    participant API as FastAPI Backend
    participant RAG as LlamaIndex Engine
    participant DB as Supabase pgvector
    participant LLM as Groq API (Llama 3.3)

    Student->>API: POST /api/v1/query (natural language question)
    API->>RAG: Process query with current session context
    RAG->>DB: Query nearest neighbors (cosine similarity <=> threshold 0.75)
    DB-->>RAG: Return top-k legal chunks (Articles, Book, Title, SPIJ URL)
    RAG->>LLM: Generate answer with system prompt & retrieved chunks
    LLM-->>RAG: Stream synthesized answer with bracketed citations
    RAG-->>API: Stream token chunks
    API-->>Student: Render streaming answer with interactive links [Código Civil, Art. 1969]
```

### 3. Entity-Relationship Diagram (ERD)
```mermaid
erDiagram
    PROFILES ||--o{ QUERY_SESSIONS : owns
    QUERY_SESSIONS ||--o{ QUERY_LOGS : contains
    LEGAL_CHUNKS ||--o{ CITATION_REFS : referenced_in
    QUERY_LOGS ||--o{ CITATION_REFS : includes

    PROFILES {
        uuid id PK
        string email UK
        string full_name
        timestamp created_at
    }

    QUERY_SESSIONS {
        uuid id PK
        uuid user_id FK
        string title
        timestamp created_at
    }

    LEGAL_CHUNKS {
        uuid id PK
        string document_name
        string book
        string title
        int article_number
        text content
        string official_url
    }

    QUERY_LOGS {
        uuid id PK
        uuid session_id FK
        text user_query
        text answer_text
        int feedback_score
        timestamp created_at
    }
```

### 4. State Diagram (Sprint Task Lifecycle)
```mermaid
stateDiagram-v2
    [*] --> ProductBacklog : New Requirement
    ProductBacklog --> Ready : Fulfill 100% DoR
    Ready --> SprintBacklog : Sprint Planning Selection
    SprintBacklog --> InProgress : Developer Pulls (WIP <= 4)
    InProgress --> InReview : Open PR (WIP <= 3)
    InReview --> InProgress : Request Changes
    InReview --> Done : Fulfill 100% DoD & Merge main
    Done --> [*]
```

## GitHub Native Rendering Guardrails

GitHub runs a strict client-side parser and DOM sanitizer. To ensure 100% rendering reliability on GitHub:

1. **Always Quote Node Labels with Special Characters**:
   - Correct: `node_a["User (Student)"]`
   - Incorrect: `node_a[User (Student)]` (parentheses break parsing).
2. **Never Use Reserved Keywords as IDs**:
   - In sequence diagrams, keywords `loop`, `alt`, `opt`, `end`, `par`, `rect` cannot be used as bare participant names.
   - Correct: `participant L as LoopComponent`
3. **No Semicolons in Message Text**:
   - Do not write: `App->>Server: Request; retry on fail` (semicolon truncates text or errors).
   - Write: `App->>Server: Request - retry on fail`
4. **Avoid `C4Context` / `C4Container` Syntax**:
   - GitHub does NOT bundle the Mermaid C4 extension.
   - Always represent architecture using `flowchart TD` or `flowchart LR` with `subgraph` blocks.
5. **No Interactive JavaScript**:
   - GitHub strips `click` events and custom JavaScript handlers.
6. **No Raw HTML or Complex Tags**:
   - Avoid `<b>`, `<br/>`, `<table>` inside nodes. Use plain text or standard Markdown line breaks.
7. **No Emojis or Pictographs**:
   - Never insert emoji characters in node names or connection labels, in strict adherence to `clean-technical-content`.

## Diagram Quality & Readability Standards

1. **Orientation**:
   - Use `flowchart TD` (Top-to-Bottom) for hierarchical architectures, decision trees, and layered stacks.
   - Use `flowchart LR` (Left-to-Right) for pipelines, data ingestion, and sequential process phases.
2. **Component Density**:
   - Limit nodes per diagram to 12-18 elements. If a system has more, split it into Context, Container, and Component views.
3. **Line Crossings**:
   - Arrange subgraphs and node order to minimize edge crossings. Symmetrical layouts are easier to scan.
4. **Naming Consistency**:
   - Use exact class, table, and module names from the codebase (e.g. `RAGOrchestrator`, `legal_chunks`).

## Documentation Agent Workflow

When generating documentation:

1. **Analyze Content**: Determine what concepts require visual representation.
2. **Select Diagram Type**: Use the Diagram Selection Guide table above.
3. **Draft Diagram**: Write valid, clean Mermaid code following the specific reference guide.
4. **Validate Syntax**: Check against GitHub guardrails (quoted labels, no reserved words, clean characters).
5. **Embed in Markdown**: Place within ````mermaid```` code fences directly in the target `docs/*.md` document.

## Reference Modules

Load the matching reference from `references/` for deep dive patterns:

- [`references/architecture-diagrams.md`](references/architecture-diagrams.md): System architecture, layered designs, and cloud infrastructure.
- [`references/sequence-diagrams.md`](references/sequence-diagrams.md): API flows, auth sequences, and multi-service coordination.
- [`references/flowcharts.md`](references/flowcharts.md): Process maps, logic branches, and workflow pipelines.
- [`references/erd-diagrams.md`](references/erd-diagrams.md): Database modeling and relational keys.
- [`references/state-diagrams.md`](references/state-diagrams.md): Entity state machines and lifecycle progressions.
- [`references/class-diagrams.md`](references/class-diagrams.md): Domain modeling and OOP structures.
- [`references/github-rendering-guardrails.md`](references/github-rendering-guardrails.md): Complete GitHub compatibility rules.
