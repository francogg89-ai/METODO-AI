# Continuidad del trabajo: alcance pendiente

Este documento delimita la siguiente etapa. No es un protocolo ejecutable de esta entrega.
`DETENER` y `CONTINUAR` están definidos en transporte/ORQUESTADOR.md para las mismas instancias.

La operación futura `DETENER, GUARDAR Y PREPARAR PARA NUEVO ORQUESTADOR` debe permitir solicitar
el guardado en cualquier momento y completarlo en una frontera segura: entrega preservada y
auditada, sin iniciar trabajo material nuevo salvo completar información indispensable.

El paquete en CONTINUIDAD-AI deberá identificar el corte, reglas, bootstraps, rutas, punto de
transporte e instrucciones mínimas. Organizar por carril y WORK_ID; usar commits para versiones.
No duplicar el trabajo ni introducir un registro manual de avance. Evitar autorreferencias al
SHA del commit que crea un archivo: publicar primero el paquete y después su locator de arranque.

La reanudación deberá comenzar con auditor y luego constructor frescos, conservando el trabajo y
la secuencia de transporte. No constituye de nuevo, no recrea bootstraps ni repite auditorías.
El auditor comprueba el corte y cambios posteriores antes de habilitar trabajo. Conserva las
necesidades humanas abiertas. Un guardado limpio y una recuperación por falla no son equivalentes.

Antes de habilitarlo se deben resolver y probar: autoría y publicación limitada del paquete;
retiro comprobable de la ejecución anterior; prevención de dos orquestadores activos; envíos
inciertos y operaciones en curso; reanudación de necesidades humanas; formato mínimo sin duplicación.

Hoy, ante ese comando, no fabricar un paquete ni prometer un arranque recuperable. Informar que
no está implementado y preservar la ejecución mediante DETENER. El núcleo expone esa limitación
explícitamente. No cerrar las instancias necesarias para CONTINUAR.
