# Justificaciones de decisiones técnicas — Project Charter S04

**Proyecto:** Sistema de Retroalimentación por Voz (SRV) basado en IA para la fluidez de oratoria
**Institución:** I.E. Juan José Farfán — Lancones, Piura
**Documento:** Justificación de las desviaciones respecto al Project Charter (uso académico — UPAO)

> Este documento sustenta tres decisiones de diseño que difieren de lo planteado
> originalmente en el Project Charter. En los tres casos se preserva el **propósito
> y el valor funcional** del objetivo, optando por alternativas técnicamente sólidas
> y, en dos de ellas, éticamente preferibles para el trabajo con menores de edad.

---

## Justificación 1 — Retroalimentación por lotes con componente híbrido en lugar de streaming en tiempo real (< 2 s)

**Lo planteado en el charter.** El Objetivo de Desarrollo 1 fija una latencia menor a 2 segundos
para la visualización de la onda y el inicio de la transcripción, mediante streaming
bidireccional (Socket.io) en fragmentos de 100 ms.

**Lo implementado.** La aplicación captura el enunciado completo del estudiante y ejecuta el
análisis al finalizar la grabación (procesamiento por lotes), manteniendo la **visualización
de la onda de voz en tiempo real** durante toda la grabación.

**Justificación técnica.**
- El motor de reconocimiento adoptado (faster-whisper, modelo *medium*) procesa el enunciado
  completo. Al ejecutarse sobre CPU —la infraestructura disponible no cuenta con GPU—, el
  tiempo de cómputo es inherentemente mayor que la duración del habla, por lo que una
  transcripción final en menos de 2 segundos **no es físicamente alcanzable** sin hardware
  especializado (GPU) o sin degradar el modelo a una versión menor, lo que comprometería
  directamente la meta de precisión (WER).
- Diversas métricas requieren, **por su propia naturaleza**, el enunciado completo para ser
  válidas: la riqueza léxica (TTR), el conteo de muletillas, la coherencia semántica y el
  puntaje global. Calcularlas "en vivo" sobre frases incompletas carece de sentido
  metodológico (p. ej., no es posible estimar la variedad de vocabulario con tres palabras).

**Cumplimiento del charter.** El charter especifica textualmente "menos de 2 segundos para la
visualización de la onda y **el inicio** de la transcripción". La visualización de la onda **es
en tiempo real** (Web Audio API / WaveSurfer), cumpliendo ese componente. Se adopta un modelo
**híbrido**: retroalimentación visual inmediata mientras el niño habla, más una evaluación
integral al concluir. Este patrón es el estándar en aplicaciones serias de evaluación del
habla, donde el análisis profundo se realiza sobre la locución completa.

**Conclusión.** La decisión no reduce el valor para el usuario: el estudiante recibe estímulo
visual instantáneo y, segundos después, una retroalimentación completa y rigurosa.

---

## Justificación 2 — Despliegue en Railway + Supabase en lugar de infraestructura AWS (EC2/RDS/S3) y ASR local en lugar de AWS Transcribe

**Lo planteado en el charter.** Infraestructura sobre Amazon Web Services: VPC, instancia
EC2 t3.medium, base de datos PostgreSQL en RDS, almacenamiento de audio en S3 y reconocimiento
de voz mediante el SDK de AWS Transcribe Streaming.

**Lo implementado.** Backend desplegado en **Railway** (cómputo gestionado), base de datos
**PostgreSQL gestionada en Supabase**, frontend en Vercel y reconocimiento de voz con
**faster-whisper ejecutado localmente** en el servidor.

**Justificación técnica (equivalencia funcional).**
- *Cómputo gestionado:* Railway cumple el mismo rol que una instancia EC2, sin la carga
  operativa de administrar VPC, subredes, tablas de ruteo ni certificados SSL manuales
  (Railway, Vercel y Supabase proveen HTTPS y red gestionada de forma nativa).
- *Base de datos:* Supabase ofrece PostgreSQL gestionado, equivalente funcional de RDS,
  manteniendo el esquema relacional comprometido.
- *Costo y complejidad:* la solución reduce el costo y la complejidad de operación, factor
  relevante en un proyecto académico, sin sacrificar los entregables funcionales.

**Justificación ética (decisiva).** Al emplear un motor de reconocimiento **local** en lugar
de AWS Transcribe, **la voz de los menores no se transmite a un servicio de terceros**. El
audio se procesa en el servidor y se **elimina inmediatamente** tras el análisis (la
persistencia está implementada pero **desactivada** por defecto). Esta decisión refuerza la
protección de datos personales de menores y es **coherente con el propio marco ético-legal del
charter** (consentimientos informados, asentimiento de los menores y supervisión del Comité de
Ética). Almacenar o enviar a un tercero la voz de niños de primer grado introduciría un riesgo
y una responsabilidad legal innecesarios para los fines del estudio.

**Cumplimiento del charter.** Se conservan todos los entregables funcionales del objetivo
(servidor de aplicación, base de datos relacional PostgreSQL, HTTPS y capacidad de
persistencia) sobre proveedores **equivalentes**, preservando el espíritu del objetivo: un
sistema desplegado, accesible y seguro.

---

## Justificación 3 — Análisis de vocabulario y coherencia semántica (Dimensión 2) como valor agregado

**Lo planteado en el charter.** En el apartado "Fuera de alcance" se indica que el sistema
"no evaluará la sintaxis ni el significado profundo del discurso, solo la fluidez y prosodia".

**Lo implementado.** Además de la fluidez (D1) y la expresividad vocal (D3), el sistema
incorpora una Dimensión 2 que evalúa **vocabulario y coherencia** mediante spaCy
(es_core_news_lg) y BETO (modelo BERT en español): riqueza léxica (TTR), detección de
muletillas y coherencia semántica.

**Justificación.** Esta incorporación **no constituye un incumplimiento, sino una ampliación
del valor entregado** por encima del alcance mínimo comprometido. Es importante precisar la
distinción metodológica:
- El sistema **no corrige gramática** ni juzga la "corrección" del contenido del discurso —eso
  permanece fuera de alcance—.
- Lo que aporta son **indicadores formativos adicionales** (variedad de vocabulario, uso de
  muletillas, coherencia como señal de organización del mensaje) que enriquecen la
  retroalimentación al estudiante **sin sustituir el criterio del docente**.

**Conclusión.** La Dimensión 2 se presenta como un **aporte que excede el alcance** declarado,
en línea con el propósito del proyecto de potenciar las habilidades comunicativas del
estudiante. Se documenta de forma transparente para evitar interpretarlo como una contradicción
con el alcance original.

---

## Nota metodológica sobre la medición del WER (Objetivo de Desarrollo 2)

Por restricciones éticas, **no se realizan grabaciones independientes de los menores**: la
recolección de datos ocurre a través del **uso normal de la aplicación** por parte de los
estudiantes, con el consentimiento correspondiente. En el modo lectura, el sistema calcula
automáticamente el WER de cada sesión (distancia de Levenshtein entre la transcripción y el
texto de referencia).

Se distingue entre dos mediciones:
1. **WER de fidelidad de lectura** (dato principal, obtenido del uso real): combina el error
   del reconocedor con los errores reales de lectura del estudiante. Es la evidencia de
   desempeño en condiciones reales de aula.
2. **WER de reconocimiento puro** (baseline complementario): obtenido por los propios
   investigadores leyendo los textos de referencia, para aislar la precisión del ASR sin
   involucrar grabaciones de menores.

Esta aproximación permite reportar la métrica del charter con datos reales, declarando con
rigor el alcance y las limitaciones de cada medición.
