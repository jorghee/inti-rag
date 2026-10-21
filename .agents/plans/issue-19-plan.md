# Execution Plan: Issue #19 - [TASK-03.1] Desarrollar script de extracción/descarga del Código Civil desde el SPIJ

## Metadata
- **Branch**: `feat/19-spij-civil-code-scraper`
- **Phase**: `HUMAN_GATE`
- **Assigned Agents**: `backend-implementer, code-reviewer`
- **Iteration Count**: `1`
- **Last Updated**: `2026-10-21T16:23:00-05:00`

## Acceptance Criteria Checklist
- [x] Criteria 1: Asynchronous HTTP client implemented using httpx with institutional User-Agent and 30s timeout.
- [x] Criteria 2: Politeness delay (>= 1.5s between sequential requests) and exponential backoff on HTTP 429/503 (delay = 1.5 * 2^attempt + jitter, max 3 retries).
- [x] Criteria 3: Extraction script downloads Peruvian Civil Code (D.L. 295 / SPIJ H682695) and persists raw payload in data/raw/.
- [x] Criteria 4: Telemetry logging of execution time, bytes downloaded, HTTP status codes, timestamp, and payload SHA-256 checksum.
- [x] Criteria 5: Deterministic offline contingency fallback for offline testing and CI environments.
- [x] Criteria 6: Clean technical content (zero emojis, English ASCII code identifiers and comments).

## Task Breakdown
- [x] Task 1: Create ingestion package structure (`ingestion/__init__.py`, `ingestion/spij_client.py`).
- [x] Task 2: Implement extraction script and CLI interface (`ingestion/fetch_civil_code.py`).
- [x] Task 3: Implement bundled official offline mirror fixture (`ingestion/fixtures/spij_civil_code_mirror.html`).
- [x] Task 4: Implement automated unit tests for rate limiting, retry backoff, and network error handling (`tests/unit/test_spij_client.py`).
- [x] Task 5: Implement automated integration tests for civil code download workflow and telemetry log (`tests/integration/test_spij_fetch.py`).

## Local Verification Gates
- [x] Lint Gate: `ruff check ingestion/ tests/` (0 errors)
- [x] Format Gate: `ruff format --check ingestion/ tests/` (0 files reformatted)
- [x] Test Gate: `pytest tests/ -v` (26 passed in 3.51s)
- [x] Content Gate: clean technical content check (zero emojis, formal Spanish orthography in docs/reviews)

## Review History
- Iteration 1: APPROVED (`.agents/plans/issue-19-review-1.md`)

## Pull Request Draft
- **Title**: `feat(ingestion): implement spij scraper for civil code with backoff and rate limiting (#19)`
- **Closure Keyword**: `Closes #19`
- **Status**: `READY_FOR_HUMAN_GATE`
