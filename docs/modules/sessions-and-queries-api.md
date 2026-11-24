# Sessions and Legal Queries API Contract

> **Subsystems:** Query History (`HU-06`) and Hybrid Legal Query (`HU-01` partial)
> **Base Prefix:** `/api/v1`
> **Authentication:** All endpoints require `Authorization: Bearer <jwt>` issued for an `@unsa.edu.pe` institutional account.

---

## 1. List User Sessions

* **Method & Path:** `GET /api/v1/sessions`
* **Auth:** Bearer JWT (`@unsa.edu.pe`)
* **Query Parameters:** `limit` (int, default `50`, range `1..100`)
* **Response `200 OK`:** Array of session summaries ordered by `last_active_at DESC`.
* **Errors:** `401` (missing/invalid/expired token), `403` (non-UNSA domain), `503` (Supabase unavailable).

```json
[
  {
    "id": "8e1c4a90-2b8d-4e92-a312-901a4f7b2c10",
    "user_id": "11111111-1111-4111-8111-111111111101",
    "session_title": "¿Qué establece el artículo 1529 sobre compraventa?",
    "started_at": "2026-11-23T19:40:00Z",
    "last_active_at": "2026-11-23T19:41:12Z",
    "query_count": 2
  }
]
```

---

## 2. Create Session

* **Method & Path:** `POST /api/v1/sessions`
* **Auth:** Bearer JWT (`@unsa.edu.pe`)
* **Request Body:**
```json
{
  "session_title": "Investigación sobre responsabilidad extracontractual"
}
```
* **Response `201 Created`:** `SessionSummaryResponse`
* **Errors:** `401`, `403`, `422` (invalid title length), `503`.

---

## 3. Get Session Detail

* **Method & Path:** `GET /api/v1/sessions/{session_id}`
* **Auth:** Bearer JWT (`@unsa.edu.pe`)
* **Response `200 OK`:** `SessionDetailResponse` containing chronological `logs` and their persisted `citations`.
* **Errors:** `401`, `403` (session owned by another user), `404` (session not found), `503`.

---

## 4. Delete Session

* **Method & Path:** `DELETE /api/v1/sessions/{session_id}`
* **Auth:** Bearer JWT (`@unsa.edu.pe`)
* **Response `204 No Content`**
* **Errors:** `401`, `403`, `404`, `503`.

---

## 5. Execute Grounded Legal Query

* **Method & Path:** `POST /api/v1/queries`
* **Auth:** Bearer JWT (`@unsa.edu.pe`)
* **Request Body:**
```json
{
  "query": "¿Qué establece el artículo 1969 del Código Civil sobre responsabilidad extracontractual?",
  "session_id": null,
  "top_k": 5
}
```
* **Response `200 OK`:**
```json
{
  "session_id": "8e1c4a90-2b8d-4e92-a312-901a4f7b2c10",
  "query_log_id": "2a4f0f10-81bc-4c72-941a-77a1c0a3d112",
  "query": "¿Qué establece el artículo 1969 del Código Civil sobre responsabilidad extracontractual?",
  "answer": "Conforme al régimen de responsabilidad extracontractual, aquel que por dolo o culpa causa un daño a otro está obligado a indemnizarlo [Código Civil, Art. 1969].",
  "grounded": true,
  "out_of_scope": false,
  "contains_synthetic_chunks": false,
  "response_latency_ms": 1420.5,
  "model_used": "deepseek/deepseek-chat",
  "citations": [
    {
      "chunk_id": "00271a54-bcb9-4b9e-a8ca-9ff836122123",
      "statute_code": "CODIGO_CIVIL_1984",
      "article_number": 1969,
      "article_number_raw": "1969",
      "statutory_hierarchy": "Libro VII: FUENTES DE LAS OBLIGACIONES > Sección Sexta",
      "raw_content": "Aquel que por dolo o culpa causa un daño a otro está obligado a indemnizarlo.",
      "official_spij_url": "https://spij.minjus.gob.pe/spij-ext-web/#/detallenorma/H682695",
      "semantic_similarity": 0.84,
      "combined_score": 0.032,
      "is_synthetic_template": false
    }
  ],
  "retrieved_chunks": []
}
```
* **Errors:** `401`, `403` (foreign `session_id`), `404` (unknown `session_id`), `422` (query < 3 chars or > 2000 chars), `503` (Supabase or OpenRouter unavailable).
