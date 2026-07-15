# Semana 1: criptografía y distribución de claves

## Objetivos

Al terminar este capítulo deberías poder:

- separar confidencialidad, integridad y autenticación;
- explicar por qué cifrar bien no resuelve automáticamente cómo compartir la clave;
- comparar seguridad perfecta y seguridad computacional sin decir que una es
  simplemente "mejor";
- distinguir QKD, cifrado cuántico, computación cuántica y criptografía
  post-cuántica;
- ubicar con precisión qué entrega la tesis y qué queda fuera de su alcance.

## 1. La pregunta central

Alice quiere enviarle a Bob un mensaje por una red controlada parcialmente por Eve.
Si Alice y Bob comparten una clave secreta adecuada, pueden usar criptografía
simétrica. Pero aparece una pregunta anterior:

> ¿Cómo obtuvieron ambos la misma clave sin que Eve también la obtuviera?

Éste es el **problema de distribución de claves**. QKD no nació para reemplazar todo
el sistema criptográfico. Ataca esta parte concreta: producir material secreto
correlacionado entre dos extremos y detectar, mediante estadísticas, si el proceso
permite extraer una clave segura bajo un modelo.

## 2. Intuición: la caja y la llave

Imaginá una caja que solo puede abrirse con una llave. Alice puede guardar un mensaje,
cerrar la caja y enviarla. El candado representa el cifrado; la llave representa el
secreto compartido.

La caja ayuda a separar dos problemas:

1. **Proteger el contenido:** usar correctamente el candado.
2. **Entregar la llave:** lograr que Bob tenga una copia sin dársela también a Eve.

QKD se ocupa principalmente del segundo. Después, una aplicación puede consumir esa
clave en AES, autenticación u otro esquema.

**Límite de la analogía:** una clave digital puede copiarse perfectamente sin dejar
marca. Una llave física no representa las propiedades de medición de estados
cuánticos ni demuestra la seguridad de QKD.

## 3. Confidencialidad, integridad y autenticación

Son objetivos distintos:

| Objetivo | Pregunta | Ejemplo de falla |
|---|---|---|
| Confidencialidad | ¿Un tercero puede leer el mensaje? | Eve ve el contenido de un archivo. |
| Integridad | ¿El mensaje fue modificado? | Eve cambia `pagar 10` por `pagar 1000`. |
| Autenticación | ¿Estoy hablando realmente con Bob? | Eve se presenta como Bob ante Alice. |

Un cifrado puede ocultar contenido sin probar identidad. También puede existir un
mensaje público íntegro y autenticado que no sea secreto. En QKD, el canal clásico
debe ser **autenticado**, pero no necesariamente confidencial: Eve puede escuchar las
bases anunciadas, pero no debe poder modificarlas o suplantar a Alice y Bob.

Sin autenticación, Eve podría ejecutar dos protocolos separados: uno con Alice
haciéndose pasar por Bob y otro con Bob haciéndose pasar por Alice. Las propiedades
cuánticas no resuelven por sí solas este ataque de intermediario.

## 4. Cifrado simétrico, OTP y AES

### 4.1 Cifrado simétrico

El mismo secreto, o secretos directamente relacionados, se usa para cifrar y
descifrar. Es rápido y apropiado para grandes volúmenes de datos. Su dificultad
operativa es distribuir, almacenar, rotar y retirar claves.

### 4.2 One-time pad

Para un mensaje binario `M` y una clave aleatoria `K` de igual longitud:

```math
C = M \oplus K
```

Bob recupera:

```math
M = C \oplus K
```

Si `K` es verdaderamente aleatoria, tan larga como el mensaje, secreta y nunca se
reutiliza, el *one-time pad* (OTP) ofrece seguridad perfecta en el sentido de Shannon:
el texto cifrado no permite preferir un mensaje posible sobre otro de igual longitud.

Cada condición es exigente. Reutilizar una clave OTP permite cancelar la clave al
combinar dos textos cifrados:

```math
C_1 \oplus C_2 = (M_1 \oplus K) \oplus (M_2 \oplus K) = M_1 \oplus M_2
```

OTP no elimina el problema de distribución: lo vuelve enorme porque requiere tantos
bits secretos como datos.

### 4.3 AES

AES es un cifrador de bloque simétrico. En un modo autenticado adecuado puede
proteger confidencialidad e integridad usando claves cortas, por ejemplo 256 bits,
para mucho más de 256 bits de datos. Su seguridad es **computacional**: depende de que
ningún adversario con recursos realistas pueda recuperar la clave o falsificar datos
dentro del modelo y tiempo considerados.

No alcanza con decir "uso AES". Importan el modo de operación, nonces, autenticación,
generación de claves y manejo del ciclo de vida. Este curso usa AES para comparar
consumo de claves, no para diseñar una aplicación criptográfica completa.

## 5. Clave pública y amenaza cuántica

La criptografía de clave pública permite coordinar secretos o firmas sin compartir de
antemano una clave privada común. RSA, Diffie-Hellman y criptografía de curva elíptica
basan su seguridad práctica en problemas matemáticos considerados difíciles para
computadoras clásicas.

El algoritmo de Shor muestra que una computadora cuántica tolerante a fallos y de
escala suficiente podría resolver eficientemente factorización y logaritmo discreto,
afectando familias ampliamente desplegadas. Esto motiva dos respuestas diferentes:

- **Criptografía post-cuántica (PQC):** algoritmos clásicos diseñados para resistir
  ataques clásicos y cuánticos conocidos; se ejecutan sobre redes y procesadores
  convencionales.
- **QKD:** hardware y protocolos que usan estados cuánticos para distribuir claves y
  estimar información potencial de un adversario.

PQC y QKD no son sinónimos ni necesariamente rivales. PQC es más fácil de desplegar a
gran escala; QKD aporta un modelo físico de distribución de claves, pero requiere
infraestructura especializada y supuestos de dispositivos.

## 6. Qué resuelve QKD y qué no resuelve

### QKD sí busca

- generar material de clave compartido;
- estimar perturbaciones e información potencial de Eve;
- abortar cuando las estadísticas no permiten extraer una clave;
- producir una clave más corta mediante reconciliación y amplificación de privacidad.

### QKD no hace por sí sola

- cifrar el tráfico de usuario;
- autenticar inicialmente a Alice y Bob sin una raíz de confianza;
- impedir robo de claves después de que una aplicación las recibe;
- proteger un detector contra todos los canales laterales;
- convertir un QBER bajo en una certificación automática;
- transportar qubits para computación distribuida general.

La expresión **criptografía cuántica** es un área amplia. QKD es una aplicación dentro
de ella. La expresión **comunicación cuántica** también incluye distribución de
entrelazamiento, repetidores, teleportación y redes cuánticas; no todo eso es QKD.

## 7. Conexión con la tesis

La tesis no construye un cifrador ni una computadora cuántica. Diseña y evalúa por
simulación un banco de pruebas de QKD BB84 con codificación time-bin y estados
señuelo.

Su cadena lógica es:

```mermaid
flowchart LR
    A[Problema: distribuir claves] --> B[BB84 time-bin]
    B --> C[Fuente, fibra, interferómetro y detector]
    C --> D[Simulación de detecciones y errores]
    D --> E[QBER y throughput]
    E --> F[Estimación analítica de SKR]
    F --> G[Decisiones para un banco de pruebas]
```

La contribución es de **ingeniería previa a la implementación**. Las curvas permiten
comparar sensibilidad a distancia, detector y visibilidad. No prueban que un equipo
real esté libre de canales laterales ni ejecutan todo el posprocesamiento de una clave
productiva.

Podés contrastar esta explicación con la [introducción de la tesis](../../paper/chapters/01_introduccion.tex)
y el [marco teórico](../../paper/chapters/02_marco_teorico.tex).

## 8. Ejemplo numérico

Alice debe transferir un archivo de `1 GiB`:

```math
1\;GiB = 2^{30}\;bytes = 8\,589\,934\,592\;bits
```

### Opción OTP

Necesita exactamente `8.589.934.592` bits aleatorios y secretos, aproximadamente
`1 GiB` de clave, usados una sola vez. Si el enlace QKD produjera `1.000 bit/s` de
clave final, acumular esa clave tomaría:

```math
t = \frac{8\,589\,934\,592\;bit}{1\,000\;bit/s}
  \approx 8{,}59\times 10^6\;s \approx 99{,}4\;días
```

### Opción AES-256 con renovación cada minuto

En una sesión de ocho horas hay `480` intervalos. Si cada intervalo consume una clave
nueva de 256 bits:

```math
K_{día} = 480 \times 256 = 122\,880\;bits = 15\,360\;bytes
```

A una SKR de `1.000 bit/s`, ese material se genera en aproximadamente `123 s`.

La comparación no demuestra que renovar AES cada minuto sea una política óptima ni
incluye claves de autenticación, overhead o reservas. Sí muestra una decisión de
arquitectura: una SKR modesta puede ser insuficiente para OTP de alto volumen y, al
mismo tiempo, más que suficiente para renovar claves de cifrado simétrico.

## 9. Errores frecuentes

1. **"QKD encripta con fotones."** No: distribuye claves; el cifrado de datos es otra
   capa.
2. **"Si es cuántico, es imposible de atacar."** La seguridad depende del protocolo,
   prueba, supuestos y dispositivos.
3. **"El canal clásico debe ser secreto."** Debe ser autenticado; puede ser público.
4. **"PQC usa fotones cuánticos."** PQC usa algoritmos clásicos resistentes a ataques
   cuánticos conocidos.
5. **"OTP siempre es la opción práctica más segura."** Sus condiciones dan seguridad
   perfecta, pero distribuir y no reutilizar una clave del tamaño del tráfico puede
   ser inviable.
6. **"Una clave de 256 bits solo cifra 256 bits."** En un cifrador como AES la clave
   puede proteger mucho más tráfico, respetando límites y modos correctos.

## 10. Preguntas de tribunal

### ¿Por qué usar QKD si existe criptografía post-cuántica?

Una respuesta sólida debe decir que resuelven el riesgo con mecanismos y costos
distintos. PQC se despliega por software y mantiene seguridad computacional; QKD usa
un canal físico especializado para distribución de claves bajo un modelo de
dispositivos. La tesis estudia la factibilidad de esta segunda opción en un banco de
pruebas, no afirma que deba reemplazar PQC.

**Repregunta:** ¿Qué usarías en una red nacional con millones de usuarios?

**Límite esperado:** no extrapolar un enlace de campus a una solución universal.

### ¿Por qué QKD necesita un canal clásico autenticado?

Porque Alice y Bob publican bases, estiman errores y coordinan posprocesamiento. Si
Eve puede modificar o originar esos mensajes, puede hacerse pasar por cada extremo y
crear dos claves diferentes.

**Repregunta:** ¿Entonces QKD necesita una clave previa?

**Respuesta esperada:** necesita una raíz inicial de autenticación; una vez obtenidas
claves nuevas, parte puede reservarse para autenticar rondas posteriores.

### ¿La tesis genera una clave final lista para AES?

No. Simula transmisión, medición y tamizado, y estima SKR mediante expresiones
analíticas. No ejecuta reconciliación y amplificación de privacidad completas ni
certifica una implementación física.

**Repregunta:** ¿Entonces por qué la SKR es útil?

**Respuesta esperada:** como cota de diseño bajo supuestos explícitos para comparar
configuraciones y decidir qué banco vale la pena construir.

## 11. Salida oral de dos minutos

Respondé sin leer:

> ¿Qué problema resuelve QKD, por qué no equivale a cifrar y qué aporta exactamente
> esta tesis?

Usá cuatro movimientos:

1. problema de distribución de claves;
2. mecanismo general de canal cuántico más canal clásico autenticado;
3. uso posterior de la clave;
4. alcance de simulación y límite de certificación.

## 12. Fuentes

- C. E. Shannon, [Communication Theory of Secrecy Systems](https://doi.org/10.1002/j.1538-7305.1949.tb00928.x), 1949.
- P. W. Shor, [Algorithms for quantum computation: discrete logarithms and factoring](https://doi.org/10.1109/SFCS.1994.365700), 1994.
- C. H. Bennett y G. Brassard, [Quantum cryptography: Public key distribution and coin tossing](https://doi.org/10.1016/j.tcs.2014.05.025), versión de archivo del trabajo de 1984.
- [Introducción de la tesis](../../paper/chapters/01_introduccion.tex).
- [Marco teórico de la tesis](../../paper/chapters/02_marco_teorico.tex).

## Próximo paso

Resolvé los [ejercicios de la semana 1](../ejercicios/semana_01.md) sin abrir las
soluciones. Después actualizá [progreso](../progreso.md) y mové al registro cualquier
respuesta que haya sonado correcta pero no pudiste justificar.
