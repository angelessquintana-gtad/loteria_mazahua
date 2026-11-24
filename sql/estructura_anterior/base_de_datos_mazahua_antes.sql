-- ============================================================================
-- Lotería Mazahua · BASE DE DATOS COMPLETA (estructura + registros)
-- ----------------------------------------------------------------------------
-- Generada a partir de base_de_datos_mazahua.sql (respaldo del 27/10/2026):
--   * Se conservan las tarjetas reales: "Mixi" (gato, UID F9 DB 91 10) y
--     "gaoo" (gallo, UID A9 DD 25 10), así como el historial de partidas.
--   * Se quitaron las 52 cartas de prueba "Sin contenido mazahua (prueba)".
--   * Se agregaron las palabras del material de la carpeta catalogo/ con su
--     imagen y su audio en mazahua (55 tarjetas en total), con UID "DEMO 00xx".
--     Al tener la tarjeta RFID física, cambia su UID en Administración → Editar.
--   * Cada tarjeta tiene descripción por defecto.
--
-- CÓMO IMPORTAR (phpMyAdmin): Importar → elegir este archivo → Continuar.
-- ATENCIÓN: reemplaza las tablas de la base loteria_mazahua. Si tu base actual
-- tiene datos que quieras conservar, exporta primero un respaldo.
-- Las cuentas de docentes no vienen aquí: créalas con 3_CREAR_ADMINISTRADOR.bat.
-- ============================================================================
CREATE DATABASE IF NOT EXISTS loteria_mazahua CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE loteria_mazahua;


/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;
DROP TABLE IF EXISTS `anuncios_partida`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `anuncios_partida` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `partida_id` int(11) NOT NULL,
  `tarjeta_id` int(11) NOT NULL,
  `contenido` longtext CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL CHECK (json_valid(`contenido`)),
  PRIMARY KEY (`id`),
  UNIQUE KEY `partida_id` (`partida_id`,`tarjeta_id`),
  KEY `tarjeta_id` (`tarjeta_id`),
  KEY `ix_anuncios_partida_partida_id` (`partida_id`),
  CONSTRAINT `anuncios_partida_ibfk_1` FOREIGN KEY (`partida_id`) REFERENCES `partidas` (`id`),
  CONSTRAINT `anuncios_partida_ibfk_2` FOREIGN KEY (`tarjeta_id`) REFERENCES `tarjetas_rfid` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=93 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

LOCK TABLES `anuncios_partida` WRITE;
/*!40000 ALTER TABLE `anuncios_partida` DISABLE KEYS */;
INSERT INTO `anuncios_partida` VALUES
(33,12,5,'{\"id\": 5, \"uid\": \"F9 DB 91 10\", \"palabra_mazahua\": \"Mixi\", \"traduccion_espanol\": \"gato\", \"categoria\": null, \"imagen_url\": \"/uploads/imagenes/640a6c4a87014614a69dfe83b3aa64c9.jpg\", \"audio_mazahua_url\": \"/uploads/audios/7af0d94bdc3f42fcb5d8d86f91872972.mp3\", \"audio_espanol_url\": \"/uploads/audios/f59c8f1b2b6343b9993516a14e17ed34.mp3\", \"created_at\": \"2026-10-23T11:36:24\"}'),
(34,12,6,'{\"id\": 6, \"uid\": \"A9 DD 25 10\", \"palabra_mazahua\": \"gaoo\", \"traduccion_espanol\": \"gallo\", \"categoria\": null, \"imagen_url\": \"/uploads/imagenes/901207ce2747487599fbfcfaca76160c.png\", \"audio_mazahua_url\": \"/uploads/audios/e7071e3500014e5aaae9dcde3bbb5cab.mp3\", \"audio_espanol_url\": \"/uploads/audios/388ce86366e2414ca726ecb89dcca02b.mp3\", \"created_at\": \"2026-10-23T11:38:59\"}'),
(87,21,5,'{\"id\": 5, \"uid\": \"F9 DB 91 10\", \"palabra_mazahua\": \"Mixi\", \"traduccion_espanol\": \"gato\", \"categoria\": null, \"imagen_url\": \"/uploads/imagenes/640a6c4a87014614a69dfe83b3aa64c9.jpg\", \"audio_mazahua_url\": \"/uploads/audios/7af0d94bdc3f42fcb5d8d86f91872972.mp3\", \"audio_espanol_url\": \"/uploads/audios/f59c8f1b2b6343b9993516a14e17ed34.mp3\", \"created_at\": \"2026-10-23T11:36:24\"}'),
(88,21,6,'{\"id\": 6, \"uid\": \"A9 DD 25 10\", \"palabra_mazahua\": \"gaoo\", \"traduccion_espanol\": \"gallo\", \"categoria\": null, \"imagen_url\": \"/uploads/imagenes/901207ce2747487599fbfcfaca76160c.png\", \"audio_mazahua_url\": \"/uploads/audios/e7071e3500014e5aaae9dcde3bbb5cab.mp3\", \"audio_espanol_url\": \"/uploads/audios/388ce86366e2414ca726ecb89dcca02b.mp3\", \"created_at\": \"2026-10-23T11:38:59\"}');
/*!40000 ALTER TABLE `anuncios_partida` ENABLE KEYS */;
UNLOCK TABLES;
DROP TABLE IF EXISTS `catalogo_asignaciones`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `catalogo_asignaciones` (
  `carpeta` varchar(100) NOT NULL,
  `tarjeta_id` int(11) NOT NULL,
  PRIMARY KEY (`carpeta`),
  UNIQUE KEY `tarjeta_id` (`tarjeta_id`),
  CONSTRAINT `catalogo_asignaciones_ibfk_1` FOREIGN KEY (`tarjeta_id`) REFERENCES `tarjetas_rfid` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

LOCK TABLES `catalogo_asignaciones` WRITE;
/*!40000 ALTER TABLE `catalogo_asignaciones` DISABLE KEYS */;
INSERT INTO `catalogo_asignaciones` VALUES
('0010_gato',5),
('0001_uno',83),
('0002_dos',84),
('0003_tres',85),
('0004_cuatro',86),
('0005_cinco',87),
('0006_tortilla',88),
('0007_burro',89),
('0008_diez',90),
('0009_pollo',91),
('0011_perro',92),
('0012_mesa',93),
('0013_mellamo',94),
('0014_hola',95),
('0015_buenosdias',96),
('0016_buenastardes',97),
('0017_buenasnoches',98),
('0018_hastaluego',99),
('0019_comoestas',100),
('0020_vaca',101),
('0021_frijol',102),
('0022_maiz',103),
('0023_fuego',104),
('0024_cuaderno',105),
('0025_silla',106),
('0026_casa',107),
('0027_hombre',108),
('0028_mujer',109),
('0029_niño',110),
('0030_niña',111),
('0031_cielo',112),
('0032_coyote',113),
('0033_hierba',114),
('0034_pan',115),
('0035_chile',116),
('0036_zapato',117),
('0037_maestro',118),
('0038_escuela',119),
('0039_huevo',120),
('0040_carne',121),
('0041_amigo',122),
('0042_hijo',123),
('0043_hija',124),
('0044_bañarse',125),
('0045_lavarselasmanos',126),
('0046_hongos',127),
('0047_leña',128),
('0048_azul',129),
('0049_verde',130),
('0050_amarillo',131),
('0051_rojo',132),
('0052_naranja',133),
('0053_morado',134),
('0054_rosa',135);
/*!40000 ALTER TABLE `catalogo_asignaciones` ENABLE KEYS */;
UNLOCK TABLES;
DROP TABLE IF EXISTS `docentes`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `docentes` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `usuario` varchar(80) NOT NULL,
  `nombre` varchar(100) NOT NULL,
  `password_hash` varchar(255) NOT NULL,
  `activo` tinyint(1) NOT NULL,
  `rol` varchar(20) NOT NULL DEFAULT 'docente',
  `estado` varchar(20) NOT NULL DEFAULT 'aprobada',
  `correo` varchar(254) DEFAULT NULL,
  `creado` datetime NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `usuario` (`usuario`),
  UNIQUE KEY `correo` (`correo`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

LOCK TABLES `docentes` WRITE;
/*!40000 ALTER TABLE `docentes` DISABLE KEYS */;
/*!40000 ALTER TABLE `docentes` ENABLE KEYS */;
UNLOCK TABLES;
DROP TABLE IF EXISTS `participantes`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `participantes` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `partida_id` int(11) NOT NULL,
  `nombre` varchar(60) NOT NULL,
  `solicitud` varchar(36) NOT NULL,
  `incorporado` datetime NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `partida_id` (`partida_id`,`solicitud`),
  KEY `ix_participantes_partida_id` (`partida_id`),
  CONSTRAINT `participantes_ibfk_1` FOREIGN KEY (`partida_id`) REFERENCES `partidas` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=80 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

LOCK TABLES `participantes` WRITE;
/*!40000 ALTER TABLE `participantes` DISABLE KEYS */;
INSERT INTO `participantes` VALUES
(62,10,'Jose','71403dd2-72cd-40cd-916a-b9aac0eb106e','2026-10-24 02:47:10'),
(63,12,'Jose','596dbaa4-a0c4-4a0b-b366-fbefa75c4376','2026-10-24 02:51:53'),
(75,21,'Angeles','573e2e6e-f6cb-41f5-9205-d8f46d383bc8','2026-10-25 17:45:24'),
(76,21,'Jose','4cee429f-587f-4cd3-9dae-2212d9fd1d18','2026-10-25 17:45:39'),
(77,21,'Rosaura','32aa7276-d351-4516-aed0-670a6d002a45','2026-10-25 17:46:06');
/*!40000 ALTER TABLE `participantes` ENABLE KEYS */;
UNLOCK TABLES;
DROP TABLE IF EXISTS `partidas`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `partidas` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `codigo` varchar(6) NOT NULL,
  `clave` varchar(64) NOT NULL,
  `estado` varchar(16) NOT NULL,
  `creada` datetime NOT NULL,
  `iniciada` datetime DEFAULT NULL,
  `finalizada` datetime DEFAULT NULL,
  `limite` int(11) NOT NULL DEFAULT 25,
  `ultima_carta` longtext CHARACTER SET utf8mb4 COLLATE utf8mb4_bin DEFAULT NULL CHECK (json_valid(`ultima_carta`)),
  `secuencia` int(11) NOT NULL DEFAULT 0,
  `ultima_actividad_docente` datetime DEFAULT NULL,
  `cierre_motivo` varchar(30) DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `codigo` (`codigo`),
  KEY `ix_partidas_estado_actividad` (`estado`,`ultima_actividad_docente`)
) ENGINE=InnoDB AUTO_INCREMENT=28 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

LOCK TABLES `partidas` WRITE;
/*!40000 ALTER TABLE `partidas` DISABLE KEYS */;
INSERT INTO `partidas` VALUES
(10,'BFBSR8','a398a5a8a54edc3071b3cec509663e72faa0687273846a54f2e401a6e623d1e2','finalizada','2026-10-24 02:46:07','2026-10-24 02:47:15','2026-11-20 02:30:59',25,NULL,0,NULL,'duracion_maxima'),
(12,'NTCNX5','28fc5f0e9a4ca07d7ce76cea414c518e2f086bbda3360bc9074a7f55b43a5c20','finalizada','2026-10-24 02:51:18','2026-10-24 02:51:58','2026-11-20 02:30:59',25,NULL,0,NULL,'duracion_maxima'),
(21,'C2GYRD','58ea6c54527e008e6f4613b9ff04112779e11f54dc83f2bf3df13cee2eaa70d8','finalizada','2026-10-25 17:43:21','2026-10-25 17:46:14','2026-11-20 02:30:59',3,'{\"id\": 5, \"uid\": \"F9 DB 91 10\", \"palabra_mazahua\": \"Mixi\", \"traduccion_espanol\": \"gato\", \"categoria\": null, \"imagen_url\": \"/uploads/imagenes/640a6c4a87014614a69dfe83b3aa64c9.jpg\", \"audio_mazahua_url\": \"/uploads/audios/7af0d94bdc3f42fcb5d8d86f91872972.mp3\", \"audio_espanol_url\": \"/uploads/audios/f59c8f1b2b6343b9993516a14e17ed34.mp3\", \"created_at\": \"2026-10-23T11:36:24\"}',3,NULL,'duracion_maxima');
/*!40000 ALTER TABLE `partidas` ENABLE KEYS */;
UNLOCK TABLES;
DROP TABLE IF EXISTS `resultados_partida`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `resultados_partida` (
  `partida_id` int(11) NOT NULL,
  `participante_id` int(11) NOT NULL,
  `fecha` datetime NOT NULL,
  PRIMARY KEY (`partida_id`),
  KEY `participante_id` (`participante_id`),
  CONSTRAINT `resultados_partida_ibfk_1` FOREIGN KEY (`partida_id`) REFERENCES `partidas` (`id`),
  CONSTRAINT `resultados_partida_ibfk_2` FOREIGN KEY (`participante_id`) REFERENCES `participantes` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

LOCK TABLES `resultados_partida` WRITE;
/*!40000 ALTER TABLE `resultados_partida` DISABLE KEYS */;
/*!40000 ALTER TABLE `resultados_partida` ENABLE KEYS */;
UNLOCK TABLES;
DROP TABLE IF EXISTS `tableros`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `tableros` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `participante_id` int(11) NOT NULL,
  `cartas` longtext CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL CHECK (json_valid(`cartas`)),
  `marcas` longtext CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL CHECK (json_valid(`marcas`)),
  PRIMARY KEY (`id`),
  UNIQUE KEY `participante_id` (`participante_id`),
  CONSTRAINT `tableros_ibfk_1` FOREIGN KEY (`participante_id`) REFERENCES `participantes` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=21 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

LOCK TABLES `tableros` WRITE;
/*!40000 ALTER TABLE `tableros` DISABLE KEYS */;
INSERT INTO `tableros` VALUES
(5,63,'[{\"id\": 67, \"uid\": \"DEMO 047\", \"palabra_mazahua\": \"Sin contenido mazahua (prueba)\", \"traduccion_espanol\": \"Carta de prueba 47\", \"categoria\": \"DEMOSTRACI\\u00d3N \\u00b7 Datos temporales\", \"imagen_url\": \"/uploads/imagenes/demo_loteria_047.svg\", \"audio_mazahua_url\": null, \"audio_espanol_url\": null, \"created_at\": \"2026-10-23T20:43:56\"}, {\"id\": 66, \"uid\": \"DEMO 046\", \"palabra_mazahua\": \"Sin contenido mazahua (prueba)\", \"traduccion_espanol\": \"Carta de prueba 46\", \"categoria\": \"DEMOSTRACI\\u00d3N \\u00b7 Datos temporales\", \"imagen_url\": \"/uploads/imagenes/demo_loteria_046.svg\", \"audio_mazahua_url\": null, \"audio_espanol_url\": null, \"created_at\": \"2026-10-23T20:43:56\"}, {\"id\": 53, \"uid\": \"DEMO 033\", \"palabra_mazahua\": \"Sin contenido mazahua (prueba)\", \"traduccion_espanol\": \"Carta de prueba 33\", \"categoria\": \"DEMOSTRACI\\u00d3N \\u00b7 Datos temporales\", \"imagen_url\": \"/uploads/imagenes/demo_loteria_033.svg\", \"audio_mazahua_url\": null, \"audio_espanol_url\": null, \"created_at\": \"2026-10-23T20:43:56\"}, {\"id\": 27, \"uid\": \"DEMO 007\", \"palabra_mazahua\": \"Sin contenido mazahua (prueba)\", \"traduccion_espanol\": \"Carta de prueba 07\", \"categoria\": \"DEMOSTRACI\\u00d3N \\u00b7 Datos temporales\", \"imagen_url\": \"/uploads/imagenes/demo_loteria_007.svg\", \"audio_mazahua_url\": null, \"audio_espanol_url\": null, \"created_at\": \"2026-10-23T20:43:56\"}, {\"id\": 74, \"uid\": \"DEMO 054\", \"palabra_mazahua\": \"Sin contenido mazahua (prueba)\", \"traduccion_espanol\": \"Carta de prueba 54\", \"categoria\": \"DEMOSTRACI\\u00d3N \\u00b7 Datos temporales\", \"imagen_url\": \"/uploads/imagenes/demo_loteria_054.svg\", \"audio_mazahua_url\": null, \"audio_espanol_url\": null, \"created_at\": \"2026-10-23T20:43:56\"}, {\"id\": 70, \"uid\": \"DEMO 050\", \"palabra_mazahua\": \"Sin contenido mazahua (prueba)\", \"traduccion_espanol\": \"Carta de prueba 50\", \"categoria\": \"DEMOSTRACI\\u00d3N \\u00b7 Datos temporales\", \"imagen_url\": \"/uploads/imagenes/demo_loteria_050.svg\", \"audio_mazahua_url\": null, \"audio_espanol_url\": null, \"created_at\": \"2026-10-23T20:43:56\"}, {\"id\": 36, \"uid\": \"DEMO 016\", \"palabra_mazahua\": \"Sin contenido mazahua (prueba)\", \"traduccion_espanol\": \"Carta de prueba 16\", \"categoria\": \"DEMOSTRACI\\u00d3N \\u00b7 Datos temporales\", \"imagen_url\": \"/uploads/imagenes/demo_loteria_016.svg\", \"audio_mazahua_url\": null, \"audio_espanol_url\": null, \"created_at\": \"2026-10-23T20:43:56\"}, {\"id\": 25, \"uid\": \"DEMO 005\", \"palabra_mazahua\": \"Sin contenido mazahua (prueba)\", \"traduccion_espanol\": \"Carta de prueba 05\", \"categoria\": \"DEMOSTRACI\\u00d3N \\u00b7 Datos temporales\", \"imagen_url\": \"/uploads/imagenes/demo_loteria_005.svg\", \"audio_mazahua_url\": null, \"audio_espanol_url\": null, \"created_at\": \"2026-10-23T20:43:56\"}, {\"id\": 26, \"uid\": \"DEMO 006\", \"palabra_mazahua\": \"Sin contenido mazahua (prueba)\", \"traduccion_espanol\": \"Carta de prueba 06\", \"categoria\": \"DEMOSTRACI\\u00d3N \\u00b7 Datos temporales\", \"imagen_url\": \"/uploads/imagenes/demo_loteria_006.svg\", \"audio_mazahua_url\": null, \"audio_espanol_url\": null, \"created_at\": \"2026-10-23T20:43:56\"}, {\"id\": 63, \"uid\": \"DEMO 043\", \"palabra_mazahua\": \"Sin contenido mazahua (prueba)\", \"traduccion_espanol\": \"Carta de prueba 43\", \"categoria\": \"DEMOSTRACI\\u00d3N \\u00b7 Datos temporales\", \"imagen_url\": \"/uploads/imagenes/demo_loteria_043.svg\", \"audio_mazahua_url\": null, \"audio_espanol_url\": null, \"created_at\": \"2026-10-23T20:43:56\"}, {\"id\": 73, \"uid\": \"DEMO 053\", \"palabra_mazahua\": \"Sin contenido mazahua (prueba)\", \"traduccion_espanol\": \"Carta de prueba 53\", \"categoria\": \"DEMOSTRACI\\u00d3N \\u00b7 Datos temporales\", \"imagen_url\": \"/uploads/imagenes/demo_loteria_053.svg\", \"audio_mazahua_url\": null, \"audio_espanol_url\": null, \"created_at\": \"2026-10-23T20:43:56\"}, {\"id\": 71, \"uid\": \"DEMO 051\", \"palabra_mazahua\": \"Sin contenido mazahua (prueba)\", \"traduccion_espanol\": \"Carta de prueba 51\", \"categoria\": \"DEMOSTRACI\\u00d3N \\u00b7 Datos temporales\", \"imagen_url\": \"/uploads/imagenes/demo_loteria_051.svg\", \"audio_mazahua_url\": null, \"audio_espanol_url\": null, \"created_at\": \"2026-10-23T20:43:56\"}, {\"id\": 38, \"uid\": \"DEMO 018\", \"palabra_mazahua\": \"Sin contenido mazahua (prueba)\", \"traduccion_espanol\": \"Carta de prueba 18\", \"categoria\": \"DEMOSTRACI\\u00d3N \\u00b7 Datos temporales\", \"imagen_url\": \"/uploads/imagenes/demo_loteria_018.svg\", \"audio_mazahua_url\": null, \"audio_espanol_url\": null, \"created_at\": \"2026-10-23T20:43:56\"}, {\"id\": 57, \"uid\": \"DEMO 037\", \"palabra_mazahua\": \"Sin contenido mazahua (prueba)\", \"traduccion_espanol\": \"Carta de prueba 37\", \"categoria\": \"DEMOSTRACI\\u00d3N \\u00b7 Datos temporales\", \"imagen_url\": \"/uploads/imagenes/demo_loteria_037.svg\", \"audio_mazahua_url\": null, \"audio_espanol_url\": null, \"created_at\": \"2026-10-23T20:43:56\"}, {\"id\": 68, \"uid\": \"DEMO 048\", \"palabra_mazahua\": \"Sin contenido mazahua (prueba)\", \"traduccion_espanol\": \"Carta de prueba 48\", \"categoria\": \"DEMOSTRACI\\u00d3N \\u00b7 Datos temporales\", \"imagen_url\": \"/uploads/imagenes/demo_loteria_048.svg\", \"audio_mazahua_url\": null, \"audio_espanol_url\": null, \"created_at\": \"2026-10-23T20:43:56\"}, {\"id\": 72, \"uid\": \"DEMO 052\", \"palabra_mazahua\": \"Sin contenido mazahua (prueba)\", \"traduccion_espanol\": \"Carta de prueba 52\", \"categoria\": \"DEMOSTRACI\\u00d3N \\u00b7 Datos temporales\", \"imagen_url\": \"/uploads/imagenes/demo_loteria_052.svg\", \"audio_mazahua_url\": null, \"audio_espanol_url\": null, \"created_at\": \"2026-10-23T20:43:56\"}]','[25, 26, 27, 36, 38, 53, 57, 63, 66, 67, 68, 70, 71, 72, 73, 74]'),
(16,75,'[{\"id\": 36, \"uid\": \"DEMO 016\", \"palabra_mazahua\": \"Sin contenido mazahua (prueba)\", \"traduccion_espanol\": \"Carta de prueba 16\", \"categoria\": \"DEMOSTRACI\\u00d3N \\u00b7 Datos temporales\", \"imagen_url\": \"/uploads/imagenes/demo_loteria_016.svg\", \"audio_mazahua_url\": null, \"audio_espanol_url\": null, \"created_at\": \"2026-10-23T20:43:56\"}, {\"id\": 47, \"uid\": \"DEMO 027\", \"palabra_mazahua\": \"Sin contenido mazahua (prueba)\", \"traduccion_espanol\": \"Carta de prueba 27\", \"categoria\": \"DEMOSTRACI\\u00d3N \\u00b7 Datos temporales\", \"imagen_url\": \"/uploads/imagenes/demo_loteria_027.svg\", \"audio_mazahua_url\": null, \"audio_espanol_url\": null, \"created_at\": \"2026-10-23T20:43:56\"}, {\"id\": 45, \"uid\": \"DEMO 025\", \"palabra_mazahua\": \"Sin contenido mazahua (prueba)\", \"traduccion_espanol\": \"Carta de prueba 25\", \"categoria\": \"DEMOSTRACI\\u00d3N \\u00b7 Datos temporales\", \"imagen_url\": \"/uploads/imagenes/demo_loteria_025.svg\", \"audio_mazahua_url\": null, \"audio_espanol_url\": null, \"created_at\": \"2026-10-23T20:43:56\"}, {\"id\": 53, \"uid\": \"DEMO 033\", \"palabra_mazahua\": \"Sin contenido mazahua (prueba)\", \"traduccion_espanol\": \"Carta de prueba 33\", \"categoria\": \"DEMOSTRACI\\u00d3N \\u00b7 Datos temporales\", \"imagen_url\": \"/uploads/imagenes/demo_loteria_033.svg\", \"audio_mazahua_url\": null, \"audio_espanol_url\": null, \"created_at\": \"2026-10-23T20:43:56\"}, {\"id\": 61, \"uid\": \"DEMO 041\", \"palabra_mazahua\": \"Sin contenido mazahua (prueba)\", \"traduccion_espanol\": \"Carta de prueba 41\", \"categoria\": \"DEMOSTRACI\\u00d3N \\u00b7 Datos temporales\", \"imagen_url\": \"/uploads/imagenes/demo_loteria_041.svg\", \"audio_mazahua_url\": null, \"audio_espanol_url\": null, \"created_at\": \"2026-10-23T20:43:56\"}, {\"id\": 44, \"uid\": \"DEMO 024\", \"palabra_mazahua\": \"Sin contenido mazahua (prueba)\", \"traduccion_espanol\": \"Carta de prueba 24\", \"categoria\": \"DEMOSTRACI\\u00d3N \\u00b7 Datos temporales\", \"imagen_url\": \"/uploads/imagenes/demo_loteria_024.svg\", \"audio_mazahua_url\": null, \"audio_espanol_url\": null, \"created_at\": \"2026-10-23T20:43:56\"}, {\"id\": 30, \"uid\": \"DEMO 010\", \"palabra_mazahua\": \"Sin contenido mazahua (prueba)\", \"traduccion_espanol\": \"Carta de prueba 10\", \"categoria\": \"DEMOSTRACI\\u00d3N \\u00b7 Datos temporales\", \"imagen_url\": \"/uploads/imagenes/demo_loteria_010.svg\", \"audio_mazahua_url\": null, \"audio_espanol_url\": null, \"created_at\": \"2026-10-23T20:43:56\"}, {\"id\": 28, \"uid\": \"DEMO 008\", \"palabra_mazahua\": \"Sin contenido mazahua (prueba)\", \"traduccion_espanol\": \"Carta de prueba 08\", \"categoria\": \"DEMOSTRACI\\u00d3N \\u00b7 Datos temporales\", \"imagen_url\": \"/uploads/imagenes/demo_loteria_008.svg\", \"audio_mazahua_url\": null, \"audio_espanol_url\": null, \"created_at\": \"2026-10-23T20:43:56\"}, {\"id\": 5, \"uid\": \"F9 DB 91 10\", \"palabra_mazahua\": \"Mixi\", \"traduccion_espanol\": \"gato\", \"categoria\": null, \"imagen_url\": \"/uploads/imagenes/640a6c4a87014614a69dfe83b3aa64c9.jpg\", \"audio_mazahua_url\": \"/uploads/audios/7af0d94bdc3f42fcb5d8d86f91872972.mp3\", \"audio_espanol_url\": \"/uploads/audios/f59c8f1b2b6343b9993516a14e17ed34.mp3\", \"created_at\": \"2026-10-23T11:36:24\"}, {\"id\": 55, \"uid\": \"DEMO 035\", \"palabra_mazahua\": \"Sin contenido mazahua (prueba)\", \"traduccion_espanol\": \"Carta de prueba 35\", \"categoria\": \"DEMOSTRACI\\u00d3N \\u00b7 Datos temporales\", \"imagen_url\": \"/uploads/imagenes/demo_loteria_035.svg\", \"audio_mazahua_url\": null, \"audio_espanol_url\": null, \"created_at\": \"2026-10-23T20:43:56\"}, {\"id\": 37, \"uid\": \"DEMO 017\", \"palabra_mazahua\": \"Sin contenido mazahua (prueba)\", \"traduccion_espanol\": \"Carta de prueba 17\", \"categoria\": \"DEMOSTRACI\\u00d3N \\u00b7 Datos temporales\", \"imagen_url\": \"/uploads/imagenes/demo_loteria_017.svg\", \"audio_mazahua_url\": null, \"audio_espanol_url\": null, \"created_at\": \"2026-10-23T20:43:56\"}, {\"id\": 72, \"uid\": \"DEMO 052\", \"palabra_mazahua\": \"Sin contenido mazahua (prueba)\", \"traduccion_espanol\": \"Carta de prueba 52\", \"categoria\": \"DEMOSTRACI\\u00d3N \\u00b7 Datos temporales\", \"imagen_url\": \"/uploads/imagenes/demo_loteria_052.svg\", \"audio_mazahua_url\": null, \"audio_espanol_url\": null, \"created_at\": \"2026-10-23T20:43:56\"}, {\"id\": 51, \"uid\": \"DEMO 031\", \"palabra_mazahua\": \"Sin contenido mazahua (prueba)\", \"traduccion_espanol\": \"Carta de prueba 31\", \"categoria\": \"DEMOSTRACI\\u00d3N \\u00b7 Datos temporales\", \"imagen_url\": \"/uploads/imagenes/demo_loteria_031.svg\", \"audio_mazahua_url\": null, \"audio_espanol_url\": null, \"created_at\": \"2026-10-23T20:43:56\"}, {\"id\": 69, \"uid\": \"DEMO 049\", \"palabra_mazahua\": \"Sin contenido mazahua (prueba)\", \"traduccion_espanol\": \"Carta de prueba 49\", \"categoria\": \"DEMOSTRACI\\u00d3N \\u00b7 Datos temporales\", \"imagen_url\": \"/uploads/imagenes/demo_loteria_049.svg\", \"audio_mazahua_url\": null, \"audio_espanol_url\": null, \"created_at\": \"2026-10-23T20:43:56\"}, {\"id\": 27, \"uid\": \"DEMO 007\", \"palabra_mazahua\": \"Sin contenido mazahua (prueba)\", \"traduccion_espanol\": \"Carta de prueba 07\", \"categoria\": \"DEMOSTRACI\\u00d3N \\u00b7 Datos temporales\", \"imagen_url\": \"/uploads/imagenes/demo_loteria_007.svg\", \"audio_mazahua_url\": null, \"audio_espanol_url\": null, \"created_at\": \"2026-10-23T20:43:56\"}, {\"id\": 41, \"uid\": \"DEMO 021\", \"palabra_mazahua\": \"Sin contenido mazahua (prueba)\", \"traduccion_espanol\": \"Carta de prueba 21\", \"categoria\": \"DEMOSTRACI\\u00d3N \\u00b7 Datos temporales\", \"imagen_url\": \"/uploads/imagenes/demo_loteria_021.svg\", \"audio_mazahua_url\": null, \"audio_espanol_url\": null, \"created_at\": \"2026-10-23T20:43:56\"}]','[]'),
(17,76,'[{\"id\": 55, \"uid\": \"DEMO 035\", \"palabra_mazahua\": \"Sin contenido mazahua (prueba)\", \"traduccion_espanol\": \"Carta de prueba 35\", \"categoria\": \"DEMOSTRACI\\u00d3N \\u00b7 Datos temporales\", \"imagen_url\": \"/uploads/imagenes/demo_loteria_035.svg\", \"audio_mazahua_url\": null, \"audio_espanol_url\": null, \"created_at\": \"2026-10-23T20:43:56\"}, {\"id\": 35, \"uid\": \"DEMO 015\", \"palabra_mazahua\": \"Sin contenido mazahua (prueba)\", \"traduccion_espanol\": \"Carta de prueba 15\", \"categoria\": \"DEMOSTRACI\\u00d3N \\u00b7 Datos temporales\", \"imagen_url\": \"/uploads/imagenes/demo_loteria_015.svg\", \"audio_mazahua_url\": null, \"audio_espanol_url\": null, \"created_at\": \"2026-10-23T20:43:56\"}, {\"id\": 39, \"uid\": \"DEMO 019\", \"palabra_mazahua\": \"Sin contenido mazahua (prueba)\", \"traduccion_espanol\": \"Carta de prueba 19\", \"categoria\": \"DEMOSTRACI\\u00d3N \\u00b7 Datos temporales\", \"imagen_url\": \"/uploads/imagenes/demo_loteria_019.svg\", \"audio_mazahua_url\": null, \"audio_espanol_url\": null, \"created_at\": \"2026-10-23T20:43:56\"}, {\"id\": 74, \"uid\": \"DEMO 054\", \"palabra_mazahua\": \"Sin contenido mazahua (prueba)\", \"traduccion_espanol\": \"Carta de prueba 54\", \"categoria\": \"DEMOSTRACI\\u00d3N \\u00b7 Datos temporales\", \"imagen_url\": \"/uploads/imagenes/demo_loteria_054.svg\", \"audio_mazahua_url\": null, \"audio_espanol_url\": null, \"created_at\": \"2026-10-23T20:43:56\"}, {\"id\": 46, \"uid\": \"DEMO 026\", \"palabra_mazahua\": \"Sin contenido mazahua (prueba)\", \"traduccion_espanol\": \"Carta de prueba 26\", \"categoria\": \"DEMOSTRACI\\u00d3N \\u00b7 Datos temporales\", \"imagen_url\": \"/uploads/imagenes/demo_loteria_026.svg\", \"audio_mazahua_url\": null, \"audio_espanol_url\": null, \"created_at\": \"2026-10-23T20:43:56\"}, {\"id\": 66, \"uid\": \"DEMO 046\", \"palabra_mazahua\": \"Sin contenido mazahua (prueba)\", \"traduccion_espanol\": \"Carta de prueba 46\", \"categoria\": \"DEMOSTRACI\\u00d3N \\u00b7 Datos temporales\", \"imagen_url\": \"/uploads/imagenes/demo_loteria_046.svg\", \"audio_mazahua_url\": null, \"audio_espanol_url\": null, \"created_at\": \"2026-10-23T20:43:56\"}, {\"id\": 53, \"uid\": \"DEMO 033\", \"palabra_mazahua\": \"Sin contenido mazahua (prueba)\", \"traduccion_espanol\": \"Carta de prueba 33\", \"categoria\": \"DEMOSTRACI\\u00d3N \\u00b7 Datos temporales\", \"imagen_url\": \"/uploads/imagenes/demo_loteria_033.svg\", \"audio_mazahua_url\": null, \"audio_espanol_url\": null, \"created_at\": \"2026-10-23T20:43:56\"}, {\"id\": 45, \"uid\": \"DEMO 025\", \"palabra_mazahua\": \"Sin contenido mazahua (prueba)\", \"traduccion_espanol\": \"Carta de prueba 25\", \"categoria\": \"DEMOSTRACI\\u00d3N \\u00b7 Datos temporales\", \"imagen_url\": \"/uploads/imagenes/demo_loteria_025.svg\", \"audio_mazahua_url\": null, \"audio_espanol_url\": null, \"created_at\": \"2026-10-23T20:43:56\"}, {\"id\": 51, \"uid\": \"DEMO 031\", \"palabra_mazahua\": \"Sin contenido mazahua (prueba)\", \"traduccion_espanol\": \"Carta de prueba 31\", \"categoria\": \"DEMOSTRACI\\u00d3N \\u00b7 Datos temporales\", \"imagen_url\": \"/uploads/imagenes/demo_loteria_031.svg\", \"audio_mazahua_url\": null, \"audio_espanol_url\": null, \"created_at\": \"2026-10-23T20:43:56\"}, {\"id\": 6, \"uid\": \"A9 DD 25 10\", \"palabra_mazahua\": \"gaoo\", \"traduccion_espanol\": \"gallo\", \"categoria\": null, \"imagen_url\": \"/uploads/imagenes/901207ce2747487599fbfcfaca76160c.png\", \"audio_mazahua_url\": \"/uploads/audios/e7071e3500014e5aaae9dcde3bbb5cab.mp3\", \"audio_espanol_url\": \"/uploads/audios/388ce86366e2414ca726ecb89dcca02b.mp3\", \"created_at\": \"2026-10-23T11:38:59\"}, {\"id\": 68, \"uid\": \"DEMO 048\", \"palabra_mazahua\": \"Sin contenido mazahua (prueba)\", \"traduccion_espanol\": \"Carta de prueba 48\", \"categoria\": \"DEMOSTRACI\\u00d3N \\u00b7 Datos temporales\", \"imagen_url\": \"/uploads/imagenes/demo_loteria_048.svg\", \"audio_mazahua_url\": null, \"audio_espanol_url\": null, \"created_at\": \"2026-10-23T20:43:56\"}, {\"id\": 54, \"uid\": \"DEMO 034\", \"palabra_mazahua\": \"Sin contenido mazahua (prueba)\", \"traduccion_espanol\": \"Carta de prueba 34\", \"categoria\": \"DEMOSTRACI\\u00d3N \\u00b7 Datos temporales\", \"imagen_url\": \"/uploads/imagenes/demo_loteria_034.svg\", \"audio_mazahua_url\": null, \"audio_espanol_url\": null, \"created_at\": \"2026-10-23T20:43:56\"}, {\"id\": 50, \"uid\": \"DEMO 030\", \"palabra_mazahua\": \"Sin contenido mazahua (prueba)\", \"traduccion_espanol\": \"Carta de prueba 30\", \"categoria\": \"DEMOSTRACI\\u00d3N \\u00b7 Datos temporales\", \"imagen_url\": \"/uploads/imagenes/demo_loteria_030.svg\", \"audio_mazahua_url\": null, \"audio_espanol_url\": null, \"created_at\": \"2026-10-23T20:43:56\"}, {\"id\": 62, \"uid\": \"DEMO 042\", \"palabra_mazahua\": \"Sin contenido mazahua (prueba)\", \"traduccion_espanol\": \"Carta de prueba 42\", \"categoria\": \"DEMOSTRACI\\u00d3N \\u00b7 Datos temporales\", \"imagen_url\": \"/uploads/imagenes/demo_loteria_042.svg\", \"audio_mazahua_url\": null, \"audio_espanol_url\": null, \"created_at\": \"2026-10-23T20:43:56\"}, {\"id\": 42, \"uid\": \"DEMO 022\", \"palabra_mazahua\": \"Sin contenido mazahua (prueba)\", \"traduccion_espanol\": \"Carta de prueba 22\", \"categoria\": \"DEMOSTRACI\\u00d3N \\u00b7 Datos temporales\", \"imagen_url\": \"/uploads/imagenes/demo_loteria_022.svg\", \"audio_mazahua_url\": null, \"audio_espanol_url\": null, \"created_at\": \"2026-10-23T20:43:56\"}, {\"id\": 34, \"uid\": \"DEMO 014\", \"palabra_mazahua\": \"Sin contenido mazahua (prueba)\", \"traduccion_espanol\": \"Carta de prueba 14\", \"categoria\": \"DEMOSTRACI\\u00d3N \\u00b7 Datos temporales\", \"imagen_url\": \"/uploads/imagenes/demo_loteria_014.svg\", \"audio_mazahua_url\": null, \"audio_espanol_url\": null, \"created_at\": \"2026-10-23T20:43:56\"}]','[6]'),
(18,77,'[{\"id\": 62, \"uid\": \"DEMO 042\", \"palabra_mazahua\": \"Sin contenido mazahua (prueba)\", \"traduccion_espanol\": \"Carta de prueba 42\", \"categoria\": \"DEMOSTRACI\\u00d3N \\u00b7 Datos temporales\", \"imagen_url\": \"/uploads/imagenes/demo_loteria_042.svg\", \"audio_mazahua_url\": null, \"audio_espanol_url\": null, \"created_at\": \"2026-10-23T20:43:56\"}, {\"id\": 23, \"uid\": \"DEMO 003\", \"palabra_mazahua\": \"Sin contenido mazahua (prueba)\", \"traduccion_espanol\": \"Carta de prueba 03\", \"categoria\": \"DEMOSTRACI\\u00d3N \\u00b7 Datos temporales\", \"imagen_url\": \"/uploads/imagenes/demo_loteria_003.svg\", \"audio_mazahua_url\": null, \"audio_espanol_url\": null, \"created_at\": \"2026-10-23T20:43:56\"}, {\"id\": 57, \"uid\": \"DEMO 037\", \"palabra_mazahua\": \"Sin contenido mazahua (prueba)\", \"traduccion_espanol\": \"Carta de prueba 37\", \"categoria\": \"DEMOSTRACI\\u00d3N \\u00b7 Datos temporales\", \"imagen_url\": \"/uploads/imagenes/demo_loteria_037.svg\", \"audio_mazahua_url\": null, \"audio_espanol_url\": null, \"created_at\": \"2026-10-23T20:43:56\"}, {\"id\": 46, \"uid\": \"DEMO 026\", \"palabra_mazahua\": \"Sin contenido mazahua (prueba)\", \"traduccion_espanol\": \"Carta de prueba 26\", \"categoria\": \"DEMOSTRACI\\u00d3N \\u00b7 Datos temporales\", \"imagen_url\": \"/uploads/imagenes/demo_loteria_026.svg\", \"audio_mazahua_url\": null, \"audio_espanol_url\": null, \"created_at\": \"2026-10-23T20:43:56\"}, {\"id\": 45, \"uid\": \"DEMO 025\", \"palabra_mazahua\": \"Sin contenido mazahua (prueba)\", \"traduccion_espanol\": \"Carta de prueba 25\", \"categoria\": \"DEMOSTRACI\\u00d3N \\u00b7 Datos temporales\", \"imagen_url\": \"/uploads/imagenes/demo_loteria_025.svg\", \"audio_mazahua_url\": null, \"audio_espanol_url\": null, \"created_at\": \"2026-10-23T20:43:56\"}, {\"id\": 53, \"uid\": \"DEMO 033\", \"palabra_mazahua\": \"Sin contenido mazahua (prueba)\", \"traduccion_espanol\": \"Carta de prueba 33\", \"categoria\": \"DEMOSTRACI\\u00d3N \\u00b7 Datos temporales\", \"imagen_url\": \"/uploads/imagenes/demo_loteria_033.svg\", \"audio_mazahua_url\": null, \"audio_espanol_url\": null, \"created_at\": \"2026-10-23T20:43:56\"}, {\"id\": 58, \"uid\": \"DEMO 038\", \"palabra_mazahua\": \"Sin contenido mazahua (prueba)\", \"traduccion_espanol\": \"Carta de prueba 38\", \"categoria\": \"DEMOSTRACI\\u00d3N \\u00b7 Datos temporales\", \"imagen_url\": \"/uploads/imagenes/demo_loteria_038.svg\", \"audio_mazahua_url\": null, \"audio_espanol_url\": null, \"created_at\": \"2026-10-23T20:43:56\"}, {\"id\": 43, \"uid\": \"DEMO 023\", \"palabra_mazahua\": \"Sin contenido mazahua (prueba)\", \"traduccion_espanol\": \"Carta de prueba 23\", \"categoria\": \"DEMOSTRACI\\u00d3N \\u00b7 Datos temporales\", \"imagen_url\": \"/uploads/imagenes/demo_loteria_023.svg\", \"audio_mazahua_url\": null, \"audio_espanol_url\": null, \"created_at\": \"2026-10-23T20:43:56\"}, {\"id\": 36, \"uid\": \"DEMO 016\", \"palabra_mazahua\": \"Sin contenido mazahua (prueba)\", \"traduccion_espanol\": \"Carta de prueba 16\", \"categoria\": \"DEMOSTRACI\\u00d3N \\u00b7 Datos temporales\", \"imagen_url\": \"/uploads/imagenes/demo_loteria_016.svg\", \"audio_mazahua_url\": null, \"audio_espanol_url\": null, \"created_at\": \"2026-10-23T20:43:56\"}, {\"id\": 60, \"uid\": \"DEMO 040\", \"palabra_mazahua\": \"Sin contenido mazahua (prueba)\", \"traduccion_espanol\": \"Carta de prueba 40\", \"categoria\": \"DEMOSTRACI\\u00d3N \\u00b7 Datos temporales\", \"imagen_url\": \"/uploads/imagenes/demo_loteria_040.svg\", \"audio_mazahua_url\": null, \"audio_espanol_url\": null, \"created_at\": \"2026-10-23T20:43:56\"}, {\"id\": 72, \"uid\": \"DEMO 052\", \"palabra_mazahua\": \"Sin contenido mazahua (prueba)\", \"traduccion_espanol\": \"Carta de prueba 52\", \"categoria\": \"DEMOSTRACI\\u00d3N \\u00b7 Datos temporales\", \"imagen_url\": \"/uploads/imagenes/demo_loteria_052.svg\", \"audio_mazahua_url\": null, \"audio_espanol_url\": null, \"created_at\": \"2026-10-23T20:43:56\"}, {\"id\": 63, \"uid\": \"DEMO 043\", \"palabra_mazahua\": \"Sin contenido mazahua (prueba)\", \"traduccion_espanol\": \"Carta de prueba 43\", \"categoria\": \"DEMOSTRACI\\u00d3N \\u00b7 Datos temporales\", \"imagen_url\": \"/uploads/imagenes/demo_loteria_043.svg\", \"audio_mazahua_url\": null, \"audio_espanol_url\": null, \"created_at\": \"2026-10-23T20:43:56\"}, {\"id\": 70, \"uid\": \"DEMO 050\", \"palabra_mazahua\": \"Sin contenido mazahua (prueba)\", \"traduccion_espanol\": \"Carta de prueba 50\", \"categoria\": \"DEMOSTRACI\\u00d3N \\u00b7 Datos temporales\", \"imagen_url\": \"/uploads/imagenes/demo_loteria_050.svg\", \"audio_mazahua_url\": null, \"audio_espanol_url\": null, \"created_at\": \"2026-10-23T20:43:56\"}, {\"id\": 69, \"uid\": \"DEMO 049\", \"palabra_mazahua\": \"Sin contenido mazahua (prueba)\", \"traduccion_espanol\": \"Carta de prueba 49\", \"categoria\": \"DEMOSTRACI\\u00d3N \\u00b7 Datos temporales\", \"imagen_url\": \"/uploads/imagenes/demo_loteria_049.svg\", \"audio_mazahua_url\": null, \"audio_espanol_url\": null, \"created_at\": \"2026-10-23T20:43:56\"}, {\"id\": 67, \"uid\": \"DEMO 047\", \"palabra_mazahua\": \"Sin contenido mazahua (prueba)\", \"traduccion_espanol\": \"Carta de prueba 47\", \"categoria\": \"DEMOSTRACI\\u00d3N \\u00b7 Datos temporales\", \"imagen_url\": \"/uploads/imagenes/demo_loteria_047.svg\", \"audio_mazahua_url\": null, \"audio_espanol_url\": null, \"created_at\": \"2026-10-23T20:43:56\"}, {\"id\": 47, \"uid\": \"DEMO 027\", \"palabra_mazahua\": \"Sin contenido mazahua (prueba)\", \"traduccion_espanol\": \"Carta de prueba 27\", \"categoria\": \"DEMOSTRACI\\u00d3N \\u00b7 Datos temporales\", \"imagen_url\": \"/uploads/imagenes/demo_loteria_027.svg\", \"audio_mazahua_url\": null, \"audio_espanol_url\": null, \"created_at\": \"2026-10-23T20:43:56\"}]','[]');
/*!40000 ALTER TABLE `tableros` ENABLE KEYS */;
UNLOCK TABLES;
DROP TABLE IF EXISTS `tarjetas_rfid`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `tarjetas_rfid` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `uid` varchar(40) NOT NULL,
  `palabra_mazahua` varchar(150) NOT NULL,
  `traduccion_espanol` varchar(150) NOT NULL,
  `categoria` varchar(100) DEFAULT NULL,
  `imagen_url` varchar(255) NOT NULL,
  `audio_mazahua_url` varchar(255) DEFAULT NULL,
  `audio_espanol_url` varchar(255) DEFAULT NULL,
  `created_at` datetime NOT NULL DEFAULT current_timestamp(),
  `descripcion` text DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `ix_tarjetas_rfid_uid` (`uid`),
  KEY `ix_tarjetas_rfid_id` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=136 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

LOCK TABLES `tarjetas_rfid` WRITE;
/*!40000 ALTER TABLE `tarjetas_rfid` DISABLE KEYS */;
INSERT INTO `tarjetas_rfid` VALUES
(5,'F9 DB 91 10','Mixi','Gato',NULL,'/catalogo/0010_gato/imagen.jpg','/catalogo/0010_gato/audio_mazahua.m4a','/uploads/audios/f59c8f1b2b6343b9993516a14e17ed34.mp3','2026-10-23 11:36:24','«Mixi» es la palabra en lengua mazahua para «gato». Escucha su pronunciación en mazahua y en español.'),
(6,'A9 DD 25 10','gaoo','gallo',NULL,'/uploads/imagenes/901207ce2747487599fbfcfaca76160c.png','/uploads/audios/e7071e3500014e5aaae9dcde3bbb5cab.mp3','/uploads/audios/388ce86366e2414ca726ecb89dcca02b.mp3','2026-10-23 11:38:59','«gaoo» es la palabra en lengua mazahua para «gallo». Escucha su pronunciación en mazahua y en español.'),
(83,'DEMO 0001','Naja','Uno',NULL,'/catalogo/0001_uno/imagen.jpg','/catalogo/0001_uno/audio_mazahua.m4a',NULL,'2026-11-20 02:30:59','«Naja» es la palabra en lengua mazahua para «uno». Escucha su pronunciación en mazahua y en español.'),
(84,'DEMO 0002','Yeje','Dos',NULL,'/catalogo/0002_dos/imagen.jpg','/catalogo/0002_dos/audio_mazahua.m4a',NULL,'2026-11-20 02:30:59','«Yeje» es la palabra en lengua mazahua para «dos». Escucha su pronunciación en mazahua y en español.'),
(85,'DEMO 0003','Jñi','Tres',NULL,'/catalogo/0003_tres/imagen.jpg','/catalogo/0003_tres/audio_mazahua.m4a',NULL,'2026-11-20 02:30:59','«Jñi» es la palabra en lengua mazahua para «tres». Escucha su pronunciación en mazahua y en español.'),
(86,'DEMO 0004','Nziyo','Cuatro',NULL,'/catalogo/0004_cuatro/imagen.jpg','/catalogo/0004_cuatro/audio_mazahua.m4a',NULL,'2026-11-20 02:30:59','«Nziyo» es la palabra en lengua mazahua para «cuatro». Escucha su pronunciación en mazahua y en español.'),
(87,'DEMO 0005','Tsicha','Cinco',NULL,'/catalogo/0005_cinco/imagen.jpg','/catalogo/0005_cinco/audio_mazahua.m4a',NULL,'2026-11-20 02:30:59','«Tsicha» es la palabra en lengua mazahua para «cinco». Escucha su pronunciación en mazahua y en español.'),
(88,'DEMO 0006','Segi','Tortilla',NULL,'/catalogo/0006_tortilla/imagen.jpg','/catalogo/0006_tortilla/audio_mazahua.m4a',NULL,'2026-11-20 02:30:59','«Segi» es la palabra en lengua mazahua para «tortilla». Escucha su pronunciación en mazahua y en español.'),
(89,'DEMO 0007','Recua','Burro',NULL,'/catalogo/0007_burro/imagen.jpg','/catalogo/0007_burro/audio_mazahua.m4a',NULL,'2026-11-20 02:30:59','«Recua» es la palabra en lengua mazahua para «burro». Escucha su pronunciación en mazahua y en español.'),
(90,'DEMO 0008','Dyecha','Diez',NULL,'/catalogo/0008_diez/imagen.jpg','/catalogo/0008_diez/audio_mazahua.m4a',NULL,'2026-11-20 02:30:59','«Dyecha» es la palabra en lengua mazahua para «diez». Escucha su pronunciación en mazahua y en español.'),
(91,'DEMO 0009','Ñgani','Pollo',NULL,'/catalogo/0009_pollo/imagen.jpg','/catalogo/0009_pollo/audio_mazahua.m4a',NULL,'2026-11-20 02:30:59','«Ñgani» es la palabra en lengua mazahua para «pollo». Escucha su pronunciación en mazahua y en español.'),
(92,'DEMO 0011','Dyoo','Perro',NULL,'/catalogo/0011_perro/imagen.jpg','/catalogo/0011_perro/audio_mazahua.m4a',NULL,'2026-11-20 02:30:59','«Dyoo» es la palabra en lengua mazahua para «perro». Escucha su pronunciación en mazahua y en español.'),
(93,'DEMO 0012','Mexa','Mesa',NULL,'/catalogo/0012_mesa/imagen.jpg','/catalogo/0012_mesa/audio_mazahua.m4a',NULL,'2026-11-20 02:30:59','«Mexa» es la palabra en lengua mazahua para «mesa». Escucha su pronunciación en mazahua y en español.'),
(94,'DEMO 0013','In chuzgo','Me llamo',NULL,'/catalogo/0013_mellamo/imagen.jpg','/catalogo/0013_mellamo/audio_mazahua.m4a',NULL,'2026-11-20 02:30:59','«In chuzgo» es la palabra en lengua mazahua para «me llamo». Escucha su pronunciación en mazahua y en español.'),
(95,'DEMO 0014','Kjimi','Hola',NULL,'/catalogo/0014_hola/imagen.jpg','/catalogo/0014_hola/audio_mazahua.m4a',NULL,'2026-11-20 02:30:59','«Kjimi» es la palabra en lengua mazahua para «hola». Escucha su pronunciación en mazahua y en español.'),
(96,'DEMO 0015','Jiasmaji','Buenos días',NULL,'/catalogo/0015_buenosdias/imagen.jpg','/catalogo/0015_buenosdias/audio_mazahua.m4a',NULL,'2026-11-20 02:30:59','«Jiasmaji» es la palabra en lengua mazahua para «buenos días». Escucha su pronunciación en mazahua y en español.'),
(97,'DEMO 0016','Ja bi chjenzha','Buenas tardes',NULL,'/catalogo/0016_buenastardes/imagen.jpg','/catalogo/0016_buenastardes/audio_mazahua.m4a',NULL,'2026-11-20 02:30:59','«Ja bi chjenzha» es la palabra en lengua mazahua para «buenas tardes». Escucha su pronunciación en mazahua y en español.'),
(98,'DEMO 0017','Tsökuaji','Buenas noches',NULL,'/catalogo/0017_buenasnoches/imagen.jpg','/catalogo/0017_buenasnoches/audio_mazahua.m4a',NULL,'2026-11-20 02:30:59','«Tsökuaji» es la palabra en lengua mazahua para «buenas noches». Escucha su pronunciación en mazahua y en español.'),
(99,'DEMO 0018','Maxa','Hasta luego',NULL,'/catalogo/0018_hastaluego/imagen.jpg','/catalogo/0018_hastaluego/audio_mazahua.m4a',NULL,'2026-11-20 02:30:59','«Maxa» es la palabra en lengua mazahua para «hasta luego». Escucha su pronunciación en mazahua y en español.'),
(100,'DEMO 0019','Jango jyasï','¿Cómo estás?',NULL,'/catalogo/0019_comoestas/imagen.jpg','/catalogo/0019_comoestas/audio_mazahua.m4a',NULL,'2026-11-20 02:30:59','«Jango jyasï» es la palabra en lengua mazahua para «¿cómo estás?». Escucha su pronunciación en mazahua y en español.'),
(101,'DEMO 0020','B’aga','Vaca',NULL,'/catalogo/0020_vaca/imagen.jpg','/catalogo/0020_vaca/audio_mazahua.m4a',NULL,'2026-11-20 02:30:59','«B’aga» es la palabra en lengua mazahua para «vaca». Escucha su pronunciación en mazahua y en español.'),
(102,'DEMO 0021','Tsjúú','Frijol',NULL,'/catalogo/0021_frijol/imagen.jpg','/catalogo/0021_frijol/audio_mazahua.m4a',NULL,'2026-11-20 02:30:59','«Tsjúú» es la palabra en lengua mazahua para «frijol». Escucha su pronunciación en mazahua y en español.'),
(103,'DEMO 0022','Trjöö','Maíz',NULL,'/catalogo/0022_maiz/imagen.jpg','/catalogo/0022_maiz/audio_mazahua.m4a',NULL,'2026-11-20 02:30:59','«Trjöö» es la palabra en lengua mazahua para «maíz». Escucha su pronunciación en mazahua y en español.'),
(104,'DEMO 0023','Sibi','Fuego/lumbre',NULL,'/catalogo/0023_fuego/imagen.jpg','/catalogo/0023_fuego/audio_mazahua.m4a',NULL,'2026-11-20 02:30:59','«Sibi» es la palabra en lengua mazahua para «fuego/lumbre». Escucha su pronunciación en mazahua y en español.'),
(105,'DEMO 0024','Skuama','Cuaderno',NULL,'/catalogo/0024_cuaderno/imagen.jpg','/catalogo/0024_cuaderno/audio_mazahua.m4a',NULL,'2026-11-20 02:30:59','«Skuama» es la palabra en lengua mazahua para «cuaderno». Escucha su pronunciación en mazahua y en español.'),
(106,'DEMO 0025','Tjujnú','Silla',NULL,'/catalogo/0025_silla/imagen.jpg','/catalogo/0025_silla/audio_mazahua.m4a',NULL,'2026-11-20 02:30:59','«Tjujnú» es la palabra en lengua mazahua para «silla». Escucha su pronunciación en mazahua y en español.'),
(107,'DEMO 0026','Ba’ni','Casa',NULL,'/catalogo/0026_casa/imagen.jpg','/catalogo/0026_casa/audio_mazahua.m4a',NULL,'2026-11-20 02:30:59','«Ba’ni» es la palabra en lengua mazahua para «casa». Escucha su pronunciación en mazahua y en español.'),
(108,'DEMO 0027','B’ezo','Hombre',NULL,'/catalogo/0027_hombre/imagen.jpg','/catalogo/0027_hombre/audio_mazahua.m4a',NULL,'2026-11-20 02:30:59','«B’ezo» es la palabra en lengua mazahua para «hombre». Escucha su pronunciación en mazahua y en español.'),
(109,'DEMO 0028','Ndixu','Mujer',NULL,'/catalogo/0028_mujer/imagen.jpg','/catalogo/0028_mujer/audio_mazahua.m4a',NULL,'2026-11-20 02:30:59','«Ndixu» es la palabra en lengua mazahua para «mujer». Escucha su pronunciación en mazahua y en español.'),
(110,'DEMO 0029','Tr’ii','Niño',NULL,'/catalogo/0029_niño/imagen.jpg','/catalogo/0029_niño/audio_mazahua.m4a',NULL,'2026-11-20 02:30:59','«Tr’ii» es la palabra en lengua mazahua para «niño». Escucha su pronunciación en mazahua y en español.'),
(111,'DEMO 0030','Xitr’i','Niña',NULL,'/catalogo/0030_niña/imagen.jpg','/catalogo/0030_niña/audio_mazahua.m4a',NULL,'2026-11-20 02:30:59','«Xitr’i» es la palabra en lengua mazahua para «niña». Escucha su pronunciación en mazahua y en español.'),
(112,'DEMO 0031','Ajense','Cielo',NULL,'/catalogo/0031_cielo/imagen.jpg','/catalogo/0031_cielo/audio_mazahua.m4a',NULL,'2026-11-20 02:30:59','«Ajense» es la palabra en lengua mazahua para «cielo». Escucha su pronunciación en mazahua y en español.'),
(113,'DEMO 0032','Miño','Coyote',NULL,'/catalogo/0032_coyote/imagen.jpg','/catalogo/0032_coyote/audio_mazahua.m4a',NULL,'2026-11-20 02:30:59','«Miño» es la palabra en lengua mazahua para «coyote». Escucha su pronunciación en mazahua y en español.'),
(114,'DEMO 0033','Pjiño','Hierba',NULL,'/catalogo/0033_hierba/imagen.jpg','/catalogo/0033_hierba/audio_mazahua.m4a',NULL,'2026-11-20 02:30:59','«Pjiño» es la palabra en lengua mazahua para «hierba». Escucha su pronunciación en mazahua y en español.'),
(115,'DEMO 0034','Trjomechi','Pan',NULL,'/catalogo/0034_pan/imagen.jpg','/catalogo/0034_pan/audio_mazahua.m4a',NULL,'2026-11-20 02:30:59','«Trjomechi» es la palabra en lengua mazahua para «pan». Escucha su pronunciación en mazahua y en español.'),
(116,'DEMO 0035','Ii','Chile',NULL,'/catalogo/0035_chile/imagen.jpg','/catalogo/0035_chile/audio_mazahua.m4a',NULL,'2026-11-20 02:30:59','«Ii» es la palabra en lengua mazahua para «chile». Escucha su pronunciación en mazahua y en español.'),
(117,'DEMO 0036','Dyatzi','Zapato',NULL,'/catalogo/0036_zapato/imagen.jpg','/catalogo/0036_zapato/audio_mazahua.m4a',NULL,'2026-11-20 02:30:59','«Dyatzi» es la palabra en lengua mazahua para «zapato». Escucha su pronunciación en mazahua y en español.'),
(118,'DEMO 0037','Xopute','Maestro',NULL,'/catalogo/0037_maestro/imagen.jpg','/catalogo/0037_maestro/audio_mazahua.m4a',NULL,'2026-11-20 02:30:59','«Xopute» es la palabra en lengua mazahua para «maestro». Escucha su pronunciación en mazahua y en español.'),
(119,'DEMO 0038','Ngunxorú','Escuela',NULL,'/catalogo/0038_escuela/imagen.jpg','/catalogo/0038_escuela/audio_mazahua.m4a',NULL,'2026-11-20 02:30:59','«Ngunxorú» es la palabra en lengua mazahua para «escuela». Escucha su pronunciación en mazahua y en español.'),
(120,'DEMO 0039','Muru','Huevo',NULL,'/catalogo/0039_huevo/imagen.jpg','/catalogo/0039_huevo/audio_mazahua.m4a',NULL,'2026-11-20 02:30:59','«Muru» es la palabra en lengua mazahua para «huevo». Escucha su pronunciación en mazahua y en español.'),
(121,'DEMO 0040','Nzee','Carne',NULL,'/catalogo/0040_carne/imagen.jpg','/catalogo/0040_carne/audio_mazahua.m4a',NULL,'2026-11-20 02:30:59','«Nzee» es la palabra en lengua mazahua para «carne». Escucha su pronunciación en mazahua y en español.'),
(122,'DEMO 0041','Inyo','Amigo',NULL,'/catalogo/0041_amigo/imagen.jpg','/catalogo/0041_amigo/audio_mazahua.m4a',NULL,'2026-11-20 02:30:59','«Inyo» es la palabra en lengua mazahua para «amigo». Escucha su pronunciación en mazahua y en español.'),
(123,'DEMO 0042','Ch’ii','Hijo',NULL,'/catalogo/0042_hijo/imagen.jpg','/catalogo/0042_hijo/audio_mazahua.m4a',NULL,'2026-11-20 02:30:59','«Ch’ii» es la palabra en lengua mazahua para «hijo». Escucha su pronunciación en mazahua y en español.'),
(124,'DEMO 0043','Chijue','Hija',NULL,'/catalogo/0043_hija/imagen.jpg','/catalogo/0043_hija/audio_mazahua.m4a',NULL,'2026-11-20 02:30:59','«Chijue» es la palabra en lengua mazahua para «hija». Escucha su pronunciación en mazahua y en español.'),
(125,'DEMO 0044','Jii','Bañarse',NULL,'/catalogo/0044_bañarse/imagen.jpg','/catalogo/0044_bañarse/audio_mazahua.m4a',NULL,'2026-11-20 02:30:59','«Jii» es la palabra en lengua mazahua para «bañarse». Escucha su pronunciación en mazahua y en español.'),
(126,'DEMO 0045','Xiñe','Lavarse las manos',NULL,'/catalogo/0045_lavarselasmanos/imagen.jpg','/catalogo/0045_lavarselasmanos/audio_mazahua.m4a',NULL,'2026-11-20 02:30:59','«Xiñe» es la palabra en lengua mazahua para «lavarse las manos». Escucha su pronunciación en mazahua y en español.'),
(127,'DEMO 0046','Kjojo','Hongos',NULL,'/catalogo/0046_hongos/imagen.jpg','/catalogo/0046_hongos/audio_mazahua.m4a',NULL,'2026-11-20 02:30:59','«Kjojo» es la palabra en lengua mazahua para «hongos». Escucha su pronunciación en mazahua y en español.'),
(128,'DEMO 0047','Zaa','Leña',NULL,'/catalogo/0047_leña/imagen.jpg','/catalogo/0047_leña/audio_mazahua.m4a',NULL,'2026-11-20 02:30:59','«Zaa» es la palabra en lengua mazahua para «leña». Escucha su pronunciación en mazahua y en español.'),
(129,'DEMO 0048','Kangua','Azul',NULL,'/catalogo/0048_azul/imagen.jpg','/catalogo/0048_azul/audio_mazahua.m4a',NULL,'2026-11-20 02:30:59','«Kangua» es la palabra en lengua mazahua para «azul». Escucha su pronunciación en mazahua y en español.'),
(130,'DEMO 0049','Mbezhe','Verde',NULL,'/catalogo/0049_verde/imagen.jpg','/catalogo/0049_verde/audio_mazahua.m4a',NULL,'2026-11-20 02:30:59','«Mbezhe» es la palabra en lengua mazahua para «verde». Escucha su pronunciación en mazahua y en español.'),
(131,'DEMO 0050','K’axt’u','Amarillo',NULL,'/catalogo/0050_amarillo/imagen.jpg','/catalogo/0050_amarillo/audio_mazahua.m4a',NULL,'2026-11-20 02:30:59','«K’axt’u» es la palabra en lengua mazahua para «amarillo». Escucha su pronunciación en mazahua y en español.'),
(132,'DEMO 0051','Mbaja','Rojo',NULL,'/catalogo/0051_rojo/imagen.jpg','/catalogo/0051_rojo/audio_mazahua.m4a',NULL,'2026-11-20 02:30:59','«Mbaja» es la palabra en lengua mazahua para «rojo». Escucha su pronunciación en mazahua y en español.'),
(133,'DEMO 0052','Naraxa','Naranja',NULL,'/catalogo/0052_naranja/imagen.jpg','/catalogo/0052_naranja/audio_mazahua.m4a',NULL,'2026-11-20 02:30:59','«Naraxa» es la palabra en lengua mazahua para «naranja». Escucha su pronunciación en mazahua y en español.'),
(134,'DEMO 0053','K’anga','Morado',NULL,'/catalogo/0053_morado/imagen.jpg','/catalogo/0053_morado/audio_mazahua.m4a',NULL,'2026-11-20 02:30:59','«K’anga» es la palabra en lengua mazahua para «morado». Escucha su pronunciación en mazahua y en español.'),
(135,'DEMO 0054','Ixki','Rosa',NULL,'/catalogo/0054_rosa/imagen.jpg','/catalogo/0054_rosa/audio_mazahua.m4a',NULL,'2026-11-20 02:30:59','«Ixki» es la palabra en lengua mazahua para «rosa». Escucha su pronunciación en mazahua y en español.');
/*!40000 ALTER TABLE `tarjetas_rfid` ENABLE KEYS */;
UNLOCK TABLES;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

