# 00-03 Matriz de Trazabilidad de Requerimientos

> **Proyecto:** Inti - Asistente Jurídico Inteligente  
> **Propósito:** Garantizar trazabilidad bidireccional desde los dolores de usuario hasta las tareas técnicas y el código en Git.

---

## 1. Mapeo Integral de Trazabilidad

| Necesidad / Dolor | Requerimiento (RF/RNF) | Historia de Usuario | Prioridad MoSCoW | Tareas Técnicas Asociadas | Módulo Responsable |
| :--- | :--- | :--- | :---: | :--- | :--- |
| **P-01:** Acceso no autorizado y cuotas de API descontroladas | RF-01 / RNF-01 | [`HU-05`](https://github.com/jorghee/inti-rag/issues/5) Autenticación `@unsa.edu.pe` | **Must Have** (5 SP) | `TASK-05.1` al `TASK-05.5` | Backend / Auth |
| **P-02:** Dispersión normativa y desactualización del Código Civil | RF-02 / RF-03 | [`HU-03`](https://github.com/jorghee/inti-rag/issues/3) Ingesta jerárquica SPIJ | **Must Have** (13 SP) | `TASK-03.1` al `TASK-03.4` | Ingestion / DB |
| **P-03:** Alucinaciones de LLMs y respuestas sin sustento legal | RF-04 / RNF-02 | [`HU-01`](https://github.com/jorghee/inti-rag/issues/1) Búsqueda semántica RAG | **Must Have** (8 SP) | Tareas Sprint 3 | Motor RAG |
| **P-04:** Imposibilidad de verificar citas legales en fuentes oficiales | RF-05 / RNF-03 | [`HU-02`](https://github.com/jorghee/inti-rag/issues/2) Citas hipervinculadas SPIJ | **Must Have** (8 SP) | Tareas Sprint 4 | Motor RAG / Frontend |
| **P-05:** Inaccesibilidad desde dispositivos móviles durante clases | RF-06 / RNF-04 | [`HU-08`](https://github.com/jorghee/inti-rag/issues/8) UI Web móvil responsiva | **Must Have** (5 SP) | Tareas Sprint 3 | Frontend Web |
| **P-06:** Necesidad de jurisprudencia constitucional vinculante | RF-07 | [`HU-04`](https://github.com/jorghee/inti-rag/issues/4) Ingesta del Tribunal Constitucional | **Should Have** (8 SP) | Post-MVP (Sprint 5) | Ingestion / TC |
| **P-07:** Pérdida de consultas previas entre sesiones | RF-08 | [`HU-06`](https://github.com/jorghee/inti-rag/issues/6) Historial de consultas de usuario | **Could Have** (3 SP) | Sprint 2 | Base de Datos |
| **P-08:** Preguntas de seguimiento encadenadas | RF-09 | [`HU-07`](https://github.com/jorghee/inti-rag/issues/7) Contexto conversacional | **Should Have** (8 SP) | Sprint 4 | Motor RAG |

---

## 2. Compromiso del Producto Mínimo Viable (MVP)

El MVP comprende estrictamente las 5 historias de usuario **Must Have** con un volumen total de **39 Story Points**:
$$\text{Alcance MVP} = \text{HU-05 (5 SP)} + \text{HU-03 (13 SP)} + \text{HU-01 (8 SP)} + \text{HU-02 (8 SP)} + \text{HU-08 (5 SP)} = 39\text{ SP}$$
Cualquier alteración a este conjunto de historias activa mandatoriamente el protocolo formal de Control Integrado de Cambios.
