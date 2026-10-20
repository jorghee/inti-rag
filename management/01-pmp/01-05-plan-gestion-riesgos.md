# 01-05 Plan de Gestión de Riesgos (Risk Baseline)

> **Proyecto:** Inti - Asistente Jurídico Inteligente  
> **Área:** Gestión de los Riesgos (PMBOK 7ma Edición)  
> **Documento Wiki:** `01-05-plan-gestion-riesgos`  
> **Estado:** Aprobado por el Scrum Master y Línea Base Congelada

---

## 1. Metodología de Evaluación y Matriz de Probabilidad e Impacto

El Plan de Gestión de Riesgos de **Inti** identifica, clasifica y gestiona preventivamente las amenazas técnicas, operativas y de gobierno que podrían desviar el proyecto de sus líneas base de alcance, tiempo y costo.

Se adopta una escala semicuantitativa estándar de 5 niveles conforme al PMBOK:

$$\text{Nivel de Riesgo (Severidad)} = \text{Probabilidad (1 a 5)} \times \text{Impacto (1 a 5)}$$

- **Bajo (1--5):** Se acepta el riesgo y se monitorea en retrospectivas.
- **Moderado (6--9):** Se asigna responsable técnico y se implementa plan de contingencia pasivo.
- **Alto (10--14):** Requiere mitigación técnica activa y pruebas automatizadas preventivas.
- **Crítico / Muy Alto (15--25):** Amenaza existencial para el proyecto; requiere salvaguarda arquitectónica inmediata.

```mermaid
quadrantChart
    title Matriz de Probabilidad e Impacto (5x5)
    x-axis Impacto Bajo --> Impacto Critico
    y-axis Probabilidad Baja --> Probabilidad Alta
    quadrant-1 Riesgos Criticos (Atencion Inmediata)
    quadrant-2 Riesgos de Alta Probabilidad
    quadrant-3 Riesgos Aceptables
    quadrant-4 Riesgos de Alto Impacto
    "R-05: Scope Creep": [0.85, 0.80]
    "R-03: Rate Limits Groq": [0.65, 0.75]
    "R-01: Bloqueo Scraper SPIJ": [0.75, 0.60]
    "R-02: Alucinacion Juridica": [0.95, 0.40]
    "R-04: Acceso no Institucional": [0.70, 0.35]
```

---

## 2. Registro y Catálogo de Riesgos Prioritarios

| ID | Riesgo Identificado | Categoría | Prob. (1-5) | Imp. (1-5) | Severidad ($P \times I$) | Estrategia de Mitigación Técnica | Rol Responsable |
| :--- | :--- | :---: | :---: | :---: | :---: | :--- | :--- |
| **R-01** | Bloqueo del scraper automatizado por cambios en HTML o filtros anti-bot del SPIJ | Técnico / Externo | 3 | 4 | **12 (Alto)** | Implementación de cabeceras rotativas de User-Agent, reintentos con retroceso exponencial (*backoff*), y almacenamiento en caché de respuestas crudas. | Lead Backend |
| **R-02** | Alucinación en citas jurídicas por recuperación de normas ambiguas o derogadas | Calidad / Legal | 2 | 5 | **10 (Alto)** | Filtrado estricto por concordancias vigentes, umbral de similitud coseno $\ge 0.75$ y rechazo explícito de respuesta ante baja confianza. | Lead AI / RAG |
| **R-03** | Agotamiento de cuota en Groq Cloud API en horas pico de talleres jurídicos | Operativo / Cloud | 4 | 3 | **12 (Alto)** | Failover programático automático en FastAPI hacia modelos de contingencia en OpenRouter (DeepSeek / GPT-6 Luna) financiado con la reserva de caja. | Lead Backend |
| **R-04** | Registro indebido de usuarios con dominios externos a `@unsa.edu.pe` | Seguridad | 2 | 4 | **8 (Moderado)** | Validación dual: filtro regex estricto en el cliente frontend y restricción criptográfica forzada en el backend con Supabase GoTrue y dependencias FastAPI. | Lead DB / Auth |
| **R-05** | Corrupción del alcance (*scope creep*) por solicitudes informales de stakeholders | Gobernanza | 4 | 4 | **16 (Crítico)** | Aplicación obligatoria del protocolo de Control Integrado de Cambios. Todo cambio mayor requiere análisis cuantitativo de impacto y resolución formal del CCB. | Scrum Master / PO |

---

## 3. Planes de Respuesta y Protocolos de Contingencia

### Protocolo frente a R-01 (Caída o Bloqueo del Portal SPIJ):
1. **Detección:** El job de ingesta captura respuestas HTTP `403 Forbidden`, `429 Too Many Requests` o `502 Bad Gateway`.
2. **Acción Inmediata:** Activación del modo desacoplado leyendo el snapshot legal respaldado en el repositorio (`ingestion/raw/codigo_civil_snapshot.json`).
3. **Recuperación:** Reintento programado en horario nocturno (02:00 UTC-5) con tasa reducida de solicitudes ($0.5\text{ req/s}$).

### Protocolo frente a R-02 (Detección de Alucinación en Citas):
1. **Detección:** El verificador de citas no encuentra correspondencia exacta entre el número de artículo citado y los metadatos fácticos del chunk recuperado de `pgvector`.
2. **Acción Inmediata:** Interrupción del flujo de generación; el sistema emite el mensaje estandarizado: *"El asistente no dispone de evidencia normativa suficiente en el Código Civil para fundamentar esta respuesta sin riesgo de imprecisión."*
3. **Aislamiento:** El prompt y la consulta fallida se registran en la tabla `rag_eval_failures` para ajuste de Few-Shot prompts.

### Protocolo frente a R-03 (Agotamiento de Cuota de Inferencia Groq):
1. **Detección:** Captura de error HTTP `429 Rate Limit Exceeded` en el cliente de Groq.
2. **Acción Inmediata:** Cambio transparente de proveedor de inferencia hacia OpenRouter mediante la clase `ContingencyLLMClient`, sin interrupción visible para el estudiante.
3. **Control Financiero:** Notificación al Scrum Master para monitorear el consumo de la reserva de S/. 6.64.

---

## 4. Gobernanza y Monitoreo Continuo

- **Monitoreo Diario (Daily Scrum):** Cada integrante reporta si su tarea técnica activa enfrenta disparadores de los riesgos R-01 a R-04.
- **Revisión de Riesgos por Sprint (Sprint Review / Retrospective):** El Scrum Master y el Product Owner auditan la matriz de riesgos, ajustan probabilidades residuales y verifican el estado del fondo de reserva para mantener las líneas base intactas.
