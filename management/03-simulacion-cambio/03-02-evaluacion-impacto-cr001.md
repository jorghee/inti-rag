# 03-02 Evaluación Multidimensional de Impacto (CR-001)

> **Proyecto:** Inti - Asistente Jurídico Inteligente  
> **Actividad:** Laboratorio 05 — Actividad 3: Simulación de Caso  
> **Estado:** Estructura preparada para desarrollo

---

## 1. Síntesis del Análisis Cuantitativo de Ingeniería

- **Impacto en Alcance:** +8 Story Points en Sprint 3 (`HU-04`), alta complejidad algorítmica por sentencias no estructuradas (PDFs de 20 a 120 páginas).
- **Impacto en Tiempo y Cronograma:**
  - Capacidad estricta de Sprint 3: 64 horas hombre.
  - Carga planificada (`HU-01` + `HU-08`): 44 horas hombre (buffer: 20 horas).
  - Demanda técnica de `HU-04`: 28 horas hombre (`TASK-04.1` a `TASK-04.5`).
  - Total demandado: $44\text{ h} + 28\text{ h} = 72\text{ horas hombre}$ ($\mathbf{+12.5\%}$ de sobrecarga sobre el límite máximo).
- **Impacto en Costos:** 350 sentencias $\approx$ 4.89M tokens $\approx$ $0.098 USD ($\approx$ S/. 0.37). Costo monetario bajo, pero alto riesgo computacional.
- **Impacto en Recursos:** Sobrecarga del **150% en Backend** (48 horas sobre 32h disponibles).
- **Impacto en Riesgos y Calidad:** Riesgo de incremento de alucinación legal por encima del 15% (línea base: $< 5\%$) por falta de cross-encoder reranker.
