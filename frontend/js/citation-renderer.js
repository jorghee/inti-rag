/**
 * Safe DOM rendering for Markdown-formatted legal answers, inline statutory citations,
 * and normative inspector cards. Builds DOM nodes strictly via textContent (XSS-safe).
 */

const INLINE_TOKEN_REGEX =
  /(\[Código Civil,\s*Art\.\s*(?:[0-9]+[A-Za-z]?|[IVXLCDM]+)(?:[^\]]*)\]|\*\*[^*]+\*\*|\*[^*\n]+\*|`[^`]+`)/gi;

function buildCitationMap(citations) {
  const map = new Map();
  for (const cit of citations || []) {
    const rawKey = String(cit.article_number_raw || cit.article_number || '').toUpperCase();
    if (rawKey) {
      map.set(rawKey, cit);
    }
    if (cit.article_number !== undefined && cit.article_number !== null) {
      map.set(String(cit.article_number), cit);
    }
  }
  return map;
}

function appendInlineNodes(parent, text, citationMap, onSelectCitation) {
  const parts = String(text || '').split(INLINE_TOKEN_REGEX);
  for (const part of parts) {
    if (!part) continue;

    const citMatch = part.match(
      /^\[Código Civil,\s*Art\.\s*([0-9]+[A-Za-z]?|[IVXLCDM]+)(?:[^\]]*)\]$/i
    );
    if (citMatch) {
      const token = citMatch[1].toUpperCase();
      const matchedChunk = citationMap.get(token);
      if (matchedChunk) {
        const btn = document.createElement('button');
        btn.type = 'button';
        btn.className = 'citation-inline-btn';
        btn.textContent = part;
        btn.setAttribute('aria-label', `Inspeccionar ${part}`);
        btn.addEventListener('click', () => onSelectCitation(matchedChunk));
        parent.appendChild(btn);
        continue;
      }
    }

    if (part.startsWith('**') && part.endsWith('**') && part.length > 4) {
      const strong = document.createElement('strong');
      appendInlineNodes(strong, part.slice(2, -2), citationMap, onSelectCitation);
      parent.appendChild(strong);
      continue;
    }

    if (part.startsWith('*') && part.endsWith('*') && part.length > 2) {
      const em = document.createElement('em');
      appendInlineNodes(em, part.slice(1, -1), citationMap, onSelectCitation);
      parent.appendChild(em);
      continue;
    }

    if (part.startsWith('`') && part.endsWith('`') && part.length > 2) {
      const code = document.createElement('code');
      code.className = 'inline-code';
      code.textContent = part.slice(1, -1);
      parent.appendChild(code);
      continue;
    }

    parent.appendChild(document.createTextNode(part));
  }
}

/**
 * Render Markdown assistant answer with safe DOM elements and clickable citation buttons.
 * @param {HTMLElement} container
 * @param {string} answerText
 * @param {Array<Object>} citations
 * @param {Function} onSelectCitation
 */
export function renderAnswerWithCitations(container, answerText, citations, onSelectCitation) {
  container.textContent = '';
  const citationMap = buildCitationMap(citations);
  const lines = String(answerText || '').replace(/\r\n/g, '\n').split('\n');

  let activeList = null;
  let activeListType = null;
  let paragraphLines = [];

  function flushParagraph() {
    if (!paragraphLines.length) return;
    const p = document.createElement('p');
    appendInlineNodes(p, paragraphLines.join(' '), citationMap, onSelectCitation);
    container.appendChild(p);
    paragraphLines = [];
  }

  function closeList() {
    activeList = null;
    activeListType = null;
  }

  for (const rawLine of lines) {
    const trimmed = rawLine.trim();

    if (!trimmed) {
      flushParagraph();
      closeList();
      continue;
    }

    const headingMatch = trimmed.match(/^(#{1,4})\s+(.+)$/);
    if (headingMatch) {
      flushParagraph();
      closeList();
      const level = Math.min(headingMatch[1].length + 2, 5);
      const heading = document.createElement(`h${level}`);
      heading.className = 'md-heading';
      appendInlineNodes(heading, headingMatch[2], citationMap, onSelectCitation);
      container.appendChild(heading);
      continue;
    }

    const orderedMatch = rawLine.match(/^(\s*)\d+\.\s+(.+)$/);
    if (orderedMatch) {
      flushParagraph();
      const isNested = orderedMatch[1].length >= 2;
      if (activeListType !== 'ol' || !activeList) {
        activeList = document.createElement('ol');
        activeList.className = 'md-list md-list-ordered';
        container.appendChild(activeList);
        activeListType = 'ol';
      }
      const li = document.createElement('li');
      if (isNested) li.className = 'md-list-nested';
      appendInlineNodes(li, orderedMatch[2].trim(), citationMap, onSelectCitation);
      activeList.appendChild(li);
      continue;
    }

    const bulletMatch = rawLine.match(/^(\s*)[-*]\s+(.+)$/);
    if (bulletMatch) {
      flushParagraph();
      const isNested = bulletMatch[1].length >= 2;
      if (activeListType !== 'ul' || !activeList) {
        activeList = document.createElement('ul');
        activeList.className = 'md-list md-list-unordered';
        container.appendChild(activeList);
        activeListType = 'ul';
      }
      const li = document.createElement('li');
      if (isNested) li.className = 'md-list-nested';
      appendInlineNodes(li, bulletMatch[2].trim(), citationMap, onSelectCitation);
      activeList.appendChild(li);
      continue;
    }

    closeList();
    paragraphLines.push(trimmed);
  }

  flushParagraph();
}

/**
 * Render the normative inspector content for a selected statutory article.
 * @param {HTMLElement} container
 * @param {Object|null} citation
 */
export function renderInspectorCitation(container, citation) {
  container.textContent = '';

  if (!citation) {
    const empty = document.createElement('p');
    empty.className = 'inspector-empty';
    empty.textContent =
      'Seleccione cualquier cita normativa dentro de una respuesta para inspeccionar su jerarquía legal, texto oficial y enlace directo al SPIJ.';
    container.appendChild(empty);
    return;
  }

  const card = document.createElement('article');
  card.className = 'statute-card';

  const header = document.createElement('div');
  header.className = 'statute-card-header';

  const code = document.createElement('span');
  code.className = 'statute-article-code';
  const rawLabel = citation.article_number_raw || citation.article_number || 'N/A';
  code.textContent = `Código Civil — Art. ${rawLabel}`;
  header.appendChild(code);

  const scoreVal =
    typeof citation.semantic_similarity === 'number'
      ? citation.semantic_similarity
      : typeof citation.similarity_score === 'number'
        ? citation.similarity_score
        : null;
  if (scoreVal !== null) {
    const score = document.createElement('span');
    score.className = 'statute-score';
    score.textContent = `Similitud: ${(scoreVal * 100).toFixed(1)}%`;
    header.appendChild(score);
  }
  card.appendChild(header);

  if (citation.statutory_hierarchy) {
    const hierarchy = document.createElement('div');
    hierarchy.className = 'statute-hierarchy';
    hierarchy.textContent = citation.statutory_hierarchy;
    card.appendChild(hierarchy);
  }

  if (citation.raw_content) {
    const body = document.createElement('p');
    body.className = 'statute-text';
    body.textContent = citation.raw_content;
    card.appendChild(body);
  }

  if (citation.is_synthetic_template) {
    const warning = document.createElement('div');
    warning.className = 'status-banner is-visible is-warning';
    warning.textContent =
      'Aviso: este fragmento corresponde a texto de plantilla del espejo local y no al texto íntegro del SPIJ.';
    card.appendChild(warning);
  }

  if (citation.official_spij_url) {
    const link = document.createElement('a');
    link.className = 'statute-spij-link';
    link.href = citation.official_spij_url;
    link.target = '_blank';
    link.rel = 'noopener noreferrer';
    link.textContent = 'Verificar fuente oficial en SPIJ (MINJUS)';
    card.appendChild(link);
  }

  container.appendChild(card);
}
