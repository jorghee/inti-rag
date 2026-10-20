# 00-02 Políticas de Flujo de Trabajo Kanban

> **Proyecto:** Inti - Asistente Jurídico Inteligente  
> **Tablero de Control:** [GitHub Projects #3](https://github.com/users/jorghee/projects/3)  
> **Marco:** Scrumban con control estricto de Trabajo en Curso (WIP)

---

## 1. Columnas del Tablero Kanban y Límites WIP

Para maximizar el rendimiento y evitar el desperdicio derivado de la multitarea (*multitasking*), se establecen límites de Trabajo en Curso (*Work In Progress* - WIP):

| Columna | Límite WIP | Condición de Entrada | Criterios de Transición y Salida |
| :--- | :---: | :--- | :--- |
| **1. Backlog** | $\infty$ | Registro de nueva necesidad o Historia de Usuario | Cumple al 100% con la Definition of Ready (DoR) |
| **2. Sprint Backlog** | Máx. 10 tareas | Tareas técnicas atomizadas (2--6 horas) asignadas al sprint activo | El desarrollador toma la tarea y la mueve a In Progress |
| **3. In Progress** | **Máx. 4 tareas** | Estrictamente 1 tarea activa simultánea por desarrollador | Código completo localmente y pruebas unitarias pasando |
| **4. Review** | **Máx. 3 tareas** | Pull Request abierto y enlazado al issue correspondiente (`Closes #ID`) | Aprobado por al menos un revisor par + CI checks en verde |
| **5. Done** | $\infty$ | Cumple al 100% con la Definition of Done (DoD) | Fusionado en `main` y desplegado en entorno de pruebas |

---

## 2. Criterios de Preparación (Definition of Ready - DoR)

Ninguna Historia de Usuario puede ser seleccionada para un Sprint sin cumplir:
- [x] Narrativa estructurada en formato Cono de Valor: *Como [rol], quiero [acción], para [beneficio]*.
- [x] Criterios de aceptación expresados en sintaxis formal Gherkin (*Given-When-Then*).
- [x] Estimación consensuada en Story Points basada en la serie de Fibonacci modificada (1, 2, 3, 5, 8, 13).
- [x] Dependencias técnicas y arquitectónicas resueltas y mapeadas.
- [x] Descomposición preliminar en tareas técnicas atomizadas de 2 a 6 horas.

---

## 3. Criterios de Terminado (Definition of Done - DoD)

Ninguna tarea o incremento se considera finalizado sin cumplir:
- [x] Código limpio y formateado con cero advertencias de linters (`ruff check .`).
- [x] Tipado estático estricto validado en Python (`mypy`).
- [x] Pruebas unitarias automatizadas con cobertura mínima del 80% sobre la lógica implementada (`pytest`).
- [x] Revisión por pares obligatoria (*Peer Review*) aprobada en GitHub por al menos un integrante distinto al autor.
- [x] Verificación de todos los escenarios de prueba Given-When-Then definidos en la issue.
- [x] Documentación técnica de funciones (docstrings en inglés ASCII) y endpoints en OpenAPI/Swagger.
