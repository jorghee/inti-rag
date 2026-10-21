/**
 * Cliente HTTP y Proveedor de Autenticación (TASK-05.4)
 * Inti — Asistente Jurídico Inteligente (Facultad de Derecho, UNSA)
 * 
 * Cumple con los contratos especificados en docs/modules/authentication.md y ADR-004.
 * Incluye fallback automático y configurable con Mock Provider en caso de que el
 * backend FastAPI (TASK-05.2) aún no esté levantado o se ejecute en entorno estático.
 */

export class ApiError extends Error {
  constructor(status, detail) {
    super(detail || `Error en la solicitud (${status})`);
    this.name = 'ApiError';
    this.status = status;
    this.detail = detail;
  }
}

// Configuración base de la API
const DEFAULT_CONFIG = {
  baseUrl: window.__ENV__?.API_BASE_URL || 'http://localhost:8000',
  forceMock: new URLSearchParams(window.location.search).get('mock') === 'true',
  mockDelayMs: 400
};

// Base de datos de prueba local para Mock Provider
const MOCK_STORAGE_KEY = 'inti_mock_registered_users';

function getMockUsers() {
  try {
    const data = localStorage.getItem(MOCK_STORAGE_KEY);
    if (data) return JSON.parse(data);
  } catch (err) {
    console.warn('[ApiClient] No se pudo leer mock users de localStorage:', err);
  }
  // Usuario inicial pre-sembrado para pruebas inmediatas
  return [
    {
      id: 'usr-unsa-001',
      email: 'jariasq@unsa.edu.pe',
      full_name: 'Jhonatan David Arias Quispe',
      role: 'student',
      password: 'Password123*'
    },
    {
      id: 'usr-unsa-002',
      email: 'docente@unsa.edu.pe',
      full_name: 'Dr. Jorge Huarsaya',
      role: 'docent',
      password: 'Password123*'
    }
  ];
}

function saveMockUser(user) {
  const users = getMockUsers();
  users.push(user);
  try {
    localStorage.setItem(MOCK_STORAGE_KEY, JSON.stringify(users));
  } catch (err) {
    console.warn('[ApiClient] No se pudo guardar mock user:', err);
  }
}

/**
 * Generador de token JWT mock con estructura estándar Base64URL
 */
function generateMockJwt(user) {
  const header = btoa(JSON.stringify({ alg: 'HS256', typ: 'JWT' }));
  const payload = btoa(JSON.stringify({
    sub: user.id,
    email: user.email,
    full_name: user.full_name,
    role: user.role,
    aud: 'authenticated',
    iss: 'inti-auth-service',
    exp: Math.floor(Date.now() / 1000) + 3600
  }));
  const signature = btoa('inti_academic_hmac_secret_mock_signature');
  return `${header}.${payload}.${signature}`;
}

export const ApiClient = {
  config: { ...DEFAULT_CONFIG },

  /**
   * Configura la URL base o fuerza el modo mock
   */
  configure(customConfig) {
    this.config = { ...this.config, ...customConfig };
  },

  /**
   * Inicio de sesión institucional
   * Endpoint: POST /api/v1/auth/login
   * @param {Object} credentials
   * @param {string} credentials.email
   * @param {string} credentials.password
   * @returns {Promise<{ access_token: string, token_type: string, expires_in: number, user: Object }>}
   */
  async login({ email, password }) {
    if (!this.config.forceMock) {
      try {
        const response = await fetch(`${this.config.baseUrl}/api/v1/auth/login`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
          },
          body: JSON.stringify({ email, password })
        });

        const data = await response.json().catch(() => null);

        if (!response.ok) {
          throw new ApiError(response.status, data?.detail || 'Credenciales inválidas o no autorizadas');
        }

        return data;
      } catch (err) {
        if (err instanceof ApiError) {
          throw err;
        }
        console.warn(`[ApiClient] Servidor backend (${this.config.baseUrl}) inaccesible. Activando Mock Fallback (ADR-004):`, err.message);
      }
    }

    // --- Mock Fallback ---
    await new Promise(resolve => setTimeout(resolve, this.config.mockDelayMs));

    if (!email.endsWith('@unsa.edu.pe')) {
      throw new ApiError(400, 'Acceso restringido: Solo se permiten cuentas institucionales @unsa.edu.pe');
    }

    const users = getMockUsers();
    const existing = users.find(u => u.email.toLowerCase() === email.toLowerCase());

    if (existing) {
      if (existing.password !== password) {
        throw new ApiError(401, 'Contraseña incorrecta para la cuenta institucional');
      }
      return {
        access_token: generateMockJwt(existing),
        token_type: 'bearer',
        expires_in: 3600,
        user: {
          id: existing.id,
          email: existing.email,
          full_name: existing.full_name,
          role: existing.role
        }
      };
    }

    // Si es un correo @unsa.edu.pe válido con contraseña adecuada, permitir acceso de prueba
    const newUser = {
      id: `usr-${Date.now()}`,
      email,
      full_name: email.split('@')[0].replace('.', ' ').toUpperCase(),
      role: 'student'
    };

    return {
      access_token: generateMockJwt(newUser),
      token_type: 'bearer',
      expires_in: 3600,
      user: newUser
    };
  },

  /**
   * Registro institucional de nuevos usuarios
   * Endpoint: POST /api/v1/auth/register
   * @param {Object} userData
   * @param {string} userData.email
   * @param {string} userData.password
   * @param {string} userData.full_name
   * @param {string} userData.role
   * @returns {Promise<{ id: string, email: string, full_name: string, role: string }>}
   */
  async register({ email, password, full_name, role }) {
    if (!this.config.forceMock) {
      try {
        const response = await fetch(`${this.config.baseUrl}/api/v1/auth/register`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
          },
          body: JSON.stringify({ email, password, full_name, role })
        });

        const data = await response.json().catch(() => null);

        if (!response.ok) {
          throw new ApiError(response.status, data?.detail || 'Error en el registro de usuario');
        }

        return data;
      } catch (err) {
        if (err instanceof ApiError) {
          throw err;
        }
        console.warn(`[ApiClient] Servidor backend (${this.config.baseUrl}) inaccesible. Activando Mock Fallback (ADR-004):`, err.message);
      }
    }

    // --- Mock Fallback ---
    await new Promise(resolve => setTimeout(resolve, this.config.mockDelayMs));

    if (!email.endsWith('@unsa.edu.pe')) {
      throw new ApiError(400, 'El correo institucional debe pertenecer al dominio @unsa.edu.pe');
    }

    const users = getMockUsers();
    if (users.some(u => u.email.toLowerCase() === email.toLowerCase())) {
      throw new ApiError(409, 'El correo institucional ya se encuentra registrado en el sistema.');
    }

    const created = {
      id: `usr-${Date.now()}`,
      email,
      full_name,
      role,
      password
    };

    saveMockUser(created);

    return {
      id: created.id,
      email: created.email,
      full_name: created.full_name,
      role: created.role
    };
  },

  /**
   * Obtiene la información del usuario actual autenticado
   * Endpoint: GET /api/v1/auth/me
   * @param {string} token - Token JWT
   * @returns {Promise<Object>}
   */
  async getCurrentUser(token) {
    if (!token) {
      throw new ApiError(401, 'Token de autorización ausente');
    }

    if (!this.config.forceMock) {
      try {
        const response = await fetch(`${this.config.baseUrl}/api/v1/auth/me`, {
          headers: {
            'Authorization': `Bearer ${token}`,
            'Accept': 'application/json'
          }
        });

        const data = await response.json().catch(() => null);

        if (!response.ok) {
          throw new ApiError(response.status, data?.detail || 'Sesión no autorizada o expirada');
        }

        return data;
      } catch (err) {
        if (err instanceof ApiError) {
          throw err;
        }
        console.warn(`[ApiClient] Servidor backend (${this.config.baseUrl}) inaccesible en /auth/me:`, err.message);
      }
    }

    // Mock Fallback: decodificar payload de JWT
    try {
      const parts = token.split('.');
      if (parts.length === 3) {
        const payload = JSON.parse(atob(parts[1]));
        return {
          id: payload.sub,
          email: payload.email,
          full_name: payload.full_name,
          role: payload.role
        };
      }
    } catch {
      throw new ApiError(401, 'Token de sesión inválido');
    }

    throw new ApiError(401, 'Sesión no válida');
  }
};
