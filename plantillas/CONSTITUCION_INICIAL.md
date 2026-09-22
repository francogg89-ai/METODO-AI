# Constitución inicial

WORK_ID: <id>
CARRIL: <carril>
METHOD_REPO: francogg89-ai/METODO-AI
METHOD_SHA: <commit completo publicado>
MANIFEST_REPO: francogg89-ai/MANIFIESTOS-TRABAJOS-AI
MANIFEST_PATH: manifiestos/<WORK_ID>/MANIFIESTO_TRABAJO.md
MANIFEST_SHA: <commit completo publicado>
WORK_REPO: <owner/repo>
AUDIT_REPO: <owner/repo>

## Entorno y acceso
<Runtime de cada actor; raíz local y paths de clones cuando corresponda; entornos y superficies
de lectura/escritura; referencias seguras a credenciales, nunca sus valores.>

## Capacidades iniciales
<Actor, entorno, capacidad y límites. Mantener separación work/audit.>

## Política de ejecución
<Relevos manuales o cadencia/fronteras explícitas; decisiones reservadas. Máximo dos reintentos
seguros adicionales de transporte. Integración de adaptadores identificada y comprobada.>

## Fuentes auxiliares
<SOURCE_REPOS: repo, commit exacto y función; sólo las útiles, sólo lectura. Omitir si no aplica.>

<!-- Agregar PROJECT_REPO/PATH/SHA si corresponde. Omitir campos inaplicables; no publicar placeholders.
El primer auditor lee núcleo, rol y salida en METHOD_SHA, preserva BOOTSTRAP y constituye al constructor.
No recrear un trabajo existente usando esta plantilla. -->
