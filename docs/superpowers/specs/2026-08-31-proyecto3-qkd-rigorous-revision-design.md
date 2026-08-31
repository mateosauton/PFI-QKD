# Diseño de la revisión rigurosa de Proyecto 3

Fecha: 2026-08-31

## 1. Propósito

Revisar el experimento QKD y el informe de Proyecto 3 para que sus cifras puedan auditarse y sus conclusiones no excedan la evidencia. La revisión corrige el modelo decoy, registra la contabilidad interna de SeQUeNCe, reduce la cuantización causada por claves cortas y conserva los resultados de cada corrida.

El trabajo seguirá siendo una evaluación de diseño. No intentará certificar seguridad composable ni reemplazar una implementación física.

## 2. Criterio de éxito

La revisión termina cuando cumple estas condiciones:

- Las fórmulas implementadas para BB84 con estados señuelo coinciden con las referencias citadas.
- Cada figura y cifra del texto puede reconstruirse desde datos versionados.
- El manuscrito distingue throughput simulado, proxy asintótico y cota PNS o decoy.
- El texto ya no llama "validado" a un punto que solo supera una comprobación necesaria.
- Los intervalos Monte Carlo usan 30 corridas independientes por punto.
- Las pruebas, la ejecución completa, la compilación de LaTeX y la inspección visual del PDF terminan sin errores.

## 3. Modelo físico y métricas

### 3.1 Contabilidad observada

La simulación registrará por corrida:

- pulsos preparados por Alice;
- clics producidos por los tres detectores hasta la última clave completada;
- slots temporales con al menos un clic;
- slots que SeQUeNCe convirtió en un bit válido antes de comparar bases;
- bits tamizados, errores y claves completadas;
- tiempo hasta la última clave y horizonte configurado.

La instrumentación envolverá los puntos de observación de QKDNode y QSDetectorTimeBin. No modificará el comportamiento del núcleo de SeQUeNCe.

Cada corrida verificará las relaciones que correspondan a los datos observados. Los bits tamizados no podrán superar los slots válidos y los slots con clic no podrán superar los clics registrados. El informe publicará la fracción de tamizado observada y la interpretará frente a la elección aleatoria de bases, sin convertir q = 1/2 en una cota determinista para una muestra finita.

El antiguo "dominio validado" pasará a llamarse "dominio consistente con los controles de contabilidad". Los puntos que fallen permanecerán en los datos y las figuras como diagnóstico.

### 3.2 Fuente coherente y fondo

Para una intensidad x, el modelo analítico usará:

Q_x = 1 - (1 - Y_0) exp(-x eta).

La eficiencia eta incluye canal y detector. Y_0 será un rendimiento efectivo de fondo declarado. El código no restará Y_0 de ganancias que antes lo omitieron.

### 3.3 Estados señuelo

La cota Vacuum+Weak conservará:

Y_1^L = mu / (mu nu - nu^2) [Q_nu exp(nu) - Q_mu exp(mu) nu^2 / mu^2 - (mu^2 - nu^2) Y_0 / mu^2].

El error monofotónico se corregirá a:

e_1^U = [E_nu Q_nu exp(nu) - e_0 Y_0] / (Y_1^L nu), con e_0 = 1/2.

El código limitará Y_1^L al intervalo físico y e_1^U a [0, 1/2]. La tasa usará Q_1^L = mu exp(-mu) Y_1^L.

### 3.4 Métrica de los experimentos 1 a 3

La expresión R_tam [1 - f_EC h_2(E) - h_2(E)] se conservará solo como proxy asintótico monofotónico. Las variables, ejes, tablas y párrafos no la llamarán tasa secreta certificada ni cota para la fuente coherente débil.

El experimento 4 seguirá siendo híbrido. Combinará ganancias analíticas coherentes con Y_0 y errores obtenidos en SeQUeNCe. El texto declarará esa separación cada vez que interprete la tasa.

## 4. Diseño experimental

### 4.1 Muestra

Cada punto usará 30 pares de semillas independientes y deterministas. Las claves tendrán 2048 bits y se solicitarán tres claves por corrida, salvo que una prueba de tiempo documentada exija otro valor. El horizonte deberá permitir completar las claves en todo el barrido. Una corrida incompleta se marcará y no se sustituirá silenciosamente.

Los intervalos del 95 % describirán variabilidad Monte Carlo entre corridas. El manuscrito no los presentará como análisis de clave finita.

### 4.2 Experimento 1: distancia

El barrido conservará los 14 puntos entre 1 y 100 km. Publicará QBER, throughput tamizado, proxy monofotónico, probabilidad analítica de clic y métricas de contabilidad. La conclusión de distancia dependerá de los controles observados y no solo de R_tam <= R_det.

### 4.3 Experimento 2: detector y temporización

Los barridos de eficiencia y conteos oscuros usarán claves de 2048 bits para reducir el efecto de batching. Se añadirá un control factorial pequeño con dos longitudes de clave y dos retardos clásicos. Ese control decidirá si el texto puede atribuir la insensibilidad a la temporización. Si no la demuestra, el informe hablará de una hipótesis compatible con los datos.

### 4.4 Experimento 3: visibilidad

El barrido conservará la relación impuesta p_fase = (1 - V) / 2. El informe la tratará como prueba de sensibilidad interna. Las correlaciones se calcularán sobre los nuevos puntos y no se presentarán como validación de hardware.

### 4.5 Experimento 4: estados señuelo

Se publicarán tres escenarios:

1. referencia conservadora sin señuelos con mu = 0,1;
2. referencia sin señuelos con la misma intensidad de señal mu = 0,6;
3. modelo Vacuum+Weak con mu = 0,6, nu = 0,2 y el Y_0 declarado.

La comparación principal será la de igual intensidad. El caso mu = 0,1 quedará como referencia de una política conservadora distinta, no como contrafactual causal.

## 5. Datos y reproducibilidad

El programa escribirá dos niveles de datos:

- CSV resumidos, uno por experimento, con medias, intervalos y parámetros;
- un CSV de corridas con experimento, punto, repetición, semillas, parámetros, conteos, QBER, tiempos y tasas intermedias.

El resumen JSON incluirá versiones, comando de reproducción, política de semillas, fórmulas seleccionadas y nombres de datasets. El repositorio dejará de ignorar los CSV de experiments/results sin cambiar la política global para otros CSV.

El CSV decoy conservará E_mu, E_nu, Q_mu, Q_nu, Y_1^L, e_1^U, Q_1^L y las tasas de cada escenario.

## 6. Pruebas

Las pruebas se escribirán antes de modificar las funciones de producción. Deben demostrar:

- la fórmula corregida de e_1^U con un caso numérico tomado de la referencia;
- la inclusión coherente de Y_0 en Q_x;
- los límites físicos de Y_1^L y e_1^U;
- la diferencia entre proxy monofotónico, cota sin señuelos y cota decoy;
- el formato completo de los registros por corrida;
- las invariantes de contabilidad con datos sintéticos;
- la repetibilidad de semillas.

Primero se ejecutarán las nuevas pruebas contra el código actual y deberán fallar por la razón esperada. Luego se hará el cambio mínimo que las haga pasar.

## 7. Manuscrito y figuras

El informe mantendrá la estructura breve de Proyecto 3. Se actualizarán ecuaciones, tabla de configuración, figuras, síntesis y conclusiones. Las leyendas indicarán 30 repeticiones, longitud de clave, tipo de intervalo y alcance de cada tasa.

Las figuras mostrarán los puntos que fallen controles sin incorporarlos a afirmaciones de factibilidad. Se evitarán zonas llamadas "válidas" si el criterio solo mide consistencia interna.

La compilación conservará paper/proyecto3.tex y paper/proyecto3.pdf como entregables. El PDF final deberá tener referencias resueltas, texto legible, tablas sin desbordes y figuras nítidas.

## 8. Fuera de alcance

- Una prueba composable de seguridad de clave finita.
- Autenticación, reconciliación y amplificación de privacidad implementadas de extremo a extremo.
- Certificación de hardware o de una red QKD real.
- Cambios generales al núcleo de SeQUeNCe.

## 9. Entregables

- pruebas nuevas para el modelo QKD;
- simulador corregido e instrumentado;
- CSV resumidos y por corrida;
- resumen JSON reproducible;
- figuras regeneradas y el control de temporización;
- manuscrito y PDF revisados;
- documentación de reproducción actualizada.
