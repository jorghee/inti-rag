# State Diagrams

State diagrams model the lifecycle, status transitions, and finite state machines (FSM) of domain entities and user sessions. Always declare state diagrams using `stateDiagram-v2` for modern, clean visual rendering on GitHub.

## Core Syntax

- `[*] --> StateA`: Initial transition.
- `StateA --> StateB : Event / Condition`: Transition with triggering event.
- `StateB --> [*]`: Terminal transition.
- `state "Descriptive Label" as StateAlias`: Custom state descriptions.
- `<<choice>>`: Branching condition pseudostate.
- `note right of StateA`: Contextual explanations.

---

## Example 1: Statutory Ingestion Pipeline Lifecycle

Documents the progression of an official Peruvian legal document (SPIJ) from raw fetch to embedded vector persistence.

```mermaid
stateDiagram-v2
    [*] --> Scheduled : Cron or Manual Trigger
    Scheduled --> Fetching : Connect to SPIJ Portal
    Fetching --> FailedFetch : Network Timeout / Captcha
    Fetching --> Parsing : Raw HTML / PDF Acquired

    FailedFetch --> RetryBackoff : Exponential Backoff
    RetryBackoff --> Fetching : Retry (Max 3)
    RetryBackoff --> Blocked : Max Retries Exceeded

    state Parsing {
        [*] --> StructuralChunking : Identify Articles & Titles
        StructuralChunking --> HierarchyExtraction : Extract Libro / Título / Capítulo
        HierarchyExtraction --> CitationURLMapping : Map Article to Official Link
    }

    Parsing --> Embedding : Chunks Normalized
    Embedding --> Storing : Vectors Generated (1536d)

    state Storing {
        [*] --> UpsertPgVector : Store Vectors in Supabase
        UpsertPgVector --> VerifyIntegrity : Check Article Duplication
    }

    Storing --> Ingested : Verification Passes
    Ingested --> [*]
    Blocked --> [*]
```

---

## Example 2: Legal Query Session State Machine

Models the interactive lifecycle of a user query in the Inti RAG web assistant.

```mermaid
stateDiagram-v2
    [*] --> Idle : User Opens Web Interface

    Idle --> Authenticating : User Submits UNSA Credentials
    Authenticating --> Idle : Invalid Domain / Auth Failure
    Authenticating --> Ready : JWT Validated (@unsa.edu.pe)

    state Ready {
        [*] --> AwaitingPrompt : Display Welcome & Sample Queries
        AwaitingPrompt --> ProcessingQuery : User Submits Question
        ProcessingQuery --> RetrievingVectors : Vector Cosine Search
        RetrievingVectors --> SynthesizingAnswer : LLM Generation via Groq
        SynthesizingAnswer --> StreamingResponse : Stream Tokens & Citations
        StreamingResponse --> AwaitingPrompt : Response Complete
    }

    Ready --> SessionExpired : Token Expiration / Inactivity
    SessionExpired --> Idle : Redirect to Sign-In
    Ready --> [*] : User Signs Out
```

---

## Best Practices for State Diagrams

1. **GitHub Rendering**: Always use `stateDiagram-v2` instead of legacy `stateDiagram`.
2. **Substates**: Use composite states (`state EnclosingState { ... }`) to group related processing stages without cluttering the main flow.
3. **Choice Pseudostates**: Use `<<choice>>` nodes for clear decision branching.
4. **Clean Technical Content**: Avoid non-semantic emoji glyphs in state names.
