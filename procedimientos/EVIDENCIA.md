# Evidencia, defectos y desacuerdo

La afirmación del constructor no se transforma en comprobación independiente porque el auditor
la lea. Una prueba local no demuestra una propiedad exclusiva de un recurso externo.

## Verificación discriminante

Antes de ejecutar, el constructor propone en EVENTO: candidato exacto, propiedad, entorno,
mecanismo, criterio de éxito, criterio de fallo y limitaciones. Cuando pueda satisfacerse por
accidente, incluye un control negativo. El auditor evalúa y congela antes de ejecutar ninguna
mitad. Si es insuficiente, explica qué no demuestra sin diseñar por el constructor.

Proponer → evaluar → congelar → ejecutar → preservar evidencia → interpretar según el criterio.
No redefinir el criterio después de observar. Toda observación se resuelve como éxito o fallo;
no introducir una tercera salida por limitación del escenario. Una corrida agota su contrato;
otra corrida requiere otro contrato. Esto no convierte una comprobación rutinaria en un contrato
discriminante: exigirlo sólo cuando la propiedad material lo requiera.

## Defectos

Materiales (comportamiento, seguridad, datos, contrato, alcance) y de diseño bloquean.
Documentales relevantes pueden bloquear si el auditor identifica el riesgo operativo concreto.
Editoriales no bloquean. Tras dos rondas de cambios puramente editoriales no continuar bloqueando
sin riesgo demostrado. El constructor puede cuestionar la clasificación con evidencia.

Tras dos rondas sin converger sobre el mismo punto, reconocer el desacuerdo y aumentar la
capacidad discriminante: reproducción, test, fuente autoritativa o revisión independiente.
No usar al humano como árbitro técnico salvo que haga falta dominio, riesgo, prioridad o autoridad.
Un auxiliar recibe un alcance limitado, no hereda autoridad y entrega evidencia; no declara veredicto.
Si hace falta transporte humano para convocarlo, usar el mecanismo material de NECESIDADES.
