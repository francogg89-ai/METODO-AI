# Transporte local

Host Python estándar + módulo Node dentro del runtime CUA autorizado. Sin API key, servicio
web ni reconstrucción de prompts por el modelo. Claude usa su instalación autenticada.
El módulo de navegador requiere las capacidades CUA de la computadora; no es un navegador
independiente ni instala un conector. No ejecutar desde un entorno que sólo pueda transcribir
los resultados de herramientas. Respetar las capacidades y restricciones del runtime.

## Preparación única por computadora

1. Checkout limpio de METODO-AI en el SHA elegido por la constitución. Python 3.10+ y Node
   en el runtime CUA; Claude Code nativo autenticado. Configurar `claude.executable` si PATH
   resuelve un `.cmd` en lugar de `claude.exe`.
2. Configurar `work_id`, `repositories`, `locator`, `claude.cwd`, herramientas y permisos en
   un JSON fuera de work/audit. La ruta de ejecución debe estar fuera de esos repositorios.
3. En el REPL CUA, importar `transporte/browser.mjs`, `node:fs/promises` y pasar un objeto
   runtime con `newTab(url)` y `getTab(id)`, conectados a las funciones reales del entorno.
   `newTab` retorna una pestaña nueva con `id`, `url()`, `playwright`, `paste` y `clipboard`.
   `getTab` recupera ese ID, sin seleccionar la pestaña activa por intuición. El agente local
   debe comprobar estas firmas con las herramientas disponibles; no inventarlas.
4. El código del REPL llama `await serviceOne(runtime, runPath, fs)` para cada comando pendiente.
   Los argumentos contienen rutas/handles; el texto se lee y escribe dentro de código.
   Atender el mailbox mientras Python espera (proceso de terminal en segundo plano).
   Una llamada procesa como máximo una operación. No borrar claims para forzar un reenvío.

El único ajuste del runtime es conectar esas dos fábricas de pestañas. No cambiar los
algoritmos de copia, comparación o envío por instrucciones generadas por el modelo.
El módulo actual reconoce los controles en español de ChatGPT y los selectores comprobados
en la prueba. Un cambio de interfaz puede requerir actualizarlo y verificarlo localmente.

## Configuración mínima

```json
{
  "work_id": "mi-trabajo",
  "repositories": {"AUDITOR": "owner/audit", "CONSTRUCTOR": "owner/work"},
  "locator": "METODO_AI_INIT_V1|WORK_ID=mi-trabajo|CARRIL=A|CONSTITUTION_REPO=owner/manifiestos|CONSTITUTION_PATH=trabajo/CONSTITUCION_INICIAL.md|CONSTITUTION_SHA=aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
  "browser_timeout_seconds": 900,
  "claude": {
    "executable": "C:/ruta/claude.exe",
    "cwd": "C:/proyectos/work",
    "permission_mode": "default",
    "tools": ["Read", "Glob", "Grep", "Edit", "Write", "Bash", "WebFetch", "WebSearch"],
    "allowed_tools": [],
    "settings_file": "C:/configuracion/permisos.json"
  }
}
```

El SHA de ejemplo no acredita una constitución. `settings_file`, `model` y `allowed_tools`
son opcionales. Sin `model` se conserva el modelo configurado por el usuario. No se admite
bypassPermissions. No usar `--bare` para este circuito: no fue compatible con la sesión OAuth
de la instalación ensayada. No agregar directorios editables auxiliares indiscriminadamente.
Las reglas de herramientas no son un sandbox del sistema operativo. Las pruebas locales y
comandos Git necesitan permisos reales de la instalación, no sólo autorización documental.
Un permiso denegado queda en el JSON original de Claude; no se amplía automáticamente.

## Operación breve del orquestador

Desde el checkout del método:

```text
python -m transporte.local check --config CONFIG.json --run RUTA_RUNTIME
python -m transporte.local init --config CONFIG.json --run RUTA_RUNTIME
python -m transporte.local step --run RUTA_RUNTIME
```

`check` sólo comprueba ejecutable, versión, directorio y origin de work. No inicia agentes,
no comprueba credenciales ni permisos efectivos, y no acredita navegador. `init` congela
la configuración local y no envía. No editar esa copia durante una ejecución.

El primer `step` abre auditor fresh y envía exclusivamente el locator. Cada `step` siguiente
captura la respuesta esperada, llama Session.accept y entrega el siguiente prompt. Repetir
mientras el resultado sea `started` o `delivered`. Atender el mailbox desde CUA durante cada
llamada. Ante `unit`, informar brevemente sin pedir aprobación. Detener ante `human_need`,
`final`, `failed` o `capture_blocked`. Mostrar literalmente la necesidad o el reporte con
la respuesta original íntegra. No convertir un estado técnico en un nuevo gate del trabajo.

```text
python -m transporte.local stop --run RUTA_RUNTIME
python -m transporte.local continue --run RUTA_RUNTIME
python -m transporte.local resolve --run RUTA_RUNTIME --text-file RESOLUCION.txt
python -m transporte.local status --run RUTA_RUNTIME
python -m transporte.local recover --run RUTA_RUNTIME
```

`stop` deja una solicitud aun con el host ocupado; se aplica al siguiente límite de
constructor→auditor. `continue --text-file DIRECTIVA.txt` separa la directiva del sobre.
`resolve` sólo responde una necesidad existente. Esos textos humanos se leen desde archivos.

## Sesiones, recuperación y límites

- Auditor fresh: pestaña nueva vacía, identidad de conversación confirmada tras el primer envío.
  Current: recuperar la conversación registrada; si falta una pestaña, abrir esa misma URL.
  Si se pierde la identidad, detener; nunca sustituir por otra conversación.
- Constructor fresh: UUID nuevo y `--session-id`. Current: `--resume` con el UUID exacto;
  verificar también el `session_id` devuelto. Nunca `--continue` ni sesión más reciente.
  El constructor trabaja en el cwd configurado; una instancia nueva no hereda la conversación.
- UTF-8 binario en disco y stdin; el navegador lee el compositor antes de enviar. La salida
  completa de la CLI se guarda sin interpretar antes de extraer `result`.
- Captura: un intento y hasta dos recapturas del mismo ID; copia ligada al mensaje del asistente,
  sentinel nuevo y espera de hasta 2,5 segundos por intento. Conservar originales y errores.
  El contador persiste: reiniciar el proceso no concede otro presupuesto automático.
- Recibos y snapshot de Session antes/después de cada transacción. Al recuperar una transacción
  interrumpida se reproducen en memoria sólo resultados ya guardados; una mutación pendiente
  nunca se ejecuta de nuevo. Si hubo un envío incierto, detener con su evidencia.
- Un bloqueo de captura anterior a accept deja intacto el turno; `recover` puede completar los
  intentos restantes. Tras agotarlos se necesita diagnóstico explícito; no relanzar el loop.
- Un bloqueo del sistema operativo impide dos hosts simultáneos. Cada operación de navegador
  tiene un claim exclusivo duradero. Una caída entre la acción y el recibo es incertidumbre,
  aunque el mensaje pudiera estar visible: no se infiere permiso de reenvío.
- Los registros técnicos son locales, contienen prompts y respuestas; no publicarlos en Git.
  Los originales de capturas y transacciones tienen identidades únicas. No borrarlos para reiniciar.

Esto recupera transporte con las mismas identidades. **No implementa el relevo coordinado de
orquestador, auditor y constructor frescos**, ni convierte los registros técnicos en autoridad
sobre el trabajo. Ese protocolo sigue delimitado en procedimientos/CONTINUIDAD.md.

## Verificación

La prueba local de referencia completó tres turnos reales y una recuperación sin reenvío.
Esta implementación reutilizable agrega sesiones y diario duradero: sus casos automatizados
no sustituyen comprobar fresh/current de ambos roles en la instalación final. Antes de Y,
verificar esos recorridos y permisos en una carpeta sintética; no hacer una batería repetitiva
sin un riesgo concreto. Ver VALIDACION.md.

Referencias de CLI y permisos: https://code.claude.com/docs/en/cli-reference y
https://code.claude.com/docs/en/permissions. Confirmar compatibilidad con la versión instalada.
