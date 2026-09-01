# Semana 4: óptica, fibra y codificación time-bin

## Objetivos

Al terminar deberías poder convertir distancia y pérdidas fijas en transmitancia,
seguir un pulso por Alice, la fibra y Bob, explicar las tres ventanas de un
interferómetro desbalanceado y predecir cómo eficiencia, dark counts y visibilidad
afectan QBER y tasa.

## 1. De un qubit abstracto a un pulso óptico

La tesis no envía el vector `(1,0)` por un cable. Alice prepara campos ópticos débiles
cuyos **modos** representan los estados. En time-bin, los modos relevantes son dos
ventanas temporales: temprano `|e>` y tardío `|l>`.

Un fotón a longitud de onda `lambda` tiene energía:

```math
E=h\nu=\frac{hc}{\lambda}.
```

Para `lambda=1550 nm`, usando `h=6,626 x 10^-34 J s` y `c≈3 x 10^8 m/s`:

```math
E\approx1{,}28\times10^{-19}\;J\approx0{,}80\;eV.
```

Un pulso láser atenuado no contiene exactamente un fotón. Es una fuente coherente
débil con distribución de número de fotones; la semana 5 estudia esa estadística. Esta
semana alcanza con distinguir:

- **potencia media:** energía por unidad de tiempo, apropiada para instrumentos
  clásicos;
- **número medio de fotones por pulso `mu`:** parámetro de la fuente débil;
- **click:** evento macroscópico registrado por un detector, que puede deberse a señal
  o ruido.

## 2. Pérdida en dB

Para una relación de potencias `P_out/P_in`:

```math
A_{dB}=-10\log_{10}\left(\frac{P_{out}}{P_{in}}\right).
```

La transmitancia correspondiente es:

```math
\eta=\frac{P_{out}}{P_{in}}=10^{-A_{dB}/10}.
```

Los dB se suman; las transmitancias lineales se multiplican. Ésa es la ventaja de un
presupuesto de enlace en dB.

Para fibra con atenuación `alpha` en dB/km y distancia `L` en km:

```math
A_{fibra}=\alpha L,
\qquad
\eta_{fibra}=10^{-\alpha L/10}.
```

### Ejemplo de 30 km

Con `alpha=0,2 dB/km`:

```math
A_{fibra}=0{,}2\times30=6\;dB,
```

```math
\eta_{fibra}=10^{-0{,}6}\approx0{,}251.
```

Llega aproximadamente 25,1% de la potencia; para un canal lineal pasivo, la misma
transmitancia describe la probabilidad de supervivencia de cada fotón idealizado.

No significa que "se perdió 6%": 6 dB no son seis puntos porcentuales.

## 3. Presupuesto total

La fibra no es la única pérdida:

```math
A_{total}=\alpha L+N_cA_c+A_{acoplo}+A_{componentes}.
```

Supongamos 30 km, cuatro conectores de 0,5 dB y 3 dB internos:

```math
A_{total}=6+4(0{,}5)+3=11\;dB,
```

```math
\eta_{óptica}=10^{-11/10}\approx0{,}0794.
```

Con detector de eficiencia `eta_d=0,15`, la eficiencia aproximada extremo a extremo
es `0,0794 x 0,15 ≈ 0,0119`, antes de ventanas, selección de base, dead time y otros
efectos.

Esta cuenta muestra por qué distancia no basta. Un enlace corto con muchos splitters
y conectores puede perder más que un tramo limpio más largo.

## 4. Probabilidad aproximada de detección

Para una fuente coherente débil de media `mu`, transmitancia `eta_ch` y detector
`eta_d`, el script usa:

```math
P_{det}=1-\exp(-\mu\eta_{ch}\eta_d).
```

Con `mu=0,1` y eficiencia total lineal antes calculada `0,0119`:

```math
P_{det}\approx1-e^{-0{,}00119}\approx0{,}00119.
```

A 80 MHz, una multiplicación ingenua da unos `95.200 clicks/s`. No es todavía tasa de
clave: faltan selección de base, ruido, saturación, tamizado y privacidad. Sirve como
orden de magnitud y para comprobar tendencias.

## 5. Estados time-bin

En la base temporal Z:

```math
|0_Z\rangle=|e\rangle,
\qquad
|1_Z\rangle=|l\rangle.
```

Bob mide tiempo de llegada: temprano representa 0 y tardío representa 1.

En la base conjugada X:

```math
|0_X\rangle=|+\rangle=\frac{|e\rangle+|l\rangle}{\sqrt2},
```

```math
|1_X\rangle=|-\rangle=\frac{|e\rangle-|l\rangle}{\sqrt2}.
```

Ambos tienen intensidad en temprano y tardío. El bit está en la **fase relativa**:
`0` frente a `pi`. Medir solo tiempo no los distingue; Bob necesita interferencia.

Time-bin es atractivo en fibra porque las ventanas temporales pueden tolerar mejor
cambios de polarización que una codificación puramente polarimétrica. No elimina
dispersión, deriva de fase, sincronización ni dependencia de polarización de los
componentes.

## 6. Interferómetro desbalanceado y tres ventanas

El interferómetro de Bob tiene un camino corto y uno largo cuya diferencia de retardo
iguala la separación `Delta t` entre bins.

```text
Pulso temprano + camino corto  -> ventana temprana
Pulso temprano + camino largo  -> ventana central
Pulso tardío   + camino corto  -> ventana central
Pulso tardío   + camino largo  -> ventana tardía
```

En la ventana central hay dos alternativas indistinguibles: temprano-largo y
tardío-corto. Sus amplitudes se suman o restan según la fase relativa. Las salidas del
interferómetro permiten distinguir `|+>` y `|->` idealmente.

Las ventanas externas revelan qué combinación temporal ocurrió y no contienen la
misma interferencia entre ambos caminos. Según la arquitectura y protocolo, pueden
descartarse o usarse de otra manera; no deben contarse automáticamente como medición
X válida.

## 7. Visibilidad

Una definición experimental común es:

```math
V=\frac{I_{max}-I_{min}}{I_{max}+I_{min}}.
```

`V=1` representa contraste ideal; menor visibilidad implica que la salida destructiva
no se apaga por completo. En esta simulación se resume como:

```math
p_{fase}=\frac{1-V}{2}.
```

Ejemplos:

| V | Error de fase modelado |
|---:|---:|
| 0,99 | 0,5% |
| 0,98 | 1% |
| 0,90 | 5% |
| 0,80 | 10% |

Esta relación es una decisión del modelo para mapear contraste a error. Un banco real
requiere medir visibilidad, deriva temporal, desbalance de intensidades y estabilidad
térmica.

## 8. Detectores

Un detector de fotón único no informa el número exacto de fotones necesariamente;
muchos son dispositivos de umbral: click o no click.

| Parámetro | Efecto principal | Riesgo de interpretación |
|---|---|---|
| Eficiencia | Más señal incidente produce clicks útiles | No corrige pérdidas previas |
| Dark count | Clicks sin señal, aproximadamente aleatorios | Domina cuando la señal es muy débil |
| Jitter | Incertidumbre en tiempo del click | Mezcla bins o exige ventanas mayores |
| Resolución temporal | Capacidad de separar marcas de tiempo | No es idéntica al jitter total del sistema |
| Dead time | Tiempo sin responder tras un click | Satura a tasas altas |
| Count rate | Tasa operativa máxima | No equivale a SKR |

Los APD InGaAs suelen ser más simples y económicos. Los SNSPD pueden ofrecer mayor
eficiencia, menor ruido y mejor timing, a costa de criogenia y complejidad. La elección
es de sistema, no una competencia de un único número.

## 9. Sincronización

Alice y Bob necesitan asociar cada click con un símbolo y una ventana. Un banco puede
usar referencias ópticas, eléctricas, FPGA, generadores y time taggers. Si la
referencia deriva:

- clicks válidos caen fuera de ventana;
- una ventana se confunde con otra;
- ampliar ventanas recupera señal pero admite más dark counts;
- QBER y tasa cambian juntos.

SeQUeNCe agenda eventos en una timeline ideal. El parámetro de resolución existe, pero
la tesis no simula un subsistema completo de recuperación de reloj. Éste es un límite
que debe decirse en la defensa.

## 10. Mapa componente-parámetro

| Bloque físico | Función | Parámetro o efecto en el modelo |
|---|---|---|
| Láser 1550 nm | Produce pulsos | `frequency_hz`, fuente base |
| Atenuador | Fija media de fotones | `mean_photon_num` |
| Modulador de intensidad | Señal/decoy/vacío | intensidades usadas analíticamente |
| Modulador de fase | Codifica superposición | estado time-bin y fase |
| Fibra | Propaga con pérdida y retardo | `distance_km`, `attenuation_db_km` |
| Interferómetro | Mide base X | `visibility`, `phase_error` |
| Detector | Convierte señal en click | `detector_efficiency`, `dark_count_hz` |
| Electrónica/timetagger | Asigna ventanas | `time_resolution_ps`, timeline ideal |
| Límite de detector | Evita clicks arbitrariamente próximos | `count_rate_hz` como aproximación |

La [sección de hardware](../../paper/chapters/05_hardware_presupuesto.tex) desarrolla
los dispositivos candidatos. El [script](../../experiments/qkd_2node_simulation.py)
muestra el mapeo efectivo.

## 11. Errores frecuentes

- Leer 3 dB como 3%.
- sumar transmitancias lineales en vez de multiplicarlas;
- llamar fotón a cualquier pulso láser;
- afirmar que todo click demuestra llegada de señal;
- confundir resolución del timetagger con jitter total;
- decir que la ventana central "crea" el bit: convierte fase en estadística de salida;
- usar `p_fase=(1-V)/2` como ley universal de todo interferómetro;
- convertir clicks por segundo directamente en SKR.

## 12. Preguntas de tribunal

### ¿Por qué eligieron time-bin y no polarización?

Time-bin se integra bien con fibra y puede ser menos sensible a variaciones de
polarización. Además conecta el proyecto con interferencia, sincronización y
componentes de telecomunicaciones. No significa que sea inmune a deriva: exige un
interferómetro estable y control temporal.

### ¿Por qué hay tres ventanas si Alice usa dos bins?

El interferómetro agrega dos caminos. Temprano-corto llega primero, tardío-largo
último, y temprano-largo coincide con tardío-corto en el centro. Esa coincidencia hace
posible interferir las amplitudes.

### ¿Aumentar eficiencia siempre baja QBER?

Aumenta la proporción de clicks de señal frente a dark counts cuando el resto se
mantiene. Puede mejorar QBER y tasa, pero a tasas altas aparecen dead time o
saturación; tampoco corrige error de fase.

## 13. Salida oral de dos minutos

Seguí un bit X desde la elección de Alice hasta la salida del detector de Bob. Incluí
dos pulsos temporales, fase relativa, pérdida, dos caminos, ventana central,
visibilidad y click. Terminá diciendo qué parte idealiza SeQUeNCe.

## 14. Fuentes

- [Marco teórico time-bin](../../paper/chapters/02_marco_teorico.tex).
- [Hardware y presupuesto](../../paper/chapters/05_hardware_presupuesto.tex).
- [Código de simulación](../../experiments/qkd_2node_simulation.py).
- N. Gisin et al., [Quantum cryptography](https://doi.org/10.1103/RevModPhys.74.145).

## Próximo paso

Resolvé los [ejercicios de la semana 4](../ejercicios/semana_04.md) y completá el
punto de control 2 siguiendo un bit de extremo a extremo.
