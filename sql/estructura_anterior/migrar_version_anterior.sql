-- Ejecuta este script SOLO si ya usabas la versión anterior del registro RFID.
-- Haz primero una copia de seguridad desde phpMyAdmin > Exportar.
USE loteria_mazahua;

ALTER TABLE tarjetas_rfid
  ADD COLUMN audio_mazahua_url VARCHAR(255) NULL,
  ADD COLUMN audio_espanol_url VARCHAR(255) NULL;

-- La versión anterior tenía un solo campo audio_url. Se conserva como respaldo
-- y su ruta se copia al campo de audio mazahua; después puedes editar cada tarjeta
-- desde la interfaz y subir el audio español que le falta.
UPDATE tarjetas_rfid
SET audio_mazahua_url = audio_url
WHERE audio_mazahua_url IS NULL AND audio_url IS NOT NULL;
