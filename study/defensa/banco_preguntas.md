# Banco acumulativo de 80 preguntas

No memorices párrafos. Para cada pregunta practicá: respuesta directa, mecanismo,
evidencia y límite. El “atajo inaceptable” señala una respuesta que suena segura pero
fallaría ante repregunta.

## A. Fundamentos y vocabulario (1-15)

### 1. ¿Qué es QKD?
- **Criterio:** distribución/generación de claves mediante estados y estadísticas, más canal clásico autenticado.
- **Repregunta:** ¿Dónde se cifran los datos?
- **Atajo inaceptable:** “Encriptación imposible de hackear”.

### 2. ¿Qué problema resuelve?
- **Criterio:** distribución de secreto entre extremos; no el cifrado completo.
- **Repregunta:** ¿Qué se necesita antes de empezar?
- **Atajo inaceptable:** “Resuelve toda la ciberseguridad”.

### 3. Diferencie confidencialidad, integridad y autenticación.
- **Criterio:** lectura, modificación e identidad con un ejemplo independiente.
- **Repregunta:** ¿Cuál exige el canal clásico QKD?
- **Atajo inaceptable:** usar los tres como sinónimos.

### 4. ¿Por qué el canal clásico es público pero autenticado?
- **Criterio:** bases/transcript pueden oírse; no deben suplantarse o alterarse.
- **Repregunta:** describa man-in-the-middle.
- **Atajo inaceptable:** “Porque lo cuántico lo protege”.

### 5. QKD frente a PQC.
- **Criterio:** hardware/física y supuestos de dispositivos frente a algoritmos clásicos resistentes; complementariedad.
- **Repregunta:** ¿Cuál desplegaría masivamente hoy?
- **Atajo inaceptable:** afirmar superioridad universal.

### 6. ¿Qué es cifrado simétrico?
- **Criterio:** secreto compartido, uso para cifrar/descifrar y problema de gestión.
- **Repregunta:** ¿QKD reemplaza AES?
- **Atajo inaceptable:** “Usa una clave pública”.

### 7. ¿Cuándo OTP tiene seguridad perfecta?
- **Criterio:** clave aleatoria, secreta, igual longitud y uso único.
- **Repregunta:** ¿Qué ocurre al reutilizarla?
- **Atajo inaceptable:** omitir distribución de una clave enorme.

### 8. Seguridad perfecta frente a computacional.
- **Criterio:** independencia informacional frente a dificultad para recursos/tiempo/modelo.
- **Repregunta:** ¿Dónde ubica AES?
- **Atajo inaceptable:** “Perfecta significa implementación sin fallas”.

### 9. ¿Quiénes son Alice, Bob y Eve?
- **Criterio:** roles convencionales, no componentes específicos.
- **Repregunta:** ¿Charlie en TF-QKD debe ser confiable?
- **Atajo inaceptable:** definirlos solo como emisor, receptor y hacker sin rol protocolar.

### 10. QKD frente a comunicación cuántica general.
- **Criterio:** QKD produce claves; redes cuánticas también distribuyen entrelazamiento/qubits.
- **Repregunta:** ¿La tesis teleporta estados?
- **Atajo inaceptable:** llamar QKD a toda transmisión de fotones.

### 11. Clave cruda, tamizada y final.
- **Criterio:** antes de bases, después de bases, después de EC/privacidad.
- **Repregunta:** ¿Cuál mide el throughput del script?
- **Atajo inaceptable:** decir que todo click es bit final.

### 12. ¿Por qué un protocolo aborta?
- **Criterio:** parámetros no permiten cota positiva/confianza; no es falla de software necesariamente.
- **Repregunta:** ¿Abortar distingue ruido de Eve?
- **Atajo inaceptable:** “Porque se detectó a Eve con certeza”.

### 13. ¿Qué hace un KMS?
- **Criterio:** identifica, almacena, sincroniza, entrega y retira material de clave.
- **Repregunta:** ¿El KMS vuelve segura una clave?
- **Atajo inaceptable:** “Es un servidor que genera fotones”.

### 14. ¿Qué significa seguridad bajo un modelo?
- **Criterio:** capacidades de Eve, estados, dispositivos y parámetros explícitos.
- **Repregunta:** dé un canal lateral fuera del modelo.
- **Atajo inaceptable:** “Las leyes físicas no tienen supuestos”.

### 15. ¿Cuál es la pregunta de esta tesis?
- **Criterio:** factibilidad/diseño previo de banco BB84 time-bin con parámetros realistas y métricas.
- **Repregunta:** ¿Cuál es el entregable concreto?
- **Atajo inaceptable:** afirmar que construyó la red.

## B. BB84 y seguridad (16-30)

### 16. ¿Qué es un qubit?
- **Criterio:** vector complejo normalizado de sistema de dos niveles; amplitudes.
- **Repregunta:** ¿Por qué alpha no es probabilidad?
- **Atajo inaceptable:** “Un bit que vale 0 y 1”.

### 17. ¿Qué es una base de medición?
- **Criterio:** conjunto ortonormal de resultados distinguibles.
- **Repregunta:** escriba Z y X.
- **Atajo inaceptable:** confundir base con bit.

### 18. Explique la regla de Born.
- **Criterio:** módulo cuadrado de producto interno y probabilidades normalizadas.
- **Repregunta:** mida `|0>` en X.
- **Atajo inaceptable:** “El qubit elige al azar siempre”.

### 19. ¿Por qué importan estados no ortogonales?
- **Criterio:** no pueden distinguirse perfectamente en un ensayo.
- **Repregunta:** calcule `|<0|+>|^2`.
- **Atajo inaceptable:** decir que todos los estados BB84 son ortogonales.

### 20. ¿Qué afirma no clonación?
- **Criterio:** no hay clonador universal perfecto de estado desconocido arbitrario.
- **Repregunta:** ¿Se pueden copiar `|0>` y `|1>` conocidos como conjunto?
- **Atajo inaceptable:** “Nada cuántico se puede copiar”.

### 21. Mapee bit y base a los cuatro estados BB84.
- **Criterio:** Z: `|0>,|1>`; X: `|+>,|->`.
- **Repregunta:** ¿Cómo cambia en time-bin?
- **Atajo inaceptable:** invertir estados sin declarar convención.

### 22. Describa BB84 completo.
- **Criterio:** elección, preparación, medición, anuncio, tamizado, estimación y posprocesamiento.
- **Repregunta:** ¿Qué información se revela?
- **Atajo inaceptable:** terminar en el click.

### 23. ¿Por qué se descartan bases distintas?
- **Criterio:** resultado no correlacionado con bit de Alice en ideal.
- **Repregunta:** ¿Qué fracción queda en promedio?
- **Atajo inaceptable:** “Porque Bob midió mal”.

### 24. Derive 25% de intercept-resend.
- **Criterio:** Eve base errónea 1/2 y Bob error 1/2 sobre tamizadas.
- **Repregunta:** si Eve ataca 40%, ¿qué aporta?
- **Atajo inaceptable:** multiplicar también por sifting y responder 12,5% sin aclarar denominador.

### 25. Defina QBER y denominador.
- **Criterio:** errores sobre bits tamizados/relevantes.
- **Repregunta:** ¿por qué no pulsos enviados?
- **Atajo inaceptable:** errores sobre clicks totales sin base.

### 26. ¿QBER alto prueba presencia de Eve?
- **Criterio:** no; mezcla ruido/implementación/ataque, pero obliga a decisión conservadora.
- **Repregunta:** ¿para qué sirve entonces?
- **Atajo inaceptable:** atribuir causa única.

### 27. ¿QBER bajo prueba ausencia de Eve?
- **Criterio:** no; entra en cota y no cubre canales laterales automáticamente.
- **Repregunta:** dé un ataque de dispositivo.
- **Atajo inaceptable:** “Debajo de 11% es seguro”.

### 28. ¿Qué hace reconciliación?
- **Criterio:** iguala cadenas y filtra información pública contabilizable.
- **Repregunta:** ¿qué representa `f_EC`?
- **Atajo inaceptable:** “Elimina a Eve”.

### 29. ¿Qué hace amplificación de privacidad?
- **Criterio:** comprime según cota para reducir información de Eve.
- **Repregunta:** ¿puede crear secreto desde una cadena totalmente conocida?
- **Atajo inaceptable:** “Un hash cifra la clave”.

### 30. Explique la referencia de 11%.
- **Criterio:** umbral ideal aproximado/corte del código; positividad depende de fórmula y `f_EC`.
- **Repregunta:** ¿10,5% garantiza tasa positiva aquí?
- **Atajo inaceptable:** umbral universal de cualquier protocolo.

## C. Óptica, fibra y detectores (31-45)

### 31. ¿Por qué operar cerca de 1550 nm?
- **Criterio:** ventana de baja pérdida e infraestructura telecom; detectores específicos.
- **Repregunta:** ¿significa pérdida cero?
- **Atajo inaceptable:** “Es la única longitud cuántica”.

### 32. Convierta dB en transmitancia.
- **Criterio:** `eta=10^(-A/10)` con unidades y ejemplo.
- **Repregunta:** ¿20 dB?
- **Atajo inaceptable:** restar porcentaje.

### 33. ¿Qué significan 3 dB de pérdida?
- **Criterio:** transmitancia cercana a 0,5.
- **Repregunta:** ¿dos tramos de 3 dB?
- **Atajo inaceptable:** 3%.

### 34. ¿Por qué sumar conectores?
- **Criterio:** dB fijos se suman; transmitancias se multiplican.
- **Repregunta:** ¿un enlace corto puede perder más?
- **Atajo inaceptable:** usar solo `alpha L`.

### 35. ¿Qué es time-bin?
- **Criterio:** modos temprano/tardío y superposiciones con fase.
- **Repregunta:** ¿por qué atractivo en fibra?
- **Atajo inaceptable:** “El bit es únicamente hora de llegada” para ambas bases.

### 36. ¿Cómo se codifica la base X en time-bin?
- **Criterio:** dos bins con fase relativa 0/pi.
- **Repregunta:** ¿por qué medir tiempo no basta?
- **Atajo inaceptable:** asignar X a un tercer tiempo.

### 37. ¿Por qué aparecen tres ventanas?
- **Criterio:** cuatro combinaciones bin-camino; dos coinciden en centro.
- **Repregunta:** ¿cuál interfiere?
- **Atajo inaceptable:** “El detector crea un pulso extra”.

### 38. Defina visibilidad.
- **Criterio:** contraste `(Imax-Imin)/(Imax+Imin)` y estabilidad.
- **Repregunta:** ¿V=0,98 qué da en el modelo?
- **Atajo inaceptable:** confundirla con eficiencia.

### 39. ¿Es `(1-V)/2` una ley universal?
- **Criterio:** mapeo simplificado del modelo para error de fase.
- **Repregunta:** ¿qué mediría en banco?
- **Atajo inaceptable:** presentarla como especificación garantizada.

### 40. ¿Qué es eficiencia de detector?
- **Criterio:** click condicionado a fotón incidente bajo condiciones.
- **Repregunta:** ¿incluye pérdida de fibra?
- **Atajo inaceptable:** confundir con tasa máxima.

### 41. ¿Qué es un dark count?
- **Criterio:** click sin señal correspondiente; error aleatorio potencial.
- **Repregunta:** ¿por qué peor a larga distancia?
- **Atajo inaceptable:** “Fotón oscuro de Eve”.

### 42. Jitter frente a resolución temporal.
- **Criterio:** incertidumbre total de timing frente a capacidad de discretización/instrumento.
- **Repregunta:** ¿cómo cambia la ventana?
- **Atajo inaceptable:** tratarlos como idénticos.

### 43. ¿Qué es dead time?
- **Criterio:** periodo de insensibilidad posterior a click; limita tasa.
- **Repregunta:** ¿más potencia siempre ayuda?
- **Atajo inaceptable:** confundir con delay de fibra.

### 44. APD frente a SNSPD.
- **Criterio:** operación/costo frente a eficiencia, ruido, timing y criogenia.
- **Repregunta:** ¿cuál elegiría para primer banco?
- **Atajo inaceptable:** elegir por una cifra aislada.

### 45. ¿Qué sincronización modela la tesis?
- **Criterio:** timeline/resolución compacta, no recuperación completa de reloj/jitter.
- **Repregunta:** ¿qué hardware falta?
- **Atajo inaceptable:** “Picosegundos simulados prueban picosegundos reales”.

## D. WCS, PNS, decoys y tasas (46-60)

### 46. ¿Qué es una WCS?
- **Criterio:** láser atenuado con distribución Poisson y fase randomizada en modelo.
- **Repregunta:** ¿mu menor que uno implica máximo un fotón?
- **Atajo inaceptable:** llamarla fuente determinista.

### 47. Escriba Poisson y sus tres casos.
- **Criterio:** `P_mu(n)`, vacío, uno y `n>=2`.
- **Repregunta:** calcule para mu 0,1.
- **Atajo inaceptable:** interpretar media como secuencia fija.

### 48. ¿Por qué randomizar fase global?
- **Criterio:** justificar mezcla clásica de componentes de número.
- **Repregunta:** ¿la simulación lo implementa físicamente?
- **Atajo inaceptable:** “Para esconder el bit” sin modelo.

### 49. Explique PNS.
- **Criterio:** medir número, guardar fotón multifotónico, ocultar bloqueo en pérdida.
- **Repregunta:** ¿qué capacidad se concede a Eve?
- **Atajo inaceptable:** intercept-resend común.

### 50. ¿PNS viola no clonación?
- **Criterio:** no; explota múltiples sistemas ya emitidos.
- **Repregunta:** ¿por qué espera anuncio de base?
- **Atajo inaceptable:** “Sí, porque copia el bit”.

### 51. ¿Por qué no bajar mu a casi cero?
- **Criterio:** vacío domina, baja tasa y dark counts pesan.
- **Repregunta:** ¿qué aporta decoy?
- **Atajo inaceptable:** “Más bajo siempre más seguro”.

### 52. Idea esencial de decoy states.
- **Criterio:** varias mezclas Poisson acotan comportamiento monofotónico común.
- **Repregunta:** ¿cuándo revela Alice intensidad?
- **Atajo inaceptable:** “Son pulsos falsos que engañan a Eve”.

### 53. ¿Por qué signal y decoy deben ser indistinguibles?
- **Criterio:** salvo intensidad, para compartir yields por n.
- **Repregunta:** dé una etiqueta lateral.
- **Atajo inaceptable:** ignorar espectro/tiempo/polarización.

### 54. Ganancia frente a yield.
- **Criterio:** `Q_x=P(click|intensidad x)` frente a `Y_n=P(click|n)`.
- **Repregunta:** ¿cuál observa directamente Bob agregado?
- **Atajo inaceptable:** usarlos como sinónimos.

### 55. `Q_mu` frente a `Q_1`.
- **Criterio:** total de señal frente a contribución monofotónica.
- **Repregunta:** escriba `Q1=mu e^-mu Y1`.
- **Atajo inaceptable:** asumir todo click signal monofotónico.

### 56. ¿Qué significa `e1^U`?
- **Criterio:** cota superior de error monofotónico.
- **Repregunta:** ¿por qué superior y no valor exacto?
- **Atajo inaceptable:** QBER total.

### 57. Interprete los dos términos de tasa decoy.
- **Criterio:** costo EC total y crédito secreto monofotónico.
- **Repregunta:** ¿qué ocurre con multifotones?
- **Atajo inaceptable:** sumar toda detección como secreta.

### 58. ¿Qué implementa el experimento 4?
- **Criterio:** QBER/throughput simulados, ganancias/cotas analíticas asintóticas.
- **Repregunta:** ¿dónde está elección por pulso?
- **Atajo inaceptable:** “Decoy completo en SeQUeNCe”.

### 59. Asintótico frente a tamaño finito.
- **Criterio:** probabilidades límite frente a intervalos/fluctuaciones y parámetros de fallo.
- **Repregunta:** ¿por qué larga distancia lo agrava?
- **Atajo inaceptable:** “Asintótico significa muy rápido”.

### 60. SKR frente a click rate.
- **Criterio:** detecciones físicas frente a bits finales estimados tras descuentos.
- **Repregunta:** nombre cuatro descuentos.
- **Atajo inaceptable:** multiplicar frecuencia por `Pdet` y llamarlo SKR.

## E. Simulación y código (61-70)

### 61. ¿Qué es simulación de eventos discretos?
- **Criterio:** agenda de eventos relevantes ordenados, no pasos de tiempo vacíos.
- **Repregunta:** dé tres eventos QKD.
- **Atajo inaceptable:** “Una fórmula con random”.

### 62. ¿Qué hace `Timeline`?
- **Criterio:** reloj, cola y ejecución hasta horizonte.
- **Repregunta:** ¿resolución interna equivale a hardware?
- **Atajo inaceptable:** “Sincroniza físicamente Alice y Bob”.

### 63. Objetos principales del escenario.
- **Criterio:** nodos, canales cuánticos/clásicos, protocolo, detectores, eventos.
- **Repregunta:** ¿por qué canales en ambos sentidos?
- **Atajo inaceptable:** listar clases sin papel.

### 64. ¿Por qué simular si hay fórmulas?
- **Criterio:** integrar secuencia/estado/topología; fórmulas como control.
- **Repregunta:** ¿qué fórmula usaría para validar pérdida?
- **Atajo inaceptable:** despreciar uno de los dos enfoques.

### 65. ¿Qué parámetros se barren?
- **Criterio:** distancia, detector, visibilidad y decoy; demás controlados.
- **Repregunta:** ¿por qué no cambiarlos todos?
- **Atajo inaceptable:** confundir parámetro con métrica.

### 66. Explique la curva de distancia.
- **Criterio:** pérdida exponencial, señal/fondo, QBER y entropía.
- **Repregunta:** ¿último punto es alcance real?
- **Atajo inaceptable:** describir solo “baja”.

### 67. ¿Por qué eficiencia dio un cambio ruidoso/negativo?
- **Criterio:** pocas claves, semillas, combinación QBER/throughput; repetir estadística.
- **Repregunta:** ¿qué gráfica adicional haría?
- **Atajo inaceptable:** inventar una causalidad física sin evidencia.

### 68. ¿Para qué sirven semillas?
- **Criterio:** reproducibilidad/comparación; múltiples semillas para variabilidad.
- **Repregunta:** ¿una semilla basta?
- **Atajo inaceptable:** “Elimina aleatoriedad”.

### 69. ¿Qué significa corrida sin claves?
- **Criterio:** ausencia de estimador; QBER no definido, throughput cero.
- **Repregunta:** ¿por qué no QBER cero?
- **Atajo inaceptable:** ausencia de datos igual a éxito.

### 70. Clasifique cantidades de una figura.
- **Criterio:** simulada, analítica auxiliar o cota de seguridad.
- **Repregunta:** clasifique `p_detection_model` y SKR.
- **Atajo inaceptable:** llamar experimental a cualquier curva.

## F. Tesis, límites y sistema (71-80)

### 71. ¿Cuál es el entregable concreto?
- **Criterio:** modelo reproducible, barridos, criterios de hardware/campus y límites.
- **Repregunta:** ¿qué decisión habilita?
- **Atajo inaceptable:** “Una red segura funcionando”.

### 72. ¿Qué falta relevar en campus?
- **Criterio:** ruta óptica, pérdida, conectores, fibra, racks, ambiente y seguridad.
- **Repregunta:** ¿mapa físico basta?
- **Atajo inaceptable:** usar distancia recta.

### 73. ¿Demostraron aproximadamente 92 km?
- **Criterio:** último punto del barrido modelado bajo criterio, no demostración física.
- **Repregunta:** ¿de qué depende?
- **Atajo inaceptable:** “Sí, el QBER fue bajo”.

### 74. ¿Qué implica un nodo confiable?
- **Criterio:** termina enlaces/accede a claves y exige seguridad física.
- **Repregunta:** ¿es un repetidor cuántico?
- **Atajo inaceptable:** “Solo reenvía fotones”.

### 75. ¿Cómo se integra el KMS?
- **Criterio:** buffers correlacionados, IDs, políticas, autenticación y entrega.
- **Repregunta:** ¿qué pasa si consumo supera SKR?
- **Atajo inaceptable:** ignorar aplicaciones.

### 76. ¿Puede coexistir canal clásico por la misma fibra?
- **Criterio:** posible con WDM/filtros/potencia; Raman/crosstalk deben medirse.
- **Repregunta:** ¿la simulación lo valida?
- **Atajo inaceptable:** sí/no universal.

### 77. ¿Qué es TF-QKD y por qué no se usa aquí?
- **Criterio:** interferencia central, escala sqrt eta; cambia topología/protocolo/control.
- **Repregunta:** ¿es repetidor?
- **Atajo inaceptable:** “BB84 optimizado por software”.

### 78. Fibra frente a satélite.
- **Criterio:** pérdida continua/disponibilidad frente a geometría/pases/clima/tracking.
- **Repregunta:** ¿satélite debe ser confiable?
- **Atajo inaceptable:** “Satélite siempre pierde menos”.

### 79. Validez interna frente a externa.
- **Criterio:** coherencia causal/reproducibilidad del modelo frente a transferencia al banco/campus.
- **Repregunta:** dé evidencia para cada una.
- **Atajo inaceptable:** “Si corre, es válido”.

### 80. ¿Cuál es el próximo experimento mínimo?
- **Criterio:** relevamiento más enlace corto calibrado, medir pérdida/clicks/QBER/V y comparar modelo.
- **Repregunta:** ¿criterio de aceptación?
- **Atajo inaceptable:** saltar directamente a red de tres nodos.

## Uso semanal

- Semanas 1-2: preguntas 1-30.
- Semanas 3-5: agregar 31-60.
- Semanas 6-7: agregar 61-80.
- Semana 8: elegir 15 al azar, con al menos dos de cada sección.

Una pregunta pasa a verde solo si la repregunta no destruye la respuesta inicial.
