# Validación de la primera entrega

Ejecutado en Python local:

```text
python -m unittest discover -s tests -v
Ran 41 tests
OK
```

Los casos están en tests/test_core.py. Se usan respuestas sintéticas y un adaptador simulado;
no se contactaron agentes, repositorios de trabajo ni recursos externos durante estas pruebas.

| Propiedad | Casos comprobados |
|---|---|
| Forma y autoridad | Prosa exterior, múltiples sobres, claves repetidas, campos extra/ausentes, tipos incorrectos, turno incorrecto, repositorio/rol incorrectos, constructor intentando cerrar |
| Literalidad | Unicode, emoji, comillas, barras, CRLF/LF y texto que parece código conservados; original y prompt escritos sin conversión de saltos |
| Recuperación | Dos inserciones fallidas seguidas de éxito; agotamiento en tres intentos sin envío ni avance; recaptura de la misma respuesta y rechazo de otra |
| Integridad | Alteración en preparación o readback, anomalías sin readback; ausencia de readback declarada como limitación |
| Envío incierto | UNKNOWN y excepción al enviar no reintentan; NOT_SENT sí reintenta con límite |
| Instancias | Fresh distinto, promoción sólo tras envío confirmado, current perdido sin sustitución y ciclo con ambos roles frescos |
| Reparación de forma | JSON sin bloque reemitido conservando valores; cambio de payload o falta de garantía material rechazados; JSON roto no reconstruido |
| Control | Pausa en constructor→auditor, continuación literal, directiva separada, resolución humana al mismo auditor sin consumir otro turno de entrada, cierre sin entrega |
| Evidencia | Reporte conserva respuesta original y origen real; CLI conserva incluso bytes UTF-8 inválidos |
| Arranque | Locator validado/materializado, rechazo de placeholders de SHA, rutas ascendentes e inyección de campos |
| Límite de alcance | El comando de guardado no afirma soporte y solicita pausa ordinaria |

Se revisaron enlaces locales y ausencia de referencias operativas a otros métodos.
El presupuesto de entrada documental es aproximadamente 1.300 palabras por constructor/auditor
(núcleo + rol + salida), más derivación y materia pertinente. No es una medición de tokens ni de
costo de ejecución. No obliga a releer contenido inmutable en cada turno de una misma instancia.

## Límites concretos

- No se probó ChatGPT web, Claude Code, Luna ni automatización de navegador/terminal.
- No se implementaron adaptadores reales, persistencia/reinicio del proceso, publicación de
  paquetes de continuidad o exclusión entre dos orquestadores.
- El canal de reparación restringida depende del adaptador. Si no puede acreditar ausencia de
  nuevo trabajo material, se detiene con el original. No se corrige JSON roto por inferencia.
- Validar forma de un SHA no demuestra existencia del commit, veredicto ni permisos.
- La interfaz sin readback no permite demostrar igualdad en destino, aunque no observe anomalías.

## Próxima comprobación material

Conectar adaptadores en el entorno aprobado y demostrar transferencia directa desde la variable
original, identidad de instancias, fin de respuesta y comportamiento ante envíos inciertos.
Después implementar el alcance de procedimientos/CONTINUIDAD.md. Esta validación no autoriza
usar el núcleo como si esos pasos ya estuvieran completados.

## Transporte local reutilizable

Agregados tests de diario de operaciones: entrega confirmada no repetida, mutación interrumpida
no repetida, divergencia de reproducción, persistencia de Session, identidad CLI, bytes UTF-8
y cierre sin envío. Tests Node del puente: fresh, claim de envío persistido y current incorrecto.

Ejecutar `python -m unittest discover -s tests -v` y `node --test tests/test_browser.mjs`.
La prueba real previa completó auditor→constructor→auditor con cierre recuperado. La versión
generalizada requiere verificación local de fresh/current, señales UI y permisos; no se afirma
que los tests simulados hayan ejecutado esos escenarios reales.
