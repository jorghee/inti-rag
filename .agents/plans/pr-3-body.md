## Resumen de Cambios

Implementación completa de la Historia de Usuario **[HU-03] Ingesta automatizada de normativa desde el SPIJ** (Closes #3).

### Componentes Implementados

1. **Coordinador Integral de Ingesta Normativa (`ingestion/pipeline.py`):**
   - Función principal `run_statutory_ingestion()` que ejecuta de manera secuencial y robusta las 6 etapas del pipeline:
     - Extracción desde el portal oficial del SPIJ con reintentos exponenciales y soporte de réplica local oficial.
     - Sanitización y normalización de etiquetas HTML, caracteres especiales y encabezados legales.
     - Segmentación jerárquica respetando los límites canónicos (Libro > Sección > Título > Capítulo > Artículo).
     - Auditoría estricta de consistencia matemática y cobertura completa (100% de los 2,122 artículos del Código Civil y los 10 artículos del Título Preliminar).
     - Generación de vectores densos de 1536 dimensiones e inserción idempotente en el repositorio de vectores pgvector.
     - Registro y persistencia de telemetría de ejecución en `data/raw/ingestion_pipeline_summary.json`.
   - Interfaz CLI ejecutable mediante `python -m ingestion.pipeline [--live] [--log PATH]`.

2. **Adaptador de Almacenamiento Vectorial (`ingestion/vector_store.py`):**
   - Repositorio `LegalChunksVectorStore` para inserción, persistencia y consulta de fragmentos jurídicos y sus incrustaciones densas (1536d).
   - Generador determinista de incrustaciones normalizadas unitarias para entornos sin conexión, pruebas unitarias e integración continua.
   - Operación `upsert_chunks()` con idempotencia estricta que actualiza artículos modificados sin generar duplicados.
   - Búsqueda por similitud de coseno (`query_similar()`) con umbral configurable de relevancia jurídica ($\ge 0.75$).

3. **Pruebas Automatizadas Unitarias e Integradas:**
   - `tests/unit/test_vector_store.py`: 5 pruebas unitarias verificando propiedades de incrustación, inserción, recuperación por identificador numérico/romano, idempotencia en actualizaciones y similitud de coseno.
   - `tests/integration/test_normative_ingestion_pipeline.py`: 2 pruebas de integración completas que validan la ejecución integral del pipeline sobre la réplica oficial, alcanzando el 100.0% de cobertura y confirmando la ausencia de duplicados tras ejecuciones repetidas.

### Criterios de Aceptación Verificados

- [x] Ingesta integral del Código Civil peruano de 1984 dividida jerárquicamente con metadatos asociados.
- [x] Generación y almacenamiento de incrustaciones de 1536 dimensiones en pgvector.
- [x] Actualización idempotente ante modificaciones de artículos sin duplicidad de registros.
- [x] Auditoría de cobertura al 100.0% (2,122 artículos numéricos y 10 artículos del Título Preliminar).
- [x] Emisión de informe estructurado JSON con métricas de duración, conteos y estado.
- [x] Cero emojis en código, comentarios, mensajes de confirmación y documentación.

### Verificación y Pruebas

- 7 pruebas automatizadas nuevas, alcanzando un total de **230 pruebas del proyecto** (`pytest tests/ -v`) con 100% de éxito.
- Linter y formato limpios con cero advertencias (`ruff check backend/ ingestion/ tests/`, `ruff format --check backend/ ingestion/ tests/`).

Closes #3
