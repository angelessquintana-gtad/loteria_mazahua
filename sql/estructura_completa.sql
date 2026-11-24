-- ============================================================================
-- Lotería Mazahua · ESTRUCTURA DE LA BASE DE DATOS (sin registros) — MariaDB / MySQL 8
-- ----------------------------------------------------------------------------
-- No es obligatorio ejecutarlo: el backend crea las tablas al iniciar (AUTO_MIGRATE=true)
-- y convierte automáticamente la estructura anterior (migracion.py).
-- Las tarjetas están en UNA sola tabla: nombres, descripción, imagen y audios.
-- Es seguro: CREATE TABLE IF NOT EXISTS, no borra tablas ni registros.
-- Para la estructura CON tus registros usa sql/base_de_datos_mazahua.sql.
-- ============================================================================
CREATE DATABASE IF NOT EXISTS loteria_mazahua CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE loteria_mazahua;

-- Tabla tarjetas
CREATE TABLE IF NOT EXISTS tarjetas (
	id INTEGER NOT NULL AUTO_INCREMENT, 
	numero INTEGER, 
	nombre_espanol VARCHAR(150) NOT NULL, 
	nombre_mazahua VARCHAR(150) NOT NULL, 
	descripcion TEXT, 
	imagen VARCHAR(255), 
	audio_mazahua VARCHAR(255), 
	audio_espanol VARCHAR(255), 
	uid_rfid VARCHAR(40), 
	PRIMARY KEY (id), 
	UNIQUE (numero), 
	UNIQUE (uid_rfid)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Tabla usuarios
CREATE TABLE IF NOT EXISTS usuarios (
	id INTEGER NOT NULL AUTO_INCREMENT, 
	nombre VARCHAR(100) NOT NULL, 
	correo VARCHAR(254) NOT NULL, 
	password_hash VARCHAR(255) NOT NULL, 
	fecha_registro DATETIME NOT NULL, 
	PRIMARY KEY (id), 
	UNIQUE (correo)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Tabla partidas
CREATE TABLE IF NOT EXISTS partidas (
	id INTEGER NOT NULL AUTO_INCREMENT, 
	codigo VARCHAR(6) NOT NULL, 
	nombre VARCHAR(100) NOT NULL, 
	usuario_id INTEGER, 
	limite INTEGER NOT NULL DEFAULT '25', 
	estado VARCHAR(16) NOT NULL, 
	fecha_creacion DATETIME NOT NULL, 
	iniciada DATETIME, 
	finalizada DATETIME, 
	ultima_tarjeta_id INTEGER, 
	secuencia INTEGER NOT NULL DEFAULT '0', 
	ultima_actividad_docente DATETIME, 
	cierre_motivo VARCHAR(30), 
	PRIMARY KEY (id), 
	UNIQUE (codigo), 
	FOREIGN KEY(usuario_id) REFERENCES usuarios (id) ON DELETE SET NULL, 
	FOREIGN KEY(ultima_tarjeta_id) REFERENCES tarjetas (id) ON DELETE SET NULL,
	KEY ix_partidas_usuario_id (usuario_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Tabla recuperaciones_password
CREATE TABLE IF NOT EXISTS recuperaciones_password (
	token_hash VARCHAR(64) NOT NULL, 
	usuario_id INTEGER NOT NULL, 
	creada DATETIME NOT NULL, 
	vence DATETIME NOT NULL, 
	PRIMARY KEY (token_hash), 
	FOREIGN KEY(usuario_id) REFERENCES usuarios (id) ON DELETE CASCADE,
	KEY ix_recuperaciones_password_usuario_id (usuario_id),
	KEY ix_recuperaciones_password_vence (vence)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Tabla sesiones
CREATE TABLE IF NOT EXISTS sesiones (
	jti VARCHAR(64) NOT NULL, 
	usuario_id INTEGER NOT NULL, 
	vence DATETIME NOT NULL, 
	PRIMARY KEY (jti), 
	FOREIGN KEY(usuario_id) REFERENCES usuarios (id) ON DELETE CASCADE,
	KEY ix_sesiones_usuario_id (usuario_id),
	KEY ix_sesiones_vence (vence)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Tabla anuncios
CREATE TABLE IF NOT EXISTS anuncios (
	id INTEGER NOT NULL AUTO_INCREMENT, 
	partida_id INTEGER NOT NULL, 
	tarjeta_id INTEGER NOT NULL, 
	fecha DATETIME NOT NULL, 
	PRIMARY KEY (id), 
	CONSTRAINT ux_anuncio_partida_tarjeta UNIQUE (partida_id, tarjeta_id), 
	FOREIGN KEY(partida_id) REFERENCES partidas (id) ON DELETE CASCADE, 
	FOREIGN KEY(tarjeta_id) REFERENCES tarjetas (id),
	KEY ix_anuncios_partida_id (partida_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Tabla participantes
CREATE TABLE IF NOT EXISTS participantes (
	id INTEGER NOT NULL AUTO_INCREMENT, 
	partida_id INTEGER NOT NULL, 
	nombre VARCHAR(60) NOT NULL, 
	dispositivo VARCHAR(36) NOT NULL, 
	fecha_ingreso DATETIME NOT NULL, 
	gano BOOL NOT NULL DEFAULT '0', 
	avatar VARCHAR(60), 
	PRIMARY KEY (id), 
	CONSTRAINT ux_participante_dispositivo UNIQUE (partida_id, dispositivo), 
	FOREIGN KEY(partida_id) REFERENCES partidas (id) ON DELETE CASCADE,
	KEY ix_participantes_partida_id (partida_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Tabla tableros
CREATE TABLE IF NOT EXISTS tableros (
	id INTEGER NOT NULL AUTO_INCREMENT, 
	participante_id INTEGER NOT NULL, 
	creado DATETIME NOT NULL, 
	PRIMARY KEY (id), 
	UNIQUE (participante_id), 
	FOREIGN KEY(participante_id) REFERENCES participantes (id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Tabla tablero_tarjetas
CREATE TABLE IF NOT EXISTS tablero_tarjetas (
	tablero_id INTEGER NOT NULL, 
	posicion INTEGER NOT NULL, 
	tarjeta_id INTEGER NOT NULL, 
	marcada BOOL NOT NULL DEFAULT '0', 
	PRIMARY KEY (tablero_id, posicion), 
	FOREIGN KEY(tablero_id) REFERENCES tableros (id) ON DELETE CASCADE, 
	FOREIGN KEY(tarjeta_id) REFERENCES tarjetas (id),
	KEY ix_tablero_tarjetas_tarjeta_id (tarjeta_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

