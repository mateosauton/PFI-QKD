# Programa interactivo de estudio de QKD

Este curso acompaña la tesis **Diseño y evaluación por simulación de un banco de
pruebas de QKD BB84 en time-bin con estados señuelo**. Está pensado para construir
comprensión desde cero y terminar con una defensa de 30 minutos más 15 minutos de
preguntas.

## Cómo empezar hoy

1. Hacé el [diagnóstico inicial](capitulos/00_orientacion_y_diagnostico.md) sin
   consultar apuntes.
2. Leé el [plan maestro](plan_maestro.md) y elegí tres sesiones posibles para esta
   semana.
3. Registrá el resultado por categoría en [progreso](progreso.md).
4. Empezá la [Semana 1: criptografía y distribución de claves](capitulos/01_criptografia_y_claves.md).

El diagnóstico no decide si "servís" para este tema. Solo evita que estudiemos algo
que ya dominás o construyamos sobre una base que todavía no existe.

## Cómo funciona cada sesión

Cada semana tiene tres sesiones esenciales:

- **A - Intuición:** entender qué problema resuelve el concepto y representarlo con
  un ejemplo o diagrama.
- **B - Ingeniería:** usar matemática, unidades, hardware, código o datos reales.
- **C - Defensa:** recuperar sin apuntes, responder variantes y corregir lenguaje
  impreciso.

Una sesión termina con una producción observable: una explicación, una cuenta, una
predicción, una modificación de código o una respuesta oral. Leer pasivamente no
cuenta como sesión completa.

## Regla de dominio

Un tema pasa a verde cuando podés:

1. **Explicar** qué significa sin esconderte detrás de una fórmula.
2. **Calcular** un ejemplo o reconstruir la relación principal.
3. **Conectar** el concepto con la tesis, el hardware, el código o un resultado.
4. **Defender** una objeción y declarar el límite de lo que afirmás.

Los estados están definidos en [progreso](progreso.md). Los errores útiles se guardan
en [errores y dudas](errores_y_dudas.md), porque una respuesta incorrecta bien
analizada vale más que una correcta memorizada.

## Navegación

### Base del curso

- [Orientación y diagnóstico](capitulos/00_orientacion_y_diagnostico.md)
- [Plan maestro](plan_maestro.md)
- [Progreso](progreso.md)
- [Errores y dudas](errores_y_dudas.md)
- [Glosario](glosario.md)

### Capítulos

- [Semana 1: criptografía y distribución de claves](capitulos/01_criptografia_y_claves.md)
- [Semana 2: fundamentos cuánticos y BB84](capitulos/02_fundamentos_cuanticos_y_bb84.md)
- [Semana 3: seguridad, QBER y tasa de llave secreta](capitulos/03_seguridad_qber_y_skr.md)
- [Semana 4: óptica, fibra y codificación time-bin](capitulos/04_optica_fibra_y_time_bin.md)
- [Semana 5: fuentes coherentes débiles, PNS y estados señuelo](capitulos/05_wcs_pns_y_estados_senuelo.md)
- [Semana 6: SeQUeNCe, metodología y resultados](capitulos/06_sequence_y_resultados.md)
- [Semana 7: red, hardware y validez](capitulos/07_red_hardware_y_validez.md)
- [Frontera 2018-actualidad: TF-QKD, fibra y satélite](capitulos/08_frontera_qkd_2018_actualidad.md)

### Práctica y defensa

- [Ejercicios de la semana 1](ejercicios/semana_01.md)
- [Ejercicios de la semana 2](ejercicios/semana_02.md)
- [Ejercicios de la semana 3](ejercicios/semana_03.md)
- [Ejercicios de la semana 4](ejercicios/semana_04.md)
- [Ejercicios de la semana 5](ejercicios/semana_05.md)
- [Ejercicios de la semana 6](ejercicios/semana_06.md)
- [Ejercicios de la semana 7](ejercicios/semana_07.md)
- [Laboratorios de simulación](laboratorio/README.md)
- [Biblioteca visual](assets/README.md)
- [Guion de 30 minutos](defensa/guion_30_minutos.md)
- [Banco acumulativo de preguntas](defensa/banco_preguntas.md)
- [Rúbrica de simulacro 30 + 15](defensa/rubrica_simulacro.md)
- [Respuestas difíciles y manejo de límites](defensa/respuestas_dificiles.md)

## Fuentes principales

- [Tesis compilada](../paper/main.pdf)
- [Código de la simulación](../experiments/qkd_2node_simulation.py)
- [Resultados actuales](../experiments/results/)
- [Bibliografía de la tesis](../paper/references.bib)

Los capítulos traducen estas fuentes a un orden pedagógico. Cuando una explicación
simplifica un resultado, debe indicarlo explícitamente.

## Qué hacer cuando una semana se complica

Protegé las tres sesiones esenciales. Si solo completás dos, la semana siguiente
empieza con la tercera antes de abrir contenido opcional. No intentes pagar una deuda
de estudio acumulando seis horas de lectura pasiva: recuperá el mecanismo que falta y
volvé al ritmo normal.

## Cobertura del diseño

| Requisito aprobado | Implementación |
|---|---|
| Ocho semanas y ritmo flexible | [Plan maestro](plan_maestro.md) |
| Diagnóstico por áreas | [Orientación](capitulos/00_orientacion_y_diagnostico.md) |
| Criptografía desde cero | [Semana 1](capitulos/01_criptografia_y_claves.md) |
| Matemática cuántica y BB84 | [Semana 2](capitulos/02_fundamentos_cuanticos_y_bb84.md) |
| QBER, reconciliación, privacidad y SKR | [Semana 3](capitulos/03_seguridad_qber_y_skr.md) |
| Fibra, óptica, time-bin y detectores | [Semana 4](capitulos/04_optica_fibra_y_time_bin.md) |
| WCS, PNS y estados señuelo | [Semana 5](capitulos/05_wcs_pns_y_estados_senuelo.md) |
| Código, cuatro experimentos y figuras | [Semana 6](capitulos/06_sequence_y_resultados.md) y [laboratorios](laboratorio/README.md) |
| Campus, hardware, KMS y validez | [Semana 7](capitulos/07_red_hardware_y_validez.md) |
| Avances 2018-2026, TF-QKD y satélite | [Frontera](capitulos/08_frontera_qkd_2018_actualidad.md) |
| Explicar, calcular, conectar y defender | [Progreso](progreso.md) y ejercicios semanales |
| Registro adaptativo de errores | [Errores y dudas](errores_y_dudas.md) |
| Diagramas estables | [Biblioteca visual](assets/README.md) |
| Exposición 30 minutos | [Guion](defensa/guion_30_minutos.md) |
| Quince minutos de preguntas | [Banco de 80 preguntas](defensa/banco_preguntas.md) |
| Dos simulacros y criterios de salida | [Rúbrica](defensa/rubrica_simulacro.md) |
| Manejo honesto de límites | [Respuestas difíciles](defensa/respuestas_dificiles.md) |
| Validación automática | [`validate_study.py`](tools/validate_study.py) y pruebas |
