# Configuración y Variables de Entorno

> **Sistema:** Inti - Asistente Jurídico Inteligente  
> **Archivo de Configuración:** `.env` en la raíz del proyecto

---

## 1. Plantilla de Variables de Entorno (`.env.example`)

Cree un archivo `.env` en el directorio raíz de la aplicación copiando la siguiente plantilla:

```bash
# ==============================================================================
# CONFIGURACIÓN GENERAL DE LA APLICACIÓN
# ==============================================================================
APP_ENV=development                    # development | staging | production
APP_HOST=0.0.0.0
APP_PORT=8000
DEBUG=True

# ==============================================================================
# POLÍTICA DE SEGURIDAD Y DOMINIO INSTITUCIONAL
# ==============================================================================
ALLOWED_EMAIL_DOMAIN=unsa.edu.pe
CORS_ORIGINS=["http://localhost:3000", "http://localhost:8000", "https://inti.unsa.edu.pe"]

# ==============================================================================
# CREDENCIALES DE PERSISTENCIA (SUPABASE)
# ==============================================================================
# URL del proyecto Supabase (disponible en Settings > API)
SUPABASE_URL=https://xyzcompany.supabase.co

# Clave anónima pública (para operaciones con contexto de usuario y RLS)
SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...

# Clave de servicio administrativa (exclusiva para tareas de ingesta del scraper)
SUPABASE_SERVICE_ROLE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...

# Secreto JWT para verificar firmas de tokens GoTrue en FastAPI
SUPABASE_JWT_SECRET=tu-secreto-jwt-super-seguro-de-supabase

# ==============================================================================
# MODELOS DE LENGUAJE Y GENERACIÓN DE EMBEDDINGS
# ==============================================================================
# Inferencia primaria ultrarrápida (Groq Cloud API - Llama 3.3 70B)
GROQ_API_KEY=gsk_...
GROQ_MODEL=llama-3.3-70b-versatile

# Inferencia de contingencia / Failover (OpenRouter)
OPENROUTER_API_KEY=sk-or-v1-...
OPENROUTER_MODEL=deepseek/deepseek-chat

# Vectorización de fragmentos normativos y consultas
OPENAI_API_KEY=sk-proj-...
EMBEDDING_MODEL=text-embedding-3-small
EMBEDDING_DIMENSION=1536

# ==============================================================================
# PARÁMETROS DEL MOTOR RAG
# ==============================================================================
# Umbral mínimo de similitud coseno para considerar la consulta dentro de alcance
RAG_SIMILARITY_THRESHOLD=0.75

# Cantidad máxima de fragmentos legales a inyectar en el prompt
RAG_TOP_K=5

# Temperatura de generación (baja para evitar creatividad y alucinaciones)
RAG_TEMPERATURE=0.1
```

---

## 2. Descripción de Parámetros Clave

| Variable | Tipo | Obligatorio | Descripción |
|---|---|---|---|
| `ALLOWED_EMAIL_DOMAIN` | String | Sí | Dominio institucional requerido para el registro e inicio de sesión (`unsa.edu.pe`). |
| `SUPABASE_URL` | String | Sí | Endpoint HTTPS del proyecto Supabase. |
| `SUPABASE_ANON_KEY` | String | Sí | Llave pública de cliente utilizada para peticiones sujetas a políticas RLS. |
| `SUPABASE_JWT_SECRET` | String | Sí | Clave criptográfica para decodificar y validar la validez de los tokens JWT entrantes. |
| `GROQ_API_KEY` | String | Sí | Llave de API del servicio de inferencia en Groq Cloud. |
| `RAG_SIMILARITY_THRESHOLD` | Float | Sí | Umbral de corte de similitud coseno ($\ge 0.75$). Consultas por debajo de este valor se consideran fuera de alcance. |
| `RAG_TEMPERATURE` | Float | Sí | Control de estocasticidad del LLM. Se establece en $0.1$ para maximizar determinismo y groundedness. |

---

## 3. Prácticas de Seguridad y Gestión de Secretos

1. **Nunca versione el archivo `.env`:** El archivo `.env` está expresamente excluido del repositorio mediante `.gitignore`. Únicamente se versiona `.env.example` con valores ficticios.
2. **Separación de privilegios:** El backend de atención de consultas de usuarios debe utilizar exclusivamente `SUPABASE_ANON_KEY` junto con el token JWT del usuario para que las políticas de Row Level Security (RLS) aíslen los datos de cada estudiante.
3. **Uso restringido de `SERVICE_ROLE_KEY`:** La clave de servicio administrativo solo debe ser accesible por el pipeline de ingesta (`ingestion/`) para operaciones masivas de inserción de vectores en la tabla `legal_chunks`.
