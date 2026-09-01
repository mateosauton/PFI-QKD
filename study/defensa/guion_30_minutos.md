# Guion de defensa de 30 minutos

Objetivo operativo: terminar entre 28:00 y 29:30. El margen absorbe una interrupción
corta sin superar 30 minutos. El guion define ideas y transiciones, no texto para
memorizar.

## 0:00-2:30 - Problema, motivación y pregunta de tesis

- **Objetivo:** separar cifrado de distribución de claves y formular la hipótesis.
- **Visual indispensable:** arquitectura completa Alice-canal-Bob-aplicación.
- **Decir:** QKD genera claves; la tesis evalúa por simulación un banco BB84 time-bin
  antes de construirlo.
- **Transición:** “Definido el problema, necesito mostrar el mecanismo que permite
  detectar información adversaria”.
- **Interrupción probable:** “¿Por qué no PQC?”. Responder complementariedad y volver.
- **No exagerar:** no afirmar que QKD reemplaza toda criptografía.

## 2:30-6:30 - QKD y BB84

- **Objetivo:** explicar bases, medición, tamizado y Eve sin una clase completa de
  mecánica cuántica.
- **Visual indispensable:** tabla de cuatro estados y flujo BB84.
- **Decir:** misma base correlaciona; base incompatible da azar; intercept-resend ideal
  introduce 25% sobre posiciones atacadas tamizadas.
- **Transición:** “El protocolo abstracto debe convertirse en pulsos que viajen por
  fibra”.
- **Interrupción probable:** “¿No clonación prueba seguridad?”. Responder que es un
  ingrediente, no la prueba completa.
- **No exagerar:** no atribuir todo QBER a Eve.

## 6:30-10:30 - Implementación time-bin

- **Objetivo:** traducir qubits a temprano/tardío, fase e interferencia.
- **Visual indispensable:** dos bins y tres ventanas del interferómetro.
- **Decir:** Z mide tiempo; X mide fase en la ventana central; pérdida, detector,
  sincronización y visibilidad condicionan clicks/QBER.
- **Cuenta breve:** 30 km a 0,2 dB/km son 6 dB, `eta≈0,251` antes de pérdidas fijas.
- **Transición:** “El láser atenuado introduce otro problema: no emite exactamente un
  fotón”.
- **Interrupción probable:** “¿Por qué time-bin?”. Responder tolerancia en fibra y
  costo de estabilización.
- **No exagerar:** timeline de picosegundos no demuestra sincronización física.

## 10:30-14:00 - WCS, PNS y estados señuelo

- **Objetivo:** justificar por qué existe el experimento 4.
- **Visual indispensable:** Poisson con vacío, uno y varios fotones.
- **Decir:** PNS explota copias ya emitidas; decoys cambian mezclas Poisson para acotar
  `Y1/e1`.
- **Transición:** “Con estas variables físicas y criptográficas construimos el modelo
  reproducible”.
- **Interrupción probable:** “Muéstreme el protocolo decoy en SeQUeNCe”. Corregir:
  tratamiento analítico sobre corridas, no capa completa.
- **No exagerar:** decoy no elimina multifotones.

## 14:00-18:00 - Modelo y metodología

- **Objetivo:** explicar SeQUeNCe, escenario, parámetros y cuatro barridos.
- **Visual indispensable:** timeline/objetos y tabla de parámetros.
- **Decir:** eventos discretos, dos nodos, canales, semillas, variables controladas,
  QBER/throughput simulados y SKR analítica.
- **Transición:** “Ahora puedo mostrar qué relación causal produjo cada barrido”.
- **Interrupción probable:** “¿Por qué no una fórmula?”. Responder integración de
  eventos/protocolo más controles analíticos.
- **No exagerar:** semillas fijas no prueban robustez estadística.

## 18:00-24:00 - Resultados

- **Objetivo:** dedicar unos 90 segundos por experimento y una síntesis.
- **Visuales:** cinco figuras existentes, agrupadas en dos slides si es legible.
- **Distancia:** pérdida reduce señal y SKR; el último punto bajo criterio no es
  alcance demostrado.
- **Detector:** eficiencia y dark counts cambian relación señal-ruido; la muestra
  corta puede producir tendencias ruidosas.
- **Visibilidad:** el modelo usa `(1-V)/2`; menor V eleva error de fase.
- **Decoy:** comparación de cota simple y cota decoy analítica.
- **Transición:** “Estas curvas sirven si se traducen en decisiones y ensayos”.
- **Interrupción probable:** “¿Por qué eficiencia dio un cambio negativo en una
  corrida?”. Responder variabilidad, pocas claves y necesidad de múltiples semillas.
- **No exagerar:** no ocultar resultados incómodos ni inventar causalidad.

## 24:00-27:00 - Campus y hardware

- **Objetivo:** mostrar utilidad de ingeniería.
- **Visual indispensable:** arquitectura campus y tabla componente-parámetro.
- **Decir:** relevar ruta, pérdida, conectores, fibra dedicada/compartida, racks,
  detector, interferómetro, timing y KMS.
- **Transición:** “La contribución se entiende mejor al declarar sus límites”.
- **Interrupción probable:** “¿Cuál es el costo final?”. Responder que hay referencias,
  no compra cerrada sin relevamiento/cotización.
- **No exagerar:** mapa geográfico no es presupuesto óptico.

## 27:00-29:30 - Límites, conclusión y próximo paso

- **Objetivo:** cerrar con aporte, no con disculpa.
- **Visual indispensable:** tabla `evidencia | supuesto | ensayo siguiente`.
- **Decir:** modelo reproducible, variables críticas, arquitectura y criterios de
  aceptación; faltan hardware, tamaño finito completo, canales laterales y KMS.
- **Cierre:** “El resultado no es que la red ya esté validada, sino que sabemos qué
  construir, medir y exigir para validarla”.
- **Interrupción probable:** “¿Entonces funciona?”. Responder condicionalmente bajo el
  modelo y enumerar prueba corta requerida.
- **No exagerar:** no usar “seguro por leyes de física” sin supuestos.

## Plan de recorte si el tiempo se desvía

- A 10:30 deberías cerrar time-bin.
- A 18:00 deberías abrir resultados.
- Si vas 90 s tarde, reducís ejemplos históricos, no límites ni metodología.
- Si vas 3 min tarde, mostrás detector/visibilidad en una síntesis conjunta.
- Nunca recortes la aclaración decoy ni la diferencia simulación-certificación.

## Práctica

1. Ensayo solo con títulos de slides.
2. Ensayo grabado sin interrupciones.
3. Ensayo con una interrupción por bloque.
4. Simulacro completo usando la [rúbrica](rubrica_simulacro.md).
