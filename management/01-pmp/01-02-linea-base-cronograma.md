# 01-02 Línea Base del Cronograma (Schedule Baseline)

> **Proyecto:** Inti - Asistente Jurídico Inteligente  
> **Área:** Gestión del Cronograma (PMBOK 7ma Edición)  
> **Documento Wiki:** `01-02-linea-base-cronograma`  
> **Estado:** Aprobado por el Scrum Master y Línea Base Congelada

---

## 1. Parámetros del Cronograma y Cadencia Temporal

La Línea Base del Cronograma establece la distribución temporal formal para la ejecución y entrega del proyecto **Inti**, acotada a un ciclo de vida académico estricto de **8 semanas calendario** (octubre a noviembre de 2026).

El marco metodológico adoptado es **Scrumban**, combinando la cadencia de iteraciones de duración fija (*timeboxes*) con la disciplina de flujo continuo de Kanban y la supervisión de hitos contractuales (*Milestones*).

### 1.1. Capacidad Laboral del Equipo de Ingeniería

El equipo de desarrollo está compuesto por 4 ingenieros de sistemas con asignación a tiempo parcial:

$$\text{Dedicación individual} = 8\text{ horas/semana por persona}$$
$$\text{Capacidad semanal del equipo} = 4 \times 8 = 32\text{ horas/semana}$$
$$\text{Capacidad neta por Sprint (2 semanas)} = 32 \times 2 = 64\text{ horas de ingeniería por Sprint}$$
$$\text{Capacidad total disponible para el MVP (4 Sprints)} = 64 \times 4 = 256\text{ horas hombre netas}$$

---

## 2. Estructura de Iteraciones y Hitos Contractuales (Milestones)

El horizonte de 8 semanas se organiza en **4 Sprints quincenales** de 10 días laborables cada uno, vinculados de manera biunívoca con los **Milestones contractuales de GitHub**:

```mermaid
flowchart LR
    S1["Sprint 1 (Sem. 1-2)\nM1: Infraestructura y Auth\nCompromiso: 10 SP"] --> S2["Sprint 2 (Sem. 3-4)\nM2: Ingesta SPIJ y pgvector\nCompromiso: 11 SP"]
    S2 --> S3["Sprint 3 (Sem. 5-6)\nM3: Motor RAG y Web UI\nCompromiso: 13 SP"]
    S3 --> S4["Sprint 4 (Sem. 7-8)\nM4: Citas y Validación MVP\nCompromiso: 16 SP"]

    subgraph PostMVP["Fase 2: Evolutiva"]
        S5["Sprint 5 (Sem. 9-10)\nM5: Corpus TC y Filtros"]
        S6["Sprint 6 (Sem. 11-12)\nM6: QA Final y Cierre"]
    end

    S4 -.->|Cierre del MVP| S5
    S5 --> S6
```

### Detalle de Sprints y Entregables del MVP:

| Hito / Milestone | Sprint | Fechas de Ejecución | Historias / Tareas Comprometidas | Story Points | Entregable Verificable (Línea Base) |
| :--- | :---: | :---: | :--- | :---: | :--- |
| **Milestone 1** | Sprint 1 | Semanas 1 y 2 | `HU-05` (5 SP) + `HU-03` Fase 1 (5 SP) | **10 SP** | Módulo de autenticación JWT `@unsa.edu.pe` operativo y primer extractor funcional del Código Civil. |
| **Milestone 2** | Sprint 2 | Semanas 3 y 4 | `HU-03` Fase 2 (8 SP) + `HU-06` (3 SP) | **11 SP** | 2,122 artículos del Código Civil segmentados e indexados vectorialmente en `pgvector`. Historial de usuario en Supabase. |
| **Milestone 3** | Sprint 3 | Semanas 5 y 6 | `HU-01` (8 SP) + `HU-08` (5 SP) | **13 SP** | Motor RAG en FastAPI/LlamaIndex respondiendo consultas en streaming e interfaz web móvil responsiva. |
| **Milestone 4** | Sprint 4 | Semanas 7 y 8 | `HU-02` (8 SP) + `HU-07` (8 SP) | **16 SP** | Motor de citas con hipervínculos oficiales al SPIJ, soporte multi-turno y **validación formal del MVP con usuarios**. |

---

## 3. Secuenciamiento de Actividades y Ruta Crítica (CPM)

El análisis del Método de la Ruta Crítica (*Critical Path Method* - CPM) determinó las dependencias tecnológicas obligatorias que no admiten holgura sin retrasar la fecha de lanzamiento:

```mermaid
flowchart TD
    subgraph Secuencia1["Ruta Secundaria Auth (Holgura: 10h)"]
        A["TASK-05.1: Esquema Supabase Auth (3h)"] --> B["TASK-05.2: Router JWT FastAPI (4h)"]
    end

    subgraph Secuencia2["Ruta Crítica Ingesta (Duración: 17h)"]
        C["TASK-03.1: Scraper SPIJ httpx (6h)"] --> D["TASK-03.2: Limpieza HTML (3h)"]
        D --> E["TASK-03.3: Chunker Jerárquico (5h)"]
        E --> F["TASK-03.4: Test Cobertura 2,122 Arts (3h)"]
    end
    
    B --> G["Indexación Vectorial pgvector (Sprint 2)"]
    F --> G
    
    G --> H["Pipeline RAG LlamaIndex (Sprint 3)"]
    H --> I["Citas Hipervinculadas SPIJ (Sprint 4)"]
    I --> J["Validación Final de Aceptación MVP (Sprint 4)"]

    classDef criticalPath fill:#ffebee,stroke:#c62828,stroke-width:2px,color:#111111;
    classDef standardPath fill:#f5f5f5,stroke:#757575,stroke-width:1px,color:#111111;

    class C,D,E,F,G,H,I,J criticalPath;
    class A,B standardPath;
```

*Las actividades resaltadas en rojo (`TASK-03.1` a `TASK-03.4`, indexación y validación) conforman la **Ruta Crítica** (17h frente a 7h de autenticación). Cualquier retraso en la ingesta del SPIJ o en la indexación vectorial impacta directamente en la puesta en marcha del motor RAG en el Sprint 3.*

---

## 4. Reserva de Contingencia y Gestión de Holguras

Para mitigar los riesgos derivados de caídas en portales estatales externos o problemas de conectividad de APIs, se implementa una política de reserva temporal:
- **Reserva de Contingencia por Sprint:** Se programa un máximo de **44 a 50 horas de trabajo efectivo** por Sprint sobre la capacidad teórica de 64 horas, reservando una holgura técnica del **20% al 30%** (~14 a 20 horas hombre).
- **Destino de la Holgura:**
  - Resolución de bloqueos e impedimentos no previstos en el Daily Scrum.
  - Refactorización de código y mantenimiento de cobertura mínima de pruebas ($\ge 80\%$).
  - Nivelación de carga en tareas con disparidad técnica entre Backend y Frontend.
- **Inmutabilidad del Timebox:** La duración del Sprint (14 días calendario) es estrictamente inmutable. Si una tarea no satisface la Definition of Done al cierre del sprint, se devuelve al Backlog y se reprograma; jamás se amplía la fecha límite del Sprint.
