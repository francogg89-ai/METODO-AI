# Salida de los actores — metodo-ai-hop/v1

Una respuesta principal contiene exclusivamente un bloque cercado `json`, un objeto válido y
ningún texto exterior salvo espacios. No hay claves duplicadas ni campos adicionales. El método
no exige prosa conversacional ni repetir resultados publicados. El código Python define la
validación ejecutable de tipos y combinaciones; esta página explica su uso por los actores.

Campos obligatorios:

| Campo | Contenido |
|---|---|
| protocol | `metodo-ai-hop/v1` |
| work_id | Identidad del trabajo |
| turn_id | Entero positivo: inicial 1; después INCOMING_TURN_ID + 1 |
| actor | AUDITOR o CONSTRUCTOR |
| repository, commit | Repo del emisor y commit publicado completo de su intervención |
| next_actor | AUDITOR, CONSTRUCTOR o null |
| next_instance | current, fresh o null |
| next_prompt | String literal suficiente o null |
| human_need | Objeto de necesidad o null |
| unit | Transición informativa del auditor o null |
| final | Booleano; sólo el auditor puede emitir true |

Continuación: human_need=null, final=false y destino/instancia/prompt no nulos.
Necesidad: human_need no nulo, final=false y destino/instancia/prompt nulos.
Cierre: human_need=null, final=true y destino/instancia/prompt nulos.
El constructor vuelve siempre al auditor y tiene human_need/unit nulos y final=false.
El auditor que continúa envía al constructor. El protocolo ordinario no admite un pase a sí mismo.

human_need tiene exactamente: id (string), type (`material` o `no_material`), request (string
que empieza con NECESIDAD DEL HUMANO), checkpoint, guide_prompt, expected_evidence (lista no vacía
de strings), resume_actor (`AUDITOR`). Material: checkpoint={repository,commit,path} y guide_prompt
no vacío. No material: ambos null. Ver procedimientos/NECESIDADES para la autoridad de esos valores.

## Prompt del receptor constituido

```text
ROL=<AUDITOR|CONSTRUCTOR>
WORK_ID=<id>
CARRIL=<carril>
INCOMING_TURN_ID=<turn_id de este sobre>
BOOTSTRAP_REPO=<owner/repo>
BOOTSTRAP_PATH=<path>
BOOTSTRAP_SHA=<commit completo>
WORK_REPO=<owner/repo>
WORK_SHA=<commit completo>
AUDIT_REPO=<owner/repo>
AUDIT_SHA=<commit completo>
ACTOR_LOCAL_PATH=<ruta, sólo si corresponde>

<próxima acción irreducible>
```

La cabecera sirve tanto para current como fresh. No omitir datos suponiendo memoria previa.
El receptor sólo recibe este string, no el sobre exterior. No duplicar conclusiones, valores de
pruebas o historias disponibles en Git. No adelantar el resultado de una mitad de una comparación.
El orquestador no inspecciona la cabecera: comprobar su suficiencia corresponde a emisor y receptor.

Primer constructor: excepción porque aún no tiene BOOTSTRAP ni WORK_SHA. Recibe ROL, WORK_ID,
CARRIL, INCOMING_TURN_ID=1, método, manifiesto, repositorios/fuentes, rutas, entornos, capacidades
y AUDITOR_BOOTSTRAP_REPO/PATH/SHA. No inventar identidades todavía inexistentes.

turn_id es transporte, no contador metodológico. No se guarda en EVENTO ni se deriva contando
commits. Un relevo no lo reinicia. La resolución humana usa el contexto separado de NECESIDADES.
Si faltó el entero de entrada, detectar antes de escribir: no fabricar un sobre con un número supuesto.
