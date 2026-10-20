# 01-05 Plan de Gestión de Riesgos

> **Proyecto:** Inti - Asistente Jurídico Inteligente  
> **Actividad:** Laboratorio 05 — Actividad 1: Esquema del PMP  
> **Estado:** Estructura preparada para desarrollo

---

## 1. Identificación y Mitigación de Riesgos

- **Metodología:** Matriz de probabilidad e impacto (5x5).
- **Riesgos Principales Identificados:**
  1. *R-01:* Bloqueo de scraper por rate-limits o cambios en SPIJ (Prob: Media, Imp: Alto). Mitigación: User-Agents rotativos, exponential backoff y caching.
  2. *R-02:* Alucinación en citas jurídicas por recuperación ambigua (Prob: Media, Imp: Crítico). Mitigación: Umbral $\ge 0.75$, rechazo explícito de respuesta ante baja similitud.
  3. *R-03:* Agotamiento de cuota en Groq Cloud API (Prob: Alta, Imp: Moderado). Mitigación: Failover automático a OpenRouter financiado por reserva de contingencia.
  4. *R-04:* Acceso indebido de correos no institucionales (Prob: Baja, Imp: Alto). Mitigación: Verificación criptográfica en Supabase GoTrue y FastAPI.
  5. *R-05:* Corrupción del alcance (*scope creep*) (Prob: Alta, Imp: Crítico). Mitigación: Protocolo formal de control de cambios y CCB.
