# Sessions and Legal Queries API Contract

> **Subsystem:** Query History (`HU-06`)
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
