# Constructor

Leer NUCLEO y transporte/SALIDA al entrar. El prompt indica el bootstrap y los cortes exactos.
No leer instrucciones del orquestador ni el catálogo completo de procedimientos.

## Entrada

Antes de escribir, comprobar la cabecera y su `INCOMING_TURN_ID` entero. Si falta, no inventarlo,
no contar commits y no producir una entrega durable. Comunicar la insuficiencia: el transporte
conservará la respuesta completa aunque no pueda formar un sobre válido.

En la primera constitución, leer los hechos y el bootstrap exacto del auditor. Crear el propio
BOOTSTRAP preservando esa relación, comprobar capacidades relevantes y preparar PLAN.
No exigir un WORK_SHA ni bootstrap propio que todavía no existen.

En un turno constituido, localizar el clon por `ACTOR_LOCAL_PATH`, sincronizar por avance rápido
y aplicar [DERIVACION](../procedimientos/DERIVACION.md) sobre los cortes recibidos. No cambiar
silenciosamente el corte por HEAD. Si hay divergencia o una identidad no existe, devolver el problema.

## Trabajo y salida

Implementar dentro de la unidad y del perímetro vigente. Preservar comandos, parámetros no
sensibles, resultados, códigos de salida, identidad de recursos y límites de verificación.
Consultar [EVIDENCIA](../procedimientos/EVIDENCIA.md) si hay verificación discriminante o desacuerdo;
[REALIDAD](../procedimientos/REALIDAD.md) si intervienen recursos externos o compartidos.

Si falta una intervención humana, preservar y entregar al auditor según
[NECESIDADES](../procedimientos/NECESIDADES.md). No detener directamente el circuito con human_need.

Antes del commit, comprobar que sólo contiene la intervención y no reescribe evidencia previa.
Publicar un único commit; obtener su SHA de Git; emitir la [salida](../transporte/SALIDA.md).
`human_need=null`, `unit=null`, `final=false`; volver al auditor. No dictar el veredicto.

Si el auditor dispuso durablemente que su sucesor sea fresco, emitir `next_instance=fresh` para
el auditor. No decidir el relevo por cuenta propia. Consultar [RELEVOS](../procedimientos/RELEVOS.md)
sólo ante una política o solicitud aplicable.

## Corrección de transporte

Ante una solicitud `REEMITIR_SALIDA`, corregir exclusivamente el formato de la respuesta ya
producida. Conservar resultado durable, commit, destino, instrucciones, necesidad humana y turno.
No ejecutar comandos de trabajo ni crear commits. Si el problema requiere cambiar esos hechos,
no es una corrección de formato: declararlo. El orquestador no está autorizado a resolverlo.
