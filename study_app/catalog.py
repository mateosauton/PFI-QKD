"""Explicit catalog connecting guided sessions to the study material."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Final


ROOT: Final[Path] = Path(__file__).resolve().parents[1]
CAPABILITIES: Final[tuple[str, ...]] = ("explain", "calculate", "connect", "defend")


@dataclass(frozen=True)
class Prompt:
    prompt_id: str
    source: Path
    question: str
    rubric: dict[str, str]

    def to_dict(self) -> dict[str, object]:
        return {
            "prompt_id": self.prompt_id,
            "source": self.source.relative_to(ROOT).as_posix(),
            "question": self.question,
            "rubric": self.rubric,
        }


@dataclass(frozen=True)
class Module:
    id: str
    order: int
    title: str
    source: Path
    prompt: Prompt

    def to_dict(self) -> dict[str, object]:
        return {
            "id": self.id,
            "order": self.order,
            "title": self.title,
            "source": self.source.relative_to(ROOT).as_posix(),
            "prompt": self.prompt.to_dict(),
        }


def _prompt(prompt_id: str, source: str, question: str) -> Prompt:
    return Prompt(
        prompt_id=prompt_id,
        source=ROOT / source,
        question=question,
        rubric={capability: "evaluar" for capability in CAPABILITIES},
    )


MODULES: Final[tuple[Module, ...]] = (
    Module(
        "crypto-keys",
        1,
        "Criptografía y claves",
        ROOT / "study/capitulos/01_criptografia_y_claves.md",
        _prompt(
            "crypto-keys-01",
            "study/ejercicios/semana_01.md",
            "¿Qué diferencia hay entre cifrar un mensaje y distribuir una clave? Explicalo con un ejemplo.",
        ),
    ),
    Module(
        "bb84-bases",
        2,
        "Fundamentos cuánticos y BB84",
        ROOT / "study/capitulos/02_fundamentos_cuanticos_y_bb84.md",
        _prompt(
            "bb84-eve-qber-01",
            "study/ejercicios/semana_02.md",
            "¿Por qué BB84 puede detectar que Eve intervino estadísticamente aunque no pueda localizarla?",
        ),
    ),
    Module(
        "qber-skr",
        3,
        "QBER, seguridad y SKR",
        ROOT / "study/capitulos/03_seguridad_qber_y_skr.md",
        _prompt(
            "qber-skr-01",
            "study/ejercicios/semana_03.md",
            "¿Cómo se relacionan QBER, reconciliación, amplificación de privacidad y tasa de clave secreta?",
        ),
    ),
    Module(
        "optics-timebin",
        4,
        "Óptica, fibra y time-bin",
        ROOT / "study/capitulos/04_optica_fibra_y_time_bin.md",
        _prompt(
            "timebin-loss-01",
            "study/ejercicios/semana_04.md",
            "Calculá la transmisión de una fibra de 50 km con 0.2 dB/km y explicá qué representa físicamente el resultado.",
        ),
    ),
    Module(
        "decoy-states",
        5,
        "WCS, PNS y estados señuelo",
        ROOT / "study/capitulos/05_wcs_pns_y_estados_senuelo.md",
        _prompt(
            "decoy-pns-01",
            "study/ejercicios/semana_05.md",
            "¿Qué vulnerabilidad introducen los pulsos multifotónicos y cómo la mitigación decoy-state cambia la estimación de seguridad?",
        ),
    ),
    Module(
        "simulation",
        6,
        "SeQUeNCe y experimentos",
        ROOT / "study/capitulos/06_sequence_y_resultados.md",
        _prompt(
            "simulation-causality-01",
            "study/ejercicios/semana_06.md",
            "Elegí un parámetro de la simulación y predecí cómo cambiarán QBER, detecciones y SKR antes de ejecutar el barrido.",
        ),
    ),
    Module(
        "system-engineering",
        7,
        "Red, hardware y validez",
        ROOT / "study/capitulos/07_red_hardware_y_validez.md",
        _prompt(
            "system-limits-01",
            "study/ejercicios/semana_07.md",
            "¿Qué demuestra el banco de pruebas de la tesis y qué no demuestra sobre una red QKD operativa?",
        ),
    ),
    Module(
        "frontier-defense",
        8,
        "Frontera y defensa",
        ROOT / "study/capitulos/08_frontera_qkd_2018_actualidad.md",
        _prompt(
            "defense-tf-01",
            "study/defensa/banco_preguntas.md",
            "Explicá qué problema resuelve TF-QKD, qué supuesto de hardware relaja y qué dificultad experimental introduce.",
        ),
    ),
)


def get_module(module_id: str) -> Module | None:
    return next((module for module in MODULES if module.id == module_id), None)
