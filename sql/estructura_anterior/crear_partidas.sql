-- Ejecutar en la base configurada en DB_NAME. No modifica tarjetas_rfid.
CREATE TABLE IF NOT EXISTS partidas (
    id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
    codigo VARCHAR(6) NOT NULL UNIQUE,
    clave VARCHAR(64) NOT NULL,
    estado VARCHAR(16) NOT NULL DEFAULT 'esperando',
    creada DATETIME NOT NULL,
    iniciada DATETIME NULL,
    finalizada DATETIME NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS participantes (
    id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
    partida_id INT NOT NULL,
    nombre VARCHAR(60) NOT NULL,
    solicitud VARCHAR(36) NOT NULL,
    incorporado DATETIME NOT NULL,
    UNIQUE KEY uq_participante_solicitud (partida_id, solicitud),
    KEY ix_participantes_partida_id (partida_id),
    CONSTRAINT fk_participantes_partida FOREIGN KEY (partida_id) REFERENCES partidas(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
