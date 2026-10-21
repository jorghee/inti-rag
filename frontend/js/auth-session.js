/**
 * Módulo de Gestión de Sesión y Persistencia de Autenticación (TASK-05.4)
 * Inti — Asistente Jurídico Inteligente (Facultad de Derecho, UNSA)
 * 
 * Gestiona el almacenamiento del token JWT, perfil de usuario y estado de expiración
 * en localStorage (para "Recordar dispositivo") o sessionStorage (para sesión volátil).
 */

const STORAGE_KEYS = {
  TOKEN: 'inti_access_token',
  USER: 'inti_user_profile',
  EXPIRY: 'inti_token_expiry',
  REMEMBER: 'inti_remember_me'
};

export const AuthSession = {
  /**
   * Guarda los datos de autenticación obtenidos del backend / mock.
   * @param {Object} params
   * @param {string} params.accessToken - Token JWT de acceso
   * @param {Object} params.user - Objeto de usuario { id, email, full_name, role }
   * @param {number} [params.expiresIn=3600] - Tiempo de validez en segundos
   * @param {boolean} [params.remember=true] - Si persiste tras cerrar navegador
   */
  saveSession({ accessToken, user, expiresIn = 3600, remember = true }) {
    this.clearSession(); // Limpia almacenamiento previo

    const storage = remember ? localStorage : sessionStorage;
    const expiryTimestamp = Date.now() + expiresIn * 1000;

    storage.setItem(STORAGE_KEYS.TOKEN, accessToken);
    storage.setItem(STORAGE_KEYS.USER, JSON.stringify(user));
    storage.setItem(STORAGE_KEYS.EXPIRY, expiryTimestamp.toString());
    storage.setItem(STORAGE_KEYS.REMEMBER, remember ? 'true' : 'false');
  },

  /**
   * Obtiene el token JWT si está vigente. Si ha expirado, limpia la sesión y retorna null.
   * @returns {string|null}
   */
  getToken() {
    const token = localStorage.getItem(STORAGE_KEYS.TOKEN) || sessionStorage.getItem(STORAGE_KEYS.TOKEN);
    const expiry = localStorage.getItem(STORAGE_KEYS.EXPIRY) || sessionStorage.getItem(STORAGE_KEYS.EXPIRY);

    if (!token) return null;

    if (expiry && Date.now() > parseInt(expiry, 10)) {
      this.clearSession();
      return null;
    }

    return token;
  },

  /**
   * Obtiene el perfil del usuario autenticado.
   * @returns {Object|null}
   */
  getUser() {
    if (!this.getToken()) return null;

    const raw = localStorage.getItem(STORAGE_KEYS.USER) || sessionStorage.getItem(STORAGE_KEYS.USER);
    if (!raw) return null;

    try {
      return JSON.parse(raw);
    } catch {
      return null;
    }
  },

  /**
   * Verifica si existe una sesión activa y vigente.
   * @returns {boolean}
   */
  isAuthenticated() {
    return Boolean(this.getToken());
  },

  /**
   * Genera el encabezado Authorization para peticiones protegidas.
   * @returns {Object}
   */
  getAuthHeader() {
    const token = this.getToken();
    return token ? { Authorization: `Bearer ${token}` } : {};
  },

  /**
   * Elimina todos los datos de autenticación de ambos almacenamientos.
   */
  clearSession() {
    [localStorage, sessionStorage].forEach(store => {
      store.removeItem(STORAGE_KEYS.TOKEN);
      store.removeItem(STORAGE_KEYS.USER);
      store.removeItem(STORAGE_KEYS.EXPIRY);
      store.removeItem(STORAGE_KEYS.REMEMBER);
    });
  }
};
