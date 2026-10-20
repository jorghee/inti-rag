# 04-03 Auditoría y Trazabilidad de la Configuración

> **Proyecto:** Inti - Asistente Jurídico Inteligente  
> **Actividad:** Laboratorio 05 — Actividad 4: Gestión de Configuración  
> **Estado:** Estructura preparada para desarrollo

---

## 1. Mecanismos de Control y Auditoría SCM

### 1.1. Contabilidad del Estado de la Configuración (CSA)
- Registro continuo del estado de cada CI a través del historial de commits, tags y releases de GitHub.
- Mapeo unívoco de requerimientos y cambios mediante la directiva `Closes #ID`.

### 1.2. Auditorías de Configuración (IEEE Std 828-2012)
- **Auditoría Funcional de la Configuración (FCA):** Verificación de que el incremento de software cumpla el 100% de los criterios Given-When-Then especificados en la issue.
- **Auditoría Física de la Configuración (PCA):** Comprobación de que todos los artefactos de código, migraciones SQL, esquemas y documentación estén presentes en la línea base de entrega de cada Milestone.
