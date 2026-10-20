# Software Architecture Diagrams

This guide explains how to document system architecture, component layers, and cloud infrastructure using GitHub-compatible Mermaid syntax.

## Why Not Native C4 Directives?

GitHub Markdown does not bundle the `C4Context` or `C4Container` plugins. Attempting to use them produces broken code blocks. Instead, we use `flowchart TD` or `flowchart LR` with structured `subgraph` enclosures to achieve identical architectural clarity with 100% native GitHub compatibility.

## Architectural Levels

### Level 1: System Context Diagram

Visualizes the software system in its environment, including human users, external legal data sources, and cloud platforms.

```mermaid
flowchart TD
    subgraph Users["Academic Users"]
        Student["Law Student\n(Pre-graduate 1st-5th year)"]
        Professor["Law Professor\n(Academic Researcher)"]
    end

    subgraph SystemBoundary["Inti Legal Platform"]
        IntiWeb["Inti Web Application\n(Responsive UI + FastAPI API)"]
    end

    subgraph ExternalSources["Official Peruvian Legal Portales"]
        SPIJ["MINJUS SPIJ\n(National Legal Information System)"]
        TC["Tribunal Constitucional\n(Binding Jurisprudence Portal)"]
        PJ["Poder Judicial\n(Systematized Casaciones)"]
    end

    subgraph CloudServices["Managed Cloud Services"]
        Supabase["Supabase Cloud\n(PostgreSQL + pgvector + Auth)"]
        Groq["Groq Cloud\n(Llama 3.3 70B Fast LPU Inference)"]
    end

    Student -->|Natural language legal queries| IntiWeb
    Professor -->|Validates citations and casaciones| IntiWeb
    IntiWeb -->|Nightly batch ingestion| SPIJ
    IntiWeb -->|Ingests constitutional rulings| TC
    IntiWeb -->|Vector search & auth| Supabase
    IntiWeb -->|Real-time streaming inference| Groq
```

### Level 2: Container / Layered Architecture Diagram

Decomposes the system into high-level deployment containers and architectural layers.

```mermaid
flowchart TD
    subgraph Browser["Client Presentation Tier"]
        HTMLUI["Responsive Web UI\n(HTML5, Vanilla CSS, JS Client)"]
    end

    subgraph BackendAPI["Application Tier (FastAPI on Render)"]
        AuthModule["Auth & Security Router\n(JWT, @unsa.edu.pe validator)"]
        QueryModule["Query Orchestration Router\n(REST / SSE Streaming)"]
        LlamaIndexCore["LlamaIndex Engine\n(Hybrid Retriever + Prompt Synthesizer)"]
        QueryModule --> LlamaIndexCore
    end

    subgraph IngestionSystem["Ingestion Tier (Scheduled Workers)"]
        Scraper["SPIJ Scraper\n(httpx + Exponential Backoff)"]
        Chunker["Hierarchical Legal Chunker\n(Libro > Título > Art.)"]
        Scraper --> Chunker
    end

    subgraph Persistence["Persistence Tier (Supabase)"]
        AuthDB[("Supabase Auth\n(User Accounts & RLS)")]
        Postgres[("PostgreSQL\n(User Profiles, History, Feedback)")]
        VectorDB[("pgvector Extension\n(1536d Article Chunks)")]
    end

    subgraph Inference["Inference Tier"]
        EmbeddingsAPI["OpenAI text-embedding-3-small"]
        GroqLLM["Groq Meta Llama 3.3 70B (Primary)"]
        OpenRouterLLM["OpenRouter Fallback (DeepSeek/GPT-6)"]
    end

    HTMLUI -->|HTTPS / REST| AuthModule
    HTMLUI -->|HTTPS / SSE| QueryModule
    AuthModule --> AuthDB
    AuthModule --> Postgres
    LlamaIndexCore --> VectorDB
    LlamaIndexCore --> GroqLLM
    GroqLLM -.->|Failover on rate limit| OpenRouterLLM
    Chunker --> EmbeddingsAPI
    EmbeddingsAPI --> VectorDB
```
