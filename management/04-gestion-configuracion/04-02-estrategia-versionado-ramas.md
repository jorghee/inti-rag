# 04-02 Estrategia de Versionado y Políticas de Ramas

> **Proyecto:** Inti - Asistente Jurídico Inteligente  
> **Actividad:** Laboratorio 05 — Actividad 4: Gestión de Configuración  
> **Estado:** Estructura preparada para desarrollo

---

## 1. Políticas de Ramificación y Versionado

### 1.1. Semantic Versioning 2.0.0 (SemVer)
- `MAJOR.MINOR.PATCH`: `v1.0.0` para el lanzamiento del MVP.
- `MINOR`: Incremento al cierre de cada Milestone (`v0.1.0` M1, `v0.2.0` M2, `v0.3.0` M3, `v0.4.0` M4).
- `PATCH`: Corrección de errores urgentes (`v0.1.1`).
- Etiquetas anotadas de Git firmadas criptográficamente (`git tag -a v0.1.0 -m "..."`).

### 1.2. Estrategia de Ramificación (GitHub Flow Disciplinado)
- `main`: Rama de producción protegida. Prohibido el push directo y force push.
- `feat/<issue-id>-<desc>`: Nuevas historias o tareas técnicas.
- `fix/<issue-id>-<desc>`: Corrección de defectos reportados.
- `change/<cr-id>-<desc>`: Cambios autorizados por el CCB.

### 1.3. Reglas de Protección de Ramas en GitHub
- Requerimiento obligatorio de Pull Request con al menos una revisión por pares (Peer Review).
- Status checks automatizados de GitHub Actions en verde (`pytest` con cobertura $\ge 80\%$ y linters `ruff`).
- Historial lineal mediante *Squash and Merge*.
