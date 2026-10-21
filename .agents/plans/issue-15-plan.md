# Execution Plan: Issue #15 - [TASK-05.2] Endpoints de Registro y Login con JWT y validación institucional en FastAPI

## Metadata
- **Branch**: `feat/15-auth-endpoints`
- **Phase**: `HUMAN_GATE`
- **Assigned Agents**: `backend-implementer, code-reviewer`
- **Iteration Count**: `1`
- **Last Updated**: `2026-10-21T16:03:00-05:00`

## Acceptance Criteria Checklist
- [x] Criteria 1: Endpoint POST /api/v1/auth/register implements regex validation for domain @unsa.edu.pe, enforces password complexity, handles duplicate email conflict (409), and returns 201 Created.
- [x] Criteria 2: Endpoint POST /api/v1/auth/login validates credentials, enforces @unsa.edu.pe domain, issues signed JWT token, and returns user profile metadata.
- [x] Criteria 3: Dependency get_current_user and endpoint GET /api/v1/auth/me decode and verify JWT signature, enforce active session and return current user profile.
- [x] Criteria 4: All error responses match the contracts expected by the frontend client (status codes 400, 401, 409, 403).
- [x] Criteria 5: Code strictly follows clean technical formatting (zero emojis, English ASCII code identifiers and comments).

## Task Breakdown
- [x] Task 1: Create requirements.txt and pyproject.toml with FastAPI, uvicorn, pydantic, pyjwt, passlib, bcrypt, httpx, and pytest.
- [x] Task 2: Implement backend configuration and security utilities (`backend/core/config.py`, `backend/core/security.py`).
- [x] Task 3: Implement Pydantic data schemas (`backend/schemas/auth.py`).
- [x] Task 4: Implement in-memory/Supabase persistent auth service adapter (`backend/services/auth_service.py`).
- [x] Task 5: Implement dependencies and authentication router (`backend/api/dependencies.py`, `backend/api/v1/endpoints/auth.py`).
- [x] Task 6: Implement FastAPI entrypoint with CORS middleware (`backend/main.py`).
- [x] Task 7: Implement automated unit and integration tests (`tests/unit/test_auth_security.py`, `tests/integration/test_auth_endpoints.py`).

## Local Verification Gates
- [x] Lint Gate: `ruff check backend/ tests/` (0 errors)
- [x] Format Gate: `ruff format --check backend/ tests/` (0 files reformatted)
- [x] Test Gate: `pytest tests/ -v` (17 passed in 1.79s)
- [x] Content Gate: clean technical content check (zero emojis, formal Spanish orthography in docs/reviews)

## Review History
- Iteration 1: APPROVED (`.agents/plans/issue-15-review-1.md`)

## Pull Request Draft
- **Title**: `feat(backend): implement auth endpoints with jwt and unsa domain validation (#15)`
- **Closure Keyword**: `Closes #15`
- **Status**: `READY_FOR_HUMAN_GATE`
