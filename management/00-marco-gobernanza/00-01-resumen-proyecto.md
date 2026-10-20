# 00-01 Resumen del Proyecto y Marco de Trabajo

> **Proyecto:** Inti - Asistente Jurídico Inteligente (RAG)  
> **Repositorio:** `jorghee/inti-rag`  
> **Organización:** Universidad Nacional de San Agustín (UNSA 2026-B)  
> **Marco Metodológico:** Scrumban (Scrum con visualización Kanban y límites WIP)

---

## 1. Visión y Propósito del Producto

**Inti** es un asistente jurídico inteligente especializado impulsado por una arquitectura de **Generación Aumentada por Recuperación (RAG)**. Su objetivo es brindar a estudiantes de pregrado (1.° a 5.° año) y docentes de la Facultad de Derecho de la UNSA acceso rápido, confiable y 100% fundamentado a la legislación y jurisprudencia peruana.

### Diagnóstico AS-IS vs. TO-BE

- **Estado Actual (AS-IS):** La búsqueda manual en portales estatales dispersos (SPIJ del MINJUS, Tribunal Constitucional, Poder Judicial) demanda entre **30 y 90 minutos** por consulta jurídica compleja. Los modelos de lenguaje generalistas (ej. ChatGPT) presentan una tasa de **40% a 50% de alucinación** en artículos y casaciones peruanas.
- **Estado Propuesto (TO-BE con Inti):** Reduce el tiempo de respuesta a **1 a 3 minutos** (~95% de ahorro), garantiza una tasa de **alucinación inferior al 5%** y proporciona hipervínculos interactivos y trazables a las fuentes oficiales.

---

## 2. Equipo de Trabajo y Asignación de Roles Scrum

| Rol Scrum / Gestión | Integrante | Responsabilidades Principales | Dedicación |
| :--- | :--- | :--- | :---: |
| **Product Owner (PO)** | **Jhonatan David Arias Quispe** (`@JhonAQ`) | Priorización del Backlog, validación de criterios de aceptación, enlace con usuarios de Derecho | 16 h / Sprint |
| **Scrum Master (SM)** | **Jorge Luis Mamani Huarsaya** (`@jorghee`) | Facilitación ágil, remoción de impedimentos, cumplimiento de límites WIP, gobernanza | 16 h / Sprint |
| **Lead Developer** | **Rodrigo Alexander Fernandez Huarca** (`@RodrigoAlexander7`) | Endpoints FastAPI, orquestación LlamaIndex, scrapers SPIJ/TC | 16 h / Sprint |
| **QA & Database Lead** | **Rafael Diego Nina Calizaya** (`@DrN25`) | Esquemas PostgreSQL, índices `pgvector`, pruebas automatizadas Pytest | 16 h / Sprint |

**Capacidad Operativa del Equipo:**  
$$C_{\text{sprint}} = 4 \text{ ingenieros} \times 8 \text{ h/semana} \times 2 \text{ semanas} = 64 \text{ horas de ingeniería por Sprint}$$

---

## 3. Jerarquía de Autoridad Documental y Anti-Deriva

Cuando se identifiquen discrepancias de información entre fuentes del proyecto, rige el siguiente orden de precedencia:

$$\text{Nivel 1: Código en vivo en main} > \text{Nivel 2: GitHub Issues y Project Board} > \text{Nivel 3: Wiki de Gestión} > \text{Nivel 4: Informes Académicos Históricos}$$

- **Regla de Realidad Física:** Si una tarea figura como terminada en un documento pero carece de código fusionado en `main`, la tarea se considera formalmente abierta.
- **Protección del Alcance:** Queda prohibido modificar estimaciones en Story Points o prioridades MoSCoW sin autorización formal del Product Owner o resolución del CCB.
