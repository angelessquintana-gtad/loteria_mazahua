-- Ejecutar en la misma base después de crear_partidas.sql.
-- La aplicación también crea estas tablas nuevas al arrancar.
CREATE TABLE IF NOT EXISTS tableros (
 id INT AUTO_INCREMENT PRIMARY KEY,
 participante_id INT NOT NULL UNIQUE,
 cartas JSON NOT NULL,
 marcas JSON NOT NULL,
 FOREIGN KEY (participante_id) REFERENCES participantes(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
CREATE TABLE IF NOT EXISTS anuncios_partida (
 id INT AUTO_INCREMENT PRIMARY KEY,
 partida_id INT NOT NULL,
 tarjeta_id INT NOT NULL,
 contenido JSON NOT NULL,
 UNIQUE KEY uq_anuncio (partida_id, tarjeta_id),
 KEY ix_anuncios_partida_partida_id (partida_id),
 FOREIGN KEY (partida_id) REFERENCES partidas(id),
 FOREIGN KEY (tarjeta_id) REFERENCES tarjetas_rfid(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
CREATE TABLE IF NOT EXISTS resultados_partida (
 partida_id INT PRIMARY KEY,
 participante_id INT NOT NULL,
 fecha DATETIME NOT NULL,
 FOREIGN KEY (partida_id) REFERENCES partidas(id),
 FOREIGN KEY (participante_id) REFERENCES participantes(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
