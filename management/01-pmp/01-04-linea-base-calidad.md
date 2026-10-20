# 01-04 Línea Base de Calidad (Quality Baseline)

> **Proyecto:** Inti - Asistente Jurídico Inteligente  
> **Actividad:** Laboratorio 05 — Actividad 1: Esquema del PMP  
> **Estado:** Estructura preparada para desarrollo

---

## 1. Estándares y Métricas de Calidad

- **Métricas de Código:** Cobertura de pruebas unitarias $\ge 80\%$ en lógica crítica (`pytest`), linters sin advertencias (`ruff check .`), tipado estático estricto (`mypy`).
- **Métricas del Motor RAG:**
  - Similitud semántica coseno: $\ge 0.75$ en `pgvector`.
  - Tasa de alucinación legal: $< 5\%$ sobre preguntas jurídicas de prueba.
  - Precisión de citas: 100% con hipervínculos válidos a fuentes oficiales (SPIJ).
  - Latencia: $\le 3$ segundos en el primer token (SSE).
- **Gobernanza de Calidad:** Aplicación estricta de Definition of Ready (DoR) y Definition of Done (DoD).
