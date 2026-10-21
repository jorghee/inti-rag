## Resumen de Cambios

Implementación completa de la tarea técnica **[TASK-03.4] Validación de cobertura y consistencia de artículos extraídos** (Closes #22, Historia Padre: HU-03 #3).

### Componentes Implementados

1. **Motor de Auditoría de Cobertura (`ingestion/coverage_validator.py`):**
   - Clase `CivilCodeCoverageValidator` que audita el 100% de los 2,122 artículos del Código Civil peruano de 1984 (D.L. 295).
   - Verificación de secuencia matemática ininterrumpida entre el Artículo 1 y el Artículo 2122 (detección de saltos numéricos y omisiones).
   - Auditoría de los 10 artículos del Título Preliminar (Artículos I al X en numeración romana).
   - Detección de artículos truncados o vacíos (validación de longitud mínima de caracteres y conteo de palabras).
   - Verificación de asignación jerárquica obligatoria (Libro > Sección > Título > Capítulo).
   - Generación de informe estructurado `CoverageAuditReport` con exportación en formato JSON y CLI.

2. **Normalización de Artículos Preliminares (`ingestion/cleaning.py`):**
   - Extensión del patrón regex `_ARTICLE_MARKER` para admitir números romanos (`[IVXLCDM]+`), permitiendo que el Título Preliminar sea estandarizado a `Artículo I.-` y procesado adecuadamente por el *chunker*.

3. **Pruebas Automatizadas Unitarias e Integradas:**
   - `tests/unit/test_coverage_validator.py`: 6 pruebas unitarias verificando detección de entradas vacías, identificación de artículos faltantes, detección de truncamiento, omisión de artículos preliminares, jerarquías vacías y aprobación de normas íntegras al 100%.
   - `tests/integration/test_civil_code_coverage.py`: 2 pruebas de integración validando que el compendio oficial alcanza exactamente el 100.0% de cobertura (2,122 artículos numéricos y 10 preliminares) y comprobando la presencia material de artículos jurídicos clave (Art. 1, 140, 219, 923, 949, 1351, 1529, 1969, 1970, 2001, 2122).

### Criterios de Aceptación Verificados

- [x] Cobertura auditada del 100% del Código Civil (Artículos 1 al 2122 sin vacíos numéricos).
- [x] Verificación completa del Título Preliminar (Artículos I al X).
- [x] Detección de artículos vacíos o truncados con umbral mínimo de contenido.
- [x] Verificación de atribución jerárquica a Libros y Títulos canónicos.
- [x] Emisión de informe estructurado JSON y soporte por línea de comandos.
- [x] Cero emojis en código fuente, comentarios y documentación.

### Verificación y Pruebas

- 8 pruebas automatizadas añadidas, elevando el total a **223 pruebas del proyecto** (`pytest tests/ -v`) con 100% de éxito.
- Linter y formato con cero errores (`ruff check ingestion/ tests/`, `ruff format --check ingestion/ tests/`).

Closes #22
