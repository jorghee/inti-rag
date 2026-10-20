# Flowcharts

Flowcharts model algorithms, business logic branching, asynchronous state progression, and development workflows. In Mermaid, declare flowcharts using `flowchart TD` (top-to-bottom) or `flowchart LR` (left-to-right).

## Core Node Shapes

| Syntax | Shape | Usage in Diagrams |
|---|---|---|
| `id["Square Box"]` | Rectangle | Generic process, action, or state |
| `id(["Rounded Box"])` | Stadium | Start, end, or entry points |
| `id[/"Input or Output"/]` | Parallelogram | User input or external output data |
| `id(("Connector"))` | Circle | Phase markers or join points |
| `id{"Decision"}` | Diamond | Conditional checks and branching gates |
| `id[("Database")]` | Cylinder | Database or vector store |

---

## Example 1: Git Team Development Workflow

Documents the mandatory lifecycle from GitHub Issue assignment to main branch merge for the Inti RAG project.

```mermaid
flowchart TD
    Start(["Issue Assigned (#N)"]) --> CreateBranch["Create Branch\n(type/N-short-description)"]
    CreateBranch --> Develop["Implement Solution in Python / Web\n(Adhere to AGENTS.md architecture)"]
    Develop --> LocalTest{"pytest & ruff check\npasses?"}

    LocalTest -->|No| FixErrors["Fix Test / Lint Errors"]
    FixErrors --> Develop
    LocalTest -->|Yes| CommitChanges["Commit Changes\n(Conventional Commit in English)"]

    CommitChanges --> OpenPR["Open Pull Request on GitHub\n(Spanish title, template filled, Closes #N)"]
    OpenPR --> AutomatedCI{"CI Verification Gate\n(lint, build, unit tests)"}

    AutomatedCI -->|Failure| ReviewFixes["Address CI Failure on Branch"]
    ReviewFixes --> CommitChanges
    AutomatedCI -->|Success| PeerReview{"Code Review\n(code-reviewer / peers)"}

    PeerReview -->|Changes Requested| Refactor["Apply Requested Changes"]
    Refactor --> CommitChanges
    PeerReview -->|Approved| MergeSquash["Merge via Squash and Merge\n(Human approval gate verified)"]

    MergeSquash --> DeleteBranch["Delete Feature Branch"]
    DeleteBranch --> CloseIssue(["Issue #N Automatically Closed"])
```

---

## Example 2: Legal RAG Query & Grounding Pipeline

Illustrates how Inti processes natural language questions against Peruvian statutes and ensures zero hallucinations.

```mermaid
flowchart TD
    UserQuery[/"Law Student Submits Query"/] --> Embedding["Generate Query Embedding\n(text-embedding-3-small)"]
    Embedding --> VectorSearch["Supabase pgvector Search\n(Cosine Distance <=> Operands)"]

    VectorSearch --> SimCheck{"Similarity Score\n>= 0.75 threshold?"}

    SimCheck -->|No| FallbackResponse["Return Out-of-Scope Notice\n(Zero hallucination fallback)"]
    SimCheck -->|Yes| RankChunks["Rank & Select Top-K Statutory Chunks\n(Civil Code, Constitution)"]

    RankChunks --> BuildPrompt["Assemble Augmented Prompt\n(System Guardrails + Legal Chunks)"]
    BuildPrompt --> GroqLLM["Inference Call via Groq\n(Llama 3.3 70B Versatile)"]

    GroqLLM --> VerifyGrounding{"Grounding Audit\n(All claims cite returned chunks?)"}

    VerifyGrounding -->|Violation Detected| RejectResponse["Regenerate / Suppress Unsupported Claim"]
    RejectResponse --> GroqLLM
    VerifyGrounding -->|Pass| StreamResult[/"Stream Synthesized Answer\nwith Hyperlinked Official Citations"/]
```

---

## Best Practices for Flowcharts

1. **Orientation**: Default to `flowchart TD` for top-to-bottom step processes. Use `flowchart LR` only when modeling data streaming pipelines or wide progression timelines.
2. **Quoting**: Enclose node text containing parenthesis, slashes, or special characters in double quotes: `Node["Text (with details)"]`.
3. **Escapes**: Use `\n` to introduce line breaks in dense text nodes to prevent horizontal stretching.
4. **Clean Technical Content**: Never insert decorative emojis or pictorial characters in nodes or connector labels.
