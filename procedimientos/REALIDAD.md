# Entornos y concurrencia

Git prueba historia, no el estado actual de una API, base de datos, permiso o infraestructura.
Si la decisión depende de ese estado, comprobar el recurso al usarlo. Ante discrepancia detener
la operación dependiente, investigar y reconciliar. No crear un estado documental llamado drift.

PROJECT.md delimita recursos y superficies compartidas. Antes de mutar, comparar el corte
constitutivo con la referencia actual obtenida del remoto e intersectar los paths cambiados con
la superficie propia. Sin intersección hay compatibilidad de paths; eso no demuestra aislamiento
de un recurso externo. Si hay solapamiento sin resolver, el constructor preserva y entrega al
auditor, que determina resolución técnica o necesidad humana. No actualizar el corte constitutivo.

Antes de una operación material sensible, comprobar proporcionalmente impacto de otros trabajos.
Código se integra con Git; un recurso compartido puede exigir serialización, aislamiento o espera.
La autonomía dentro de permisos no elimina esas comprobaciones. No mantener una lista manual de
trabajos activos cuando las fuentes permiten resolver la pregunta.

Notas y resultados intermedios pueden vivir fuera de Git. Si perderlos impide continuar o auditar,
preservar lo indispensable en su superficie autoritativa. Al cierre identificar al humano material
local prescindible y cualquier secreto o configuración que requiera conservarse o revocarse.
