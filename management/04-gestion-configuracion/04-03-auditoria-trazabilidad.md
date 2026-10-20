# 04-03 Auditoría y Trazabilidad de la Configuración

> **Proyecto:** Inti - Asistente Jurídico Inteligente  
> **Área:** Gestión de la Configuración del Software (IEEE Std 828-2012)  
> **Documento Wiki:** `04-03-auditoria-trazabilidad`  
> **Auditoría:** CSA, FCA y PCA en GitHub

---

## 1. Contabilidad del Estado de la Configuración (CSA)

La **Contabilidad del Estado de la Configuración** (*Configuration Status Accounting* - CSA) registra continuamente la evolución histórica de cada CI:

- **Trazabilidad Bidireccional Requisito-Código:** Todo commit o Pull Request debe referenciar obligatoriamente el issue de origen mediante palabras clave (`Closes #ID`, `Fixes #ID`), vinculando la necesidad del usuario con la línea de código exacta.
- **Registro Inmutable de Líneas Base:** Cada versión entregada se asienta en la pestaña de **Releases** de GitHub, detallando el hash del commit, los tickets resueltos, las notas de la versión (*Release Notes*) y los artefactos exportables.

---

## 2. Auditorías Formales de la Configuración (IEEE Std 828-2012)

Para garantizar que el software entregado coincida exactamente con los compromisos contractuales, el Lead QA y el Scrum Master ejecutan dos tipos de auditorías al cierre de cada Milestone:

### 2.1. Auditoría Funcional de la Configuración (FCA)
- **Objetivo:** Verificar que el software implementado satisfaga rigurosamente todos los requisitos y métricas comprometidas.
- **Lista de Verificación FCA:**
  - [x] 100% de los criterios de aceptación en sintaxis Gherkin (Given-When-Then) validados mediante pruebas automatizadas.
  - [x] Cobertura de pruebas unitarias $\ge 80\%$ en backend (`pytest`).
  - [x] Umbral de similitud semántica RAG $\ge 0.75$ y tasa de alucinación $< 5\%$.
  - [x] Cero advertencias de linter (`ruff`) y tipado estático estricto (`mypy`).

### 2.2. Auditoría Física de la Configuración (PCA)
- **Objetivo:** Comprobar que todos los artefactos requeridos para compilar, configurar y desplegar el sistema estén inventariados y presentes en el repositorio.
- **Lista de Verificación PCA:**
  - [x] Código fuente, esquemas SQL DDL y fixtures de prueba debidamente versionados en sus directorios oficiales.
  - [x] Documentación técnica y actas del CCB sincronizadas y publicadas en la Wiki de GitHub.
  - [x] Variables de entorno documentadas en `.env.example` sin exposición de credenciales privadas.
  - [x] Pipeline de CI/CD (`.github/workflows/`) ejecutable y en estado verde.
