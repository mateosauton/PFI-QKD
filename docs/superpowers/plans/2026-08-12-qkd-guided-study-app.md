# QKD Guided Study App Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a local Spanish web application that guides Mateo through one QKD study session at a time, stores versioned answers, and exposes progress and feedback without requiring manual Markdown editing.

**Architecture:** Keep the existing `study/` Markdown as academic source material and add a small standard-library Python application under `study_app/`. The Python server serves static HTML/CSS/JavaScript and exposes JSON endpoints backed by atomic files under the ignored `.study_state/` directory. The assistant remains the semantic reviewer; the app records feedback and displays the next action.

**Tech Stack:** Python 3.11+ standard library (`http.server`, `json`, `pathlib`, `tempfile`), HTML/CSS/vanilla JavaScript, pytest, existing `uv` workflow.

---

## File Map

Create these focused units:

```text
study_app/
├── __init__.py              package marker
├── catalog.py               typed module and prompt catalog
├── state.py                 JSON persistence, attempts and export
├── server.py                local HTTP server and JSON API
└── static/
    ├── index.html           application shell
    ├── styles.css           responsive visual system
    └── app.js               client state, routing and rendering
tests/study_app/
├── test_catalog.py          catalog validity and source links
├── test_state.py            atomic persistence and transitions
└── test_server.py           API contract and static serving
scripts/run_study_app.py    documented local launcher
```

Modify:

- `.gitignore`: ignore `.study_state/` while keeping its schema documentation tracked.
- `study/README.md`: add the application launch command and the rule that responses are submitted through the app.

Do not modify the existing chapters to embed app logic. The catalog owns the connection between modules and Markdown files.

## Task 1: Add the catalog and application skeleton

**Files:**

- Create: `study_app/__init__.py`
- Create: `study_app/catalog.py`
- Create: `tests/study_app/test_catalog.py`
- Create: `scripts/run_study_app.py`

- [ ] **Step 1: Write catalog tests first.**

Add tests that prove the catalog has eight ordered modules, unique IDs, valid source paths, and a current prompt with a rubric containing the four thesis capabilities.

```python
from study_app.catalog import CAPABILITIES, MODULES, get_module


def test_catalog_has_eight_ordered_modules_with_existing_sources():
    assert len(MODULES) == 8
    assert [module.order for module in MODULES] == list(range(1, 9))
    assert len({module.id for module in MODULES}) == 8
    assert all(module.source.exists() for module in MODULES)


def test_bb84_prompt_has_four_capability_criteria():
    module = get_module("bb84-bases")
    assert module.prompt.prompt_id == "bb84-eve-qber-01"
    assert set(module.prompt.rubric) == set(CAPABILITIES)


def test_unknown_module_returns_none():
    assert get_module("missing") is None
```

- [ ] **Step 2: Run the focused tests and verify the expected import failure.**

Run: `uv run pytest tests/study_app/test_catalog.py -q`

Expected: FAIL with `ModuleNotFoundError: No module named 'study_app'`.

- [ ] **Step 3: Implement the typed catalog.**

Use repository-root-relative `Path` values resolved from `catalog.py`; define `CAPABILITIES = ("explain", "calculate", "connect", "defend")`; define `Prompt` and `Module` frozen dataclasses; populate exactly these modules and prompts:

```python
Module("crypto-keys", 1, "Criptografía y claves", "study/capitulos/01_criptografia_y_claves.md", Prompt("crypto-keys-01", "study/ejercicios/semana_01.md", "¿Qué diferencia hay entre cifrar un mensaje y distribuir una clave? Explicalo con un ejemplo.", CAPABILITIES)),
Module("bb84-bases", 2, "Fundamentos cuánticos y BB84", "study/capitulos/02_fundamentos_cuanticos_y_bb84.md", Prompt("bb84-eve-qber-01", "study/ejercicios/semana_02.md", "¿Por qué BB84 puede detectar que Eve intervino estadísticamente aunque no pueda localizarla?", CAPABILITIES)),
Module("qber-skr", 3, "QBER, seguridad y SKR", "study/capitulos/03_seguridad_qber_y_skr.md", Prompt("qber-skr-01", "study/ejercicios/semana_03.md", "¿Cómo se relacionan QBER, reconciliación, amplificación de privacidad y tasa de clave secreta?", CAPABILITIES)),
Module("optics-timebin", 4, "Óptica, fibra y time-bin", "study/capitulos/04_optica_fibra_y_time_bin.md", Prompt("timebin-loss-01", "study/ejercicios/semana_04.md", "Calculá la transmisión de una fibra de 50 km con 0.2 dB/km y explicá qué representa físicamente el resultado.", CAPABILITIES)),
Module("decoy-states", 5, "WCS, PNS y estados señuelo", "study/capitulos/05_wcs_pns_y_estados_senuelo.md", Prompt("decoy-pns-01", "study/ejercicios/semana_05.md", "¿Qué vulnerabilidad introducen los pulsos multifotónicos y cómo la mitigación decoy-state cambia la estimación de seguridad?", CAPABILITIES)),
Module("simulation", 6, "SeQUeNCe y experimentos", "study/capitulos/06_sequence_y_resultados.md", Prompt("simulation-causality-01", "study/ejercicios/semana_06.md", "Elegí un parámetro de la simulación y predecí cómo cambiarán QBER, detecciones y SKR antes de ejecutar el barrido.", CAPABILITIES)),
Module("system-engineering", 7, "Red, hardware y validez", "study/capitulos/07_red_hardware_y_validez.md", Prompt("system-limits-01", "study/ejercicios/semana_07.md", "¿Qué demuestra el banco de pruebas de la tesis y qué no demuestra sobre una red QKD operativa?", CAPABILITIES)),
Module("frontier-defense", 8, "Frontera y defensa", "study/capitulos/08_frontera_qkd_2018_actualidad.md", Prompt("defense-tf-01", "study/defensa/banco_preguntas.md", "Explicá qué problema resuelve TF-QKD, qué supuesto de hardware relaja y qué dificultad experimental introduce.", CAPABILITIES)),
```

Every prompt must include a Spanish question, one source path, and a rubric dictionary with all four capabilities. The catalog must convert the tuple of capability names into a rubric dictionary such as `{capability: "evaluar" for capability in CAPABILITIES}`. The first active prompt must be `bb84-eve-qber-01` after the introductory crypto module is marked available.

- [ ] **Step 4: Implement the launcher and package marker.**

`study_app/__init__.py` exports `__version__ = "0.1.0"`. `scripts/run_study_app.py` resolves the repository root, imports `create_server`, binds `127.0.0.1`, prints the URL, and calls `serve_forever()`.

- [ ] **Step 5: Run catalog tests and commit.**

Run: `uv run pytest tests/study_app/test_catalog.py -q`

Expected: `3 passed`.

Commit: `git add study_app tests/study_app scripts/run_study_app.py && git commit -m "add qkd study app catalog"`

## Task 2: Implement private state persistence and exports

**Files:**

- Create: `study_app/state.py`
- Create: `tests/study_app/test_state.py`
- Modify: `.gitignore`
- Modify: `study/README.md`

- [ ] **Step 1: Write persistence tests first.**

Cover default state, draft replacement, immutable attempts, feedback, valid transition, rejected transition, atomic JSON, and Markdown export.

```python
def test_submit_creates_immutable_attempt_and_default_progress(tmp_path):
    store = StateStore(tmp_path)
    attempt = store.submit_attempt("bb84-bases", "bb84-eve-qber-01", "Mi respuesta", "none")
    assert store.load_progress()["current_module"] == "crypto-keys"
    assert store.get_attempt(attempt["attempt_id"])["body"] == "Mi respuesta"
    with pytest.raises(FileExistsError):
        store.create_attempt_file(attempt["attempt_id"], attempt)


def test_transition_requires_valid_state_change(tmp_path):
    store = StateStore(tmp_path)
    store.set_module_status("crypto-keys", "in_progress")
    assert store.set_module_status("crypto-keys", "submitted")["modules"]["crypto-keys"]["status"] == "submitted"
    with pytest.raises(ValueError, match="invalid module transition"):
        store.set_module_status("crypto-keys", "mastered")


def test_export_contains_active_module_and_attempt_count(tmp_path):
    store = StateStore(tmp_path)
    store.submit_attempt("bb84-bases", "bb84-eve-qber-01", "Texto", "none")
    export = store.export_summary()
    assert "# Resumen de progreso QKD" in export
    assert "bb84-bases" in export
    assert "Intentos registrados: 1" in export
```

- [ ] **Step 2: Run the tests and verify the missing implementation failure.**

Run: `uv run pytest tests/study_app/test_state.py -q`

Expected: FAIL with an import error for `study_app.state`.

- [ ] **Step 3: Implement `StateStore` with atomic writes.**

The constructor receives a `Path` root and creates `attempts/`, `feedback/`, and `exports/`. `_write_json(path, value, overwrite=True)` must serialize with UTF-8, write a sibling `.tmp` file, flush it, and replace the destination. `load_progress()` returns a default schema-v1 object whose `current_module` is `crypto-keys`; `save_draft()` replaces `session.json`; `submit_attempt()` creates a timestamp-plus-random-suffix ID and refuses collisions; `get_attempt()` reads one immutable file; `save_feedback()` writes by attempt ID; `set_module_status()` enforces explicit transitions; `record_error()` updates `errors.json`; `export_summary()` writes and returns a human-readable Markdown summary.

Use these allowed transitions:

```python
ALLOWED_TRANSITIONS = {
    "locked": {"available"},
    "available": {"in_progress"},
    "in_progress": {"submitted"},
    "submitted": {"recovery", "review"},
    "recovery": {"in_progress", "review"},
    "review": {"mastered", "recovery"},
    "mastered": {"review"},
}
```

`set_module_status()` must reject unknown modules, unknown status values, and transitions not present in the map. `save_feedback()` must not change the module status implicitly; the assistant or API caller must request the transition explicitly.

- [ ] **Step 4: Add the ignored state directory and user instructions.**

Append `.study_state/` to `.gitignore`. Add a “Aplicación interactiva” section to `study/README.md` with:

```text
uv run python scripts/run_study_app.py
```

Explain that chapters remain tracked Markdown and personal responses remain local under `.study_state/`.

- [ ] **Step 5: Run tests and commit.**

Run: `uv run pytest tests/study_app/test_state.py -q`

Expected: `3 passed`.

Commit: `git add study_app/state.py tests/study_app/test_state.py .gitignore study/README.md && git commit -m "add qkd study state storage"`

## Task 3: Add the local HTTP server and JSON API

**Files:**

- Create: `study_app/server.py`
- Create: `tests/study_app/test_server.py`

- [ ] **Step 1: Write API contract tests first.**

Use a temporary `StateStore`, start `ThreadingHTTPServer` on port `0`, make `urllib.request` calls, and shut down in a fixture. Assert:

```python
def test_catalog_endpoint_returns_modules(client):
    response = client.get("/api/catalog")
    assert response.status == 200
    assert len(response.json()["modules"]) == 8


def test_submit_endpoint_persists_attempt(client):
    response = client.post("/api/attempts", {
        "module_id": "bb84-bases",
        "prompt_id": "bb84-eve-qber-01",
        "body": "Eve introduce errores al medir en una base incorrecta.",
        "help_level": "none",
    })
    assert response.status == 201
    attempt_id = response.json()["attempt_id"]
    assert client.get(f"/api/attempts/{attempt_id}").json()["body"].startswith("Eve")


def test_unknown_api_route_is_json_404(client):
    response = client.get("/api/not-a-route")
    assert response.status == 404
    assert response.json()["error"] == "not found"
```

- [ ] **Step 2: Run the API tests and verify the expected failure.**

Run: `uv run pytest tests/study_app/test_server.py -q`

Expected: FAIL because `create_server` and the handler do not exist.

- [ ] **Step 3: Implement the API handler.**

Implement `create_server(host, port, state_root)` returning a `ThreadingHTTPServer` with a handler factory that closes over the repository root and `StateStore`. Serve `/` and `/static/*` with safe path resolution. Implement these JSON endpoints:

```text
GET  /api/catalog
GET  /api/progress
GET  /api/session
GET  /api/attempts/:id
POST /api/draft
POST /api/attempts
POST /api/feedback
POST /api/progress/status
POST /api/export
```

Parse JSON with a maximum body size of 1 MiB. Return `400` with `{"error":"invalid json"}` for malformed JSON, `422` with a descriptive error for missing required fields, `404` for missing catalog items or attempts, and `409` for invalid state transitions or duplicate immutable IDs. Add `Cache-Control: no-store` to API responses and `Content-Type: application/json; charset=utf-8`.

- [ ] **Step 4: Run API tests and commit.**

Run: `uv run pytest tests/study_app/test_server.py -q`

Expected: `3 passed`.

Commit: `git add study_app/server.py tests/study_app/test_server.py && git commit -m "add qkd study local api"`

## Task 4: Build the dashboard and guided session frontend

**Files:**

- Create: `study_app/static/index.html`
- Create: `study_app/static/styles.css`
- Create: `study_app/static/app.js`

- [ ] **Step 1: Create the semantic application shell.**

`index.html` must contain a header with the app name and offline indicator, a `<main>` with `#app`, and navigation links for `Inicio`, `Historial` and `Defensa`. Load `styles.css` and `app.js` with `defer`. Include labels for the response editor and status announcements with `aria-live="polite"`.

- [ ] **Step 2: Implement the approved visual system.**

In `styles.css`, define variables for warm paper, ink, muted text, green evidence, amber attention, blue information, and border colors. Use a responsive two-column dashboard that collapses below `780px`, panels with at most `8px` radius, stable spacing, visible focus states, and a maximum content width of `1180px`. Do not use a purple gradient, decorative blobs, or text inside controls that can be represented by a familiar icon. Keep all response text inside its parent at mobile widths.

- [ ] **Step 3: Implement client data loading and route rendering.**

`app.js` must provide these functions:

```javascript
async function api(path, options = {}) {}
async function loadAppState() {}
function renderDashboard(state) {}
function renderLesson(state, moduleId) {}
function renderHistory(state) {}
function renderDefense(state) {}
function saveDraft(body) {}
async function submitAttempt(moduleId, promptId, body, helpLevel) {}
```

On startup, call `loadAppState()` and render `location.hash || "#/"`. The dashboard shows the current module, all module statuses, last attempt, and the reason for each locked state. The lesson view shows source links, prompt, rubric, textarea, help selector, draft status, and submit button. Drafts debounce to 400 ms and call `/api/draft`; if the API fails, store `study-draft:<moduleId>` in `localStorage` and show “guardado localmente”.

- [ ] **Step 4: Add a manual smoke test before proceeding.**

Run: `uv run python scripts/run_study_app.py`

Open the printed URL and verify that the dashboard loads, the first module is available, the lesson route renders, the layout collapses in a narrow browser window, and a draft survives a reload. Stop the server after the check.

- [ ] **Step 5: Commit the frontend.**

Run: `git diff --check`

Commit: `git add study_app/static && git commit -m "add guided qkd study interface"`

## Task 5: Add feedback, recovery and assistant-facing records

**Files:**

- Modify: `study_app/static/app.js`
- Modify: `study_app/static/styles.css`
- Modify: `study_app/server.py`
- Modify: `study_app/state.py`
- Create: `study_app/feedback_schema.py`
- Create: `tests/study_app/test_feedback.py`

- [ ] **Step 1: Test feedback validation and next actions.**

Add tests for a complete feedback object, missing criteria, invalid capability status, and legal next actions:

```python
def valid_feedback():
    return {
        "attempt_id": "attempt-1",
        "criteria": {capability: {"status": "green", "note": "evidencia"} for capability in CAPABILITIES},
        "strengths": ["mecanismo correcto"],
        "errors": [],
        "next_action": "advance",
        "hint": {"level": 1, "text": "seguí conectando con QBER"},
    }


def test_feedback_requires_all_four_capabilities():
    feedback = valid_feedback()
    assert validate_feedback(feedback) == []
    del feedback["criteria"]["defend"]
    assert "criteria.defend is required" in validate_feedback(feedback)


def test_feedback_rejects_unknown_next_action():
    feedback = valid_feedback()
    feedback["next_action"] = "guess"
    assert "next_action must be one of" in validate_feedback(feedback)[0]
```

- [ ] **Step 2: Implement `feedback_schema.py`.**

Define `STATUSES = ("red", "yellow", "green", "blue")`, `NEXT_ACTIONS = ("advance", "recovery", "review")`, and `validate_feedback(value) -> list[str]`. Require non-empty strings for notes, lists for strengths/errors, a positive integer hint level from 1 to 3, and the exact four capability keys.

- [ ] **Step 3: Connect feedback API and state updates.**

`POST /api/feedback` validates the object, writes feedback, and returns `201`. It must not mark a module mastered automatically. `POST /api/progress/status` receives `{module_id, status}` and uses `StateStore.set_module_status()`. Add a server-side check that `advance` is only accepted when all four feedback criteria are `green` or `blue`; `recovery` keeps the module available for another attempt.

- [ ] **Step 4: Render the feedback view.**

After an attempt is submitted, show the original answer, four criterion rows, strengths, errors, current help level, next action, and a “volver a intentar” action for recovery. Use text labels in addition to color. The frontend must distinguish “pendiente de revisión” from “dominado”.

- [ ] **Step 5: Run tests and commit.**

Run: `uv run pytest tests/study_app/test_feedback.py tests/study_app/test_state.py tests/study_app/test_server.py -q`

Expected: all tests pass.

Commit: `git add study_app tests/study_app && git commit -m "add qkd feedback workflow"`

## Task 6: Add history, error ledger, defense mode and export

**Files:**

- Modify: `study_app/state.py`
- Modify: `study_app/server.py`
- Modify: `study_app/static/app.js`
- Modify: `study_app/static/styles.css`
- Create: `tests/study_app/test_export_and_history.py`

- [ ] **Step 1: Test history and export behavior.**

Create two attempts for one prompt, record an error, save feedback, export, and assert that the response order is chronological, the error appears once in the ledger, and the Markdown export contains the next review date and module status.

```python
def test_history_preserves_attempt_order_and_deduplicates_errors(tmp_path):
    store = StateStore(tmp_path)
    first = store.submit_attempt("bb84-bases", "bb84-eve-qber-01", "primera", "none")
    second = store.submit_attempt("bb84-bases", "bb84-eve-qber-01", "segunda", "hint-1")
    store.record_error("bb84-bases", "confunde detectar con localizar", "yellow")
    store.record_error("bb84-bases", "confunde detectar con localizar", "yellow")
    assert [item["attempt_id"] for item in store.list_attempts("bb84-bases")] == [first["attempt_id"], second["attempt_id"]]
    assert len(store.load_errors()["items"]) == 1


def test_defense_export_has_30_plus_15_structure(tmp_path):
    store = StateStore(tmp_path)
    export = store.export_summary()
    assert "30 minutos" in export
    assert "15 minutos" in export
```

- [ ] **Step 2: Implement history and error endpoints.**

Add `GET /api/history?module_id=...`, `GET /api/errors`, `POST /api/errors`, and `POST /api/export`. Sort attempts by `submitted_at`, preserve all attempts, and deduplicate errors by `(module_id, concept)` while updating their count and last-seen timestamp.

- [ ] **Step 3: Implement the history and defense routes.**

History displays attempts grouped by module with the original response, help level, feedback state, and next review. Defense displays a question selected from the existing bank, a 30-minute presentation checklist, a 15-minute questions checklist, and a completion record. The defense route must not unlock academic modules; it records rehearsal evidence separately.

- [ ] **Step 4: Implement export and offline import.**

`export_summary()` writes `.study_state/exports/progress-summary.md` containing active module, status table, attempt counts, error ledger, next reviews, and defense timing. Add a browser button that downloads the current JSON package as `qkd-study-backup.json`; add an import input that validates `schema_version` and restores drafts only, never overwriting immutable attempts without an explicit duplicate check.

- [ ] **Step 5: Run focused tests and commit.**

Run: `uv run pytest tests/study_app/test_export_and_history.py tests/study_app/test_feedback.py -q`

Expected: all tests pass.

Commit: `git add study_app tests/study_app && git commit -m "add qkd study history and defense"`

## Task 7: Documentation, integration tests and visual verification

**Files:**

- Modify: `study/README.md`
- Modify: `study_app/static/index.html`
- Create: `tests/study_app/test_end_to_end.py`
- Create: `study_app/STATE_SCHEMA.md`

- [ ] **Step 1: Add the state schema documentation.**

Document the JSON files, version `1`, immutable attempt rule, feedback lifecycle, local privacy model, backup command, and recovery procedure for a corrupt state file.

- [ ] **Step 2: Write the end-to-end API test.**

Start the server with a temporary root and execute this sequence: `GET /api/session`, `POST /api/draft`, `POST /api/attempts`, `POST /api/feedback`, `POST /api/progress/status` to `review`, `GET /api/history`, and `POST /api/export`. Assert each status code and verify the export file exists.

- [ ] **Step 3: Document the user workflow.**

In `study/README.md`, add:

```text
1. Ejecutá `uv run python scripts/run_study_app.py`.
2. Abrí la URL local que imprime el servidor.
3. Respondé solo la sesión activa.
4. Enviá el intento y esperá la revisión del asistente.
5. Revisá feedback y próxima acción.
6. Respaldá `.study_state/` antes de cambiar de máquina.
```

Explain that a response should be written in the app, not by editing the learning chapter.

- [ ] **Step 4: Run the complete verification suite.**

Run:

```bash
uv run pytest tests/study_app -q
uv run pytest tests -q
uv run python study/tools/validate_study.py study
git diff --check
```

Expected: all study-app tests pass, the existing repository suite remains green, the study validator exits `0`, and no whitespace errors are reported.

- [ ] **Step 5: Verify the UI manually at two sizes.**

Start `uv run python scripts/run_study_app.py`, inspect dashboard, lesson, feedback, history and defense routes at a desktop viewport and a narrow viewport. Confirm no text overlap, no blocked state relies only on color, drafts survive reload, API errors are visible, and the application never sends requests outside localhost.

- [ ] **Step 6: Commit documentation and integration tests.**

Commit: `git add study/README.md study_app tests/study_app && git commit -m "document qkd study app workflow"`

## Task 8: Final branch verification and handoff

**Files:**

- No new files; inspect all files changed by Tasks 1-7.

- [ ] **Step 1: Run the complete commands again from a clean application state.**

Move any temporary `.study_state/` aside, run the server smoke test, run `uv run pytest tests -q`, run `uv run python study/tools/validate_study.py study`, and inspect `git status --short`. Do not stage unrelated existing files under `docs/` or generated PDFs.

- [ ] **Step 2: Confirm the handoff checklist.**

The final report must include the local launch command, the path to the state schema, the location of the academic material, test results, the exact branch and commits, and the first user action: open the dashboard and answer the active BB84 prompt.

- [ ] **Step 3: Push only after explicit user authorization.**

If the user authorizes publication, run `git push origin codex/proyecto-3-document` and report the URL. Otherwise leave the commits local and report the branch name.

## Plan Self-Review

- Spec coverage: Tasks 1-2 cover catalog, JSON state, privacy and export; Task 3 covers the local API; Task 4 covers the approved visual flow; Task 5 covers feedback, four capabilities, recovery and unlock rules; Task 6 covers history, errors, defense and backup; Task 7 covers documentation, integration tests and visual QA; Task 8 covers clean-state verification and handoff.
- Scope: the first version uses only standard-library Python and browser APIs already available in the repository; it does not add authentication, cloud storage or model integration.
- Consistency: `StateStore` is the only writer for `.study_state/`; the server calls it; the frontend only calls API endpoints and localStorage fallback; feedback validation is shared by API and tests; module status transitions are explicit.
- Completeness: every task has concrete files, commands, expected outcomes, and a commit boundary; no unfinished instruction or undefined future component remains in the plan.
