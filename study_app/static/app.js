const app = document.querySelector("#app");
const connectionState = document.querySelector("#connection-state");
const toast = document.querySelector("#toast");

const state = {
  catalog: { modules: [] },
  progress: null,
  session: null,
  errors: { items: [] },
  history: [],
  lastSubmitted: null,
  draftTimer: null,
  online: false,
};

const statusLabels = {
  locked: "bloqueado",
  available: "disponible",
  in_progress: "en curso",
  submitted: "enviado",
  recovery: "recuperación",
  review: "revisión",
  mastered: "dominado",
};

function escapeHtml(value = "") {
  return String(value).replace(/[&<>'"]/g, (character) => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", "'": "&#39;", '"': "&quot;",
  }[character]));
}

function formatDate(value) {
  if (!value) return "sin fecha";
  return new Intl.DateTimeFormat("es-AR", { dateStyle: "medium", timeStyle: "short" }).format(new Date(value));
}

function setConnection(online) {
  state.online = online;
  connectionState.classList.toggle("online", online);
  connectionState.classList.toggle("offline", !online);
  connectionState.innerHTML = `<span class="state-dot"></span> ${online ? "servidor local" : "modo local"}`;
}

function showToast(message) {
  toast.textContent = message;
  toast.classList.add("visible");
  window.clearTimeout(showToast.timer);
  showToast.timer = window.setTimeout(() => toast.classList.remove("visible"), 2800);
}

async function api(path, options = {}) {
  const response = await fetch(path, {
    headers: { "Content-Type": "application/json", ...(options.headers || {}) },
    ...options,
  });
  const data = await response.json().catch(() => ({}));
  if (!response.ok) throw new Error(data.error || `Error ${response.status}`);
  setConnection(true);
  return data;
}

async function loadAppState() {
  try {
    const [catalog, progress, session, errors] = await Promise.all([
      api("/api/catalog"), api("/api/progress"), api("/api/session"), api("/api/errors"),
    ]);
    state.catalog = catalog;
    state.progress = progress;
    state.session = session;
    state.errors = errors;
    setConnection(true);
  } catch (error) {
    setConnection(false);
    app.innerHTML = `<section class="error-box"><strong>No pude conectar con la ruta guiada.</strong><p>${escapeHtml(error.message)}</p><p>Podés seguir escribiendo borradores locales, pero iniciá el servidor con <code>uv run python scripts/run_study_app.py</code> para guardar intentos.</p></section>`;
    return;
  }
  renderRoute();
}

function moduleState(moduleId) {
  return state.progress?.modules?.[moduleId] || { status: "locked" };
}

function activeModule() {
  return state.catalog.modules.find((module) => module.id === state.progress?.current_module) || state.catalog.modules[0];
}

function renderRoute() {
  const route = window.location.hash || "#/";
  document.querySelectorAll(".primary-nav a").forEach((link) => link.classList.toggle("active", link.getAttribute("href") === route.split("/").slice(0, 2).join("/") || (route === "#/" && link.getAttribute("href") === "#/")));
  if (route.startsWith("#/lesson/")) return renderLesson(state, route.split("/")[2]);
  if (route.startsWith("#/feedback/")) return renderFeedback(route.split("/")[2]);
  if (route === "#/history") return renderHistory(state);
  if (route === "#/defense") return renderDefense(state);
  renderDashboard(state);
}

function renderDashboard(current) {
  const active = activeModule();
  const activeProgress = moduleState(active.id);
  const mastered = current.catalog.modules.filter((module) => moduleState(module.id).status === "mastered").length;
  const list = current.catalog.modules.map((module) => {
    const progress = moduleState(module.id);
    const locked = progress.status === "locked";
    const href = locked ? "#" : `#/lesson/${module.id}`;
    return `<a class="module-item ${progress.status} ${module.id === active.id ? "active" : ""}" href="${href}" data-module-id="${module.id}" ${locked ? 'aria-disabled="true"' : ""}>
      <span class="module-number">0${module.order}</span><span class="module-title">${escapeHtml(module.title)}</span><span class="module-status">${statusLabels[progress.status] || progress.status}</span>
    </a>`;
  }).join("");
  app.innerHTML = `<div class="dashboard-head">
    <div><div class="eyebrow">Ruta guiada · siguiente acción</div><h1>Aprendé para poder defenderlo.</h1><p class="lede">Una sesión activa, una respuesta concreta y una devolución que decide el próximo paso. Tu progreso no se mide por cuánto leés, sino por lo que podés reconstruir.</p></div>
    <div class="progress-stamp"><span>avance de módulos</span><strong>${mastered} / ${current.catalog.modules.length}</strong><span>dominio registrado</span></div>
  </div>
  <div class="dashboard-grid">
    <section class="panel panel-pad"><div class="panel-heading"><h3>Mapa de estudio</h3><span>8 módulos</span></div><div class="module-list">${list}</div><p class="module-reason"><strong>Ahora:</strong> ${escapeHtml(activeProgress.status === "locked" ? "completá el prerrequisito anterior" : `trabajá ${active.title}`)}.</p></section>
    <section class="panel panel-pad"><div class="active-kicker"><span>módulo ${String(active.order).padStart(2, "0")}</span><strong>${statusLabels[activeProgress.status]}</strong></div><div class="eyebrow">${escapeHtml(active.title)}</div><h2 class="active-question">${escapeHtml(active.prompt.question)}</h2><p class="lede">No necesitás escribir una respuesta perfecta. Necesitás hacer visible tu modelo mental para que podamos corregirlo juntos.</p><div class="action-row" style="margin-top: 28px"><a class="button" href="#/lesson/${active.id}">Abrir sesión</a><a class="button secondary" href="${escapeHtml(`/${active.source}`)}" target="_blank" rel="noreferrer">Ver capítulo</a></div></section>
  </div>`;
  app.querySelectorAll('[aria-disabled="true"]').forEach((link) => link.addEventListener("click", (event) => event.preventDefault()));
}

function localDraft(moduleId) {
  try { return JSON.parse(localStorage.getItem(`study-draft:${moduleId}`) || "null"); } catch { return null; }
}

function renderLesson(current, moduleId) {
  const module = current.catalog.modules.find((item) => item.id === moduleId) || activeModule();
  const progress = moduleState(module.id);
  if (progress.status === "locked") return renderDashboard(current);
  const draft = current.session?.draft?.module_id === module.id ? current.session.draft : localDraft(module.id);
  const source = `/${module.source}`;
  app.innerHTML = `<div class="eyebrow">Sesión guiada · módulo ${String(module.order).padStart(2, "0")}</div><div class="lesson-layout">
    <section class="panel panel-pad"><div class="lesson-meta"><span>${escapeHtml(module.title)}</span><span>estado: ${statusLabels[progress.status]}</span><a href="${escapeHtml(source)}" target="_blank" rel="noreferrer">abrir material ↗</a></div><h1 class="prompt-copy">${escapeHtml(module.prompt.question)}</h1><label class="response-label" for="response-editor">Tu explicación</label><textarea id="response-editor" maxlength="12000" placeholder="Escribí con tus palabras. Podés incluir fórmulas, cuentas o una duda concreta.">${escapeHtml(draft?.body || "")}</textarea><div class="editor-footer"><span id="saved-status" class="saved-status">${draft ? "borrador recuperado" : "todavía no guardado"}</span><span id="char-count">0 caracteres</span></div><div class="help-row"><label for="help-level">Nivel de ayuda usado</label><select id="help-level"><option value="none">Intento sin ayuda</option><option value="hint-1">Pista inicial</option><option value="hint-2">Ejemplo parcial</option><option value="full">Explicación completa</option></select></div><div class="action-row"><button class="button" id="submit-attempt" type="button">Enviar respuesta</button><a class="button secondary" href="#/">Volver al mapa</a></div></section>
    <aside class="side-stack"><section class="side-card"><h3>Qué voy a mirar</h3><ul class="rubric-list">${Object.keys(module.prompt.rubric).map((capability) => `<li>${escapeHtml(capabilityLabel(capability))}</li>`).join("")}</ul></section><section class="side-card context-note"><strong>Regla de la ruta:</strong><br>si falta un prerrequisito, no repetimos todo. Te doy una recuperación concreta y volvemos a intentarlo.</section></aside>
  </div>`;
  const editor = document.querySelector("#response-editor");
  const savedStatus = document.querySelector("#saved-status");
  const count = document.querySelector("#char-count");
  const updateCount = () => { count.textContent = `${editor.value.length} caracteres`; };
  const save = () => saveDraft(module.id, editor.value, savedStatus);
  editor.addEventListener("input", () => { updateCount(); window.clearTimeout(state.draftTimer); state.draftTimer = window.setTimeout(save, 400); });
  updateCount();
  document.querySelector("#submit-attempt").addEventListener("click", () => submitAttempt(module.id, module.prompt.prompt_id, editor.value, document.querySelector("#help-level").value));
}

function capabilityLabel(capability) {
  return { explain: "Explicar el mecanismo sin apuntes", calculate: "Calcular la relación central", connect: "Conectar con tesis, código o figura", defend: "Defenderlo ante una repregunta" }[capability] || capability;
}

function saveDraft(moduleId, body, statusElement) {
  const draft = { module_id: moduleId, body };
  localStorage.setItem(`study-draft:${moduleId}`, JSON.stringify(draft));
  statusElement.textContent = "guardando...";
  api("/api/draft", { method: "POST", body: JSON.stringify(draft) }).then(() => { statusElement.textContent = "borrador guardado"; }).catch(() => { statusElement.textContent = "guardado localmente"; setConnection(false); });
}

async function submitAttempt(moduleId, promptId, body, helpLevel) {
  if (!body.trim()) { showToast("Escribí una respuesta antes de enviarla."); return; }
  const button = document.querySelector("#submit-attempt");
  button.disabled = true;
  try {
    const attempt = await api("/api/attempts", { method: "POST", body: JSON.stringify({ module_id: moduleId, prompt_id: promptId, body, help_level: helpLevel }) });
    state.lastSubmitted = attempt;
    localStorage.removeItem(`study-draft:${moduleId}`);
    showToast("Respuesta enviada para revisión.");
    app.innerHTML = `<section class="panel panel-pad"><div class="eyebrow">Intento registrado</div><h2>Tu respuesta quedó guardada.</h2><p class="lede">El siguiente paso es revisar el mecanismo, no perseguir una nota. El intento conserva exactamente lo que escribiste.</p><div class="context-note" style="margin: 24px 0"><strong>ID:</strong> <code>${escapeHtml(attempt.attempt_id)}</code><br><strong>Estado:</strong> pendiente de revisión</div><div class="action-row"><a class="button" href="#/feedback/${encodeURIComponent(attempt.attempt_id)}">Ver estado</a><a class="button secondary" href="#/history">Ver historial</a></div></section>`;
  } catch (error) { button.disabled = false; showToast(error.message); }
}

async function renderFeedback(attemptId) {
  try {
    const [attempt, feedback] = await Promise.all([api(`/api/attempts/${encodeURIComponent(attemptId)}`), api(`/api/feedback/${encodeURIComponent(attemptId)}`).catch(() => null)]);
    if (!feedback) {
      app.innerHTML = `<section class="panel panel-pad"><div class="eyebrow">Revisión pendiente</div><h2>Tu respuesta está en espera.</h2><p class="lede">El intento fue guardado, pero todavía no tiene feedback. Cuando lo revisemos, vas a ver acá cada criterio y la próxima acción.</p><div class="context-note" style="margin: 24px 0"><strong>Respuesta enviada:</strong><br>${escapeHtml(attempt.body)}</div><div class="action-row"><a class="button" href="#/history">Volver al historial</a><a class="button secondary" href="#/">Volver al mapa</a></div></section>`;
      return;
    }
    const criteria = Object.entries(feedback.criteria || {}).map(([key, value]) => `<div class="feedback-criterion"><span class="criterion-status status-${escapeHtml(value.status)}">${escapeHtml(value.status)}</span><div><strong>${escapeHtml(capabilityLabel(key))}</strong><p>${escapeHtml(value.note)}</p></div></div>`).join("");
    const nextAction = { advance: "avanzar", recovery: "hacer recuperación", review: "repasar más adelante" }[feedback.next_action] || feedback.next_action;
    app.innerHTML = `<div class="eyebrow">Feedback · ${escapeHtml(attempt.module_id)}</div><div class="lesson-layout"><section class="panel panel-pad"><div class="lesson-meta"><span>respuesta original</span><span>${escapeHtml(formatDate(attempt.submitted_at))}</span></div><h1 class="prompt-copy">Qué mostró tu respuesta</h1><div class="submitted-answer">${escapeHtml(attempt.body)}</div><div class="feedback-grid">${criteria}</div><div class="feedback-columns"><div><h3>Fortalezas</h3><ul>${(feedback.strengths || []).map((item) => `<li>${escapeHtml(item)}</li>`).join("") || "<li>todavía no registradas</li>"}</ul></div><div><h3>Errores a trabajar</h3><ul>${(feedback.errors || []).map((item) => `<li>${escapeHtml(item)}</li>`).join("") || "<li>ninguno registrado</li>"}</ul></div></div></section><aside class="side-stack"><section class="side-card context-note"><strong>Próxima acción: ${escapeHtml(nextAction)}</strong><br>${escapeHtml(feedback.hint?.text || "Revisá el criterio marcado y volvé a intentarlo.")}</section><section class="side-card"><h3>Ayuda usada</h3><p class="muted">${escapeHtml(attempt.help_level)}</p><a class="button secondary" href="#/lesson/${encodeURIComponent(attempt.module_id)}">Volver a practicar</a></section></aside></div>`;
  } catch (error) {
    app.innerHTML = `<section class="error-box"><strong>No pude cargar este feedback.</strong><p>${escapeHtml(error.message)}</p></section>`;
  }
}

async function renderHistory() {
  try { state.history = (await api("/api/history")).attempts; } catch { state.history = []; }
  const content = state.history.length ? state.history.slice().reverse().map((attempt) => `<article class="history-item"><header><h3>${escapeHtml(attempt.module_id)}</h3><time>${escapeHtml(formatDate(attempt.submitted_at))}</time></header><p>${escapeHtml(attempt.body)}</p><p class="mono muted" style="margin-top: 12px">ayuda: ${escapeHtml(attempt.help_level)} · ${escapeHtml(attempt.attempt_id)}</p></article>`).join("") : '<div class="empty-state">Todavía no hay respuestas enviadas. La primera sesión activa te espera en Inicio.</div>';
  app.innerHTML = `<div class="eyebrow">Registro de aprendizaje</div><h1>Tu razonamiento, en evolución.</h1><p class="lede">Cada intento queda como evidencia. Volver a leer una respuesta anterior permite ver qué cambió y qué todavía necesita práctica.</p><div class="action-row" style="margin-top: 22px"><button class="button secondary" id="download-backup" type="button">Descargar respaldo</button><label class="button secondary" for="import-backup">Importar borrador<input id="import-backup" type="file" accept="application/json" hidden></label></div><div class="history-list">${content}</div>`;
  document.querySelector("#download-backup").addEventListener("click", downloadBackup);
  document.querySelector("#import-backup").addEventListener("change", importBackup);
}

function renderDefense() {
  app.innerHTML = `<div class="eyebrow">Modo defensa</div><h1>Treinta minutos para explicar. Quince para sostenerlo.</h1><p class="lede">La defensa se entrena después de construir el mecanismo. Esta vista reúne el guion, el banco de preguntas y los simulacros.</p><div class="defense-list"><article class="defense-item"><header><h3>Exposición principal</h3><time>30 minutos</time></header><p>Problema → BB84 → implementación time-bin → estados señuelo → simulación → límites → frontera.</p></article><article class="defense-item"><header><h3>Preguntas del jurado</h3><time>15 minutos</time></header><p>Responder con una estructura fija: respuesta directa, mecanismo, evidencia y límite.</p></article></div><div class="action-row" style="margin-top: 24px"><a class="button" href="/study/defensa/guion_30_minutos.md" target="_blank" rel="noreferrer">Abrir guion</a><a class="button secondary" href="/study/defensa/banco_preguntas.md" target="_blank" rel="noreferrer">Abrir banco</a><button class="button secondary" id="record-rehearsal" type="button">Registrar simulacro</button></div>`;
  document.querySelector("#record-rehearsal").addEventListener("click", async () => {
    try { await api("/api/defense", { method: "POST", body: JSON.stringify({ kind: "full_rehearsal", duration_minutes: 45, note: "Simulacro registrado desde la ruta guiada." }) }); showToast("Simulacro registrado."); }
    catch (error) { showToast(error.message); }
  });
}

async function downloadBackup() {
  try {
    const backup = await api("/api/backup");
    const blob = new Blob([JSON.stringify(backup, null, 2)], { type: "application/json" });
    const link = document.createElement("a");
    link.href = URL.createObjectURL(blob);
    link.download = "qkd-study-backup.json";
    link.click();
    URL.revokeObjectURL(link.href);
    showToast("Respaldo descargado.");
  } catch (error) { showToast(error.message); }
}

async function importBackup(event) {
  const file = event.target.files?.[0];
  if (!file) return;
  try {
    const backup = JSON.parse(await file.text());
    await api("/api/import", { method: "POST", body: JSON.stringify(backup) });
    showToast("Borrador importado. Volvé a Inicio para continuar.");
  } catch (error) { showToast(`No se pudo importar: ${error.message}`); }
}

window.addEventListener("hashchange", renderRoute);
window.addEventListener("DOMContentLoaded", loadAppState);
