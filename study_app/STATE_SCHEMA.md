# Esquema de estado de la ruta guiada

La aplicación guarda el estado personal fuera de Git, en `.study_state/`.
Todos los archivos tienen `schema_version: 1`.

```text
.study_state/
├── progress.json       estado de módulos y capacidades
├── session.json        último borrador guardado
├── attempts/           un JSON inmutable por envío
├── feedback/           feedback asociado a cada intento
├── errors.json         ledger deduplicado de errores
├── defense.json        registros de simulacros
└── exports/            resumen Markdown generado
```

Los intentos enviados no se editan ni se reemplazan. Un nuevo envío crea otro
archivo con un nuevo `attempt_id`. El borrador sí puede reemplazarse porque no
representa todavía una respuesta entregada.

Los estados válidos de un módulo son `locked`, `available`, `in_progress`,
`submitted`, `recovery`, `review` y `mastered`. La transición es explícita y
el feedback no marca por sí solo un módulo como dominado.

El feedback contiene cuatro criterios: `explain`, `calculate`, `connect` y
`defend`. Cada criterio tiene un estado `red`, `yellow`, `green` o `blue`, más
una nota. El próximo paso es `advance`, `recovery` o `review`.

## Privacidad y respaldo

Las respuestas no salen de `localhost`. Para respaldar el estado, abrí
Historial y elegí “Descargar respaldo”, o copiá `.study_state/` con el servidor
detenido. El JSON descargado contiene el progreso y las respuestas para
consulta; la importación de la aplicación restaura solamente el borrador y no
sobrescribe intentos inmutables.

## Recuperación

Si un archivo JSON se daña, conservá una copia del directorio y restaurá el
último backup válido. No edites una respuesta enviada para corregirla: agregá
un nuevo intento. El resumen humano está en
`.study_state/exports/progress-summary.md`.
