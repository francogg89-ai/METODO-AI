# Derivación desde un corte

El corte contiene repositorio y commit exacto de work y de audit. No buscar por contenido,
mensajes de commit o listados crecientes para reconstruir la próxima acción.

1. Resolver la identidad work del corte: última entrega material relevante.
2. `git show --format= --name-only <WORK_SHA>`: unidad tocada, o raíz antes de las unidades.
3. La misma operación sobre AUDIT_SHA: paths de esa intervención auditora.
4. Leer esos paths en AUDIT_SHA: próxima acción, necesidad humana y PERIMETRO_ULTIMA_MODIFICACION.
5. Consultar siempre `AUDIT_SHA:auditorias/<WORK_SHA>.md`. Existe: entrega auditada; no existe:
   entrega pendiente. Su existencia no equivale a aprobación: leer su veredicto.
6. Componer el perímetro desde BOOTSTRAP y la cadena mínima de deltas descrita abajo.

Cada intervención auditora declara PERIMETRO_ULTIMA_MODIFICACION:
- `ESTA_INTERVENCION`: aquí cambió; declarar actor, entorno, capacidad, alcance resultante de esa
  capacidad, clase de cambio y referencia a la modificación anterior.
- `CONSTITUCION`: no hubo modificaciones; usar capacidades del BOOTSTRAP de work.
- Commit exacto de la intervención que modificó el perímetro por última vez: seguir esa arista.

Para cada capacidad prevalece el delta más reciente; una revocación deja alcance vacío.
No guardar el perímetro compuesto. El costo crece con los cambios de capacidad, no con todas
las entregas. Detectar ciclos, referencias ausentes o incompatibles; no inventar continuidad.

Preguntas históricas: `git log -n 2 <corte> -- <unidad>/EVENTO.md` y leer la versión previa;
`git diff <anterior> <actual> -- <unidad>/` para el delta; la auditoría histórica se localiza
por `auditorias/<SHA>.md`. No hay convención obligatoria de mensajes de commit.

Si faltan los invariantes que permiten estas operaciones, declarar la insuficiencia. No construir
un índice paralelo ni suponer que un prompt o una memoria sustituyen a Git.
