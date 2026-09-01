# Semana 5: fuentes coherentes débiles, PNS y estados señuelo

## Objetivos

Al terminar deberías poder calcular probabilidades de vacío, uno y varios fotones;
explicar cómo pérdida y pulsos multifotónicos habilitan PNS; describir la inferencia
decoy mediante ganancias e *yields*; y declarar exactamente qué parte implementa la
tesis de forma simulada y cuál de forma analítica.

## 1. El problema de la fuente real

BB84 suele explicarse diciendo "Alice envía un fotón". Una fuente determinista ideal
de fotones únicos a alta tasa, integrada y económica no es la opción habitual de un
banco de telecomunicaciones. Es práctico usar un láser atenuado: una **weak coherent
source** (WCS).

Aunque la media `mu` sea menor que uno, un pulso individual puede contener 0, 1, 2 o
más fotones. La media no es una etiqueta exacta.

Para aplicar el modelo Poisson usado en decoy-state BB84 también se supone
randomización global de fase entre pulsos. Sin ella, coherencias entre emisiones
pueden invalidar la descomposición clásica en números de fotones que usa la prueba.

## 2. Distribución de Poisson

La probabilidad de `n` fotones con media `mu` es:

```math
P_\mu(n)=e^{-\mu}\frac{\mu^n}{n!}.
```

Casos útiles:

```math
P_\mu(0)=e^{-\mu},
\qquad
P_\mu(1)=\mu e^{-\mu},
```

```math
P_\mu(n\ge2)=1-e^{-\mu}(1+\mu).
```

| `mu` | `P(0)` | `P(1)` | `P(n>=2)` |
|---:|---:|---:|---:|
| 0,1 | 0,9048 | 0,0905 | 0,0047 |
| 0,2 | 0,8187 | 0,1637 | 0,0175 |
| 0,6 | 0,5488 | 0,3293 | 0,1219 |

Subir `mu` aumenta eventos monofotónicos útiles, pero también la fracción
multifotónica. Bajarla reduce multifotones, pero hace que casi todos los pulsos sean
vacíos. No existe una solución gratuita variando solo intensidad.

## 3. Por qué un pulso multifotónico importa

En un pulso ideal de BB84, todos los fotones comparten la misma codificación. Si hay
dos, Eve puede intentar conservar uno y permitir que otro llegue a Bob.

| Componente | Estrategia PNS idealizada | Riesgo para Alice y Bob |
|---|---|---|
| Vacío `n=0` | No hay estado que extraer | No produce señal útil |
| Un fotón `n=1` | Bloquear o interactuar afecta disponibilidad/estado | La prueba BB84 acota información |
| Varios `n>=2` | Separar uno y reenviar los restantes | Eve espera anuncio de base y mide su copia |

El modelo fuerte concede a Eve medición no destructiva de número de fotones, memoria
cuántica y control del canal. Puede bloquear muchos pulsos monofotónicos y reenviar
multifotónicos por un canal mejor. Bob atribuye parte de la baja detección a pérdida
normal.

PNS no viola no clonación: Eve no fabrica una copia de un estado desconocido. Explota
copias físicas ya presentes en el mismo pulso.

## 4. La idea decoy

Alice elige aleatoriamente intensidades, por ejemplo:

- `mu`: intensidad de señal usada para formar clave;
- `nu`: intensidad señuelo más débil;
- `0`: vacío para estimar fondo.

Después revela qué intensidad usó, no antes de que Eve interactúe. Los pulsos deben
ser indistinguibles en tiempo, espectro, polarización y forma salvo por la intensidad
declarada. Si el modulador deja otra etiqueta, Eve podría tratarlos distinto sin ser
detectada por el argumento decoy.

La clave conceptual es:

> Eve puede conocer el número de fotones, pero el comportamiento de un componente de
> `n` fotones no debería depender de si provino de la distribución signal o decoy.

Variando los pesos Poisson y observando detecciones totales, Alice y Bob acotan el
componente de un fotón.

## 5. Ganancia, yield y error

El **yield** `Y_n` es la probabilidad de click condicionada a que se emitieron `n`
fotones:

```math
Y_n=P(click\mid n).
```

La **ganancia** `Q_x` para intensidad `x` es la probabilidad total de click por pulso:

```math
Q_x=\sum_{n=0}^{\infty}P_x(n)Y_n.
```

La ganancia de error es:

```math
E_xQ_x=\sum_{n=0}^{\infty}P_x(n)e_nY_n,
```

donde `E_x` es QBER observado para intensidad `x` y `e_n` el error condicional del
componente `n`.

No confundas:

- `mu`: fotones medios preparados;
- `Q_mu`: clicks por pulso de señal;
- `Y_1`: clicks condicionados a emitir un fotón;
- `E_mu`: error total de señal;
- `e_1`: error del componente de un fotón.

## 6. Cotas implementadas en el script

Para señal `mu`, decoy `nu` y yield de vacío `Y_0`, el código calcula una cota inferior
de `Y_1`:

```math
Y_1^L=\frac{\mu}{\mu\nu-\nu^2}
\left[
Q_\nu e^\nu-Q_\mu e^\mu\left(\frac{\nu}{\mu}\right)^2
-\frac{\mu^2-\nu^2}{\mu^2}Y_0
\right].
```

Luego acota el error monofotónico:

```math
e_1^U=\frac{E_\nu Q_\nu-e_0Y_0}{Y_1^L\nu e^{-\nu}},
```

con `e_0≈1/2` para clicks de fondo aleatorios. El código recorta resultados a rangos
físicos y devuelve valores conservadores cuando el denominador no es utilizable.

La contribución de señal de un fotón es:

```math
Q_1^L=\mu e^{-\mu}Y_1^L.
```

## 7. Tasa decoy asintótica

La tesis usa:

```math
R_{decoy}\ge qf_{rep}
\left[-Q_\mu f_{EC}h_2(E_\mu)+Q_1^L(1-h_2(e_1^U))\right].
```

| Símbolo | Significado |
|---|---|
| `q=1/2` | factor de tamizado BB84 en esta forma |
| `f_rep` | pulsos emitidos por segundo |
| `Q_mu` | ganancia total de señal |
| `E_mu` | QBER total de señal |
| `Q_1^L` | cota inferior de ganancia monofotónica |
| `e_1^U` | cota superior del error monofotónico |
| `f_EC` | ineficiencia de reconciliación |

El primer término paga corrección sobre todos los clicks de señal. El segundo acredita
secreto del componente monofotónico acotado. La parte multifotónica no se trata como
secreta en esta cota conservadora.

## 8. Qué implementa exactamente la tesis

> **Límite central:** SeQUeNCe no ejecuta aquí un protocolo decoy completo con
> selección aleatoria, anuncios y estimación finita. El experimento 4 simula QBER y
> throughput para intensidades signal/decoy, calcula ganancias WCS mediante un modelo
> analítico y aplica cotas asintóticas `Y_1/e_1` en posprocesamiento.

Esto permite comparar tendencias y enseñar el efecto de cotas monofotónicas. No
demuestra una implementación decoy operativa ni incluye fluctuaciones de intensidad,
randomización de fase, canales laterales del modulador o tamaño finito completo.

Las funciones relevantes son
[`decoy_yield_y1_lower`, `decoy_e1_upper` y `secret_key_rate_asymptotic_decoy`](../../experiments/qkd_2node_simulation.py).

## 9. Cómo detecta PNS estadísticamente

Sin decoys, Alice y Bob observan una ganancia total y no separan bien cuánto proviene
de `n=1` o `n>=2`. Con varias intensidades conocen distintas mezclas Poisson de los
mismos `Y_n`. Un ataque que bloquee selectivamente monofotones cambia la relación
entre las ganancias de signal y decoy.

No observan cada ataque individual ni identifican el número de fotones de cada click.
Restringen estadísticamente explicaciones compatibles con los datos.

## 10. Compromisos de implementación

- **Más intensidades:** potencialmente mejores cotas, más control y calibración.
- **Decoy muy débil:** útil para separar componentes, pero con pocas detecciones y
  mayor incertidumbre finita.
- **Vacío:** estima fondo, aunque un modulador real no produce cero perfecto.
- **Frecuencia alta:** más datos, pero exige moduladores, detectores y timing.
- **Estabilidad de intensidad:** un error sistemático cambia las probabilidades
  supuestas.
- **Indistinguibilidad:** cualquier etiqueta lateral debilita la inferencia.

## 11. Errores frecuentes

- Decir que `mu=0,1` significa un fotón cada diez pulsos de forma determinista.
- Confundir media de fotones con probabilidad de click.
- Afirmar que decoy elimina pulsos multifotónicos.
- Decir que Eve no sabe qué intensidad hubo nunca; se revela después.
- Confundir `Q_1` con `Q_mu`.
- Presentar la cota asintótica como protocolo completo ejecutado.
- Omitir randomización de fase o indistinguibilidad de pulsos.

## 12. Preguntas de tribunal

### ¿Por qué no usar `mu` extremadamente pequeño y evitar PNS?

Porque domina el vacío y la tasa útil cae. Además, con pérdida y dark counts la
relación señal-ruido empeora. Decoy permite usar una señal práctica y acotar su parte
monofotónica.

### ¿Bob sabe cuántos fotones tenía el pulso que produjo un click?

No en este esquema con detectores de umbral. Las cotas se infieren de estadísticas
agregadas de varias intensidades.

### ¿El experimento 4 prueba que los decoys mejoran cualquier enlace?

No. Compara dos estimaciones dentro de parámetros y modelos concretos. Una
implementación completa necesita selección, calibración, datos finitos y control de
canales laterales.

## 13. Salida oral de dos minutos

Explicá la cadena `WCS -> Poisson -> multifotones -> PNS -> intensidades decoy ->
ganancias -> cota Y1/e1 -> SKR`. Terminá separando lo simulado de lo analítico.

## 14. Fuentes

- W.-Y. Hwang, [Quantum Key Distribution with High Loss: Toward Global Secure Communication](https://doi.org/10.1103/PhysRevLett.91.057901).
- H.-K. Lo, X. Ma y K. Chen, [Decoy State Quantum Key Distribution](https://doi.org/10.1103/PhysRevLett.94.230504).
- X. Ma et al., [Practical decoy state for quantum key distribution](https://doi.org/10.1103/PhysRevA.72.012326).
- [Marco teórico de la tesis](../../paper/chapters/02_marco_teorico.tex).
- [Código del experimento 4](../../experiments/qkd_2node_simulation.py).

## Próximo paso

Resolvé los [ejercicios de la semana 5](../ejercicios/semana_05.md). Si podés aplicar
la fórmula pero no explicar qué se está acotando, el estado sigue amarillo.
