-- Solo para instalaciones anteriores que gestionen la migración manualmente.
-- La aplicación agrega automáticamente estas columnas faltantes al arrancar.
-- Ejecutar cada ALTER únicamente si la columna todavía no existe.
ALTER TABLE partidas ADD COLUMN limite INT NOT NULL DEFAULT 25;
ALTER TABLE partidas ADD COLUMN ultima_carta JSON NULL;
ALTER TABLE partidas ADD COLUMN secuencia INT NOT NULL DEFAULT 0;
