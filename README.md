# METODO-AI

Trabajo asistido por IA con constructor, auditor y transporte mecánico.
Git conserva materia, evidencia y decisiones; las conversaciones pueden reemplazarse.

## Entrada por función

| Función | Leer al entrar | Consultar sólo si corresponde |
|---|---|---|
| Constructor | [Núcleo](NUCLEO.md), [rol](roles/CONSTRUCTOR.md), [salida](transporte/SALIDA.md) | [Derivación](procedimientos/DERIVACION.md) al reconstruir; evidencia, relevos o necesidades según la acción |
| Auditor | [Núcleo](NUCLEO.md), [rol](roles/AUDITOR.md), [salida](transporte/SALIDA.md) | [Derivación](procedimientos/DERIVACION.md) al reconstruir; evidencia, relevos o necesidades según la acción |
| Orquestador | [Reglas](transporte/ORQUESTADOR.md), [adaptadores](transporte/ADAPTADORES.md) | [Uso del núcleo](transporte/USO.md) para conectar las funciones mecánicas |
| Preparación de un trabajo | [Constitución](CONSTITUIR.md) | Plantillas citadas allí |

No cargar todo el repositorio en cada turno. Una instancia que ya leyó una instrucción en el
mismo commit puede reutilizarla; esto no evita reconstruir el corte ni verificar recursos reales.
Los roles consultan directamente los documentos enlazados. Este README es un índice, no otra regla.

## Alcance de esta entrega

El núcleo Python, sin dependencias externas, valida sobres, conserva respuestas originales,
prepara texto, verifica integridad, limita reintentos seguros y produce reportes de fallas.
Incluye un [host local reutilizable](transporte/LOCAL.md) con adaptadores para Claude Code y
ChatGPT mediante el runtime CUA autorizado. Rutas, identidades y permisos son configurables;
los recibos y las capturas se conservan en disco para evitar reenvíos al recuperar una ejecución.
La integración concreta se comprueba en la computadora que ejecuta el circuito. Luna puede
operar las interfaces, sin regenerar los textos que ya recibió el código.

```text
python -m unittest discover -s tests -v
python -m transporte --help
```

[VALIDACION.md](VALIDACION.md) identifica las comprobaciones y sus límites.

## Organización

Este repositorio gobierna el método, sus plantillas y el transporte `metodo-ai-hop/v1`.
[MANIFIESTOS-TRABAJOS-AI](https://github.com/francogg89-ai/MANIFIESTOS-TRABAJOS-AI)
conserva documentos aprobados de trabajos nuevos. Work y audit son repositorios independientes.
Las ejecuciones fijan un commit exacto de METODO-AI: una actualización no se adopta sola.

CONOCIMIENTO-AI y CONTINUIDAD-AI son destinos previstos para conocimiento y reanudaciones.
La publicación automática de aprendizajes y el guardado para renovar los tres agentes no
están implementados en esta entrega. [Continuidad](procedimientos/CONTINUIDAD.md) delimita
ese trabajo pendiente; no habilita ejecutar un protocolo incompleto.
