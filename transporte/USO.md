# Uso del núcleo

Python 3.10 o posterior, sólo biblioteca estándar. Ejecutar desde la raíz del repositorio.
No instalar dependencias, servicios, brokers ni bases de datos.

## Validar una captura

```text
python -m transporte validate --response respuesta.txt --work-id ejemplo --actor AUDITOR --repository usuario/audit --last-turn 0 --output-dir .runtime/comprobacion-1
```

El directorio debe ser nuevo. Siempre conserva respuesta-original.txt byte por byte, incluso si
el JSON o UTF-8 fallan. Si es válido, escribe sobre.json y next_prompt.txt sin normalizar el string.
reporte.json identifica resultado, turno y archivos. Código de salida 0=validado, 2=fallo.
Validar no envía ni consume un turno. Para mostrar una falla, presentar reporte y original completo.
El original no se regenera a partir de sobre.json. No subir capturas de trabajos a este repositorio.

## Materializar arranque

Completar una configuración como plantillas/ARRANQUE_ORQUESTADOR.md con identidades reales:

```text
python -m transporte init --config inicio.json --output arranque.txt
```

No sobrescribe archivos. Verifica forma, no consulta Git ni prueba autorización humana.

## Integrar interfaces

`Session` recibe work_id y repositorios de AUDITOR/CONSTRUCTOR. `start(adapter, locator)` abre
el auditor fresco; `accept(adapter, Capture(...), source_actor=...)` recibe cada respuesta
completa de la instancia activa. Usar métodos del objeto en un único flujo secuencial: no es
thread-safe y no admite dos llamadas accept en paralelo. Los strings viajan como valores Python.

Implementar Adapter según ADAPTADORES.md. Capturar la respuesta antes de invocar accept; si no
hay confirmación de completitud usar complete=false. El adaptador confirma identidades, no un modelo.
`request_stop()` marca la pausa; `continue_()` entrega el pendiente exacto. `continue_(directive=...)`
encapsula por separado la directiva humana para el auditor current. `resolve_human()` conserva
el turno de la necesidad y envía su resolución al mismo auditor. No llamar accept tras un fallo
ni recrear una Session para repetir un envío incierto.

El resultado failed contiene el original completo y todas las capturas/reemisiones en memoria.
El host debe mostrarlo y conservarlo fuera de Git antes de descartar la sesión. La CLI implementa
preservación local para validaciones de archivos; la Session no escribe automáticamente a disco.
No hay reanudación de proceso ni guardado durable del loop en esta entrega.

## Integración no demostrada

Pasar next_prompt a otra llamada mediante una transcripción del modelo no cumple el contrato.
El host debe conectar prepare con la variable recibida por código. Sin adaptadores reales
verificados, este paquete es un núcleo probado y una especificación, no un loop operativo.

## Interfaces reales

Para la ejecución con ChatGPT web y Claude Code ver [LOCAL.md](LOCAL.md).
El CLI de este documento conserva su función de validación offline.
