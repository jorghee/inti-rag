# Architecture Decision Records (ADRs): Inti Asistente Jurídico

> **System:** Inti - Asistente Jurídico Inteligente  
> **Repository:** `jorghee/inti-rag`  
> **Course:** Software Project Management — UNSA 2026-B  
> **Standard:** Michael Nygard ADR Format (Status, Context, Decision, Consequences, Alternatives)

---

## Index of Decisions

* [ADR-001: Unified Relational and Vector Storage with Supabase (PostgreSQL + pgvector)](#adr-001-unified-relational-and-vector-storage-with-supabase-postgresql--pgvector)
* [ADR-002: Hierarchical Chunking Pipeline for Peruvian Codified Norms](#adr-002-hierarchical-chunking-pipeline-for-peruvian-codified-norms)
* [ADR-003: Multi-Tiered LLM Inference Engine (Groq Llama 3.3 with OpenRouter Contingency)](#adr-003-multi-tiered-llm-inference-engine-groq-llama-33-with-openrouter-contingency)
* [ADR-004: UNSA Institutional Email Validation Strategy (@unsa.edu.pe)](#adr-004-unsa-institutional-email-validation-strategy-unsaedupe)
* [ADR-005: Mobile-Responsive Web Application Over Native Mobile Implementations](#adr-005-mobile-responsive-web-application-over-native-mobile-implementations)
* [ADR-006: Rejection of Automated CEJ Scraping and Pre-2004 OCR for the MVP](#adr-006-rejection-of-automated-cej-scraping-and-pre-2004-ocr-for-the-mvp)

---

### ADR-001: Unified Relational and Vector Storage with Supabase (PostgreSQL + pgvector)

* **Status:** Accepted (2026-09-30, Lab 03)
* **Context:** The system requires storing relational entities (user accounts, session history, ingestion logs, query telemetry) and vector embeddings (1536-dimensional vectors of legal article chunks) with fast hybrid querying capability. Operating on a strict zero-dollar infrastructure budget for the MVP requires leveraging managed free tiers.
* **Decision:** Adopt **Supabase** (PostgreSQL with `pgvector` extension) as the unified persistence engine.
* **Rationale:**
  1. *Unified Architecture:* Avoids maintaining dual databases (e.g., PostgreSQL for relational data + Pinecone/Qdrant for vectors).
  2. *Hybrid Search:* Enables executing combined SQL queries combining full-text search (`tsvector`), metadata filtering (e.g., `branch = 'civil'`), and cosine similarity distance (`<=>`).
  3. *Cost & Tiering:* Supabase provides 500 MB of storage, Row Level Security (RLS), and built-in JWT authentication within its Free Tier.
* **Consequences:**
  * *Positive:* Single backup, single connection pool, ACID transactions across metadata and vectors, lower complexity.
  * *Negative:* Vector index memory must be monitored to stay within Supabase free-tier RAM limits (mitigated by using `HNSW` index with optimized `m` and `ef_construction` parameters).
* **Alternatives Considered:**
  * *Pinecone / Weaviate:* Dedicated vector databases; rejected due to tier expiration and fragmentation of relational user data.
  * *Self-hosted Chroma / Milvus on VM:* Rejected due to lack of a free 24/7 dedicated compute server.

---

### ADR-002: Hierarchical Chunking Pipeline for Peruvian Codified Norms

* **Status:** Accepted (2026-10-07, Lab 04)
* **Context:** Peruvian codified legislation (such as the Código Civil with 2,122 articles) possesses a strict structural hierarchy: *Libro $\rightarrow$ Sección $\rightarrow$ Título $\rightarrow$ Capítulo $\rightarrow$ Artículo*. Naive fixed-size character/token chunking (e.g., 500 tokens with 50-token overlap) fractures legal clauses, separates article titles from their operative paragraphs, and loses normative context.
* **Decision:** Implement a **domain-aware hierarchical chunker** that parses documents by structural markers and preserves full article integrity.
* **Rationale:**
  1. *Context Preservation:* Legal articles are self-contained logical units. Breaking an article across chunk boundaries creates retrieval inaccuracies.
  2. *Rich Metadata Attachment:* Each chunk embeds explicit metadata attributes:
     - `document`: e.g., "Código Civil"
     - `book`: e.g., "Libro VII - Fuentes de las Obligaciones"
     - `title`: e.g., "Título IX - Responsabilidad Extracontractual"
     - `article`: e.g., "Artículo 1969"
     - `source_url`: Permanent SPIJ direct URL
  3. *Prompt Context Augmentation:* When retrieved, the chunk header injected into the LLM context contains the full hierarchy, enabling precise statutory interpretation.
* **Consequences:**
  * *Positive:* Zero fragmentation of legal articles; citations precisely reference the exact article and book.
  * *Negative:* Scraper parsing logic is more complex than generic markdown chunking and requires handling irregular sub-clauses (*numerales* and *literales*).

---

### ADR-003: Multi-Tiered LLM Inference Engine (Groq Llama 3.3 with OpenRouter Contingency)

* **Status:** Accepted (2026-10-13, Lab 04)
* **Context:** Real-time query performance requires Time-To-First-Token (TTFT) $< 2$ seconds and complete answers in $< 5$ seconds (RNF-01.2, RNF-01.3). The project budget has only S/. 88.18 in pocket money, while commercial LLMs (e.g., Claude 3.5 Sonnet, GPT-4o) would deplete this budget during automated testing and student pilot evaluations.
* **Decision:** Implement a two-tiered inference strategy:
  1. **Primary Inference:** **Groq Cloud API** hosting **Meta Llama 3.3 70B Versatile**. Free tier provides lightning-fast LPU inference ($>250$ tokens/sec) at zero financial cost.
  2. **Contingency / Complex Failover:** **OpenRouter API** accessing **DeepSeek-V4.1-Flash** ($0.15/M input) or **GPT-6 Luna** backed by a S/. 30.00 cash reserve.
* **Rationale:**
  * Groq eliminates runtime inference cost during standard university lab demonstrations.
  * Llama 3.3 70B exhibits sufficient Spanish legal comprehension when provided with grounded context via LlamaIndex.
  * Fallback to OpenRouter triggers automatically if Groq rate limits are encountered.
* **Consequences:**
  * *Positive:* Sub-second response streaming; budget strictly conserved.
  * *Negative:* Groq imposes daily request limits on free accounts (mitigated by semantic caching of frequent student queries in Supabase).

---

### ADR-004: UNSA Institutional Email Validation Strategy (@unsa.edu.pe)

* **Status:** Accepted (2026-10-07, Lab 04)
* **Context:** The system is tailored exclusively for the UNSA academic community (HU-05). Allowing arbitrary public email registrations (@gmail.com, @hotmail.com) would exhaust free tier API allocations and defeat the product's focus on university student adoption.
* **Decision:** Enforce institutional domain restriction at two independent layers:
  1. **FastAPI Application Layer:** Pydantic email validator rejecting any email whose domain suffix is not exactly `@unsa.edu.pe`.
  2. **Supabase Auth Hook Layer:** PostgreSQL trigger or auth constraint preventing registration if domain does not match.
* **Rationale:**
  * Double defense prevents circumvention via direct Supabase API calls.
  * Ensures 100% of onboarded users belong to the targeted stakeholder group.
* **Consequences:**
  * *Positive:* Closed student beta; clean user analytics; protection of free API quotas.
  * *Negative:* External reviewers or evaluators must use designated test accounts pre-provisioned with `@unsa.edu.pe` aliases.

---

### ADR-005: Mobile-Responsive Web Application Over Native Mobile Implementations

* **Status:** Accepted (2026-09-30, Lab 03 & Issue #13)
* **Context:** Field interviews revealed students often study and check laws using smartphones in study halls or courtrooms. However, developing native apps for iOS (Swift) and Android (Kotlin) requires:
  - Apple Developer Program fee ($99 USD/year).
  - Google Play Console registration fee ($25 USD).
  - Maintaining three codebases with a team of only 4 developers in a 12-week timebox.
* **Decision:** Build a single, fully responsive web application using modern HTML5, CSS Flexbox/Grid, and responsive viewports (HU-08), explicitly classifying native apps as **Won't Have**.
* **Rationale:**
  * Eliminates $124 USD in store fees, aligning with the S/. 88.18 real pocket budget.
  * 100% accessibility from any browser (iOS Safari, Android Chrome, Windows, Linux, macOS).
  * Instant deployment updates without app store review delays.
* **Consequences:**
  * *Positive:* Single frontend codebase; zero store subscription costs; immediate availability.
  * *Negative:* No offline native push notifications (acceptable for an online search assistant).

---

### ADR-006: Rejection of Automated CEJ Scraping and Pre-2004 OCR for the MVP

* **Status:** Accepted (2026-10-07, Lab 04 & Issue #13)
* **Context:** Initial requirements gathering suggested integrating judicial case files from the Consulta de Expedientes Judiciales (CEJ) and pre-2004 Supreme Court casaciones.
* **Decision:** Formally exclude both features from the MVP backlog (Won't Have):
  1. *CEJ Integration:* Excluded due to legal and technical barriers (mandatory DNI entry and dynamic anti-bot Captcha).
  2. *Pre-2004 OCR:* Excluded due to scanned image degradation requiring GPU-heavy Tesseract/EasyOCR processing pipelines that exceed the 12-week schedule.
* **Rationale:**
  * Attempting to bypass government Captchas risks IP blacklisting and potential legal liability under Peruvian cybersecurity norms.
  * Focusing on SPIJ digital texts and Tribunal Constitucional digital decisions provides high-value, clean text for the MVP.
* **Consequences:**
  * *Positive:* Eliminates the primary risk of catastrophic project delay.
  * *Negative:* Case coverage is limited to post-2004 digitized jurisprudence and current statutory codes.
