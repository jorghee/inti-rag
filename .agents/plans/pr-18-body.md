## Resumen de Cambios

Implementación exhaustiva de pruebas unitarias y de integración para la tarea técnica:
**[TASK-05.5] Pruebas unitarias y de integración de flujo de registro y contraseñas** (Closes #18).

Historia Padre: **[HU-05] Registro y autenticación de usuarios institucional UNSA** (#5).

---

### Componentes y Escenarios Cubiertos

1. **Pruebas Unitarias de Validación de Contraseñas (`tests/unit/test_auth_registration.py`):**
   - Validación de contraseñas robustas que cumplen la totalidad de criterios (mínimo 8 caracteres, mayúscula, minúscula, dígito, carácter especial).
   - Verificación de límites de longitud (rechazo en longitud 0, 3, 5, 6 y frontera de 7 caracteres).
   - Rechazo específico de contraseñas sin mayúsculas, sin minúsculas, sin números y sin caracteres especiales.
   - Verificación de que todos los caracteres definidos en `SPECIAL_CHARACTERS` satisfacen el criterio de símbolo.

2. **Pruebas Unitarias de Dominio Institucional UNSA (`tests/unit/test_auth_registration.py`):**
   - Aceptación de direcciones válidas bajo `@unsa.edu.pe` (incluyendo variantes con puntos, guiones, más, números y mayúsculas normalizadas).
   - Rechazo de dominios comerciales (`@gmail.com`, `@hotmail.com`, `@yahoo.es`, `@outlook.com`).
   - Rechazo de otras universidades e instituciones (`@pucp.edu.pe`, `@uni.edu.pe`, `@unmsm.edu.pe`).
   - Rechazo de ataques de sufijo y subdominios no autorizados (`@cs.unsa.edu.pe`, `@derecho.unsa.edu.pe`, `@unsa.edu.pe.attacker.com`).
   - Rechazo de sintaxis malformadas e inyecciones de código.

3. **Pruebas de Conflictos por Correo Duplicado (`tests/unit/test_auth_registration.py`):**
   - Detección de duplicados con emisión de código HTTP 409 Conflict.
   - Validación de insensibilidad a mayúsculas/minúsculas en la detección de correos duplicados.
   - Protección contra registro de cuentas base presembradas.
   - Verificación de hashing criptográfico bcrypt seguro donde el texto plano nunca es persistido.

4. **Pruebas de Integración de Flujo y Criterios Gherkin (`tests/integration/test_auth_registration_flow.py`):**
   - Escenario 1 (HU-05): Registro exitoso con correo `@unsa.edu.pe` y contraseña segura creando la cuenta (HTTP 201 Created).
   - Escenario 2 (HU-05): Rechazo de correo ya registrado con HTTP 409 Conflict y mensaje estructurado.
   - Rechazo en frontera HTTP de dominios no institucionales (HTTP 400 Bad Request).
   - Rechazo en frontera HTTP de contraseñas débiles (HTTP 400 Bad Request).
   - Ciclo completo de vida: Registro -> Inicio de sesión con emisión de token JWT -> Inspección de perfil `/api/v1/auth/me`.

---

### Criterios de Aceptación Verificados

- [x] Verificación de rechazo de contraseñas débiles en todas las condiciones de frontera.
- [x] Verificación de rechazo de correos ajenos al dominio `@unsa.edu.pe`.
- [x] Verificación de rechazo de correos duplicados con código HTTP 409 Conflict.
- [x] Cobertura del 100% en `auth_service.py`, `schemas/auth.py` y endpoints de autenticación.
- [x] 206 pruebas automatizadas aprobadas en el repositorio sin fallos ni advertencias de deprecación críticas.
- [x] Verificación de estilo y formato con ruff sin errores ni advertencias.
- [x] Ausencia total de emojis decorativos y cumplimiento de directrices de AGENTS.md.

Closes #18
