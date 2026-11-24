# Evidencias en video (YouTube)

Los enlaces se muestran en la página **/videos** como miniaturas; al hacer clic se abre el video en YouTube. Para agregarlos:

1. **Administración → Videos de YouTube**: pegar el enlace en cada video y pulsar **Guardar videos**; o bien
2. editar `videos_youtube.json` en la carpeta principal y escribir el enlace en `"url"`.

Se aceptan enlaces `https://www.youtube.com/watch?v=...`, `https://youtu.be/...` y `https://youtube.com/shorts/...`. Si el video se sube como **No listado** en YouTube, se puede ver con el enlace aunque no aparezca en búsquedas.

## Guion sugerido (entregable 6 del documento)

| Video | Qué mostrar | Enlace |
|---|---|---|
| 1. Backend con FastAPI y Swagger UI | Ventana del servidor iniciado; `/docs`; probar `GET /api/vocabulario?buscar=gato`; registrar, editar y eliminar una tarjeta (`POST`, `PUT`, `DELETE /api/tarjetas`); tabla `tarjetas_rfid` en phpMyAdmin. | Pendiente |
| 2. Frontend con Astro | Inicio, Vocabulario con búsqueda, Simulador, Videos; vista en celular; carpeta `frontend/src/pages`. | Pendiente |
| 3. Consumo de la API | Herramientas de desarrollador (F12) → Red: las páginas llaman a `/api/vocabulario` y `/api/videos`; cambiar un dato en Administración y ver el cambio en Vocabulario. | Pendiente |
| 4. Multimedia y dinámica | Subir foto y audios; reproducir pronunciaciones; partida en el simulador hasta “¡Lotería!”; opcionalmente lectura con el ESP32. | Pendiente |

Los títulos y descripciones se pueden cambiar libremente. No se han inventado enlaces: los videos aparecen como “Enlace pendiente” hasta que se agreguen los reales.
