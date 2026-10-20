# 04-01 Catálogo de Elementos de Configuración (CIs)

> **Proyecto:** Inti - Asistente Jurídico Inteligente  
> **Actividad:** Laboratorio 05 — Actividad 4: Gestión de Configuración  
> **Estado:** Estructura preparada para desarrollo

---

## 1. Identificación de Elementos de Configuración (CIs)

| ID | Elemento de Configuración (CI) | Ubicación en Repositorio | Responsable Técnico | Frecuencia de Línea Base |
| :--- | :--- | :--- | :--- | :--- |
| **CI-01** | Código Fuente Backend (FastAPI / RAG) | `backend/app/` | Lead Backend | Por PR integrado en `main` |
| **CI-02** | Pipeline de Ingesta SPIJ / Scraper | `ingestion/` | Lead Backend | Por versión de scraper |
| **CI-03** | Esquemas DDL, RLS y Migraciones BD | `supabase/migrations/` | Lead Database | Por migración SQL aplicada |
| **CI-04** | Prompts de Inferencia y Configuración LLM | `backend/app/rag/prompts/` | Lead AI | Por ajuste de template |
| **CI-05** | Documentación de Arquitectura y ADRs | `docs/architecture/` | Scrum Master | Por cada ADR aprobada |
| **CI-06** | Suites de Pruebas Automatizadas y Fixtures | `tests/` | Lead QA | Por cada incremento funcional |
