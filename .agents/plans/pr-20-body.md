## Resumen de Cambios

Implementación de las tareas técnicas del pipeline de ingesta de normativa legal para el Sprint 1:
- **[TASK-03.2] Desarrollar módulo de limpieza y normalización de texto jurídico** (Closes #20)
- **[TASK-03.3] Implementar algoritmo de segmentación jerárquica (chunking por Artículo/Título)** (Closes #21)

Historia Padre: **[HU-03] Ingesta automatizada de normativa desde el SPIJ** (#3).

---

### Componentes Implementados

1. **Módulo de Limpieza y Normalización (`ingestion/cleaning.py`):**
   - Eliminación de etiquetas HTML (`script`, `style`, `noscript`, `iframe`, metadatos y comentarios).
   - Supresión de elementos de navegación, menús, barras de herramientas y pies de página institucionales del SPIJ.
   - Remoción de bloques de concordancias y referencias cruzadas.
   - Normalización Unicode (NFC, comillas tipográficas, guiones largos, espacios de no separación, soft hyphens).
   - Estandarización de marcadores de artículos al formato canónico `Artículo N.- `.
   - Normalización de encabezados estructurales (`LIBRO`, `SECCIÓN`, `TÍTULO`, `CAPÍTULO`) a mayúsculas.
   - Consolidación y colapso de espacios en blanco y líneas vacías redundantes.
   - Función principal `clean_legal_text(raw_html)` que orquesta todo el flujo de limpieza.

2. **Módulo de Segmentación Jerárquica (`ingestion/chunker.py`):**
   - Detección precisa de límites jerárquicos: Libro > Sección > Título > Capítulo > Artículo.
   - Extracción atómica de artículos preservando la ruta jerárquica completa (`statutory_hierarchy`).
   - Salvaguarda para mega-artículos (`MEGA_ARTICLE_WORD_THRESHOLD = 500` palabras): partición por incisos o numerales preservando la cláusula introductoria y la jerarquía.
   - Generación de texto compuesto (`composite_text`) para vectorización con embeddings (`Norm: ...\nHierarchy: ...\nArticle N: ...`).
   - Conversión de identificadores romanos a numéricos para títulos preliminares y números con sufijo literal (`2A`).
   - Generación de URLs canónicas del SPIJ para cada fragmento legal.

3. **Fixtures y Pruebas Automatizadas:**
   - `tests/fixtures/__init__.py`: Fragmentos HTML realistas simulando el portal del SPIJ (Código Civil, Libro VII de Fuentes de Obligaciones, texto con caracteres Unicode complejos, contenido solo boilerplate y marcadores inconsistentes).
   - `tests/unit/test_cleaning.py`: 48 pruebas unitarias cubriendo sanitización HTML, normalización Unicode, consolidación de espacios, normalización de marcadores, eliminación de boilerplate y pipeline completo.
   - `tests/unit/test_chunker.py`: 38 pruebas unitarias validando extracción de artículos, reseteo de jerarquías entre libros y títulos, manejo de artículos multilínea, subsegmentación de mega-artículos, formato de texto compuesto y prueba de integración extremo a extremo (`clean_legal_text` + `parse_statute`).

---

### Criterios de Aceptación Verificados

- [x] Sanitización completa de etiquetas HTML y chrome del SPIJ sin pérdida de texto normativo.
- [x] Preservación de la jerarquía normativa completa en metadatos estructurados.
- [x] Partición atómica por artículo y subpartición por incisos en artículos mayores a 500 palabras.
- [x] Formato canónico de texto compuesto para generación de embeddings.
- [x] 100% de pruebas aprobadas (86 pruebas en el módulo de ingesta, 130 pruebas totales en el repositorio).
- [x] Verificación de estilo y formato con ruff sin errores ni advertencias.
- [x] Ausencia total de emojis decorativos y cumplimiento de directrices de AGENTS.md.

Closes #20
Closes #21
