# Necesidad humana

Existe cuando continuar requiere intervención fuera del perímetro delegado vigente.
El constructor preserva, registra y entrega; el auditor comprueba si es real. Sólo el auditor
emite human_need. No solicitar otra vez una capacidad ya vigente o una decisión ya preservada.

Token durable: `NECESIDAD DEL HUMANO`. El request del sobre empieza con ese token y expresa la
acción concreta. La respuesta de transporte sigue siendo sólo su bloque JSON.

Una decisión no material usa type=no_material, checkpoint=null y guide_prompt=null.
Una necesidad material requiere una acción externa, acceso o verificación fuera del circuito.
El constructor preserva `<unidad>/CHECKPOINT_HUMANO.md`, identificado por repo, path y commit.
Empieza con un prompt para un auxiliar fresco y contiene sólo necesidad, referencias, acción,
límites y evidencia de retorno. No contiene secretos. El auditor comprueba su suficiencia.
El auxiliar no se convierte en actor principal. El checkpoint no sirve para un relevo ordinario.

El sobre detenido tiene next_actor/next_instance/next_prompt=null y final=false. El orquestador
conserva ese sobre y muestra la necesidad. Al recibir resolución, entrega al mismo auditor current:

```text
RESUME_CONTEXT:
INCOMING_TURN_ID=<turn_id del sobre detenido>

HUMAN_RESOLUTION_LITERAL:
<texto humano exacto>
```

El orquestador no incrementa ese número ni interpreta la resolución. El auditor la preserva en
audit: qué se resolvió, sobre qué identidad, alcance y exclusiones; emite el sucesor del turno.
Si la resolución es una credencial, preservar sólo la referencia segura y la capacidad habilitada.
Si se perdió current, detener y reportar. No sustituirlo por fresh bajo esta operación.

Una necesidad prevista en el plan se reevalúa al llegar a ella; haberla previsto no autoriza su
ejecución. Guardar para reanudar con otro auditor se tratará en CONTINUIDAD, no mediante un atajo.
