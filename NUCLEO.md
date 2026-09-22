# Núcleo

## Autoridades

- El humano decide intención, dominio, prioridades, aceptación de riesgos y capacidades delegadas.
- El constructor diseña, implementa y resuelve problemas técnicos. Escribe sólo en work.
- El auditor verifica evidencia, clasifica defectos y decide veredicto y próxima acción. Escribe sólo en audit.
- El orquestador transporta. No interpreta el trabajo ni decide permisos, relevos o veredictos.

La separación work/audit es estructural. Un auxiliar no permite eludirla. Cambiarla exige cambiar
la intención del método, no ampliar una capacidad ordinaria. Los entornos externos se operan dentro
de capacidades delimitadas por actor, entorno, acción y límites. No se pide otra vez una autorización
ya vigente; ante duda material sobre su alcance o revocación se comprueba antes de actuar.

## Fuentes y artefactos

Materia, evento, auditoría e historia Git tienen funciones distintas. El sobre sólo transporta.
Una afirmación que puede volverse falsa por un evento posterior no se almacena como estado presente:
se deriva al usarla o se registra como hecho situado en un corte exacto.

- `MANIFIESTO_TRABAJO.md`: intención, alcance, exclusiones, restricciones y éxito observable.
- `PLAN.md`: unidades reales, dependencias, verificaciones y terminación. Su aprobación se registra
  en audit vinculada al SHA; no se cambia el plan sólo para escribir "aprobado".
- `<unidad>/EVENTO.md`: qué recibió e hizo el constructor, por qué, evidencia, resultado y límites.
  Se actualiza; las versiones anteriores viven en Git, no dentro del archivo.
- `BOOTSTRAP.md`: hechos de origen de cada actor; no se reescribe para simular estado actual.
- `auditorias/<TARGET_WORK_SHA>.md`: auditoría de la entrega exacta; se escribe una sola vez.

Una intervención principal del constructor produce un único commit autoritativo y publicado.
Cada commit de work es una entrega. Toca una sola unidad, o la raíz antes de las unidades.
No se crean commits de control. Cada intervención auditora preserva su veredicto o próxima acción.
Git demuestra los cambios de archivos; EVENTO explica su significado sin duplicar el diff.

Toda auditoría enlaza `TARGET_WORK_REPO` y `TARGET_WORK_SHA`. Toda intervención auditora declara
`PERIMETRO_ULTIMA_MODIFICACION` según [derivación](procedimientos/DERIVACION.md).
Las decisiones humanas se preservan con identidad exacta, alcance y exclusiones. Los secretos
nunca se copian: sólo se conserva una referencia segura a dónde puede usarlos el actor autorizado.

## Avance proporcional

Un cambio local no altera intención, arquitectura o secuencia macro, dependencias, terminación
ni decisiones humanas. Si altera el plan, se modifica el mismo PLAN, se audita y se obtiene una
nueva decisión humana sobre su SHA. Si altera intención, se modifica el manifiesto con aprobación.

Aceptado el plan, no hay gate humano automático entre unidades. El auditor audita antes de cerrar
una unidad o el trabajo. Sólo él emite transición, cierre o necesidad humana. Una decisión técnica
no se traslada al humano para evitar resolverla.

Al actuar se reconstruye desde el corte exacto, sin depender de memoria conversacional. Una entrega
pendiente se audita antes de relevar. La información indispensable se publica antes del relevo;
las notas temporales locales pueden desaparecer sin impedir continuar.

## Carga mínima

No mantener contadores metodológicos, listas vivas de avance, copias numeradas, handoffs ceremoniales
ni resúmenes que sustituyan fuentes. Cada mecanismo debe proteger una propiedad concreta.
Skills y memoria ayudan a localizar o ejecutar; no conceden autoridad ni reemplazan evidencia.
No se exige registrar aprendizajes en cada turno. No se vuelven a leer fuentes sin necesidad,
pero las comprobaciones del corte y de recursos cambiantes no se sustituyen por recuerdos.
