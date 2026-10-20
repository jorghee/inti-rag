# Guía de Instalación y Entorno de Desarrollo

> **Sistema:** Inti - Asistente Jurídico Inteligente  
> **Requisitos Mínimos:** Python 3.11+, Git, cuenta activa en Supabase (PostgreSQL + pgvector) y clave de API de Groq Cloud

---

## 1. Prerrequisitos del Sistema

Antes de iniciar la instalación local, asegúrese de contar con las siguientes herramientas en su entorno Linux / macOS / WSL:
- **Python:** Versión `3.11` o superior (`python3 --version`).
- **Gestor de paquetes:** `pip` actualizado o `poetry`.
- **Git:** Versión `2.34+`.
- **Navegador Web:** Chrome, Firefox o Edge compatible con ES6 y Server-Sent Events.

---

## 2. Pasos de Instalación Local

### Paso 1: Clonar el Repositorio
```bash
git clone https://github.com/jorghee/inti-rag.git
cd inti-rag
```

### Paso 2: Crear y Activar el Entorno Virtual
```bash
python3 -m venv .venv
source .venv/bin/activate
```

### Paso 3: Instalar Dependencias del Proyecto
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

*Si trabaja en modo desarrollo con herramientas de calidad de código:*
```bash
pip install pytest pytest-asyncio pytest-cov ruff mypy
```

---

## 3. Configuración Inicial de la Base de Datos

1. Cree un proyecto nuevo en la plataforma de [Supabase](https://supabase.com).
2. Abra el **SQL Editor** en el panel de control de Supabase.
3. Ejecute el script DDL de creación de tablas y funciones vectoriales detallado en [`../architecture/data-model.md`](../architecture/data-model.md).
4. Verifique que la extensión `vector` se encuentre habilitada:
   ```sql
   SELECT * FROM pg_extension WHERE extname = 'vector';
   ```

---

## 4. Ejecución del Servidor de Desarrollo

Inicie la aplicación FastAPI mediante el servidor ASGI Uvicorn:

```bash
uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
```

El servidor quedará disponible en:
- **API Base:** `http://localhost:8000`
- **Documentación Interactiva Swagger:** `http://localhost:8000/docs`
- **Especificación OpenAPI (JSON):** `http://localhost:8000/openapi.json`
- **Cliente Web:** `http://localhost:8000/static/index.html` (o servidor estático local)

---

## 5. Ejecución de Pruebas Automatizadas y Linters

### Ejecución de Pruebas Unitarias
```bash
pytest tests/unit/ -v --cov=backend --cov-report=term-missing
```

### Verificación de Formato y Calidad de Código
```bash
# Verificación estática con Ruff
ruff check backend/ ingestion/

# Verificación de formato
ruff format --check backend/ ingestion/

# Comprobación de tipos estáticos
mypy backend/
```
