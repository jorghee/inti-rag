# Installation Guide and Development Environment

> **System:** Inti - Legal AI Assistant  
> **Minimum Requirements:** Python 3.11+, Git, active Supabase project (PostgreSQL + pgvector), and Groq Cloud API key

---

## 1. System Prerequisites

Before initiating local installation, verify that the following tools are installed in your Linux, macOS, or WSL environment:
- **Python:** Version `3.11` or higher (`python3 --version`).
- **Package Manager:** `pip` (latest) or `poetry`.
- **Git:** Version `2.34+`.
- **Web Browser:** Modern browser supporting ES6 and Server-Sent Events (Chrome, Firefox, Safari, Edge).

---

## 2. Local Installation Steps

### Step 1: Clone the Repository
```bash
git clone https://github.com/jorghee/inti-rag.git
cd inti-rag
```

### Step 2: Create and Activate a Virtual Environment
```bash
python3 -m venv .venv
source .venv/bin/activate
```

### Step 3: Install Project Dependencies
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

*For local testing, linting, and quality analysis:*
```bash
pip install pytest pytest-asyncio pytest-cov ruff mypy
```

---

## 3. Database Initialization

1. Create a new project in the [Supabase](https://supabase.com) console.
2. Open the **SQL Editor** in the Supabase dashboard.
3. Execute the DDL table creation and vector retrieval script detailed in [`../architecture/data-model.md`](../architecture/data-model.md).
4. Verify that the `vector` extension is enabled:
   ```sql
   SELECT * FROM pg_extension WHERE extname = 'vector';
   ```

---

## 4. Launching the Development Server

Start the FastAPI application via the Uvicorn ASGI server:

```bash
uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
```

The application will be accessible at:
- **Base API Endpoint:** `http://localhost:8000`
- **Interactive Swagger Documentation:** `http://localhost:8000/docs`
- **OpenAPI Schema (JSON):** `http://localhost:8000/openapi.json`
- **Web Client UI:** `http://localhost:8000/static/index.html`

---

## 5. Running Automated Tests and Quality Linters

### Automated Unit Testing
```bash
pytest tests/unit/ -v --cov=backend --cov-report=term-missing
```

### Code Formatting and Static Analysis
```bash
# Static lint checks with Ruff
ruff check backend/ ingestion/

# Formatting check
ruff format --check backend/ ingestion/

# Static type checking with Mypy
mypy backend/
```
