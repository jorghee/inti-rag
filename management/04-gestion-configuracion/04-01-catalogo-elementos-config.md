# 04-01 Catálogo de Elementos de Configuración (CIs)

> **Proyecto:** Inti - Asistente Jurídico Inteligente  
> **Área:** Gestión de la Configuración del Software (IEEE Std 828-2012)  
> **Documento Wiki:** `04-01-catalogo-elementos-config`  
> **Herramienta de Control:** GitHub Repositories (`jorghee/inti-rag`)

---

## 1. Identificación y Clasificación de Elementos de Configuración (CIs)

De conformidad con el estándar IEEE Std 828-2012, un **Elemento de Configuración** (*Configuration Item* - CI) es cualquier entidad de software o documentación sujeta a control formal de cambios y versionado.

Para el proyecto **Inti**, los artefactos controlados se estructuran en cuatro categorías fundamentales:

| ID del CI | Categoría | Elemento de Configuración Controlado | Ubicación en GitHub | Herramienta de Control | Responsable Técnico | Frecuencia de Línea Base |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **CI-01** | **Código Fuente** | API REST Backend (FastAPI, LlamaIndex, Groq) | `backend/app/` | Git / GitHub | Lead Backend | Por Pull Request integrado |
| **CI-02** | **Código Fuente** | Pipeline de Ingesta SPIJ y Chunker Legal | `ingestion/` | Git / GitHub | Lead Backend | Por versión de scraper |
| **CI-03** | **Código Fuente** | Interfaz Web Responsiva (HTML5/CSS/JS) | `frontend/` | Git / GitHub | Product Owner / Frontend | Por Sprint / Milestone |
| **CI-04** | **Datos y Esquemas** | Esquemas DDL, Migraciones SQL e Índices HNSW | `supabase/migrations/` | Git / Supabase CLI | Lead Database | Por migración de esquema |
| **CI-05** | **Datos y Esquemas** | Snapshots y Corpus Normativo Offline | `ingestion/raw/` | Git LFS / GitHub | Lead Database | Por corte normativo |
| **CI-06** | **Pruebas** | Suites de Pruebas Automatizadas (Pytest) | `tests/` | Git / GitHub Actions | Lead QA | Por incremento de código |
| **CI-07** | **Documentación** | Plan de Gestión (PMP), Líneas Base y ADRs | `docs/`, `management/` | Git / GitHub Wiki | Scrum Master | Por aprobación del CCB |
| **CI-08** | **Documentación** | Actas de Resolución y Fichas de Cambio | `management/03-*` | Git / Issues de GitHub | Scrum Master | Por sesión del CCB |
| **CI-09** | **Configuración / CI** | Workflows de CI/CD (Tests, Lint, Wiki Sync) | `.github/workflows/` | GitHub Actions | Scrum Master / Tech Lead | Por ajuste de pipeline |

---

## 2. Justificación de la Herramienta Seleccionada: GitHub

La elección de **GitHub** como plataforma única de SCM sobre alternativas como GitLab o Bitbucket responde a las siguientes ventajas técnicas operativas:

1. **Plataforma Todo-en-Uno Unificada:** Integra en un único repositorio el código fuente, la trazabilidad de requerimientos (Issues), el flujo ágil (Projects), el versionado documental (GitHub Wiki) y la automatización CI/CD (GitHub Actions), evitando la dispersión de herramientas.
2. **Ecosistema Nativo para Educación e Investigación:** Ofrece cuotas gratuitas ilimitadas para repositorios académicos y automatizaciones (GitHub Free Tier), alineándose con el presupuesto de bolsillo del proyecto (S/. 88.18).
3. **Reglas Estrictas de Protección de Ramas (*Branch Protection*):** Permite exigir revisiones por pares (*Peer Review*) y cheques automáticos de pruebas unitarias (`pytest --cov >= 80%`) antes de autorizar cualquier fusión a la rama principal (`main`).
