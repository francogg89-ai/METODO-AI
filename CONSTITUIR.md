# Constituir un trabajo

Cerrar con el humano sólo lo materialmente necesario: objetivo, resultado, alcance, exclusiones,
restricciones, éxito, riesgos y decisiones reservadas. Cuando corresponda: proyecto, repositorios,
recursos, entornos, capacidades, evidencia y política de relevo. No repetir preguntas ya resueltas
ni convertir la entrevista en un formulario. Las capacidades se expresan por actor/entorno/acción/
límites, no con etiquetas vagas de autonomía.

## Publicación y arranque

1. Redactar el manifiesto con [su plantilla](plantillas/MANIFIESTO_TRABAJO.md).
2. Obtener aprobación humana explícita. El silencio no aprueba.
3. Publicar en MANIFIESTOS-TRABAJOS-AI, `manifiestos/<WORK_ID>/MANIFIESTO_TRABAJO.md`.
4. Si existe proyecto compartido, publicar [PROJECT](plantillas/PROJECT.md) con límites ya acordados.
5. Obtener de Git los commits exactos y preparar [constitución](plantillas/CONSTITUCION_INICIAL.md).
6. Publicarla y verificar su identidad. Materializar [arranque](plantillas/ARRANQUE_ORQUESTADOR.md)
   con `python -m transporte init --config ... --output ...`; no generar SHA ni copiar contenido GUI.
7. El orquestador abre auditor nuevo y entrega sólo el locator. El auditor lee la constitución,
   publica BOOTSTRAP y emite el primer sobre al constructor fresh. Éste crea su BOOTSTRAP,
   preserva la relación con el del auditor, comprueba capacidades y prepara PLAN.

## Autoridad documental

Identidad publicada = repositorio + path + commit SHA completo obtenido y verificado en Git.
Ramas, abreviaturas y blobs no sustituyen commits. WORK_ID es único; carril no lo sustituye.
Las revisiones conservan path e historia; no crear copias numeradas. Cambiar intención requiere
aprobación; cambiar capacidades requiere decisión preservada. Una revisión no cambia por sí sola
las identidades de un trabajo en curso. BOOTSTRAP conserva origen, no se reescribe con revisiones.

La constitución fija METHOD_REPO/METHOD_SHA de este repositorio: ejecución, transporte y plantillas
se seleccionan como una unidad. Referencias internas usan paths, sin congelar SHAs circulares.
No existe un RULES_SHA independiente. Los scripts utilizados deben pertenecer al METHOD_SHA fijado.

## Proyecto y conocimiento

PROJECT identifica PROJECT_ID, WORK_ID, repositorios y funciones, paths permitidos/protegidos,
entornos y recursos, dependencias y límites de integración. Sólo materializa condiciones acordadas;
no concede permisos ni guarda locks, actores activos, últimos SHAs, despliegues o estados vivos.
Los cambios compartidos se comprueban según procedimientos/REALIDAD, no por presunción de aislamiento.

Fuentes auxiliares útiles se declaran en SOURCE_REPOS con commit y función, sólo lectura. Cargar
únicamente lo pertinente. Una skill no autoriza acciones y una memoria no sustituye el corte.
No exigir skills o Engram para arrancar. Su integración compartida se desarrollará por separado.

## Runtimes y controles

Declarar runtime de cada rol, clones/rutas y superficies de lectura/escritura. Paths Windows con
barras `/` salvo exigencia comprobada del entorno. Nunca incluir secretos, sólo referencias seguras.
La política declara cuándo relevar; el auditor la aplica, nunca el orquestador.
El transporte admite como máximo dos reintentos seguros adicionales. No ampliar ese límite por
prompt. Antes de un circuito real, comprobar adaptadores y fidelidad del texto en esos runtimes.
Una aprobación documental no demuestra que exista esa integración.
