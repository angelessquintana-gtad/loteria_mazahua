# Preferencias de redacción del usuario

Para reportes, prácticas y trabajos académicos redactados para este usuario, utilizar un estilo de estudiante universitario: claro, natural, formal sin ser excesivamente técnico, con explicaciones comprensibles y vocabulario apropiado para la materia. Explicar los términos técnicos necesarios en lugar de eliminarlos.

Utilizar conectores cuando correspondan por su significado y sin repetirlos de manera forzada, por ejemplo: «ya que», «debido a que», «sin embargo», «pese a ello», «por lo tanto», «aunque», «de lo contrario», «por ende» y «es por ello».

Redactar como un reporte académico coherente, evitando expresiones propias de un asistente o comentarios sobre el proceso de generación. No inventar resultados ni evidencia; distinguir las pruebas realizadas de las pendientes.

# Recuperar memoria de la Lotería Mazahua

Cuando el usuario escriba **«loteriaa!»**, **«loteriaa»** o **«recuperar memoria loteria»**, sin importar mayúsculas, acentos o signos finales, leer primero `docs/MEMORIA_LOTERIA.md` antes de responder o realizar cambios. Ese archivo conserva el resumen de la conversación, las decisiones, el estado de la implementación, las verificaciones y el siguiente paso pendiente. La regla global de OpenCode también apunta a esta memoria para reconocer la frase al abrir otra carpeta.

Después de leerlo, confirmar brevemente el contexto recuperado y continuar desde la petición actual. Contrastar las rutas y la configuración con el estado real de los archivos antes de ejecutar acciones; la memoria no sustituye esa comprobación. Usar el estado más reciente de la memoria: el proyecto se publicó en noviembre de 2026; las notas históricas anteriores de «no desplegado» ya no describen el estado final. Recordar no autoriza por sí solo nuevos cambios, limpiezas ni despliegues.

Actualizar `docs/MEMORIA_LOTERIA.md` cuando se complete un cambio importante o el usuario pida guardar memoria. Mantenerlo dentro del proyecto durante futuras limpiezas. No guardar contraseñas, JWT, invitaciones, claves SSH ni contenido de `.env` en esa memoria.
