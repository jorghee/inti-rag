# Módulo de Citas Verificables y Control de Alucinaciones

> **Subsistema:** Generador de Citas Jurídicas y Motor de Grounding  
> **Historia de Usuario:** `HU-02` (Trazabilidad de Citas con Enlace Directo a la Fuente Oficial)  
> **Objetivo de Calidad:** Reducción de la tasa de alucinación del 40-50% (modelos generalistas) a menos del 5%.

---

## 1. Propósito y Alcance

La validez académica y profesional de un asistente jurídico depende por completo de la exactitud de sus referencias normativas. El módulo de citas garantiza que **ninguna afirmación jurídica quede huérfana de respaldo normativo**, vinculando cada respuesta con su artículo exacto en el Sistema Peruano de Información Jurídica (SPIJ).

---

## 2. Formato Canónico de Citas

Toda respuesta emitida por el motor RAG debe estructurar las citas siguiendo el estándar interactivo definido para el proyecto:

### 2.1. Sintaxis en Texto
```markdown
[Código Civil, Art. {número}](https://spij.minjus.gob.pe/#/detallenorma/H682695)
```

### 2.2. Ejemplo Concreto de Respuesta Generada
> "En el régimen de responsabilidad extracontractual peruano, aquel que por dolo o culpa causa un daño a otro está obligado a indemnizarlo [[Código Civil, Art. 1969](https://spij.minjus.gob.pe/spij-ext-web/#/detallenorma/H682695)]. Asimismo, si el daño se produce mediante el ejercicio de una actividad riesgosa o peligrosa, el autor responde objetivamente [[Código Civil, Art. 1970](https://spij.minjus.gob.pe/spij-ext-web/#/detallenorma/H682695)]."

---

## 3. Arquitectura del Verificador de Grounding

```mermaid
flowchart TD
    GeneratedResponse[/"Respuesta Generada por LLM"/] --> ParseCitations["Extractor Sintáctico de Citas\nRegex: \[Código Civil, Art\. ([0-9]+)\]"]
    ParseCitations --> MatchChunks{"¿El artículo citado\nfigura en los fragmentos\nrecuperados por pgvector?"}

    MatchChunks -->|No (Alucinación Detectada)| RejectClaim["Regla de Corrección Automática:\nEliminar o reformular afirmación huérfana"]
    RejectClaim --> FlagAnomaly["Registrar Advertencia en Telemetría"]
    
    MatchChunks -->|Sí (Fundamentado)| InjectHyperlink["Inyectar URL Oficial Permanente\ndel portal SPIJ"]
    InjectHyperlink --> SaveCitationRef[("Registrar en tabla citation_refs\n(query_log_id, chunk_id, similarity)")]
    SaveCitationRef --> VerifiedOutput[/"Salida Final con Enlaces Interactivos"/]
```

---

## 4. Persistencia y Trazabilidad

Cada cita generada se almacena en la tabla relacional `citation_refs` vinculada al identificador del log de consulta (`query_log_id`) y al identificador del fragmento (`chunk_id`).

Esto permite:
1. **Auditoría académica:** Docentes y evaluadores pueden contrastar el texto sugerido por la IA contra el texto de la ley con un solo clic.
2. **Evaluación continua de calidad:** Permite calcular métricas automatizadas de fidelidad semántica (*faithfulness*) y cobertura de citas (*citation recall*).
3. **Métricas de satisfacción:** Si un estudiante reporta una cita errónea mediante el botón de retroalimentación (`HU-11`), el registro permite identificar qué fragmento provocó el desajuste.
