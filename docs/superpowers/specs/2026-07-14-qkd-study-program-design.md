# Diseño del programa interactivo de estudio de QKD

Fecha: 2026-07-14

## 1. Propósito

Construir un programa de estudio en español que permita a Mateo comprender y defender integralmente la tesis **“Diseño y evaluación por simulación de un banco de pruebas de QKD BB84 en time-bin con estados señuelo”**.

El programa debe partir desde conocimientos iniciales mínimos de criptografía, mecánica cuántica y telecomunicaciones. Debe alcanzar un nivel suficiente para exponer durante 30 minutos y responder 15 minutos de preguntas técnicas sobre cualquier parte del trabajo.

La meta no es memorizar el documento. La meta es poder reconstruir sus argumentos, explicar sus mecanismos, resolver sus cuentas centrales, interpretar sus resultados y declarar con precisión sus límites.

## 2. Perfil y restricciones

- Buen dominio de matemática y lógica.
- Poco conocimiento inicial de criptografía, QKD y telecomunicaciones ópticas.
- Nivel intermedio de Python: puede comprender código con una explicación paso a paso.
- Idioma principal de estudio y defensa: español. Los términos técnicos y papers conservan sus nombres originales en inglés.
- Plazo disponible: ocho semanas.
- Disponibilidad variable, con un mínimo garantizado de tres sesiones semanales de 45 a 60 minutos.
- Alcance: debe dominar toda la tesis, no solamente un conjunto de capítulos asignados.

## 3. Enfoque elegido

Se utilizará aprendizaje en espiral orientado a la defensa.

El sistema recorrerá el trabajo varias veces con profundidad creciente:

1. Historia completa y vocabulario básico.
2. Mecanismos físicos y criptográficos.
3. Matemática, hardware y simulación.
4. Evidencia, supuestos, ataques y límites.
5. Exposición oral y preguntas de tribunal.

Este enfoque evita dos problemas. Un recorrido académico puramente lineal demoraría demasiado en llegar a la tesis. Un recorrido limitado a memorizar sus afirmaciones dejaría huecos que aparecerían ante repreguntas del jurado.

## 4. Arquitectura semanal

Cada semana contiene tres sesiones esenciales:

- **Sesión A - Construir intuición:** concepto, ejemplo visual, experimento mental y explicación en lenguaje cotidiano.
- **Sesión B - Convertir intuición en ingeniería:** matemática, números realistas, hardware, código y conexión directa con la tesis.
- **Sesión C - Aprender a defender:** recuperación sin apuntes, preguntas acumulativas, mini exposición y corrección de imprecisiones.

Cuando exista tiempo adicional, se habilitarán bloques opcionales de papers, ejercicios extensos, código, flashcards o ensayos. Ningún contenido esencial dependerá de estos bloques. Una semana con mayor disponibilidad permitirá profundizar, pero una semana difícil no romperá la secuencia principal.

## 5. Anatomía de una sesión

Una sesión de 60 minutos tendrá esta estructura de referencia:

| Minutos | Actividad |
|---:|---|
| 0-5 | Recuperar lo anterior sin apuntes |
| 5-20 | Explicación guiada y preguntas |
| 20-35 | Ejemplo, cálculo o simulación mental |
| 35-45 | Conexión con una página, ecuación, figura o fragmento de código de la tesis |
| 45-55 | Explicación oral y preguntas de tribunal |
| 55-60 | Registrar dudas, errores y próximo repaso |

La duración podrá reducirse a 45 minutos conservando recuperación, actividad práctica, conexión con la tesis y salida oral. Leer sin producir una explicación, un cálculo o una defensa no contará como una sesión completada.

## 6. Programa de ocho semanas

### Semana 1 - Criptografía y distribución de claves

- Confidencialidad, integridad y autenticación.
- Cifrado simétrico, OTP, AES y clave pública.
- Diferencia entre cifrar datos y distribuir claves.
- Amenaza cuántica, QKD y criptografía post-cuántica.
- Resumen, introducción, hipótesis, objetivos y alcance de la tesis.

### Semana 2 - Fundamentos cuánticos y BB84 ideal

- Bits, qubits, vectores de estado y bases.
- Regla de Born, medición y estados no ortogonales.
- Superposición y teorema de no clonación.
- BB84 completo, desde preparación hasta tamizado.
- Marco teórico de la tesis hasta el protocolo BB84.

### Semana 3 - Seguridad, QBER y clave secreta

- Modelo de Alice, Bob y Eve.
- Ataque intercept-resend y origen del error detectable.
- Canal clásico autenticado.
- Estimación de parámetros, reconciliación y amplificación de privacidad.
- Entropía binaria, QBER, throughput y SKR.
- Alcance y significado de las cotas usadas en la tesis.

### Semana 4 - Óptica, fibra, time-bin y detectores

- Fotones, pulsos láser y fuentes coherentes débiles.
- Potencia, energía, dB, atenuación y presupuesto de enlace.
- Codificación time-bin y bases temporal e interferométrica.
- Interferómetro desbalanceado, fase y visibilidad.
- APD, SNSPD, eficiencia, dark counts, jitter, dead time y temporización.
- Arquitectura física y hardware propuesto en la tesis.

### Semana 5 - Implementaciones prácticas y estados señuelo

- Distribución de Poisson y pulsos multifotónicos.
- Ataque photon-number splitting.
- Intensidades signal, decoy y vacuum.
- Ganancias, yields, errores y cotas de fotón único.
- Diferencia entre implementar un protocolo decoy y aplicar una estimación analítica.
- Fórmulas decoy y supuestos de la tesis.

### Semana 6 - SeQUeNCe y experimentos

- Simulación de eventos discretos.
- Timeline, nodos, canales, eventos, semillas y métricas.
- Lectura guiada del código Python relevante.
- Barridos de distancia, detector, visibilidad y estados señuelo.
- Lectura causal de cada figura de resultados.
- Diferencia entre magnitud simulada, posprocesamiento analítico y evidencia experimental.

### Semana 7 - Ingeniería de sistema y validez

- Presupuesto de enlace y selección de componentes.
- Red de campus, canal clásico, KMS y nodos confiables.
- Enlace punto a punto frente a red QKD.
- Ataques de implementación y supuestos de confianza.
- Estado del arte, normalización y productos comerciales.
- Validez interna, validez externa, limitaciones y trabajo futuro.

### Semana 8 - Defensa integral

- Guion de 30 minutos y diseño de la narrativa.
- Explicación de figuras, ecuaciones y decisiones técnicas.
- Banco de preguntas básicas, técnicas y hostiles.
- Estrategias para repreguntas y bloqueos.
- Dos simulacros completos de 30 minutos más 15 minutos de preguntas.

## 7. Formato de cada capítulo de aprendizaje

Cada capítulo estable seguirá el mismo recorrido:

1. Pregunta concreta que se intenta resolver.
2. Explicación intuitiva y ejemplo visual o mental.
3. Formalización matemática paso a paso.
4. Conexión exacta con la tesis.
5. Ejemplo numérico con unidades y valores realistas.
6. Ejercicios con pistas separadas de las soluciones.
7. Preguntas de tribunal con repreguntas y errores frecuentes.
8. Explicación oral de salida de aproximadamente dos minutos.

Los capítulos no asumirán que una analogía sustituye la física. Cada analogía indicará qué representa correctamente y dónde deja de ser válida.

## 8. Criterio de dominio

Cada concepto deberá superar cuatro pruebas:

1. **Explicar:** describirlo sin fórmulas y sin apuntes.
2. **Calcular:** resolver un ejemplo cuantitativo o derivar su relación central.
3. **Conectar:** localizar su función en el hardware, código, ecuación o figura de la tesis.
4. **Defender:** responder una objeción o variante formulada como pregunta de tribunal.

El seguimiento usará cuatro estados:

- **Rojo:** no puede reconstruir el concepto sin ayuda.
- **Amarillo:** puede explicarlo, pero falla al calcular o responder variantes.
- **Verde:** supera las cuatro pruebas sin apuntes.
- **Azul:** puede enseñarlo y conectarlo con otras capas del sistema.

Los temas verdes y azules continuarán apareciendo mediante recuperación espaciada y preguntas mezcladas.

## 9. Materiales del repositorio

El programa se implementará en una carpeta estable `study/` dentro del proyecto y se publicará en el repositorio GitHub existente.

La estructura prevista es:

```text
study/
├── README.md
├── plan_maestro.md
├── progreso.md
├── errores_y_dudas.md
├── capitulos/
├── ejercicios/
├── laboratorio/
├── defensa/
└── assets/
```

Funciones principales:

- `README.md`: punto de entrada y modo de uso.
- `plan_maestro.md`: calendario flexible, sesiones esenciales y bloques opcionales.
- `progreso.md`: semáforo de dominio y próximos repasos.
- `errores_y_dudas.md`: confusiones detectadas y correcciones.
- `capitulos/`: material conceptual y matemático.
- `ejercicios/`: problemas, pistas y soluciones.
- `laboratorio/`: guías de código, experimentos y lectura de resultados.
- `defensa/`: guion, banco de preguntas, rúbricas y simulacros.
- `assets/`: diagramas estables usados por las lecciones.

Las pantallas temporales del compañero visual permanecerán fuera de Git mediante `.gitignore`. Los commits y mensajes de pull request serán pequeños y concisos.

## 10. Adaptación y manejo de dificultades

- Si falla la intuición, se cambia la representación: objetos, diagrama, tabla de probabilidades o experimento mental.
- Si la intuición funciona pero falla la matemática, se desarma la derivación en pasos y se verifica cada supuesto.
- Si la teoría funciona pero falla la conexión con la tesis, se trabaja sobre una página, figura o bloque de código concreto.
- Si el contenido se comprende pero la respuesta oral es imprecisa, se entrena la estructura: respuesta directa, mecanismo, evidencia, límite.
- Si una semana solo permite dos sesiones, la siguiente comienza recuperando la tercera sesión esencial; no se acumulan bloques opcionales atrasados.
- Las respuestas incorrectas se conservan en el registro de errores para volver a examinarlas con una variante.

## 11. Criterios de preparación final

Mateo estará listo para la defensa cuando pueda:

- Exponer el trabajo completo en 28 a 30 minutos sin leer un texto memorizado.
- Explicar todas las figuras, ecuaciones importantes y decisiones de diseño de la tesis.
- Resolver las cuentas centrales de probabilidad, dB, detección, QBER, entropía, SKR y Poisson.
- Modificar parámetros relevantes de la simulación con ayuda mínima y predecir cualitativamente su efecto antes de ejecutarla.
- Distinguir con precisión resultados simulados, fórmulas analíticas, supuestos y evidencia experimental.
- Responder al menos el 80 % del banco acumulativo sin apuntes.
- Completar dos simulacros consecutivos de 30 + 15 minutos sin errores conceptuales graves.
- Reconocer lo que el trabajo no demuestra y responder una pregunta desconocida sin inventar.

## 12. Fuera de alcance

- Completar una formación general equivalente a cursos universitarios enteros de mecánica cuántica, criptografía u óptica.
- Producir una prueba formal nueva de seguridad de BB84.
- Certificar seguridad comercial o experimental del banco simulado.
- Convertir todos los papers de referencia en lecturas obligatorias completas.
- Sustituir la revisión de los directores de tesis sobre contenido académico y criterios institucionales.

## 13. Validación del diseño

El usuario aprobó explícitamente:

- El aprendizaje en espiral orientado a la defensa.
- La arquitectura de ocho semanas.
- Las tres sesiones semanales y su formato interactivo.
- El orden del temario.
- Las cuatro pruebas de dominio.
- Los materiales y criterios de preparación final.
- La creación de una carpeta propia en el proyecto y su publicación en GitHub.

El paso siguiente, después de la revisión de este documento, será escribir un plan de implementación detallado para construir `study/` por entregas pequeñas y verificables.
