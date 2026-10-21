# Verifiable Citations and Hallucination Control Module

> **Subsystem:** Legal Citation Generator and Grounding Engine  
> **User Story:** `HU-02` (Citation Traceability with Direct Links to Official Sources)  
> **Quality Target:** Reduction of hallucination rate from 40–50% (generalist LLMs) to $< 5\%$

---

## 1. Purpose and Scope

The academic and professional validity of a legal assistant depends entirely on the accuracy and grounding of its statutory citations. The citations module ensures that **no legal assertion is presented without verified statutory support**, linking every synthesized claim directly to its exact article in the official Sistema Peruano de Información Jurídica (SPIJ).

---

## 2. Canonical Citation Format

Every answer emitted by the RAG pipeline must structure legal references adhering to the interactive project standard:

### 2.1. Inline Markdown Syntax
```markdown
[Código Civil, Art. {number}](https://spij.minjus.gob.pe/#/detallenorma/H682695)
```

### 2.2. Concrete Generated Response Example
> "Under the Peruvian tort liability regime, whoever by intent or fault causes damage to another is obliged to indemnify it [[Código Civil, Art. 1969](https://spij.minjus.gob.pe/spij-ext-web/#/detallenorma/H682695)]. Furthermore, if the damage is caused through the exercise of a hazardous or risky activity, the author bears strict liability [[Código Civil, Art. 1970](https://spij.minjus.gob.pe/spij-ext-web/#/detallenorma/H682695)]."

---

## 3. Grounding Verifier Architecture

The system enforces grounding through a **two-phase verification architecture** reconciling real-time token streaming with strict academic auditability:

```mermaid
flowchart TD
    subgraph StreamingPhase["Phase 1: Real-Time Stream Validation"]
        TokenStream[/"Incoming LLM Token Stream"/] --> RollingBuffer["Rolling Character Buffer\n(Detects [Código Civil, Art. X])"]
        RollingBuffer --> InStreamCheck{"Is cited article\nin retrieved\ncontext chunks?"}
        InStreamCheck -->|Yes| StreamLink["Emit Active Link with SPIJ URL"]
        InStreamCheck -->|No| StreamWarning["Emit Plaintext Reference\n(Suppresses Unverified Link)"]
        StreamLink --> SSEFlush[/"Flush SSE Event to Client"/]
        StreamWarning --> SSEFlush
    end

    subgraph AuditPhase["Phase 2: Post-Generation Audit & Persistence"]
        CompletedResponse[/"Complete Synthesized Answer"/] --> Extraction["Extract All Legal Citations\nRegex: \[Código Civil, Art\. ([0-9]+)\]"]
        Extraction --> DBValidation{"Validate against\nlegal_chunks DB"}
        DBValidation -->|Grounded| PersistCitation[("Insert into citation_refs\n(query_log_id, chunk_id, similarity)")]
        DBValidation -->|Ungrounded / Orphan| LogAnomaly["Flag Telemetry Alert\n(Hallucination Incident Log)"]
    end

    SSEFlush -.-> CompletedResponse
```

### 3.1. Phase 1: Real-Time Stream Validation (Synchronous)
During generation, the backend streaming proxy buffers potential citation tokens. As soon as an article number pattern (`Art. 1969`) is parsed, it verifies membership against the pre-retrieved top-5 chunk metadata. If the article was legitimately retrieved, the complete hyperlink is streamed; if ungrounded, the hyperlink is withheld, preventing dead or misleading citations from reaching the client.

### 3.2. Phase 2: Post-Generation Audit and Persistence (Asynchronous)
Once the response stream closes:
1. The full text is parsed to extract all cited articles.
2. Verified citations are linked to their corresponding `legal_chunks.id` and stored in `citation_refs`.
3. If an ungrounded citation is detected, it is flagged in the telemetry logs to calculate the model's empirical hallucination rate and trigger prompt refinement.

---

## 4. Persistence and Traceability

Every generated citation reference is persisted in the relational `citation_refs` table, linked to the interaction log (`query_log_id`) and the retrieved chunk (`chunk_id`).

This provides:
1. **Academic Auditing:** Faculty and evaluators can verify the AI response against the official statutory text with a single click.
2. **Continuous Quality Benchmarking:** Enables automated computation of RAG triad metrics, specifically *faithfulness* and *citation recall*.
3. **Feedback Loop Telemetry:** If a student reports an erroneous citation via the user feedback interface (`HU-11`), developers can immediately pinpoint which chunk triggered the discrepancy.
