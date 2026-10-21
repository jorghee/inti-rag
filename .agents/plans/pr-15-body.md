## Resumen de Cambios

Implementación completa de la tarea técnica **[TASK-05.2] Endpoints de Registro y Login con JWT y validación institucional en FastAPI** (Closes #15, Historia Padre: HU-05 #5).

### Componentes Implementados

1. **Configuración y Seguridad (`backend/core/`):**
   - `backend/core/config.py`: Gestión de configuración con Pydantic Settings, carga de variables de entorno y análisis dinámico de `CORS_ORIGINS`.
   - `backend/core/security.py`: Validación con regex institucional (`^[a-zA-Z0-9._%+-]+@unsa\.edu\.pe$`), verificación de complejidad de contraseña, hashing seguro con `bcrypt` y emisión/decodificación de tokens JWT (`HS256`, audiencia `authenticated`).

2. **Esquemas Pydantic (`backend/schemas/auth.py`):**
   - Modelos para `UserRegisterRequest`, `UserLoginRequest`, `UserProfileResponse` y `LoginResponse`.

3. **Capa de Servicio (`backend/services/auth_service.py`):**
   - Servicio thread-safe de autenticación con usuarios presembrados (`jariasq@unsa.edu.pe`, `docente@unsa.edu.pe`) para pruebas y desarrollo local offline.
   - Prevención de duplicados con emisión de código HTTP 409 Conflict.
   - Control de credenciales con emisión de código HTTP 401 Unauthorized.

4. **Dependencias y Enrutadores FastAPI (`backend/api/`):**
   - `backend/api/dependencies.py`: Inyección `get_current_user` mediante `HTTPBearer` con validación estricta de firma JWT y dominio institucional (HTTP 403 Forbidden).
   - `backend/api/v1/endpoints/auth.py`: Rutas `POST /api/v1/auth/register` (201 Created), `POST /api/v1/auth/login` (200 OK) y `GET /api/v1/auth/me` (200 OK).
   - `backend/api/v1/api.py`: Enrutador v1 unificado con verificación de estado del servicio (`GET /api/v1/health`).

5. **Punto de Entrada (`backend/main.py`):**
   - Configuración de FastAPI con middleware CORS, inclusión del enrutador `/api/v1` y montaje de archivos estáticos del frontend (`frontend/`).

### Criterios de Aceptación Verificados

- [x] Acceso y registro restringido al dominio `@unsa.edu.pe`.
- [x] Validación de contraseñas complejas y hashing criptográfico `bcrypt`.
- [x] Generación de tokens JWT estándar de sesión con audiencia `authenticated`.
- [x] Retorno de perfiles de usuario y compatibilidad total con `frontend/js/api-client.js`.
- [x] Códigos HTTP estandarizados (200, 201, 400, 401, 403, 409).

### Verificación y Pruebas

- 17 pruebas automatizadas (`pytest tests/ -v`) aprobadas:
  - 7 pruebas unitarias de seguridad (`tests/unit/test_auth_security.py`).
  - 10 pruebas de integración de endpoints (`tests/integration/test_auth_endpoints.py`).
- Cero errores de estilo o formato (`ruff check backend/ tests/`, `ruff format --check backend/ tests/`).
- Cero emojis en código, comentarios y documentación.

Closes #15
