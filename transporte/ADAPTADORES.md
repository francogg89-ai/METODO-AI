# Contrato del adaptador

Un adaptador conecta el núcleo con una interfaz concreta. El host de referencia está en
[LOCAL.md](LOCAL.md): Claude Code local y ChatGPT mediante un runtime CUA autorizado.
Las pruebas automatizadas usan dobles; la conexión final se verifica en la computadora del usuario.

| Operación | Propiedad exigida |
|---|---|
| capture | Devolver Capture con texto, identidad de respuesta e indicador complete; la misma identidad en recapturas |
| open_fresh | Crear instancia identificable nueva y devolver handle opaco |
| is_current | Comprobar que el handle puede recuperarse como la misma instancia |
| prepare | Limpiar sólo la entrada pendiente e insertar el valor recibido; no generar texto con un modelo |
| readback | Devolver el string efectivamente preparado, o None si la interfaz carece de lectura de vuelta |
| send | Devolver DELIVERED, NOT_SENT o UNKNOWN; NOT_SENT exige evidencia de que no empezó ejecución y es seguro repetir |
| repair | Opcional; reemisión exclusivamente de formato, sin nuevo trabajo material, con constancia comprobable |

prepare devuelve el valor efectivamente pasado a la primitiva de inserción y un indicador de
anomalía. Adjuntos, uploads, truncamiento o transformaciones son anomalías; nunca enviar así.
El valor preparado se compara siempre con el original. Si readback no existe, sólo se admite
continuar sin anomalías observadas; eso no demuestra igualdad en el receptor y se informa como límite.
No crear file://, adjuntos ni uploads para demostrar igualdad. Un doble chequeo del mismo string
antes de insertarlo no sustituye la lectura de vuelta de la interfaz.

El adaptador no debe usar una llamada de generación para reconstruir los parámetros de prepare.
En un entorno de herramientas puede transferir la variable original dentro del mismo proceso de
código. Si sólo puede volver a transcribirla mediante el modelo, la integración no cumple.

repair no se habilita por una promesa textual del agente. El runtime debe poder impedir o
comprobar ejecución material nueva. Si no ofrece esa propiedad, devolver None y detener con
el original íntegro. Capturas parciales llevan complete=false. Una excepción de send es UNKNOWN,
no NOT_SENT. El núcleo nunca deduce por timeout que se puede reenviar.

Antes de usar en vivo comprobar: Unicode, rutas Windows, comillas, saltos, texto largo, marcador
de fin de respuesta, conversación realmente fresh, current recuperado y resultado ambiguo de send.
La autorización del trabajo no demuestra esas propiedades técnicas.
