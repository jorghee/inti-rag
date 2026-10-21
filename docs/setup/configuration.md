# Configuration and Environment Variables

> **System:** Inti - Legal AI Assistant  
> **Configuration File:** `.env` in repository root

---

## 1. Environment Variable Template (`.env.example`)

Create a `.env` file in the root directory by copying the following configuration template:

```bash
# ==============================================================================
# GENERAL APPLICATION CONFIGURATION
# ==============================================================================
APP_ENV=development                    # development | staging | production
APP_HOST=0.0.0.0
APP_PORT=8000
DEBUG=True

# ==============================================================================
# SECURITY POLICY AND INSTITUTIONAL DOMAIN
# ==============================================================================
ALLOWED_EMAIL_DOMAIN=unsa.edu.pe
CORS_ORIGINS=["http://localhost:3000", "http://localhost:8000", "https://inti.unsa.edu.pe"]

# ==============================================================================
# PERSISTENCE CREDENTIALS (SUPABASE)
# ==============================================================================
# Supabase project URL (Settings > API)
SUPABASE_URL=https://xyzcompany.supabase.co

# Public anonymous key (used for client-scoped operations with RLS context)
SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...

# Administrative service role key (restricted strictly to scraper ingestion tasks)
SUPABASE_SERVICE_ROLE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...

# JWT secret key to verify GoTrue token signatures within FastAPI
SUPABASE_JWT_SECRET=your-secure-supabase-jwt-secret-here

# ==============================================================================
# LLM INFERENCE AND EMBEDDING GENERATION
# ==============================================================================
# Primary low-latency inference (Groq Cloud API - Llama 3.3 70B)
GROQ_API_KEY=gsk_...
GROQ_MODEL=llama-3.3-70b-versatile

# Contingency failover inference (OpenRouter)
OPENROUTER_API_KEY=sk-or-v1-...
OPENROUTER_MODEL=deepseek/deepseek-chat

# Vector embeddings for statutory chunks and search queries
OPENAI_API_KEY=sk-proj-...
EMBEDDING_MODEL=text-embedding-3-small
EMBEDDING_DIMENSION=1536

# ==============================================================================
# RAG ENGINE RETRIEVAL PARAMETERS
# ==============================================================================
# RAG ENGINE RETRIEVAL PARAMETERS (HYBRID SEARCH)
# ==============================================================================
# Minimum cosine similarity threshold for standalone vector filtering
RAG_SIMILARITY_THRESHOLD=0.70

# Reciprocal Rank Fusion (RRF) smoothing parameter (default: 60)
RAG_RRF_K=60

# Hybrid weights: vector dense search vs full-text lexical search
RAG_VECTOR_WEIGHT=1.0
RAG_FULLTEXT_WEIGHT=1.0

# Maximum number of statutory chunks injected into the prompt context
RAG_TOP_K=5

# Generation temperature (low to minimize creativity and prevent hallucinations)
RAG_TEMPERATURE=0.1
```

---

## 2. Key Parameter Descriptions

| Variable | Type | Required | Description |
|---|---|---|---|
| `ALLOWED_EMAIL_DOMAIN` | String | Yes | Institutional domain enforced for registration and login (`unsa.edu.pe`). |
| `SUPABASE_URL` | String | Yes | HTTPS endpoint of the Supabase project instance. |
| `SUPABASE_ANON_KEY` | String | Yes | Public client key used for API requests governed by Row Level Security (RLS). |
| `SUPABASE_JWT_SECRET` | String | Yes | Cryptographic secret used by FastAPI middleware to decode and verify JWT signatures. |
| `GROQ_API_KEY` | String | Yes | API authentication key for primary inference on Groq Cloud. |
| `RAG_SIMILARITY_THRESHOLD` | Float | Yes | Semantic similarity cutoff ($\ge 0.70$). Queries failing semantic and lexical checks trigger refusal. |
| `RAG_RRF_K` | Integer | No | Reciprocal Rank Fusion constant ($k=60$) balancing dense and sparse rankings. |
| `RAG_TOP_K` | Integer | Yes | Maximum statutory chunks injected into prompt context ($5$). |
| `RAG_TEMPERATURE` | Float | Yes | LLM sampling temperature. Set to $0.1$ to enforce deterministic, grounded output. |

---

## 3. Security Practices and Secrets Governance

1. **Never Commit Secrets:** The `.env` file is excluded from git tracking via `.gitignore`. Only `.env.example` containing dummy template values is maintained in version control.
2. **Privilege Separation:** End-user query endpoints must interact with Supabase using `SUPABASE_ANON_KEY` combined with the user's JWT bearer token so that Row Level Security (RLS) policies isolate each student's data.
3. **Restricted Service Role Key:** The `SUPABASE_SERVICE_ROLE_KEY` bypasses RLS and must be isolated to ingestion batch scripts (`ingestion/`) for bulk upsert operations into the `legal_chunks` table.
