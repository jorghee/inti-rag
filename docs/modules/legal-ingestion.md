# Legal Ingestion and Hierarchical Chunking Module

> **Subsystem:** Statutory Ingestion and Vectorization Pipeline  
> **User Story:** `HU-03` (Automated Statutory Ingestion from SPIJ)  
> **Architecture Decision:** [`../architecture/decisions.md#adr-002`](../architecture/decisions.md#adr-002-hierarchical-chunking-pipeline-for-peruvian-codified-norms)

---

## 1. Purpose and Scope

The legal ingestion module extracts, sanitizes, structures, and vectorizes the Peruvian Civil Code (and subsequent binding jurisprudence) directly from the official portal of the Sistema Peruano de Información Jurídica (SPIJ).

Its design resolves two critical legal domain challenges:
1. **Loss of Statutory Context:** Generic character-count splitters fragment paragraphs arbitrarily, separating articles from their parent Chapter, Title, or Book.
2. **Server Access Controls:** The SPIJ portal lacks a public REST API and enforces strict rate limits against traffic bursts, requiring adaptive rate limiting with pauses.

---

## 2. Ingestion Pipeline Flow

```mermaid
flowchart TD
    Trigger(["Pipeline Trigger\n(CLI or Scheduled Task)"]) --> FetchRaw["Async HTTP Download (httpx)\nwith institutional User-Agent"]
    FetchRaw --> CheckStatus{"200 OK Response?"}

    CheckStatus -->|Error 429 / 503| Backoff["Exponential Backoff\n(1.5s * 2^attempt)"]
    Backoff --> FetchRaw
    CheckStatus -->|Success| CleanHTML["HTML Sanitization / UTF-8 Normalization\n(Strip scripts, styles, and boilerplate)"]

    CleanHTML --> ParseHierarchy["Syntactic Hierarchical Parser\nDetects: Book > Title > Chapter"]
    ParseHierarchy --> ExtractArticles["Atomic Article Extraction\nRegex: ^Artículo [0-9]+[.-]"]
    
    ExtractArticles --> AssembleChunk["Assemble Chunk Metadata\n(hierarchy, article_number, official_url)"]
    AssembleChunk --> Embeddings["Generate 1536d Embeddings\n(OpenAI text-embedding-3-small)"]

    Embeddings --> UpsertDB[("Idempotent Upsert into Supabase\nON CONFLICT (statute_code, article_number) DO UPDATE")]
    UpsertDB --> VerifyCount{"Total count matches\nofficial article count?"}

    VerifyCount -->|Discrepancy| AlertLog["Ingestion Log Alert"]
    VerifyCount -->|Consistent| Finish(["Ingestion Completed Successfully"])
```

---

## 3. Hierarchical Chunking Algorithm

The parser avoids fixed token chunking, slicing text strictly along canonical statutory boundaries:

```text
[CÓDIGO CIVIL DE 1984]
 └── LIBRO VII: Fuentes de las Obligaciones
      └── SECCIÓN SEGUNDA: Contratos Nominados
           └── TÍTULO I: Compraventa
                └── CAPÍTULO PRIMERO: Disposiciones Generales
                     └── ARTÍCULO 1529: Definición del contrato de compraventa
```

### Statutory Chunk Schema (JSON Payload)
```json
{
  "statute_code": "CODIGO_CIVIL_1984",
  "statutory_hierarchy": "Libro VII: Fuentes de las Obligaciones > Sección Segunda: Contratos Nominados > Título I: Compraventa > Capítulo Primero",
  "article_number": 1529,
  "raw_content": "Por la compraventa el vendedor se obliga a transferir la propiedad de un bien al comprador y este a pagar su precio en dinero.",
  "official_spij_url": "https://spij.minjus.gob.pe/spij-ext-web/#/detallenorma/H682695",
  "metadata": {
    "total_words": 26,
    "has_modifications": false,
    "last_amendment": null
  }
}
```

### Composite Text for Embedding and Retrieval
To ensure the embedding vector captures complete semantic context, the string vectorized by `text-embedding-3-small` prepends the statutory hierarchy to the article body:

```text
Norm: Código Civil de 1984
Hierarchy: Libro VII: Fuentes de las Obligaciones > Título I: Compraventa
Article 1529: Por la compraventa el vendedor se obliga a transferir la propiedad de un bien al comprador y este a pagar su precio en dinero.
```

---

## 4. Scraping Strategy and Rate-Limit Safeguards

- **Networking Library:** Asynchronous `httpx` with explicit 30-second timeouts.
- **Mandatory Request Delay:** Minimum 1.5-second sleep interval between sequential HTTP calls.
- **Exponential Backoff:** When receiving HTTP status codes 429 (Too Many Requests) or 503, the pipeline applies exponential backoff:
  $$\text{Delay} = 1.5 \times 2^{\text{attempt}} + \text{random jitter}$$
- **Retry Threshold:** Maximum 3 retry attempts before aborting execution and recording the incident in the audit log.
- **Idempotency Guarantee:** The unique constraint `(statute_code, article_number)` in the `legal_chunks` table guarantees that re-running the ingestion pipeline updates existing records without duplicating vectors or corrupting the HNSW index.
