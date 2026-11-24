/**
 * Dashboard controller for Inti Legal AI Assistant.
 * Manages authenticated session history (HU-06), grounded legal queries (HU-01 partial),
 * and the responsive normative citation inspector (desktop sidebar / mobile bottom sheet).
 */

import { ApiClient, ApiError } from './api-client.js';
import { AuthSession } from './auth-session.js';
import { renderAnswerWithCitations, renderInspectorCitation } from './citation-renderer.js';
import { Icons } from './icons.js';

const MOBILE_BREAKPOINT = 1024;

const state = {
  token: null,
  user: null,
  sessions: [],
  activeSessionId: null,
  activeLogs: [],
  isSubmitting: false
};

const dom = {
  userName: document.getElementById('user-display-name'),
  userRole: document.getElementById('user-display-role'),
  sidebarUserEmail: document.getElementById('sidebar-user-email'),
  btnLogout: document.getElementById('btn-logout'),
  btnOpenDrawer: document.getElementById('btn-open-drawer'),
  btnCloseDrawer: document.getElementById('btn-close-drawer'),
  btnCloseInspector: document.getElementById('btn-close-inspector'),
  btnNewSession: document.getElementById('btn-new-session'),
  backdrop: document.getElementById('overlay-backdrop'),
  sidebar: document.getElementById('sessions-sidebar'),
  inspector: document.getElementById('citation-inspector'),
  inspectorBody: document.getElementById('inspector-body'),
  sessionsList: document.getElementById('sessions-list'),
  researchTitle: document.getElementById('research-title'),
  statusBanner: document.getElementById('status-banner'),
  thread: document.getElementById('conversation-thread'),
  queryForm: document.getElementById('query-form'),
  queryInput: document.getElementById('legal-query-input'),
  btnSubmitQuery: document.getElementById('btn-submit-query')
};

function formatRole(role) {
  switch (role) {
    case 'student':
      return 'Estudiante de Derecho';
    case 'docent':
      return 'Docente Universitario';
    case 'faculty':
      return 'Personal Académico';
    case 'admin':
      return 'Administrador';
    default:
      return 'Miembro UNSA';
  }
}

function formatDate(isoString) {
  if (!isoString) return '';
  try {
    return new Intl.DateTimeFormat('es-PE', {
      day: '2-digit',
      month: 'short',
      hour: '2-digit',
      minute: '2-digit'
    }).format(new Date(isoString));
  } catch {
    return '';
  }
}

function showBanner(message, type = 'error') {
  if (!dom.statusBanner) return;
  dom.statusBanner.textContent = message;
  dom.statusBanner.className = `status-banner is-visible is-${type}`;
}

function hideBanner() {
  if (!dom.statusBanner) return;
  dom.statusBanner.textContent = '';
  dom.statusBanner.className = 'status-banner';
}

function closeAllOverlays() {
  dom.sidebar?.classList.remove('is-open');
  dom.inspector?.classList.remove('is-open');
  dom.backdrop?.classList.remove('is-visible');
  dom.btnOpenDrawer?.setAttribute('aria-expanded', 'false');
}

function openMobileDrawer() {
  dom.inspector?.classList.remove('is-open');
  dom.sidebar?.classList.add('is-open');
  dom.backdrop?.classList.add('is-visible');
  dom.btnOpenDrawer?.setAttribute('aria-expanded', 'true');
}

function openCitationInspector(citation) {
  renderInspectorCitation(dom.inspectorBody, citation);
  if (window.innerWidth < MOBILE_BREAKPOINT) {
    dom.sidebar?.classList.remove('is-open');
    dom.inspector?.classList.add('is-open');
    dom.backdrop?.classList.add('is-visible');
    dom.btnCloseInspector?.focus();
  }
}

function renderSessionsList() {
  if (!dom.sessionsList) return;
  dom.sessionsList.textContent = '';

  if (state.sessions.length === 0) {
    const empty = document.createElement('p');
    empty.className = 'loading-state-text';
    empty.textContent = 'Aún no tiene consultas registradas en su historial.';
    dom.sessionsList.appendChild(empty);
    return;
  }

  for (const session of state.sessions) {
    const btn = document.createElement('button');
    btn.type = 'button';
    btn.className = `session-item${session.id === state.activeSessionId ? ' is-active' : ''}`;
    btn.setAttribute('aria-current', session.id === state.activeSessionId ? 'true' : 'false');

    const title = document.createElement('span');
    title.className = 'session-item-title';
    title.textContent = session.session_title;

    const meta = document.createElement('span');
    meta.className = 'session-item-meta';
    const countLabel = session.query_count === 1 ? '1 consulta' : `${session.query_count} consultas`;
    meta.textContent = `${countLabel} · ${formatDate(session.last_active_at)}`;

    btn.appendChild(title);
    btn.appendChild(meta);
    btn.addEventListener('click', () => {
      selectSession(session.id);
      if (window.innerWidth < MOBILE_BREAKPOINT) {
        closeAllOverlays();
      }
    });
    dom.sessionsList.appendChild(btn);
  }
}

function renderEmptyThread() {
  dom.thread.textContent = '';

  const card = document.createElement('section');
  card.className = 'empty-state';

  const heading = document.createElement('h2');
  heading.className = 'empty-state-heading';
  heading.textContent = 'Mesa de Consulta Normativa — Código Civil de 1984';

  const body = document.createElement('p');
  body.className = 'empty-state-body';
  body.textContent =
    'Formule una consulta jurídica en lenguaje natural. Inti recuperará los artículos pertinentes mediante búsqueda híbrida y guardará el análisis en su historial institucional.';

  const samples = document.createElement('div');
  samples.className = 'sample-queries';

  const sampleQuestions = [
    '¿Qué establece el artículo 1969 del Código Civil sobre responsabilidad extracontractual?',
    '¿Cuáles son las causales de nulidad del acto jurídico según el artículo 219?',
    '¿Qué obliga al vendedor y al comprador en un contrato de compraventa?'
  ];

  for (const q of sampleQuestions) {
    const btn = document.createElement('button');
    btn.type = 'button';
    btn.className = 'sample-query-btn';
    btn.textContent = q;
    btn.addEventListener('click', () => {
      dom.queryInput.value = q;
      dom.queryInput.focus();
    });
    samples.appendChild(btn);
  }

  card.appendChild(heading);
  card.appendChild(body);
  card.appendChild(samples);
  dom.thread.appendChild(card);
}

function renderThread() {
  if (!state.activeLogs.length) {
    renderEmptyThread();
    return;
  }

  dom.thread.textContent = '';
  for (const turn of state.activeLogs) {
    const article = document.createElement('article');
    article.className = 'turn-card';

    const qBlock = document.createElement('div');
    qBlock.className = 'turn-question';
    const qLabel = document.createElement('span');
    qLabel.className = 'turn-label';
    qLabel.textContent = 'Consulta formulada';
    const qText = document.createElement('p');
    qText.className = 'turn-question-text';
    qText.textContent = turn.user_query;
    qBlock.appendChild(qLabel);
    qBlock.appendChild(qText);
    article.appendChild(qBlock);

    const aBlock = document.createElement('div');
    aBlock.className = 'turn-answer';
    const aLabel = document.createElement('span');
    aLabel.className = 'turn-label';
    aLabel.textContent = 'Respuesta fundamentada';
    const aBody = document.createElement('div');
    aBody.className = 'turn-answer-body';
    renderAnswerWithCitations(aBody, turn.assistant_response, turn.citations || [], openCitationInspector);
    aBlock.appendChild(aLabel);
    aBlock.appendChild(aBody);

    if (turn.citations && turn.citations.length > 0) {
      const citBar = document.createElement('div');
      citBar.className = 'turn-citations-bar';

      const citLabel = document.createElement('span');
      citLabel.className = 'turn-label';
      citLabel.textContent = 'Fuentes verificadas:';
      citBar.appendChild(citLabel);

      for (const cit of turn.citations) {
        const pill = document.createElement('button');
        pill.type = 'button';
        pill.className = 'citation-inline-btn';
        const artLabel = cit.article_number_raw || cit.article_number;
        pill.textContent = `Art. ${artLabel}`;
        pill.addEventListener('click', () => openCitationInspector(cit));
        citBar.appendChild(pill);
      }
      aBlock.appendChild(citBar);
    }

    article.appendChild(aBlock);

    const meta = document.createElement('footer');
    meta.className = 'turn-meta';

    const badge = document.createElement('span');
    const isRefusal =
      turn.model_used === 'refusal-guardrail' || turn.model_used === 'synthetic-template-guardrail';
    badge.className = isRefusal ? 'meta-pill-refusal' : 'meta-pill-grounded';
    badge.textContent = isRefusal ? 'Sin respaldo suficiente' : 'Fundamentado en corpus';
    meta.appendChild(badge);

    const modelSpan = document.createElement('span');
    modelSpan.textContent = `Modelo: ${turn.model_used}`;
    meta.appendChild(modelSpan);

    if (typeof turn.response_latency_ms === 'number') {
      const latSpan = document.createElement('span');
      latSpan.textContent = `Latencia: ${Math.round(turn.response_latency_ms)} ms`;
      meta.appendChild(latSpan);
    }

    article.appendChild(meta);
    dom.thread.appendChild(article);
  }
}

async function loadSessions() {
  if (!dom.sessionsList) return;
  dom.sessionsList.textContent = '';
  const loading = document.createElement('p');
  loading.className = 'loading-state-text';
  loading.textContent = 'Cargando historial de sesiones...';
  dom.sessionsList.appendChild(loading);

  try {
    state.sessions = await ApiClient.listSessions(state.token);
    renderSessionsList();
  } catch (err) {
    dom.sessionsList.textContent = '';
    const errText = document.createElement('p');
    errText.className = 'loading-state-text';
    errText.textContent = 'Historial no disponible en este momento.';
    dom.sessionsList.appendChild(errText);
    if (err instanceof ApiError && err.status === 401) {
      AuthSession.clearSession();
      window.location.replace('index.html');
      return;
    }
    showBanner(err.message || 'No se pudo cargar el historial desde el servidor.', 'error');
  }
}

async function selectSession(sessionId) {
  hideBanner();
  state.activeSessionId = sessionId;
  renderSessionsList();

  dom.thread.textContent = '';
  const loading = document.createElement('p');
  loading.className = 'loading-state-text';
  loading.textContent = 'Recuperando expediente de consultas...';
  dom.thread.appendChild(loading);

  try {
    const detail = await ApiClient.getSession(state.token, sessionId);
    state.activeLogs = detail.logs || [];
    dom.researchTitle.textContent = detail.session_title;
    renderThread();

    const lastWithCitation = [...state.activeLogs]
      .reverse()
      .find((log) => log.citations && log.citations.length > 0);
    renderInspectorCitation(
      dom.inspectorBody,
      lastWithCitation ? lastWithCitation.citations[0] : null
    );
  } catch (err) {
    showBanner(err.message || 'No se pudo recuperar el detalle de la sesión.', 'error');
    renderEmptyThread();
  }
}

function startNewSession() {
  hideBanner();
  state.activeSessionId = null;
  state.activeLogs = [];
  dom.researchTitle.textContent = 'Nueva consulta jurídica';
  renderSessionsList();
  renderEmptyThread();
  renderInspectorCitation(dom.inspectorBody, null);
  if (window.innerWidth < MOBILE_BREAKPOINT) {
    closeAllOverlays();
  }
  dom.queryInput?.focus();
}

async function handleQuerySubmit(event) {
  event.preventDefault();
  if (state.isSubmitting) return;

  const query = dom.queryInput.value.trim();
  if (query.length < 3) {
    showBanner('Ingrese una consulta jurídica de al menos 3 caracteres.', 'warning');
    dom.queryInput.focus();
    return;
  }

  hideBanner();
  state.isSubmitting = true;
  dom.btnSubmitQuery.disabled = true;
  dom.btnSubmitQuery.textContent = 'Consultando corpus...';

  try {
    const result = await ApiClient.executeQuery(state.token, {
      query,
      sessionId: state.activeSessionId,
      topK: 5
    });

    dom.queryInput.value = '';
    state.activeSessionId = result.session_id;

    state.activeLogs.push({
      id: result.query_log_id,
      session_id: result.session_id,
      user_query: result.query,
      assistant_response: result.answer,
      response_latency_ms: result.response_latency_ms,
      model_used: result.model_used,
      citations: result.citations || []
    });

    if (result.contains_synthetic_chunks && !result.out_of_scope) {
      showBanner(
        'Algunos candidatos recuperados pertenecen al espejo sintético; se priorizaron artículos con texto normativo íntegro.',
        'warning'
      );
    }

    renderThread();
    if (result.citations && result.citations.length > 0) {
      renderInspectorCitation(dom.inspectorBody, result.citations[0]);
    }
    await loadSessions();
  } catch (err) {
    if (err instanceof ApiError && err.status === 401) {
      AuthSession.clearSession();
      window.location.replace('index.html');
      return;
    }
    showBanner(err.message || 'Ocurrió un error al consultar el asistente jurídico.', 'error');
  } finally {
    state.isSubmitting = false;
    dom.btnSubmitQuery.disabled = false;
    dom.btnSubmitQuery.textContent = 'Consultar Asistente';
  }
}

function hydrateIcons() {
  document.querySelectorAll('[data-icon]').forEach((el) => {
    const key = el.getAttribute('data-icon');
    if (Icons[key]) {
      el.innerHTML = Icons[key];
    }
  });
}

function init() {
  if (!AuthSession.isAuthenticated()) {
    window.location.replace('index.html');
    return;
  }

  state.user = AuthSession.getUser();
  state.token = AuthSession.getToken();

  hydrateIcons();

  if (state.user) {
    const displayName = state.user.full_name || state.user.email.split('@')[0];
    dom.userName.textContent = displayName;
    dom.userRole.textContent = formatRole(state.user.role);
    dom.sidebarUserEmail.textContent = state.user.email;
  }

  renderEmptyThread();
  renderInspectorCitation(dom.inspectorBody, null);

  dom.btnLogout?.addEventListener('click', () => {
    AuthSession.clearSession();
    window.location.replace('index.html');
  });
  dom.btnOpenDrawer?.addEventListener('click', openMobileDrawer);
  dom.btnCloseDrawer?.addEventListener('click', closeAllOverlays);
  dom.btnCloseInspector?.addEventListener('click', closeAllOverlays);
  dom.backdrop?.addEventListener('click', closeAllOverlays);
  dom.btnNewSession?.addEventListener('click', startNewSession);
  dom.queryForm?.addEventListener('submit', handleQuerySubmit);

  document.addEventListener('keydown', (event) => {
    if (event.key === 'Escape') {
      closeAllOverlays();
    }
  });

  loadSessions();
}

init();
