# Diseño de la plataforma de estudio guiado de QKD

Fecha: 2026-08-08

## 1. Decisión aprobada

Construir una aplicación web local, en español, para estudiar y defender la tesis de QKD mediante una ruta guiada. La interfaz será el punto de entrada cotidiano: mostrará una sola sesión activa, recibirá la respuesta del estudiante, conservará el historial y explicará el siguiente paso.

La aplicación no reemplazará los capítulos Markdown existentes. Los capítulos, ejercicios, laboratorios y materiales de defensa seguirán siendo la fuente académica estable. La aplicación agregará una capa de navegación, práctica, registro y desbloqueo progresivo.

La dinámica aprobada es:

```text
ver sesión activa
      |
      v
leer contexto breve y consigna
      |
      v
escribir una respuesta sin buscar perfección
      |
      v
enviar intento versionado
      |
      v
revisar feedback por criterios
      |
      +--> avanzar y desbloquear
      |
      +--> recibir pista y repetir
      |
      +--> volver a un prerrequisito
```

El modo de ayuda será de pistas progresivas: primero se intenta sin ayuda; luego se ofrece una pregunta guía, un ejemplo parcial o una explicación completa según la dificultad observada.

## 2. Problema que resuelve

El flujo actual obliga a decidir manualmente qué archivo abrir, dónde escribir una respuesta y cómo informar el progreso. Eso introduce fricción y hace difícil distinguir entre:

- haber leído un concepto;
- poder explicarlo;
- poder calcularlo;
- poder conectarlo con la tesis;
- poder defenderlo ante una repregunta.

La aplicación debe convertir cada sesión en evidencia observable. No intentará medir solamente tiempo de lectura. Guardará respuestas, intentos, errores, nivel de ayuda utilizado, evaluación y próxima acción.

## 3. Usuarios y contexto de uso

El usuario principal es Mateo, estudiante de ingeniería con buena base de matemática y lógica, pero con conocimiento inicial limitado de criptografía, telecomunicaciones ópticas y QKD.

El uso esperado es local, desde una computadora personal, durante sesiones de 45 a 60 minutos. La información no debe depender de una cuenta remota ni de un servicio externo. El asistente leerá los registros en turnos posteriores para corregir respuestas y decidir qué desbloquear.

## 4. Alcance de la primera versión

### Incluido

- Dashboard con estado general, sesión activa y mapa de módulos.
- Ruta guiada con un único módulo recomendado como siguiente acción.
- Capítulos y ejercicios enlazados al material Markdown existente.
- Editor de respuesta con guardado automático de borrador.
- Envío de intentos inmutables y versionados.
- Historial de intentos por concepto.
- Feedback estructurado por las cuatro pruebas de dominio: explicar, calcular, conectar y defender.
- Registro de errores y dudas.
- Estados de progreso y desbloqueo controlados por datos.
- Modo de recuperación cuando una respuesta muestra un prerrequisito faltante.
- Modo defensa para preguntas acumulativas y simulacros de 30 + 15 minutos.
- Persistencia local en archivos JSON legibles y exportación Markdown de resumen.
- Fallback con `localStorage` y exportación manual si el servidor local no está activo.

### Fuera de alcance

- Corrección automática por un modelo de lenguaje dentro del navegador.
- Cuentas, login, sincronización en la nube o publicación de respuestas.
- Sistema de calificaciones universitarias.
- Reemplazo de la revisión del asistente en la conversación.
- Edición colaborativa en tiempo real.
- Aplicación móvil nativa.

La decisión de no automatizar la corrección semántica es deliberada. Una respuesta de tesis puede ser formalmente correcta pero conceptualmente incompleta; el asistente debe leer el razonamiento y formular repreguntas, no producir una nota falsa de precisión.

## 5. Arquitectura propuesta

### 5.1 Material académico

Los archivos actuales de `study/` siguen siendo documentos de contenido:

```text
study/
├── capitulos/       contenido conceptual
├── ejercicios/      preguntas, pistas y soluciones
├── laboratorio/     código y experimentos
├── defensa/         guion, banco y simulacros
└── assets/          diagramas
```

La aplicación tendrá un catálogo pequeño y explícito que conecta cada módulo con sus archivos, objetivos, prerrequisitos y criterios de salida. No dependerá de inferir rutas a partir de nombres de archivos.

### 5.2 Aplicación web

La primera versión usará HTML, CSS y JavaScript modular sin framework pesado. El repositorio ya es principalmente Python y Markdown; una interfaz vanilla reduce instalación, facilita la lectura del código y permite ejecutarla con las herramientas existentes.

Componentes principales:

- `Dashboard`: estado, ruta y siguiente acción.
- `ModuleRail`: módulos bloqueados, disponibles, en revisión y dominados.
- `LessonView`: contexto, objetivo, pregunta y enlaces al material.
- `ResponseEditor`: borrador, contador, guardado y envío.
- `FeedbackView`: criterios, errores, fortalezas, pista y próxima acción.
- `AttemptHistory`: versiones anteriores y evolución del razonamiento.
- `ErrorLedger`: confusiones recurrentes y repasos pendientes.
- `DefenseView`: preguntas, cronómetro opcional y simulacro.

La navegación puede ser por hash para mantener la aplicación estática y simple:

```text
/#/                 dashboard
/#/lesson/:id       sesión activa
/#/history          intentos y errores
/#/defense          banco y simulacros
/#/settings         exportación y diagnóstico local
```

### 5.3 Servidor local y persistencia

Se agregará un servidor local mínimo en Python, basado en la biblioteca estándar, para servir la interfaz y escribir registros. No habrá llamadas externas.

Los datos dinámicos se guardarán fuera del contenido académico, en una carpeta ignorada por Git:

```text
.study_state/
├── progress.json
├── session.json
├── attempts/
│   └── <attempt-id>.json
├── feedback/
│   └── <attempt-id>.json
├── errors.json
└── exports/
    └── progress-summary.md
```

Esta separación evita mezclar respuestas personales con los capítulos versionados. Los archivos JSON son la fuente de datos operativa porque son fáciles de leer, consultar y procesar; el resumen Markdown es la vista humana y de respaldo.

Cada escritura debe ser atómica: escribir a un archivo temporal, validar JSON y reemplazar el destino. Los registros tendrán `schema_version`, `created_at`, `updated_at`, `module_id`, `attempt_id` y `source`.

Si el servidor no está activo, la interfaz guardará el borrador en `localStorage` y mostrará una advertencia clara. El usuario podrá exportar un paquete JSON para incorporarlo al registro local después.

## 6. Modelo de datos

### 6.1 Progreso

```json
{
  "schema_version": 1,
  "current_module": "bb84-bases",
  "modules": {
    "crypto-keys": {
      "status": "mastered",
      "explain": "green",
      "calculate": "yellow",
      "connect": "green",
      "defend": "yellow",
      "next_review_at": "2026-08-10"
    }
  }
}
```

Los estados de módulo serán `locked`, `available`, `in_progress`, `submitted`, `recovery`, `mastered` y `review`. El semáforo por capacidad conservará la distinción entre explicar, calcular, conectar y defender.

### 6.2 Intento

Cada envío crea un registro nuevo; los intentos anteriores nunca se sobrescriben.

```json
{
  "schema_version": 1,
  "attempt_id": "2026-08-08T19-30-00Z-bb84-bases-01",
  "module_id": "bb84-bases",
  "prompt_id": "bb84-eve-qber-01",
  "body": "...respuesta del estudiante...",
  "help_level": "none",
  "submitted_at": "2026-08-08T19:30:00Z",
  "self_assessment": "uncertain",
  "source": "guided-web"
}
```

El borrador puede actualizarse. El intento enviado es inmutable y recibe feedback en un archivo separado para conservar la diferencia entre lo que se respondió y lo que se aprendió después.

### 6.3 Feedback

```json
{
  "schema_version": 1,
  "attempt_id": "2026-08-08T19-30-00Z-bb84-bases-01",
  "criteria": {
    "explain": {"status": "green", "note": "..."},
    "calculate": {"status": "yellow", "note": "..."},
    "connect": {"status": "yellow", "note": "..."},
    "defend": {"status": "red", "note": "..."}
  },
  "strengths": ["..."],
  "errors": ["..."],
  "next_action": "recovery",
  "hint": {
    "level": 1,
    "text": "..."
  },
  "reviewed_at": "2026-08-08T20:00:00Z",
  "reviewed_by": "assistant"
}
```

## 7. Regla de desbloqueo

El frontend no decidirá por sí solo que un tema está dominado. La aplicación podrá mostrar estados y aceptar una transición explícita, pero la evaluación semántica quedará bajo revisión del asistente.

Una transición típica será:

```text
locked -> available -> in_progress -> submitted
                                      |
                         +------------+------------+
                         v                         v
                     recovery                   review
                         |                         |
                         +------> mastered <------+
```

Un módulo podrá pasar a `mastered` cuando la evidencia registrada muestre las cuatro capacidades en verde o azul, o cuando una revisión explícita del asistente documente una excepción. En caso contrario, se asignará una recuperación concreta, no una repetición genérica del capítulo.

La interfaz siempre mostrará el motivo de un bloqueo: prerrequisito faltante, respuesta pendiente, recuperación recomendada o revisión espaciada.

## 8. Flujo de interacción entre Mateo y el asistente

### En la aplicación

1. Mateo abre el dashboard.
2. Lee la sesión activa y responde sin editar los documentos académicos.
3. Guarda borrador automáticamente mientras escribe.
4. Envía el intento y puede agregar autoevaluación o duda puntual.
5. Ve que el intento quedó “pendiente de revisión”.

### En la conversación

1. El asistente lee el intento y el progreso desde `.study_state/`.
2. Corrige el razonamiento por las cuatro capacidades.
3. Guarda o genera el feedback estructurado.
4. Formula una repregunta, pista o mini ejercicio si es necesario.
5. Actualiza el estado del módulo y define la siguiente sesión.

### En la siguiente visita

La aplicación muestra el feedback, el próximo objetivo y cualquier recuperación pendiente. Mateo no necesita reconstruir el contexto desde el historial del chat.

## 9. Diseño de interfaz

La dirección visual aprobada es una herramienta de estudio editorial y técnica: fondo claro cálido, tinta oscura, verde para evidencia positiva y ámbar para atención o próximos pasos. Los paneles son planos y densos; no se utilizará una estética de marketing ni una pared de tarjetas decorativas.

Principios:

- Una acción principal por pantalla.
- El siguiente paso siempre visible.
- El motivo de cada estado bloqueado es explícito.
- La respuesta ocupa el centro de la sesión, no un documento externo.
- Los colores nunca serán la única señal; cada estado tendrá texto e icono.
- La interfaz debe funcionar en notebook y en una pantalla angosta.
- Las animaciones serán discretas: entrada de sesión, cambio de estado y confirmación de guardado.

Pantallas iniciales:

- Dashboard: ruta, sesión activa, última actividad y próxima revisión.
- Sesión: contexto, pregunta, editor, nivel de ayuda y envío.
- Feedback: respuesta original, criterios, errores, pista y decisión.
- Historial: intentos por concepto y evolución.
- Defensa: pregunta actual, evidencia acumulada y simulacro.

## 10. Privacidad, errores y recuperación

- No se enviarán respuestas a Internet.
- El estado dinámico se ignorará en Git por defecto.
- El servidor devolverá errores legibles si no puede escribir.
- La interfaz no perderá un borrador por una recarga.
- Un envío duplicado recibirá un nuevo identificador, nunca sobrescribirá el intento anterior.
- Un JSON corrupto se aislará y se mostrará un aviso de recuperación desde la última copia válida.
- La exportación permitirá respaldar progreso antes de cambiar de computadora.
- El modo sin servidor permitirá seguir escribiendo y luego importar datos.

## 11. Verificación

La primera implementación deberá probar:

- Renderizado del dashboard y los estados de módulo.
- Guardado y restauración de borradores.
- Creación de intentos inmutables.
- Lectura y escritura atómica de JSON.
- Exportación Markdown.
- Transiciones de desbloqueo válidas e inválidas.
- Mensajes de error cuando el servidor no está disponible.
- Navegación de notebook y viewport angosto sin solapamientos.
- Flujo completo: abrir sesión, responder, enviar, leer feedback y ver próxima acción.

La aceptación funcional será un recorrido manual reproducible con una respuesta ficticia. La aceptación pedagógica será que el registro permita responder estas preguntas sin abrir el chat anterior: qué concepto está activo, qué respondió Mateo, qué error tiene, qué capacidad debe reforzar y cuál es la próxima tarea.

## 12. Fases de implementación

1. Catálogo de módulos, esquema de datos y servidor local.
2. Dashboard, ruta guiada y sesión activa.
3. Editor, persistencia, intentos versionados y exportación.
4. Feedback, errores, recuperación y desbloqueo.
5. Historial, modo defensa y simulacros.
6. Pruebas, revisión visual y documentación de uso.

La aplicación se implementará sobre esta especificación después de la revisión del usuario y de un plan técnico separado.
