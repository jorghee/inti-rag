# 02-03 Flujo de Control de Cambios Paso a Paso

> **Proyecto:** Inti - Asistente Jurídico Inteligente  
> **Actividad:** Laboratorio 05 — Actividad 2: Plan de Cambios  
> **Estado:** Estructura preparada para desarrollo

---

## 1. Ciclo de Vida del Cambio en 5 Fases

1. **Fase 1: Solicitud Formal (CR):** Apertura de issue con plantilla `change-request.yml` y etiqueta `type: change-request`.
2. **Fase 2: Análisis de Impacto de Ingeniería:** Evaluación técnica y cuantitativa sobre Alcance, Tiempo, Costo, Recursos y Riesgos.
3. **Fase 3: Deliberación y Resolución del CCB:** Sesión formal del comité emitiendo dictamen: *Aprobado*, *Rechazado* o *Pospuesto*.
4. **Fase 4: Ajuste de Líneas Base:** Actualización de GitHub Projects, Milestones y aplicación de permuta de alcance (*scope swap*).
5. **Fase 5: Implementación, Verificación y Cierre:** Desarrollo en rama `change/CR-XXX-<desc>`, Pull Request con revisión par, paso de CI y cierre con `Closes #ID`.
