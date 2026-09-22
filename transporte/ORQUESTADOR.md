# Orquestador

El orquestador usa el núcleo de código. No lee el candidato ni Git para mejorar un next_prompt,
no reescribe texto y no decide sobre trabajo, permisos, veredictos o relevos.

## Arranque

La entrada externa es `METODO_AI_INIT_V1|WORK_ID=...|CARRIL=...|CONSTITUTION_REPO=owner/repo|CONSTITUTION_PATH=...|CONSTITUTION_SHA=...`.
Es ASCII de una línea. Sólo se tolera un BOM inicial y espacios ASCII exteriores. El código
valida campos y SHA. Abrir auditor fresh, entregar sólo el locator canónico y confirmar entrega.
El primer sobre debe provenir de ese auditor con turn_id=1. El orquestador no crea BOOTSTRAP.

## Loop

Esperar finalización y capturar la respuesta completa de la intervención identificada. Conservar
el original antes del parseo. Validar forma, campos, tipos, rol de origen, work_id, repositorio
del emisor, secuencia y combinaciones. No inferir campos desde prosa. Tomar next_prompt directamente
del objeto, pasarlo al adaptador y verificar integridad. Nunca reemitirlo mediante generación IA.

Sólo un envío confirmado avanza last_turn en una continuación. Un sobre válido de necesidad o
cierre se acepta al detener y avanza last_turn. Un intento fallido no lo avanza. La notificación
unit no cambia unidades ni crea gate. Se muestra después de validar; no habilita un envío inválido.

## Recuperación limitada

Hasta dos reintentos adicionales por operación. No abrir otro ciclo de intentos para eludir el límite.
Recapturar la misma respuesta si la captura fue incompleta. Si el texto preparado cambió y no se
envió, limpiar sólo esa entrada y reinsertar el original. Comparar UTF-8, longitud y SHA-256 sin
normalizar caracteres. Un error de parseo con captura completa no demuestra un error de captura.

Un sobre original inválido requiere corrección del emisor, no del orquestador. Se habilita sólo
si el adaptador tiene un canal de reparación restringido y puede acreditar ausencia de trabajo
material nuevo. Conservar la respuesta original y las reemisiones. No cambiar turno ni resultado.
Una corrección que altera decisiones no es admisible. El núcleo soporta reparación exclusivamente
si se puede extraer un único objeto previo y la reemisión conserva todos sus valores; si no puede
comprobarlo, detiene. Este límite evita inventar contenido de JSON roto o de múltiples candidatos.

Si send confirma NOT_SENT y que es seguro repetir, reintentar. Si confirma DELIVERED, continuar.
Si hubo excepción, pérdida de recibo o incertidumbre después de enviar, marcar entrega incierta,
detener y no repetir. Una identificación de turno por sí sola no vuelve idempotente al receptor.
Reiniciar el objeto de código no es un mecanismo de recuperación de una entrega incierta.

## Instancias y detención

current debe ser la misma instancia identificable. fresh debe ser distinta de todas las conocidas
de ese rol. Promover fresh y retirar current anterior sólo al confirmar la primera entrega.
Cerrar ventanas antiguas es opcional; volver a seleccionarlas está prohibido. Nunca degradar
current perdido a fresh. Un mecanismo nativo de resume sólo sirve si conserva esa identidad.

DETENER se solicita durante la ejecución y se aplica entre intervenciones: si el constructor
está activo, esperar su entrega, validar y conservar el sobre sin enviarlo al auditor. Si el
auditor está activo y continúa, permitir esa siguiente intervención del constructor y detener
antes de su auditoría. Una necesidad humana o cierre natural prevalece. CONTINUAR entrega el
mismo sobre pendiente; no lo reconstruye contra un estado nuevo.

Durante pausa, entregar al auditor competente ACTOR_PROMPT_LITERAL y HUMAN_DIRECTIVE_LITERAL
como entradas separadas, sin alterar el sobre pendiente. Relevar nunca saltea su auditoría.
La API del núcleo implementa la pausa del sobre constructor→auditor y la separación de la
directiva; el adaptador debe esperar la intervención en curso antes de llamar accept.

El guardado para cambiar los tres agentes no está implementado: ante el comando largo aplicar
DETENER, informar la limitación y conservar current. No emitir una promesa de reanudación durable.

## Reporte y estado

Ante falla final: código y causa concreta, origen, turno esperado, número de intentos, situación
del envío y respuesta original completa. Incluir reemisiones y texto preparado si hubo alteración.
Si la captura fue incompleta indicarlo. No corregir ni resumir el original. El núcleo puede guardar
el reporte y respuestas exactas en archivos locales fuera de Git; esos archivos pueden contener
información del trabajo y no se publican automáticamente. Nunca incluir valores secretos.

Estado runtime: handles, último turno aceptado, respuesta/sobre pendiente, stop_requested y
fallo/recibo de entrega. No es autoridad sobre trabajo. Esta entrega es en memoria; reiniciar el
proceso requiere recuperación externa y no autoriza reutilizar automáticamente un turno.
No hay dashboard, base de pases ni contadores de unidades dentro del transporte.
