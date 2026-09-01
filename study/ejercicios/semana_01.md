# Ejercicios de la semana 1

Intentá cada ejercicio antes de desplegar la pista. Escribí una respuesta aunque sea
incompleta; comparar tu razonamiento es más útil que reconocer una solución.

## 1. Tres objetivos distintos

Eve puede leer un mensaje, no puede modificarlo y sabe con certeza que lo envió
Alice. ¿Qué propiedades se cumplen y cuál falla?

<details>
<summary>Pista</summary>

Evaluá por separado lectura, modificación e identidad.
</details>

<details>
<summary>Solución</summary>

Se cumplen integridad y autenticación. Falla confidencialidad porque Eve puede leer
el mensaje.
</details>

## 2. La clave antes del cifrado

Explicá por qué un algoritmo simétrico excelente no resuelve por sí solo la
distribución inicial de claves.

<details>
<summary>Pista</summary>

Preguntá qué información necesita Bob antes de descifrar.
</details>

<details>
<summary>Solución</summary>

Bob necesita poseer el secreto correcto. El algoritmo define cómo usarlo, pero no
cómo Alice y Bob obtienen copias auténticas sin revelarlas a Eve. Esa coordinación es
un problema adicional.
</details>

## 3. QKD no es un cifrador

Una empresa anuncia: “Los fotones QKD cifran directamente todos nuestros videos”.
Corregí la frase sin quitarle el posible uso real de QKD.

<details>
<summary>Pista</summary>

Separá generación de clave y cifrado del tráfico.
</details>

<details>
<summary>Solución</summary>

QKD puede generar o renovar claves compartidas. Esas claves luego pueden alimentar
un cifrador autenticado, por ejemplo basado en AES, que protege los videos. Los
fotones no transportan normalmente el video cifrado del usuario.
</details>

## 4. Clasificación de tecnologías

Clasificá cada caso como QKD, PQC, cifrado simétrico o comunicación cuántica no QKD:

1. Intercambio de claves basado en retículas ejecutado en servidores comunes.
2. AES-GCM protege paquetes IP.
3. Alice y Bob estiman QBER a partir de estados ópticos.
4. Dos procesadores distribuyen entrelazamiento para teleportar un qubit.

<details>
<summary>Pista</summary>

Preguntá si requiere estados cuánticos, qué producto entrega y dónde se ejecuta.
</details>

<details>
<summary>Solución</summary>

1. PQC. 2. Cifrado simétrico autenticado. 3. QKD. 4. Comunicación cuántica no QKD.
</details>

## 5. Ataque de intermediario

Alice y Bob usan un canal cuántico ideal, pero no autentican el canal clásico. ¿Qué
puede hacer Eve sin violar el teorema de no clonación?

<details>
<summary>Pista</summary>

Eve no necesita copiar el mismo estado si puede presentarse como un extremo distinto
en cada conversación.
</details>

<details>
<summary>Solución</summary>

Puede ejecutar un protocolo con Alice haciéndose pasar por Bob y otro con Bob
haciéndose pasar por Alice. Obtiene una clave con cada uno y retransmite mensajes. No
clona estados desconocidos; explota la falta de identidad autenticada.
</details>

## 6. Consumo de OTP

Alice quiere proteger `250 MiB` con OTP. ¿Cuántos bits de clave necesita? ¿Cuánto
tarda en acumularlos con una SKR de `20 kbit/s`?

<details>
<summary>Pista</summary>

`1 MiB = 2^20 bytes` y `1 byte = 8 bits`.
</details>

<details>
<summary>Solución</summary>

```math
K=250\times2^{20}\times8=2\,097\,152\,000\;bits
```

Con `20.000 bit/s`:

```math
t=\frac{2\,097\,152\,000}{20\,000}=104\,857{,}6\;s
```

Son unas `29,1 h`. No se incluyó material adicional para autenticación.
</details>

## 7. Renovación de claves

Un servicio funciona 24 horas y cambia una clave AES-256 cada 10 minutos. Calculá el
material diario de clave y el tiempo necesario para generarlo con `500 bit/s` de SKR.

<details>
<summary>Pista</summary>

Hay seis intervalos por hora.
</details>

<details>
<summary>Solución</summary>

Hay `24 x 6 = 144` claves:

```math
K=144\times256=36\,864\;bits=4\,608\;bytes
```

A `500 bit/s`, se generan en `36.864 / 500 = 73,728 s`. El cálculo no decide si esa
política es segura; solo estima consumo.
</details>

## 8. Pregunta de tribunal

“Si QKD requiere autenticación previa y usa AES después, ¿no es completamente
redundante?” Respondé en menos de 90 segundos.

<details>
<summary>Pista</summary>

Separá raíz inicial, expansión/renovación de material y cifrado de datos. Incluí un
límite.
</details>

<details>
<summary>Criterio de respuesta</summary>

Una respuesta defendible reconoce que QKD no elimina todos los secretos iniciales ni
reemplaza el cifrado. Su aporte potencial es generar material fresco cuya seguridad
se relaciona con mediciones físicas y un modelo, reservando parte para autenticar
rondas futuras. AES consume ese material para proteger datos. También debe admitirse
que el costo de hardware y los supuestos de implementación pueden hacer preferible
PQC u otra arquitectura en muchos casos.
</details>

## Cierre sin apuntes

1. Definí QKD en una frase sin usar la palabra “cuántico”.
2. Explicá por qué el canal clásico debe ser autenticado.
3. Compará OTP y AES usando consumo de claves.
4. Nombrá dos cosas que la tesis no certifica.

Actualizá [progreso](../progreso.md) y registrá los errores que deban reaparecer en
[errores y dudas](../errores_y_dudas.md).
