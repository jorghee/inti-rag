# Inti - Asistente Jurídico Inteligente (Wiki de Gestión)

Bienvenido a la Wiki de Gestión del proyecto **Inti - Asistente Jurídico Inteligente**, una plataforma basada en arquitectura Retrieval-Augmented Generation (RAG) diseñada para estudiantes y docentes de la Facultad de Derecho de la Universidad Nacional de San Agustín (UNSA).

Este espacio documenta formalmente la planificación, el control integrado de cambios y la gestión de la configuración del software, en estricto cumplimiento de los estándares **PMBOK 7ma edición**, **IEEE Std 828-2012** e **ISO/IEC/IEEE 12207**.

---

## Índice General de Gestión

### 1. Marco de Gobernanza y Fundamentos
- [00-01 Resumen del proyecto y marco de trabajo](00-marco-gobernanza/00-01-resumen-proyecto.md)
- [00-02 Políticas de flujo de trabajo Kanban (WIP, DoR y DoD)](00-marco-gobernanza/00-02-politicas-flujo-kanban.md)
- [00-03 Matriz de trazabilidad de requerimientos](00-marco-gobernanza/00-03-matriz-trazabilidad.md)

### 2. Plan de Gestión del Proyecto (PMP)
- [01-00 Índice y resumen ejecutivo del PMP](01-pmp/01-00-indice-pmp.md)
- [01-01 Línea base del alcance (Backlog, MVP 39 SP y WBS)](01-pmp/01-01-linea-base-alcance.md)
- [01-02 Línea base del cronograma (8 semanas, 4 Sprints, 64h/sprint)](01-pmp/01-02-linea-base-cronograma.md)
- [01-03 Línea base de costos y presupuesto operativo (S/. 88.18)](01-pmp/01-03-linea-base-costos.md)
- [01-04 Línea base de calidad y métricas RAG](01-pmp/01-04-linea-base-calidad.md)
- [01-05 Plan de gestión de riesgos y mitigaciones](01-pmp/01-05-plan-gestion-riesgos.md)

### 3. Protocolo de Gestión de Cambios
- [02-00 Índice de gestión de cambios](02-gestion-cambios/02-00-indice-gestion-cambios.md)
- [02-01 Protocolo y taxonomía de cambios (Niveles 1, 2 y 3)](02-gestion-cambios/02-01-protocolo-tipologia-cambios.md)
- [02-02 Estatuto del Comité de Control de Cambios (CCB)](02-gestion-cambios/02-02-estatuto-ccb.md)
- [02-03 Flujo de control de cambios paso a paso (Solicitud a PR)](02-gestion-cambios/02-03-flujo-control-cambios.md)

### 4. Simulación de Caso de Cambio (CR-001)
- [03-00 Índice de simulación de caso](03-simulacion-cambio/03-00-indice-simulacion.md)
- [03-01 Ficha de solicitud de cambio CR-001 (Consulta Expedientes CEJ)](03-simulacion-cambio/03-01-solicitud-cambio-cr001.md)
- [03-02 Evaluación multidimensional de impacto de ingeniería](03-simulacion-cambio/03-02-evaluacion-impacto-cr001.md)
- [03-03 Acta de resolución y dictamen formal del CCB](03-simulacion-cambio/03-03-acta-resolucion-ccb.md)

### 5. Plan de Gestión de la Configuración (SCM)
- [04-00 Índice del plan de configuración SCM](04-gestion-configuracion/04-00-indice-configuracion-scm.md)
- [04-01 Catálogo de elementos de configuración (CIs)](04-gestion-configuracion/04-01-catalogo-elementos-config.md)
- [04-02 Estrategia de versionado (SemVer) y políticas de ramas en Git](04-gestion-configuracion/04-02-estrategia-versionado-ramas.md)
- [04-03 Auditoría y trazabilidad de la configuración](04-gestion-configuracion/04-03-auditoria-trazabilidad.md)

---

## Equipo de Proyecto y Roles

| Rol Scrum / Gestión | Integrante | Perfil Técnico Principal | Dedicación |
| :--- | :--- | :--- | :---: |
| **Product Owner (PO)** | **Jhonatan David Arias Quispe** (`@JhonAQ`) | Frontend / Requerimientos | 16 h / Sprint |
| **Scrum Master (SM)** | **Jorge Luis Mamani Huarsaya** (`@jorghee`) | Gestión / Backend / Gobernanza | 16 h / Sprint |
| **Lead Developer** | **Rodrigo Alexander Fernandez Huarca** (`@RodrigoAlexander7`) | Backend / RAG / Scraping | 16 h / Sprint |
| **QA & Database Lead** | **Rafael Diego Nina Calizaya** (`@DrN25`) | PostgreSQL / pgvector / Testing | 16 h / Sprint |

---

*Repositorio oficial:* [`jorghee/inti-rag`](https://github.com/jorghee/inti-rag)  
*Curso:* Gestión de Proyectos de Software — Universidad Nacional de San Agustín (UNSA 2026-B)
