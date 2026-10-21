import { Icons } from './icons.js';
import { ApiClient } from './api-client.js';
import { AuthSession } from './auth-session.js';

let switchTabFn = null;

document.addEventListener('DOMContentLoaded', () => {
  // Redirección si ya cuenta con una sesión activa vigente
  if (AuthSession.isAuthenticated()) {
    window.location.replace('dashboard.html');
    return;
  }

  // Inicialización de iconos en el DOM
  initStaticIcons();

  // Gestión de pestañas (Tabs)
  initTabSwitching();

  // Control de visibilidad de contraseñas (Toggle Password)
  initPasswordToggles();

  // Validaciones y conexión con el API Client
  initLoginFormValidation();
  initRegisterFormValidation();
});

/**
 * Inserta los iconos vectoriales SVG en los contenedores designados
 */
function initStaticIcons() {
  document.querySelectorAll('[data-icon]').forEach(el => {
    const iconName = el.getAttribute('data-icon');
    if (Icons[iconName]) {
      el.innerHTML = Icons[iconName];
    }
  });
}

/**
 * Control de navegación entre Pestaña Login y Pestaña Registro
 */
function initTabSwitching() {
  const tabLogin = document.getElementById('tab-login');
  const tabRegister = document.getElementById('tab-register');
  const panelLogin = document.getElementById('panel-login');
  const panelRegister = document.getElementById('panel-register');
  const alertBanner = document.getElementById('global-alert');

  function switchTab(target) {
    clearAlert(alertBanner);
    if (target === 'login') {
      tabLogin.classList.add('active');
      tabLogin.setAttribute('aria-selected', 'true');
      tabRegister.classList.remove('active');
      tabRegister.setAttribute('aria-selected', 'false');

      panelLogin.classList.add('active');
      panelRegister.classList.remove('active');
      document.getElementById('login-email')?.focus();
    } else {
      tabRegister.classList.add('active');
      tabRegister.setAttribute('aria-selected', 'true');
      tabLogin.classList.remove('active');
      tabLogin.setAttribute('aria-selected', 'false');

      panelRegister.classList.add('active');
      panelLogin.classList.remove('active');
      document.getElementById('reg-name')?.focus();
    }
  }

  switchTabFn = switchTab;

  tabLogin?.addEventListener('click', () => switchTab('login'));
  tabRegister?.addEventListener('click', () => switchTab('register'));

  // Enlaces directos dentro de los formularios
  document.querySelectorAll('[data-switch-tab]').forEach(btn => {
    btn.addEventListener('click', (e) => {
      e.preventDefault();
      switchTab(btn.getAttribute('data-switch-tab'));
    });
  });
}

/**
 * Alterna visibilidad de campos de contraseña mediante iconos SVG
 */
function initPasswordToggles() {
  document.querySelectorAll('.btn-toggle-password').forEach(btn => {
    btn.innerHTML = Icons.eye;
    btn.setAttribute('aria-label', 'Mostrar contraseña');

    btn.addEventListener('click', () => {
      const targetId = btn.getAttribute('data-target');
      const input = document.getElementById(targetId);
      if (!input) return;

      const isPassword = input.getAttribute('type') === 'password';
      if (isPassword) {
        input.setAttribute('type', 'text');
        btn.innerHTML = Icons.eyeOff;
        btn.setAttribute('aria-label', 'Ocultar contraseña');
      } else {
        input.setAttribute('type', 'password');
        btn.innerHTML = Icons.eye;
        btn.setAttribute('aria-label', 'Mostrar contraseña');
      }
    });
  });
}

/**
 * Regex oficial para validar dominio institucional @unsa.edu.pe
 */
const UNSA_EMAIL_REGEX = /^[a-zA-Z0-9._%+-]+@unsa\.edu\.pe$/;

/**
 * Validación y submit del Formulario de Login conectado a ApiClient y AuthSession (TASK-05.4)
 */
function initLoginFormValidation() {
  const form = document.getElementById('form-login');
  if (!form) return;

  const emailInput = document.getElementById('login-email');
  const passInput = document.getElementById('login-password');
  const rememberCheckbox = document.getElementById('remember-me');
  const alertBanner = document.getElementById('global-alert');
  const submitBtn = form.querySelector('.btn-submit');

  emailInput?.addEventListener('input', () => validateEmailField(emailInput));
  emailInput?.addEventListener('blur', () => validateEmailField(emailInput));

  passInput?.addEventListener('input', () => validateRequiredField(passInput, 'Ingrese su contraseña'));
  passInput?.addEventListener('blur', () => validateRequiredField(passInput, 'Ingrese su contraseña'));

  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    clearAlert(alertBanner);

    const isEmailValid = validateEmailField(emailInput);
    const isPassValid = validateRequiredField(passInput, 'Ingrese su contraseña institucional');

    if (!isEmailValid || !isPassValid) {
      showAlert(alertBanner, 'Por favor, corrija los campos marcados en rojo antes de continuar.', 'error');
      return;
    }

    setButtonLoading(submitBtn, true, 'Iniciando sesión...');

    try {
      const email = emailInput.value.trim();
      const password = passInput.value;
      const remember = rememberCheckbox ? rememberCheckbox.checked : true;

      // Consumo de endpoint POST /api/v1/auth/login con fallback mock
      const sessionData = await ApiClient.login({ email, password });

      // Persistencia segura de sesión
      AuthSession.saveSession({
        accessToken: sessionData.access_token,
        user: sessionData.user,
        expiresIn: sessionData.expires_in,
        remember
      });

      showAlert(
        alertBanner,
        `¡Bienvenido(a), ${sessionData.user.full_name}! Redirigiendo al Asistente Jurídico...`,
        'success'
      );

      // Redirección suave al Dashboard
      setTimeout(() => {
        window.location.replace('dashboard.html');
      }, 750);

    } catch (err) {
      setButtonLoading(submitBtn, false, 'Iniciar Sesión');
      showAlert(
        alertBanner,
        err.detail || err.message || 'Error en las credenciales o servidor no disponible.',
        'error'
      );
    }
  });
}

/**
 * Validación y submit del Formulario de Registro conectado a ApiClient (TASK-05.4)
 */
function initRegisterFormValidation() {
  const form = document.getElementById('form-register');
  if (!form) return;

  const nameInput = document.getElementById('reg-name');
  const emailInput = document.getElementById('reg-email');
  const roleSelect = document.getElementById('reg-role');
  const passInput = document.getElementById('reg-password');
  const passConfirmInput = document.getElementById('reg-password-confirm');
  const termsCheckbox = document.getElementById('reg-terms');
  const alertBanner = document.getElementById('global-alert');
  const submitBtn = form.querySelector('.btn-submit');

  // Elementos del checklist de requisitos
  const reqLen = document.getElementById('req-len');
  const reqUpper = document.getElementById('req-upper');
  const reqNum = document.getElementById('req-num');
  const reqSpecial = document.getElementById('req-special');

  nameInput?.addEventListener('input', () => validateRequiredField(nameInput, 'Ingrese sus nombres y apellidos completos'));
  emailInput?.addEventListener('input', () => validateEmailField(emailInput));
  emailInput?.addEventListener('blur', () => validateEmailField(emailInput));
  roleSelect?.addEventListener('change', () => validateRequiredField(roleSelect, 'Seleccione un rol académico'));

  passInput?.addEventListener('input', () => {
    const val = passInput.value;
    const hasLen = val.length >= 8;
    const hasUpper = /[A-Z]/.test(val);
    const hasNum = /[0-9]/.test(val);
    const hasSpecial = /[^a-zA-Z0-9]/.test(val);

    updateRequirementItem(reqLen, hasLen);
    updateRequirementItem(reqUpper, hasUpper);
    updateRequirementItem(reqNum, hasNum);
    updateRequirementItem(reqSpecial, hasSpecial);

    if (passConfirmInput.value) {
      validatePasswordMatch(passInput, passConfirmInput);
    }
  });

  passConfirmInput?.addEventListener('input', () => validatePasswordMatch(passInput, passConfirmInput));
  passConfirmInput?.addEventListener('blur', () => validatePasswordMatch(passInput, passConfirmInput));

  termsCheckbox?.addEventListener('change', () => {
    const group = termsCheckbox.closest('.form-group');
    if (!termsCheckbox.checked) {
      showFieldError(group, 'Debe aceptar los términos de uso ético y académico');
    } else {
      clearFieldError(group);
    }
  });

  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    clearAlert(alertBanner);

    const isNameValid = validateRequiredField(nameInput, 'Ingrese sus nombres y apellidos completos');
    const isEmailValid = validateEmailField(emailInput);
    const isRoleValid = validateRequiredField(roleSelect, 'Seleccione un rol académico');
    const isPassValid = validateFullPassword(passInput);
    const isMatchValid = validatePasswordMatch(passInput, passConfirmInput);
    const isTermsValid = termsCheckbox ? termsCheckbox.checked : true;

    if (!isTermsValid) {
      showFieldError(termsCheckbox.closest('.form-group'), 'Debe aceptar los términos de uso ético y académico');
    }

    if (!isNameValid || !isEmailValid || !isRoleValid || !isPassValid || !isMatchValid || !isTermsValid) {
      showAlert(alertBanner, 'Por favor, revise los errores indicados en el formulario.', 'error');
      return;
    }

    setButtonLoading(submitBtn, true, 'Registrando cuenta institucional...');

    try {
      const name = nameInput.value.trim();
      const email = emailInput.value.trim();
      const role = roleSelect.value;
      const password = passInput.value;

      // Consumo de endpoint POST /api/v1/auth/register con fallback mock
      const registered = await ApiClient.register({
        email,
        password,
        full_name: name,
        role
      });

      setButtonLoading(submitBtn, false, 'Crear Cuenta');
      showAlert(
        alertBanner,
        `¡Cuenta creada exitosamente para ${registered.email}! Proceda a iniciar sesión.`,
        'success'
      );

      form.reset();
      resetPasswordRequirements();

      // Transición automática a la pestaña de inicio de sesión
      setTimeout(() => {
        if (switchTabFn) {
          switchTabFn('login');
          const loginEmail = document.getElementById('login-email');
          if (loginEmail) {
            loginEmail.value = registered.email;
            document.getElementById('login-password')?.focus();
          }
        }
      }, 1200);

    } catch (err) {
      setButtonLoading(submitBtn, false, 'Crear Cuenta');
      showAlert(
        alertBanner,
        err.detail || err.message || 'Error al procesar el registro.',
        'error'
      );
    }
  });
}

function validateEmailField(input) {
  const group = input.closest('.form-group');
  const val = input.value.trim();

  if (!val) {
    showFieldError(group, 'El correo institucional es obligatorio');
    return false;
  }

  if (!UNSA_EMAIL_REGEX.test(val)) {
    showFieldError(group, 'Acceso restringido: El correo debe terminar estrictamente en @unsa.edu.pe');
    return false;
  }

  clearFieldError(group);
  return true;
}

function validateRequiredField(input, message) {
  const group = input.closest('.form-group');
  const val = input.value.trim();

  if (!val) {
    showFieldError(group, message);
    return false;
  }

  clearFieldError(group);
  return true;
}

function validateFullPassword(input) {
  const group = input.closest('.form-group');
  const val = input.value;

  const valid = val.length >= 8 && /[A-Z]/.test(val) && /[0-9]/.test(val) && /[^a-zA-Z0-9]/.test(val);

  if (!valid) {
    showFieldError(group, 'La contraseña no cumple con todos los requisitos de seguridad');
    return false;
  }

  clearFieldError(group);
  return true;
}

function validatePasswordMatch(passInput, confirmInput) {
  const group = confirmInput.closest('.form-group');
  if (confirmInput.value !== passInput.value || !confirmInput.value) {
    showFieldError(group, 'Las contraseñas no coinciden');
    return false;
  }

  clearFieldError(group);
  return true;
}

function updateRequirementItem(el, isValid) {
  if (!el) return;
  if (isValid) {
    el.classList.add('valid');
    el.querySelector('.req-icon').innerHTML = Icons.check;
  } else {
    el.classList.remove('valid');
    el.querySelector('.req-icon').innerHTML = Icons.alertCircle;
  }
}

function resetPasswordRequirements() {
  ['req-len', 'req-upper', 'req-num', 'req-special'].forEach(id => {
    const el = document.getElementById(id);
    if (el) {
      el.classList.remove('valid');
      el.querySelector('.req-icon').innerHTML = Icons.alertCircle;
    }
  });
}

function showFieldError(group, message) {
  if (!group) return;
  group.classList.add('has-error');
  const msgEl = group.querySelector('.field-error-msg');
  if (msgEl) {
    msgEl.innerHTML = `${Icons.alertCircle} <span>${message}</span>`;
  }
}

function clearFieldError(group) {
  if (!group) return;
  group.classList.remove('has-error');
  const msgEl = group.querySelector('.field-error-msg');
  if (msgEl) {
    msgEl.innerHTML = '';
  }
}

function showAlert(banner, message, type) {
  if (!banner) return;
  banner.className = `alert-banner active alert-${type}`;
  const icon = type === 'error' ? Icons.alertCircle : Icons.check;
  banner.innerHTML = `${icon} <div>${message}</div>`;
}

function clearAlert(banner) {
  if (!banner) return;
  banner.className = 'alert-banner';
  banner.innerHTML = '';
}

function setButtonLoading(button, isLoading, text) {
  if (!button) return;
  if (isLoading) {
    button.disabled = true;
    button.innerHTML = `${Icons.spinner} <span>${text}</span>`;
  } else {
    button.disabled = false;
    button.innerHTML = `<span>${text}</span>`;
  }
}
