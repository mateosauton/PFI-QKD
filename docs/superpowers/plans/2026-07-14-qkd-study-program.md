# QKD Study Program Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build and publish a complete Spanish-language, eight-week interactive study system that prepares Mateo to understand and defend the entire QKD thesis.

**Architecture:** Store the stable course under `study/`, with one focused Markdown chapter per conceptual layer, one exercise set per week, guided laboratories tied to the real simulation, and a separate defense kit. Use GitHub-rendered Markdown, equations, Mermaid diagrams, and existing SVG assets; add a small Python validator so broken local links and unfinished markers are caught before each commit.

**Tech Stack:** Markdown, GitHub Mermaid, SVG/PNG, Python 3.11 standard library, pytest, SeQUeNCe, NumPy, Matplotlib, Git.

---

## File Map

### Course entry and tracking

- Create `study/README.md`: entry point, study rules, navigation and quick start.
- Create `study/plan_maestro.md`: flexible eight-week calendar and session contract.
- Create `study/progreso.md`: mastery traffic light and spaced-review table.
- Create `study/errores_y_dudas.md`: durable misconception and question log.
- Create `study/glosario.md`: Spanish definitions with English technical terms.

### Conceptual chapters

- Create `study/capitulos/00_orientacion_y_diagnostico.md`: baseline test and mental map.
- Create `study/capitulos/01_criptografia_y_claves.md`: week 1.
- Create `study/capitulos/02_fundamentos_cuanticos_y_bb84.md`: week 2.
- Create `study/capitulos/03_seguridad_qber_y_skr.md`: week 3.
- Create `study/capitulos/04_optica_fibra_y_time_bin.md`: week 4.
- Create `study/capitulos/05_wcs_pns_y_estados_senuelo.md`: week 5.
- Create `study/capitulos/06_sequence_y_resultados.md`: week 6.
- Create `study/capitulos/07_red_hardware_y_validez.md`: week 7 engineering layer.
- Create `study/capitulos/08_frontera_qkd_2018_actualidad.md`: modern QKD, TF-QKD, fiber and satellite.

### Exercises and laboratories

- Create `study/ejercicios/semana_01.md` through `study/ejercicios/semana_07.md`: problems, collapsible hints and solutions.
- Create `study/laboratorio/README.md`: environment and experiment map.
- Create `study/laboratorio/01_recorrido_codigo.md`: guided code reading.
- Create `study/laboratorio/02_distancia.md`: distance and link-loss experiment.
- Create `study/laboratorio/03_detector_y_visibilidad.md`: detector and interferometer experiments.
- Create `study/laboratorio/04_estados_senuelo.md`: decoy-state analytical layer.

### Defense and visuals

- Create `study/defensa/guion_30_minutos.md`: timed narrative.
- Create `study/defensa/banco_preguntas.md`: cumulative jury questions and answer criteria.
- Create `study/defensa/rubrica_simulacro.md`: 30 + 15 minute rehearsal rubric.
- Create `study/defensa/respuestas_dificiles.md`: response structures for limitations and unknowns.
- Create `study/assets/README.md`: visual index and provenance.
- Create `study/assets/*.svg`: stable copies of the six existing QKD diagrams.

### Validation

- Create `study/tools/validate_study.py`: placeholder and broken-link checker.
- Create `tests/test_study_validator.py`: validator unit tests.

## Source Map

- Primary thesis: `paper/main.pdf` and `paper/chapters/*.tex`.
- Simulation: `experiments/qkd_2node_simulation.py`.
- Current figures: `experiments/results/*.png`.
- Research synthesis: `docs/qkd_deep_research.md` and `docs/qkd_lectura_avion.md`.
- Existing diagrams: `docs/qkd_assets/*.svg`.
- Bibliography: `paper/references.bib`.
- Approved design: `docs/superpowers/specs/2026-07-14-qkd-study-program-design.md`.

---

### Task 1: Add Study-Material Validation

**Files:**
- Create: `study/tools/validate_study.py`
- Create: `tests/test_study_validator.py`

- [ ] **Step 1: Write failing validator tests**

Create `tests/test_study_validator.py` with tests for a clean document, unfinished markers and broken relative links:

```python
from pathlib import Path

from study.tools.validate_study import broken_links, unfinished_markers


def test_clean_markdown_has_no_violations(tmp_path: Path) -> None:
    (tmp_path / "target.md").write_text("# Target\n", encoding="utf-8")
    source = tmp_path / "source.md"
    source.write_text("# Source\n\n[Target](target.md)\n", encoding="utf-8")

    assert unfinished_markers(tmp_path) == []
    assert broken_links(tmp_path) == []


def test_reports_unfinished_markers(tmp_path: Path) -> None:
    path = tmp_path / "lesson.md"
    path.write_text("# Lesson\n\nTODO: explain this.\n", encoding="utf-8")

    assert unfinished_markers(tmp_path) == [f"{path}:3:TODO: explain this."]


def test_reports_broken_relative_links(tmp_path: Path) -> None:
    path = tmp_path / "lesson.md"
    path.write_text("# Lesson\n\n[Missing](missing.md)\n", encoding="utf-8")

    assert broken_links(tmp_path) == [f"{path}:3:missing.md"]
```

- [ ] **Step 2: Run the tests and verify the expected failure**

Run:

```bash
uv run pytest tests/test_study_validator.py -q
```

Expected: collection fails with `ModuleNotFoundError` because `study.tools.validate_study` does not exist.

- [ ] **Step 3: Implement the validator**

Create `study/tools/validate_study.py`:

```python
from __future__ import annotations

import argparse
import re
from pathlib import Path

MARKER_RE = re.compile(r"\b(?:TODO|TBD|FIXME|PLACEHOLDER)\b", re.IGNORECASE)
LINK_RE = re.compile(r"\[[^\]]+\]\(([^)]+)\)")


def markdown_files(root: Path) -> list[Path]:
    return sorted(path for path in root.rglob("*.md") if path.is_file())


def unfinished_markers(root: Path) -> list[str]:
    violations: list[str] = []
    for path in markdown_files(root):
        for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            if MARKER_RE.search(line):
                violations.append(f"{path}:{line_number}:{line.strip()}")
    return violations


def broken_links(root: Path) -> list[str]:
    violations: list[str] = []
    for path in markdown_files(root):
        for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            for raw_target in LINK_RE.findall(line):
                target = raw_target.split("#", 1)[0].strip()
                if not target or target.startswith(("http://", "https://", "mailto:")):
                    continue
                if not (path.parent / target).resolve().exists():
                    violations.append(f"{path}:{line_number}:{raw_target}")
    return violations


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate QKD study Markdown files")
    parser.add_argument("root", nargs="?", default="study", type=Path)
    args = parser.parse_args()
    violations = unfinished_markers(args.root) + broken_links(args.root)
    for violation in violations:
        print(violation)
    return 1 if violations else 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 4: Run the validator tests**

Run:

```bash
uv run pytest tests/test_study_validator.py -q
```

Expected: `3 passed`.

- [ ] **Step 5: Commit the validation tooling**

```bash
git add study/tools/validate_study.py tests/test_study_validator.py
git commit -m "add study material validation"
```

---

### Task 2: Create the Study Hub and Diagnostic

**Files:**
- Create: `study/README.md`
- Create: `study/plan_maestro.md`
- Create: `study/progreso.md`
- Create: `study/errores_y_dudas.md`
- Create: `study/glosario.md`
- Create: `study/capitulos/00_orientacion_y_diagnostico.md`

- [ ] **Step 1: Create the course entry point**

Write `study/README.md` with these exact top-level sections:

```markdown
# Programa interactivo de estudio de QKD

## Cómo empezar hoy
## Cómo funciona cada sesión
## Regla de dominio
## Navegación
## Fuentes principales
## Qué hacer cuando una semana se complica
```

Under `Cómo empezar hoy`, link in order to the diagnostic, master plan, progress log and first chapter. Under `Navegación`, include every planned chapter, exercise set, laboratory and defense file; mark files not yet created as plain text until their task creates them so validation never contains intentionally broken links.

- [ ] **Step 2: Write the flexible calendar**

Write `study/plan_maestro.md` with:

- The three-session weekly contract: intuition, engineering and defense.
- A table for weeks 1-8 with essential outcomes and optional work.
- A 45-minute compressed session and a 60-minute standard session.
- Recovery rule: complete the missing essential session before optional material.
- Four cumulative checkpoints at the ends of weeks 2, 4, 6 and 8.

- [ ] **Step 3: Create tracking files**

Write `study/progreso.md` with one row per chapter and columns `Estado`, `Explicar`, `Calcular`, `Conectar`, `Defender`, `Último repaso`, and `Próximo repaso`. Initialize every state as `Rojo - sin evaluar` rather than leaving blanks.

Write `study/errores_y_dudas.md` with the fields `Fecha`, `Tema`, `Respuesta inicial`, `Por qué falló`, `Corrección`, and `Fecha de reintento`, followed by the empty-state sentence `Todavía no se registraron errores ni dudas.`

Write `study/glosario.md` as an alphabetical table containing at least Alice, Bob, Eve, APD, base, bit, canal clásico autenticado, canal cuántico, dark count, decoy state, fotón, interferómetro, KMS, PNS, QBER, qubit, reconciliación, SKR, SNSPD, time-bin, WCS and yield.

- [ ] **Step 4: Write the baseline diagnostic**

Write `study/capitulos/00_orientacion_y_diagnostico.md` with:

- A non-graded 20-question diagnostic: five cryptography, five probability/linear algebra, five fiber/optics and five Python/simulation questions.
- A mental map separating physical, protocol, computational and cryptographic planes.
- A two-minute prompt: “¿Qué problema intenta resolver esta tesis?”
- A rubric that maps each category to `Rojo`, `Amarillo`, `Verde` or `Azul` without producing a single global grade.
- Instructions to record misconceptions in `errores_y_dudas.md`.

- [ ] **Step 5: Validate and commit the hub**

Run:

```bash
uv run python study/tools/validate_study.py study
uv run pytest tests/test_study_validator.py -q
```

Expected: validator exits 0 and `3 passed`.

Commit:

```bash
git add study/README.md study/plan_maestro.md study/progreso.md study/errores_y_dudas.md study/glosario.md study/capitulos/00_orientacion_y_diagnostico.md
git commit -m "add qkd study hub"
```

---

### Task 3: Build Week 1 - Cryptography and Keys

**Files:**
- Create: `study/capitulos/01_criptografia_y_claves.md`
- Create: `study/ejercicios/semana_01.md`
- Modify: `study/README.md`

- [ ] **Step 1: Write the conceptual chapter**

Use `paper/chapters/01_introduccion.tex`, sections 2.1 and 2.3 of `paper/chapters/02_marco_teorico.tex`, and the approved research guide. Include the fixed chapter contract:

```markdown
# Semana 1: criptografía y distribución de claves
## 1. La pregunta central
## 2. Intuición: la caja y la llave
## 3. Confidencialidad, integridad y autenticación
## 4. Cifrado simétrico, OTP y AES
## 5. Clave pública y amenaza cuántica
## 6. Qué resuelve QKD y qué no resuelve
## 7. Conexión con la tesis
## 8. Ejemplo numérico
## 9. Errores frecuentes
## 10. Preguntas de tribunal
## 11. Salida oral de dos minutos
## 12. Fuentes
```

The numerical example must compare key consumption for OTP with periodic AES key refresh. Explicitly distinguish QKD from encryption, quantum communication and post-quantum cryptography.

- [ ] **Step 2: Add active-recall exercises**

Write `study/ejercicios/semana_01.md` with eight questions: three conceptual, two scenario classifications, two calculations and one jury question. Put each hint and solution in separate collapsed `<details>` blocks so the learner attempts the problem first.

- [ ] **Step 3: Link, validate and commit**

Add live links for week 1 to `study/README.md`. Run the validator and tests, then commit:

```bash
uv run python study/tools/validate_study.py study
uv run pytest tests/test_study_validator.py -q
git add study/README.md study/capitulos/01_criptografia_y_claves.md study/ejercicios/semana_01.md
git commit -m "add cryptography study chapter"
```

Expected: validator exits 0 and tests pass.

---

### Task 4: Build Week 2 - Quantum Foundations and BB84

**Files:**
- Create: `study/capitulos/02_fundamentos_cuanticos_y_bb84.md`
- Create: `study/ejercicios/semana_02.md`
- Modify: `study/README.md`

- [ ] **Step 1: Write quantum foundations from the learner's math strengths**

Use vectors and inner products before physical jargon. Derive the computational and diagonal bases, normalize a qubit, apply the Born rule and show why measuring `|0>` in the diagonal basis produces equal probabilities. State clearly that measurement disturbance alone is not a complete security proof.

Use these exact sections:

```markdown
# Semana 2: fundamentos cuánticos y BB84
## 1. De un bit a un qubit
## 2. Vectores, bases y normalización
## 3. Medición y regla de Born
## 4. Estados no ortogonales y no clonación
## 5. BB84 paso a paso
## 6. Ejemplo completo con 12 posiciones
## 7. Ataque intercept-resend
## 8. Conexión con la tesis
## 9. Límites de las analogías
## 10. Preguntas de tribunal
## 11. Salida oral de dos minutos
## 12. Fuentes
```

- [ ] **Step 2: Add the first Mermaid protocol diagram**

Embed a Mermaid sequence diagram showing Alice preparing states, Bob choosing bases, public basis comparison and sifting. Do not show error correction or privacy amplification as part of the quantum channel; place them after sifting on the authenticated classical channel.

- [ ] **Step 3: Add exercises and checkpoint 1**

Write `study/ejercicios/semana_02.md` with vector normalization, Born probabilities, basis matching, a 12-position BB84 table and intercept-resend QBER reasoning. End with checkpoint 1: explain BB84 first without equations, then using state vectors.

- [ ] **Step 4: Link, validate and commit**

```bash
uv run python study/tools/validate_study.py study
uv run pytest tests/test_study_validator.py -q
git add study/README.md study/capitulos/02_fundamentos_cuanticos_y_bb84.md study/ejercicios/semana_02.md
git commit -m "add bb84 foundations chapter"
```

Expected: validator exits 0 and tests pass.

---

### Task 5: Build Week 3 - Security, QBER and SKR

**Files:**
- Create: `study/capitulos/03_seguridad_qber_y_skr.md`
- Create: `study/ejercicios/semana_03.md`
- Modify: `study/README.md`

- [ ] **Step 1: Build the post-processing chain**

Explain raw detections, sifted key, parameter estimation, reconciliation, leakage accounting, privacy amplification and final key. Derive:

```math
QBER = \frac{N_{error}}{N_{sifted}}
```

```math
h_2(x) = -x\log_2 x -(1-x)\log_2(1-x)
```

and the thesis's simple Shor-Preskill-style rate expression. Explain every symbol, unit and assumption before substituting numbers.

- [ ] **Step 2: Separate security claims by strength**

Add a table distinguishing `observed low QBER`, `positive analytical lower bound`, `security under a device/model assumption`, and `certified implementation`. Include authenticated classical channel requirements and explain why QKD without authentication is vulnerable to man-in-the-middle attacks.

- [ ] **Step 3: Add exercises**

Write eight problems covering QBER, binary entropy, simple SKR, reconciliation leakage, the approximate 11% reference threshold and the question “¿Un QBER bajo demuestra seguridad?”. Include numerical solutions with units.

- [ ] **Step 4: Link, validate and commit**

```bash
uv run python study/tools/validate_study.py study
uv run pytest tests/test_study_validator.py -q
git add study/README.md study/capitulos/03_seguridad_qber_y_skr.md study/ejercicios/semana_03.md
git commit -m "add qber and secret rate chapter"
```

Expected: validator exits 0 and tests pass.

---

### Task 6: Build Week 4 - Optics, Fiber and Time-Bin

**Files:**
- Create: `study/capitulos/04_optica_fibra_y_time_bin.md`
- Create: `study/ejercicios/semana_04.md`
- Modify: `study/README.md`

- [ ] **Step 1: Explain how abstract states become optical signals**

Cover wavelength, frequency, photon energy, coherent laser pulses, mean photon number, fiber attenuation, insertion loss and detector efficiency. Derive:

```math
\eta_{ch}=10^{-\alpha L/10}
```

for `alpha` in dB/km and `L` in km. Work an explicit 30 km example at 0.2 dB/km before adding connector and detector losses.

- [ ] **Step 2: Explain time-bin in both bases**

Show early/late states for the time basis and relative-phase superpositions for the conjugate basis. Explain the three arrival windows of an unbalanced interferometer and why the middle window carries interference information. Connect visibility to the model relation `phase_error = (1 - V) / 2` without presenting it as a universal device law.

- [ ] **Step 3: Build a component-to-parameter table**

Map source, attenuator, intensity modulator, phase modulator, interferometer, fiber, detector, time tagger and synchronization electronics to the parameters in `experiments/qkd_2node_simulation.py`. Include efficiency, dark count, jitter/time resolution, count rate and visibility.

- [ ] **Step 4: Add exercises and checkpoint 2**

Write link-budget, arrival-window, visibility and detector-noise problems. End with checkpoint 2: follow one bit from Alice's random choice through the optical bench to Bob's click and the sifted key.

- [ ] **Step 5: Link, validate and commit**

```bash
uv run python study/tools/validate_study.py study
uv run pytest tests/test_study_validator.py -q
git add study/README.md study/capitulos/04_optica_fibra_y_time_bin.md study/ejercicios/semana_04.md
git commit -m "add time-bin optics chapter"
```

Expected: validator exits 0 and tests pass.

---

### Task 7: Build Week 5 - WCS, PNS and Decoy States

**Files:**
- Create: `study/capitulos/05_wcs_pns_y_estados_senuelo.md`
- Create: `study/ejercicios/semana_05.md`
- Modify: `study/README.md`

- [ ] **Step 1: Derive the photon-number model**

Introduce a phase-randomized weak coherent source and derive the Poisson probability:

```math
P_\mu(n)=e^{-\mu}\frac{\mu^n}{n!}
```

Calculate `P(0)`, `P(1)` and `P(n >= 2)` for at least two values of `mu`. Explain why lowering `mu` alone also lowers useful detections.

- [ ] **Step 2: Explain PNS as Eve's information advantage**

Use a pulse-by-pulse table to show vacuum, single-photon and multiphoton cases. State which capabilities are granted to Eve in the model and why ordinary loss can hide selective blocking.

- [ ] **Step 3: Build decoy-state intuition before formulas**

Explain why signal and decoy pulses must be indistinguishable except for intensity, and how comparing their gains constrains single-photon yield. Then map `Q_mu`, `Q_nu`, `Y_0`, `Y_1`, `E_mu` and `e_1` to functions in `experiments/qkd_2node_simulation.py`.

- [ ] **Step 4: State the exact thesis limitation**

Include a highlighted statement that the simulation does not implement a complete decoy protocol inside SeQUeNCe; experiment 4 combines simulated QBER/throughput with analytical WCS gains and asymptotic bounds.

- [ ] **Step 5: Add exercises, validate and commit**

Write Poisson, PNS, gain/yield and interpretation problems. Then run:

```bash
uv run python study/tools/validate_study.py study
uv run pytest tests/test_study_validator.py -q
git add study/README.md study/capitulos/05_wcs_pns_y_estados_senuelo.md study/ejercicios/semana_05.md
git commit -m "add decoy-state study chapter"
```

Expected: validator exits 0 and tests pass.

---

### Task 8: Build Week 6 - SeQUeNCe and the Four Experiments

**Files:**
- Create: `study/capitulos/06_sequence_y_resultados.md`
- Create: `study/ejercicios/semana_06.md`
- Create: `study/laboratorio/README.md`
- Create: `study/laboratorio/01_recorrido_codigo.md`
- Create: `study/laboratorio/02_distancia.md`
- Create: `study/laboratorio/03_detector_y_visibilidad.md`
- Create: `study/laboratorio/04_estados_senuelo.md`
- Modify: `study/README.md`

- [ ] **Step 1: Write the simulation mental model**

Explain discrete-event simulation, `Timeline`, `QKDNode`, quantum and classical channels, events, random seeds and measurements. Map each concept to exact functions or classes used in `experiments/qkd_2node_simulation.py`.

- [ ] **Step 2: Create the code-reading laboratory**

In `01_recorrido_codigo.md`, guide the learner through these functions in dependency order:

1. `channel_transmittance`
2. `SimulationParams`
3. `run_once`
4. `binary_entropy`
5. `secret_key_rate_simple`
6. `decoy_yield_y1_lower`
7. `decoy_e1_upper`
8. `secret_key_rate_asymptotic_decoy`
9. The four `experiment_*` functions
10. `main`

For each, require: inputs, outputs, units, physical meaning, assumptions and one prediction before execution.

- [ ] **Step 3: Create the three experiment laboratories**

Each laboratory must use the cycle `predecir -> ejecutar -> observar -> explicar -> limitar`.

Use the real command:

```bash
uv run python experiments/qkd_2node_simulation.py
```

Expected output files:

```text
experiments/results/exp1_distance_sweep.png
experiments/results/exp1_skr_distance.png
experiments/results/exp2_detector_sensitivity.png
experiments/results/exp3_visibility.png
experiments/results/exp4_decoy_impact.png
```

The distance lab must identify exponential channel loss; the detector/visibility lab must distinguish efficiency, dark counts and phase error; the decoy lab must separate simulated quantities from analytical post-processing.

- [ ] **Step 4: Add result-defense exercises and checkpoint 3**

Write exercises that present an unlabeled curve and ask the learner to infer the swept parameter, mechanism, expected trend and unjustified conclusions. End with checkpoint 3: defend one thesis figure from code, physics and cryptography perspectives.

- [ ] **Step 5: Execute, validate and commit**

```bash
uv run python experiments/qkd_2node_simulation.py
uv run python study/tools/validate_study.py study
uv run pytest tests/test_study_validator.py -q
git add study/README.md study/capitulos/06_sequence_y_resultados.md study/ejercicios/semana_06.md study/laboratorio
git commit -m "add qkd simulation laboratories"
```

Expected: the simulator exits 0, all five PNG files exist, the validator exits 0 and tests pass.

---

### Task 9: Build Week 7 - Network, Hardware and Validity

**Files:**
- Create: `study/capitulos/07_red_hardware_y_validez.md`
- Create: `study/ejercicios/semana_07.md`
- Modify: `study/README.md`

- [ ] **Step 1: Connect the point-to-point link to the campus system**

Use `paper/chapters/04_diseno_campus.tex` and `paper/chapters/05_hardware_presupuesto.tex`. Explain quantum channel, authenticated classical channel, optional wavelength coexistence, KMS, trusted nodes, application key consumption and physical security. Include a Mermaid architecture diagram for Alice, Bob, channels, KMS and consuming applications.

- [ ] **Step 2: Teach link-budget and component decisions**

Walk through the thesis's preliminary budget and hardware choices. For each component, distinguish required specification, modeled value, commercial reference and unvalidated assumption.

- [ ] **Step 3: Build the validity matrix**

Use `paper/chapters/09_discusion_validez.tex` to create a four-column table:

```text
Claim | Evidence available | Assumption | What would validate it experimentally
```

Include QBER, SKR, maximum useful distance, visibility sensitivity, decoy advantage and campus feasibility.

- [ ] **Step 4: Add system-design and limitation exercises**

Write scenarios involving a trusted intermediate node, loss budget, detector selection, classical-channel authentication and a claim that exceeds the simulation. Require answers in the structure `respuesta directa -> mecanismo -> evidencia -> límite`.

- [ ] **Step 5: Link, validate and commit**

```bash
uv run python study/tools/validate_study.py study
uv run pytest tests/test_study_validator.py -q
git add study/README.md study/capitulos/07_red_hardware_y_validez.md study/ejercicios/semana_07.md
git commit -m "add qkd system engineering chapter"
```

Expected: validator exits 0 and tests pass.

---

### Task 10: Add the Modern QKD Frontier and Visual Library

**Files:**
- Create: `study/capitulos/08_frontera_qkd_2018_actualidad.md`
- Create: `study/assets/README.md`
- Create: `study/assets/qkd_big_picture.svg`
- Create: `study/assets/qkd_protocol_map.svg`
- Create: `study/assets/qkd_timeline.svg`
- Create: `study/assets/fiber_loss_tf_scaling.svg`
- Create: `study/assets/tf_qkd_architecture.svg`
- Create: `study/assets/satellite_vs_fiber.svg`
- Modify: `study/README.md`

- [ ] **Step 1: Write the 2018-present frontier chapter**

Synthesize `docs/qkd_deep_research.md` and `docs/qkd_lectura_avion.md`. Cover:

- The repeaterless bound and why ordinary prepare-and-measure QKD scales with total channel transmittance.
- Twin-field QKD, central interference, single-photon paths and square-root scaling intuition.
- Phase stabilization, frequency locking, timing, indistinguishability and detector requirements.
- MDI-QKD, TF-QKD variants, finite-key demonstrations and network integration.
- Fiber QKD versus satellite QKD: loss mechanisms, geometry, trust assumptions, weather, daylight and key availability.
- The difference between laboratory record, field trial, network demonstration and deployable product.
- Direct paper links and a `Qué debe poder defender Mateo` summary.

- [ ] **Step 2: Promote the existing diagrams into the stable course**

Copy the six SVG sources from `docs/qkd_assets/` to `study/assets/` with stable names. Do not copy PNG derivatives unless a renderer fails to display an SVG.

Create `study/assets/README.md` with one row per asset: concept, chapter, source/provenance and alt-text description.

- [ ] **Step 3: Embed each visual where it teaches a relationship**

Use relative image links and descriptive alt text. Put the big-picture and protocol map in early chapters, fiber scaling and TF architecture in chapter 8, satellite comparison in chapter 8, and the timeline in the chapter's historical section.

- [ ] **Step 4: Verify assets, links and commit**

Run:

```bash
for file in study/assets/*.svg; do xmllint --noout "$file"; done
uv run python study/tools/validate_study.py study
uv run pytest tests/test_study_validator.py -q
```

Expected: every SVG parses, validator exits 0 and tests pass.

Commit:

```bash
git add study/README.md study/capitulos/08_frontera_qkd_2018_actualidad.md study/assets
git commit -m "add modern qkd study material"
```

---

### Task 11: Build the 30 + 15 Minute Defense Kit

**Files:**
- Create: `study/defensa/guion_30_minutos.md`
- Create: `study/defensa/banco_preguntas.md`
- Create: `study/defensa/rubrica_simulacro.md`
- Create: `study/defensa/respuestas_dificiles.md`
- Modify: `study/README.md`
- Modify: `study/progreso.md`

- [ ] **Step 1: Write the timed narrative**

Create a 28-30 minute outline with explicit time budgets:

```text
0:00-2:30   Problem, motivation and thesis question
2:30-6:30   QKD and BB84 intuition
6:30-10:30  Time-bin implementation
10:30-14:00 WCS, PNS and decoy states
14:00-18:00 Simulation model and methodology
18:00-24:00 Four experiment results
24:00-27:00 Campus/hardware implications
27:00-29:30 Limitations, conclusions and next step
```

For each block, include objective, one indispensable visual, transition sentence, likely interruption and the one claim that must not be overstated.

- [ ] **Step 2: Build the cumulative question bank**

Write at least 80 questions grouped into:

- 15 fundamentals and vocabulary.
- 15 BB84 and security.
- 15 optics, fiber and detectors.
- 15 WCS, PNS, decoy states and rates.
- 10 simulation and code.
- 10 thesis limitations and system design.

Each question must include answer criteria, one likely reprompt and one unacceptable shortcut. Do not provide a memorized speech as the model answer.

- [ ] **Step 3: Add difficult-response structures**

Cover unknown answers, disputed assumptions, mistakes found live, questions outside scope and requests to justify a number not measured experimentally. Use the four-part response structure `respuesta directa -> mecanismo -> evidencia -> límite` and include concrete QKD examples.

- [ ] **Step 4: Create the rehearsal rubric**

Score 0-3 on conceptual correctness, causal reasoning, quantitative control, thesis traceability, limitation awareness, clarity and timing. Define a grave conceptual error and require two consecutive rehearsals without one.

- [ ] **Step 5: Link, validate and commit**

```bash
uv run python study/tools/validate_study.py study
uv run pytest tests/test_study_validator.py -q
git add study/README.md study/progreso.md study/defensa
git commit -m "add qkd defense kit"
```

Expected: validator exits 0 and tests pass.

---

### Task 12: Perform End-to-End Review and Publish

**Files:**
- Modify: `study/README.md`
- Modify: any `study/**/*.md` file with a verified inconsistency

- [ ] **Step 1: Check design coverage**

Compare every section of `docs/superpowers/specs/2026-07-14-qkd-study-program-design.md` against the course. Record the mapping in a final `Cobertura del diseño` table in `study/README.md`; every design requirement must point to a real file and section.

- [ ] **Step 2: Run complete automated verification**

```bash
uv run python study/tools/validate_study.py study
uv run pytest tests/test_study_validator.py -q
uv run python experiments/qkd_2node_simulation.py
for file in study/assets/*.svg; do xmllint --noout "$file"; done
git diff --check
```

Expected: validator exits 0, validator tests pass, simulation regenerates five figures, all SVG files parse and `git diff --check` emits no output.

- [ ] **Step 3: Perform manual learning-quality review**

For every conceptual chapter, confirm:

- The opening question is answered.
- Every equation defines symbols and units.
- Every analogy states its limit.
- At least one numerical example is fully worked.
- The connection to the thesis is explicit.
- Exercises have hidden hints and solutions.
- Jury questions include reprompts.
- Security claims distinguish assumptions from evidence.

- [ ] **Step 4: Render and inspect visual material**

Open `study/README.md` through a GitHub-compatible Markdown preview. Verify Mermaid diagrams render, SVG text is legible, equations are not clipped and no image has missing alt text. Correct only observed issues and rerun Step 2 after any edit.

- [ ] **Step 5: Commit final integration changes**

```bash
git add study
git commit -m "finish qkd study program"
```

If there are no integration changes after review, skip this commit rather than creating an empty one.

- [ ] **Step 6: Publish the branch to GitHub**

```bash
git status --short
git log --oneline --decorate -12
git push origin codex/proyecto-3-document
```

Expected: working tree contains only pre-existing unrelated untracked files, the course commits appear in the log, and the branch push succeeds. Do not stage or commit `proyecto3.pdf` or unrelated untracked research files unless the user separately approves them.

---

## Execution Order and First Usable Milestone

Tasks 1 and 2 create the first usable milestone: the learner can run the diagnostic, understand the eight-week workflow and begin tracking misconceptions. Task 3 immediately unlocks the first real study week. Tasks 4-10 then deepen the course in dependency order; Task 11 converts that knowledge into defense performance; Task 12 publishes only after both automated and manual verification.

The implementation must not wait for all twelve tasks before the user starts studying. After Task 3, begin the first interactive lesson while later course material is still being built.
