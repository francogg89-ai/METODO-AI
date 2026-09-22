# Arranque del orquestador

El comando `python -m transporte init` materializa este contenido funcional desde datos JSON
verificados; no se sustituye manualmente un SHA. Su archivo de salida contiene:

- METHOD_REPO y METHOD_SHA: cargar transporte/ORQUESTADOR.md y transporte/ADAPTADORES.md.
- Runtimes aprobados y ruta local del constructor.
- Abrir auditor realmente nuevo; entregar únicamente el locator METODO_AI_INIT_V1.
- Esperar respuesta completa, validar primer sobre actor=AUDITOR y turn_id=1.
- Transportar mediante el núcleo; no regenerar next_prompt, crear bootstraps ni escribir work/audit.
- Aplicar recuperación limitada, pausa, necesidad humana y cierre conforme al método exacto.

Configuración de entrada del materializador (campos exactos, sin placeholders en un uso real):

```json
{
  "work_id": "ejemplo",
  "carril": "X",
  "method_repo": "francogg89-ai/METODO-AI",
  "method_sha": "<commit completo>",
  "constitution_repo": "francogg89-ai/MANIFIESTOS-TRABAJOS-AI",
  "constitution_path": "manifiestos/ejemplo/CONSTITUCION_INICIAL.md",
  "constitution_sha": "<commit completo>",
  "auditor_runtime": "ChatGPT web",
  "constructor_runtime": "Claude Code local",
  "constructor_local_path": "C:/raiz/work"
}
```

Este ejemplo no constituye un trabajo ni contiene referencias ejecutables. El materializador
valida forma, no existencia en Git ni aprobación humana: comprobar ambas antes de usar su salida.
