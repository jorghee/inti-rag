## Resumen de Cambios

Implementación completa de la tarea técnica **[TASK-03.1] Desarrollar script de extracción/descarga del Código Civil desde el SPIJ** (Closes #19, Historia Padre: HU-03 #3).

### Componentes Implementados

1. **Cliente Asíncrono Resiliente (`ingestion/spij_client.py`):**
   - Basado en `httpx.AsyncClient` con timeout explícito de 30 segundos y cabecera de *User-Agent* institucional (`IntiLegalAssistant/1.0 (UNSA Academic Research; contacto@unsa.edu.pe)`).
   - Pausa de cortesía mínima entre peticiones secuenciales ($\ge 1.5$ segundos) para evitar bloqueos del servidor.
   - Algoritmo de retroceso exponencial (*exponential backoff* con fluctuación aleatoria *jitter*) ante respuestas HTTP 429 (Too Many Requests) o 503 (Service Unavailable): $\text{delay} = 1.5 \times 2^{\text{attempt}} + \text{jitter}$, con un umbral máximo de 3 reintentos.

2. **Script de Extracción y Persistencia (`ingestion/fetch_civil_code.py`):**
   - Descarga el compendio normativo del Código Civil peruano (norma oficial SPIJ `H682695` / D.L. 295).
   - Calcula el *checksum* criptográfico SHA-256 del contenido descargado para trazabilidad y auditoría.
   - Persiste el documento base en `data/raw/codigo_civil_1984.html`.
   - Genera bitácora de ejecución en formato JSON (`data/raw/ingestion_civil_code.json`) con métricas: tiempo de ejecución, volumen en bytes extraídos, código HTTP de respuesta, marca temporal y *checksum*.
   - Admite ejecución por línea de comandos (CLI) con banderas `--output`, `--log`, `--no-fallback` y `--force-mirror`.

3. **Contingencia Offline Reproducible (`ingestion/fixtures/spij_civil_code_mirror.html`):**
   - Réplica oficial estructurada que preserva los 2,122 artículos del Código Civil peruano más el Título Preliminar, garantizando que los entornos de integración continua (CI) y las pruebas automatizadas se ejecuten de manera determinista ante caídas o cortafuegos del portal gubernamental.

4. **Gestión de Configuración (`.gitignore`):**
   - Se añadió `data/` al `.gitignore` para no contaminar el historial de git con descargas dinámicas de ejecución.

### Criterios de Aceptación Verificados

- [x] Cliente asíncrono con `httpx`, *User-Agent* institucional y timeout de 30s.
- [x] Control de tasa con pausas $\ge 1.5$ s y retroceso exponencial ante 429/503 (máx 3 reintentos).
- [x] Descarga íntegra del Código Civil persistida en `data/raw/`.
- [x] Bitácora JSON de telemetría con *checksum* SHA-256 y métricas de ejecución.
- [x] Contingencia *offline* determinista para CI y pruebas locales.
- [x] Cero emojis en código fuente, comentarios y documentación.

### Verificación y Pruebas

- 9 pruebas automatizadas añadidas (6 unitarias y 3 de integración), totalizando **26 pruebas del proyecto** (`pytest tests/ -v`) con 100% de éxito:
  - `tests/unit/test_spij_client.py`: Cabeceras por defecto, espaciado de peticiones, cálculo de backoff, reintentos ante 429 y 503, y agotamiento de reintentos.
  - `tests/integration/test_spij_fetch.py`: Extracción con contingencia *mirror*, descarga simulada en vivo y control de excepciones sin *fallback*.
- Linter y formato con cero errores (`ruff check ingestion/ tests/`, `ruff format --check ingestion/ tests/`).

Closes #19
