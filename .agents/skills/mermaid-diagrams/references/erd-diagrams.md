# Entity-Relationship Diagrams (ERD)

Entity-Relationship Diagrams model relational database schemas, table structures, keys, and foreign-key cardinalities. Mermaid provides native support via `erDiagram`.

## Cardinality Notation

Mermaid uses Crow's Foot notation for relationships:

| Notation | Left Side Meaning | Right Side Meaning | Typical Meaning |
|---|---|---|---|
| `||--||` | Exactly one | Exactly one | One-to-One mandatory |
| `||--o|` | Exactly one | Zero or one | One-to-One optional |
| `||--o{` | Exactly one | Zero or more | One-to-Many optional |
| `||--|{` | Exactly one | One or more | One-to-Many mandatory |
| `o|--o{` | Zero or one | Zero or more | Optional parent to many |

---

## Example: Inti Relational & Vector Schema

Models the core entities for student authentication, query logging, statutory chunk embeddings, and official legal citation references in Supabase PostgreSQL + pgvector.

```mermaid
erDiagram
    PROFILES ||--o{ QUERY_SESSIONS : "initiates"
    QUERY_SESSIONS ||--o{ QUERY_LOGS : "records"
    QUERY_LOGS ||--o{ CITATION_REFS : "cites"
    LEGAL_CHUNKS ||--o{ CITATION_REFS : "referenced_in"

    PROFILES {
        uuid id PK "Matches auth.users id"
        string email UK "@unsa.edu.pe institutional address"
        string full_name "Student or faculty name"
        string role "student | faculty | admin"
        timestamp created_at
        timestamp updated_at
    }

    QUERY_SESSIONS {
        uuid id PK
        uuid user_id FK
        string session_title "Auto-generated from first prompt"
        timestamp started_at
        timestamp last_active_at
    }

    QUERY_LOGS {
        uuid id PK
        uuid session_id FK
        string user_query "Natural language question"
        string assistant_response "Grounded synthesized answer"
        float response_latency_ms
        int prompt_tokens
        int completion_tokens
        timestamp created_at
    }

    LEGAL_CHUNKS {
        uuid id PK
        string statute_code "e.g. CODIGO_CIVIL_1984"
        string statutory_hierarchy "Libro > Título > Capítulo > Artículo"
        int article_number "Article identifier"
        string raw_content "Official statutory text from SPIJ"
        string official_spij_url "Direct hyperlink to official portal"
        vector embedding "1536-dimensional vector for cosine search"
        timestamp ingested_at
    }

    CITATION_REFS {
        uuid id PK
        uuid query_log_id FK
        uuid chunk_id FK
        float similarity_score "Cosine similarity value"
        int inline_citation_index "Bracket index in response"
    }
```

---

## Best Practices for ER Diagrams

1. **Entity Names**:
   - Use uppercase singular or plural nouns matching database tables (`PROFILES`, `LEGAL_CHUNKS`).
2. **Key Annotations**:
   - Always flag `PK` (Primary Key), `FK` (Foreign Key), and `UK` (Unique Key) after attribute names.
3. **Attribute Types**:
   - Use standard database data types (`uuid`, `string`, `int`, `float`, `vector`, `timestamp`).
4. **Relationship Labels**:
   - Enclose relationship descriptors in double quotes: `||--o{ QUERY_LOGS : "records"`.
5. **No Emojis**:
   - Never use emoji icons in table headers or relationship text.
