-- ============================================================================
-- Lotería Interactiva Mazahua · BASE DE DATOS — MariaDB / MySQL
-- ----------------------------------------------------------------------------
-- Contiene tus datos (respaldo del 27/10/2026) y el material Loteria_Mazahua
-- (54 audios en español grabados; tortilla = T'zeyi), organizados así:
--
--   tarjetas ........... TABLA ÚNICA de las tarjetas: numero, nombre_espanol,
--                        nombre_mazahua, descripcion, imagen, audio_mazahua,
--                        audio_espanol (rutas de los archivos) y uid_rfid (opcional)
--   usuarios ........... cuentas de docentes (nombre, correo, contraseña con hash, fecha)
--   partidas ........... código de acceso, nombre, límite, estado, fecha  (FK → usuarios)
--   participantes ...... alumnos de cada partida, su avatar y fecha de ingreso (FK → partidas)
--   tableros ........... tablero de cada alumno                           (FK → participantes)
--   tablero_tarjetas ... las 16 cartas de cada tablero y si están marcadas (FK → tableros, tarjetas)
--   anuncios ........... cartas cantadas en cada partida                  (FK → partidas, tarjetas)
--   sesiones ........... sesiones abiertas de los docentes (se llena sola)
--   recuperaciones_password ... enlaces temporales de recuperación (solo su hash)
--
-- Las imágenes y audios son ARCHIVOS (carpetas catalogo/ y uploads/); la tabla
-- tarjetas guarda su ruta. No trae cuentas: cada docente crea la suya en /acceso.
--
-- IMPORTAR: phpMyAdmin → Importar → este archivo → Importar.
-- ATENCIÓN: reemplaza las tablas de loteria_mazahua.
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
DROP TABLE IF EXISTS `anuncios`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `anuncios` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `partida_id` int(11) NOT NULL,
  `tarjeta_id` int(11) NOT NULL,
  `fecha` datetime NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `ux_anuncio_partida_tarjeta` (`partida_id`,`tarjeta_id`),
  KEY `tarjeta_id` (`tarjeta_id`),
  KEY `ix_anuncios_partida_id` (`partida_id`),
  CONSTRAINT `anuncios_ibfk_1` FOREIGN KEY (`partida_id`) REFERENCES `partidas` (`id`) ON DELETE CASCADE,
  CONSTRAINT `anuncios_ibfk_2` FOREIGN KEY (`tarjeta_id`) REFERENCES `tarjetas` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=89 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

LOCK TABLES `anuncios` WRITE;
/*!40000 ALTER TABLE `anuncios` DISABLE KEYS */;
INSERT INTO `anuncios` VALUES
(33,12,5,'2026-11-21 00:51:30'),
(34,12,6,'2026-11-21 00:51:30'),
(87,21,5,'2026-11-21 00:51:30'),
(88,21,6,'2026-11-21 00:51:30');
/*!40000 ALTER TABLE `anuncios` ENABLE KEYS */;
UNLOCK TABLES;
DROP TABLE IF EXISTS `participantes`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `participantes` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `partida_id` int(11) NOT NULL,
  `nombre` varchar(60) NOT NULL,
  `dispositivo` varchar(36) NOT NULL,
  `fecha_ingreso` datetime NOT NULL,
  `gano` tinyint(1) NOT NULL DEFAULT 0,
  `avatar` varchar(60) DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `ux_participante_dispositivo` (`partida_id`,`dispositivo`),
  KEY `ix_participantes_partida_id` (`partida_id`),
  CONSTRAINT `participantes_ibfk_1` FOREIGN KEY (`partida_id`) REFERENCES `partidas` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=78 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

LOCK TABLES `participantes` WRITE;
/*!40000 ALTER TABLE `participantes` DISABLE KEYS */;
INSERT INTO `participantes` VALUES
(62,10,'Jose','71403dd2-72cd-40cd-916a-b9aac0eb106e','2026-10-24 02:47:10',0,NULL),
(63,12,'Jose','596dbaa4-a0c4-4a0b-b366-fbefa75c4376','2026-10-24 02:51:53',0,NULL),
(75,21,'Angeles','573e2e6e-f6cb-41f5-9205-d8f46d383bc8','2026-10-25 17:45:24',0,NULL),
(76,21,'Jose','4cee429f-587f-4cd3-9dae-2212d9fd1d18','2026-10-25 17:45:39',0,NULL),
(77,21,'Rosaura','32aa7276-d351-4516-aed0-670a6d002a45','2026-10-25 17:46:06',0,NULL);
/*!40000 ALTER TABLE `participantes` ENABLE KEYS */;
UNLOCK TABLES;
DROP TABLE IF EXISTS `partidas`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `partidas` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `codigo` varchar(6) NOT NULL,
  `nombre` varchar(100) NOT NULL,
  `usuario_id` int(11) DEFAULT NULL,
  `limite` int(11) NOT NULL DEFAULT 25,
  `estado` varchar(16) NOT NULL,
  `fecha_creacion` datetime NOT NULL,
  `iniciada` datetime DEFAULT NULL,
  `finalizada` datetime DEFAULT NULL,
  `ultima_tarjeta_id` int(11) DEFAULT NULL,
  `secuencia` int(11) NOT NULL DEFAULT 0,
  `ultima_actividad_docente` datetime DEFAULT NULL,
  `cierre_motivo` varchar(30) DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `codigo` (`codigo`),
  KEY `ultima_tarjeta_id` (`ultima_tarjeta_id`),
  KEY `ix_partidas_usuario_id` (`usuario_id`),
  CONSTRAINT `partidas_ibfk_1` FOREIGN KEY (`usuario_id`) REFERENCES `usuarios` (`id`) ON DELETE SET NULL,
  CONSTRAINT `partidas_ibfk_2` FOREIGN KEY (`ultima_tarjeta_id`) REFERENCES `tarjetas` (`id`) ON DELETE SET NULL
) ENGINE=InnoDB AUTO_INCREMENT=22 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

LOCK TABLES `partidas` WRITE;
/*!40000 ALTER TABLE `partidas` DISABLE KEYS */;
INSERT INTO `partidas` VALUES
(10,'BFBSR8','Partida BFBSR8',NULL,25,'finalizada','2026-10-24 02:46:07','2026-10-24 02:47:15','2026-11-20 02:30:59',NULL,0,NULL,'duracion_maxima'),
(12,'NTCNX5','Partida NTCNX5',NULL,25,'finalizada','2026-10-24 02:51:18','2026-10-24 02:51:58','2026-11-20 02:30:59',NULL,0,NULL,'duracion_maxima'),
(21,'C2GYRD','Partida C2GYRD',NULL,3,'finalizada','2026-10-25 17:43:21','2026-10-25 17:46:14','2026-11-20 02:30:59',5,3,NULL,'duracion_maxima');
/*!40000 ALTER TABLE `partidas` ENABLE KEYS */;
UNLOCK TABLES;
DROP TABLE IF EXISTS `recuperaciones_password`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `recuperaciones_password` (
  `token_hash` varchar(64) NOT NULL,
  `usuario_id` int(11) NOT NULL,
  `creada` datetime NOT NULL,
  `vence` datetime NOT NULL,
  PRIMARY KEY (`token_hash`),
  KEY `ix_recuperaciones_password_usuario_id` (`usuario_id`),
  KEY `ix_recuperaciones_password_vence` (`vence`),
  CONSTRAINT `recuperaciones_password_ibfk_1` FOREIGN KEY (`usuario_id`) REFERENCES `usuarios` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

LOCK TABLES `recuperaciones_password` WRITE;
/*!40000 ALTER TABLE `recuperaciones_password` DISABLE KEYS */;
/*!40000 ALTER TABLE `recuperaciones_password` ENABLE KEYS */;
UNLOCK TABLES;
DROP TABLE IF EXISTS `sesiones`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `sesiones` (
  `jti` varchar(64) NOT NULL,
  `usuario_id` int(11) NOT NULL,
  `vence` datetime NOT NULL,
  PRIMARY KEY (`jti`),
  KEY `ix_sesiones_vence` (`vence`),
  KEY `ix_sesiones_usuario_id` (`usuario_id`),
  CONSTRAINT `sesiones_ibfk_1` FOREIGN KEY (`usuario_id`) REFERENCES `usuarios` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

LOCK TABLES `sesiones` WRITE;
/*!40000 ALTER TABLE `sesiones` DISABLE KEYS */;
/*!40000 ALTER TABLE `sesiones` ENABLE KEYS */;
UNLOCK TABLES;
DROP TABLE IF EXISTS `tablero_tarjetas`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `tablero_tarjetas` (
  `tablero_id` int(11) NOT NULL,
  `posicion` int(11) NOT NULL,
  `tarjeta_id` int(11) NOT NULL,
  `marcada` tinyint(1) NOT NULL DEFAULT 0,
  PRIMARY KEY (`tablero_id`,`posicion`),
  KEY `ix_tablero_tarjetas_tarjeta_id` (`tarjeta_id`),
  CONSTRAINT `tablero_tarjetas_ibfk_1` FOREIGN KEY (`tablero_id`) REFERENCES `tableros` (`id`) ON DELETE CASCADE,
  CONSTRAINT `tablero_tarjetas_ibfk_2` FOREIGN KEY (`tarjeta_id`) REFERENCES `tarjetas` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

LOCK TABLES `tablero_tarjetas` WRITE;
/*!40000 ALTER TABLE `tablero_tarjetas` DISABLE KEYS */;
INSERT INTO `tablero_tarjetas` VALUES
(16,8,5,0),
(17,9,6,1);
/*!40000 ALTER TABLE `tablero_tarjetas` ENABLE KEYS */;
UNLOCK TABLES;
DROP TABLE IF EXISTS `tableros`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `tableros` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `participante_id` int(11) NOT NULL,
  `creado` datetime NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `participante_id` (`participante_id`),
  CONSTRAINT `tableros_ibfk_1` FOREIGN KEY (`participante_id`) REFERENCES `participantes` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=19 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

LOCK TABLES `tableros` WRITE;
/*!40000 ALTER TABLE `tableros` DISABLE KEYS */;
INSERT INTO `tableros` VALUES
(5,63,'2026-11-21 00:51:30'),
(16,75,'2026-11-21 00:51:30'),
(17,76,'2026-11-21 00:51:30'),
(18,77,'2026-11-21 00:51:30');
/*!40000 ALTER TABLE `tableros` ENABLE KEYS */;
UNLOCK TABLES;
DROP TABLE IF EXISTS `tarjetas`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `tarjetas` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `numero` int(11) DEFAULT NULL,
  `nombre_espanol` varchar(150) NOT NULL,
  `nombre_mazahua` varchar(150) NOT NULL,
  `descripcion` text DEFAULT NULL,
  `imagen` varchar(255) DEFAULT NULL,
  `audio_mazahua` varchar(255) DEFAULT NULL,
  `audio_espanol` varchar(255) DEFAULT NULL,
  `uid_rfid` varchar(40) DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `numero` (`numero`),
  UNIQUE KEY `uid_rfid` (`uid_rfid`)
) ENGINE=InnoDB AUTO_INCREMENT=136 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

LOCK TABLES `tarjetas` WRITE;
/*!40000 ALTER TABLE `tarjetas` DISABLE KEYS */;
INSERT INTO `tarjetas` VALUES
(5,10,'Gato','Mixi','«Mixi» es la palabra en lengua mazahua para «gato». Escucha su pronunciación en mazahua y en español.','/catalogo/0010_gato/imagen.jpg','/catalogo/0010_gato/audio_mazahua.m4a','/catalogo/0010_gato/audio_espanol.m4a','F9 DB 91 10'),
(6,NULL,'gallo','gaoo','«gaoo» es la palabra en lengua mazahua para «gallo». Escucha su pronunciación en mazahua y en español.','/uploads/imagenes/901207ce2747487599fbfcfaca76160c.png','/uploads/audios/e7071e3500014e5aaae9dcde3bbb5cab.mp3','/uploads/audios/388ce86366e2414ca726ecb89dcca02b.mp3','A9 DD 25 10'),
(83,1,'Uno','Naja','«Naja» es la palabra en lengua mazahua para «uno». Escucha su pronunciación en mazahua y en español.','/catalogo/0001_uno/imagen.jpg','/catalogo/0001_uno/audio_mazahua.m4a','/catalogo/0001_uno/audio_espanol.m4a','DEMO 0001'),
(84,2,'Dos','Yeje','«Yeje» es la palabra en lengua mazahua para «dos». Escucha su pronunciación en mazahua y en español.','/catalogo/0002_dos/imagen.jpg','/catalogo/0002_dos/audio_mazahua.m4a','/catalogo/0002_dos/audio_espanol.m4a','DEMO 0002'),
(85,3,'Tres','Jñi','«Jñi» es la palabra en lengua mazahua para «tres». Escucha su pronunciación en mazahua y en español.','/catalogo/0003_tres/imagen.jpg','/catalogo/0003_tres/audio_mazahua.m4a','/catalogo/0003_tres/audio_espanol.m4a','DEMO 0003'),
(86,4,'Cuatro','Nziyo','«Nziyo» es la palabra en lengua mazahua para «cuatro». Escucha su pronunciación en mazahua y en español.','/catalogo/0004_cuatro/imagen.jpg','/catalogo/0004_cuatro/audio_mazahua.m4a','/catalogo/0004_cuatro/audio_espanol.m4a','DEMO 0004'),
(87,5,'Cinco','Tsicha','«Tsicha» es la palabra en lengua mazahua para «cinco». Escucha su pronunciación en mazahua y en español.','/catalogo/0005_cinco/imagen.jpg','/catalogo/0005_cinco/audio_mazahua.m4a','/catalogo/0005_cinco/audio_espanol.m4a','DEMO 0005'),
(88,6,'Tortilla','T\'zeyi','«T\'zeyi» es la palabra en lengua mazahua para «tortilla». Escucha su pronunciación en mazahua y en español.','/catalogo/0006_tortilla/imagen.png','/catalogo/0006_tortilla/audio_mazahua.m4a','/catalogo/0006_tortilla/audio_espanol.m4a','DEMO 0006'),
(89,7,'Burro','Recua','«Recua» es la palabra en lengua mazahua para «burro». Escucha su pronunciación en mazahua y en español.','/catalogo/0007_burro/imagen.jpg','/catalogo/0007_burro/audio_mazahua.m4a','/catalogo/0007_burro/audio_espanol.m4a','DEMO 0007'),
(90,8,'Diez','Dyecha','«Dyecha» es la palabra en lengua mazahua para «diez». Escucha su pronunciación en mazahua y en español.','/catalogo/0008_diez/imagen.jpg','/catalogo/0008_diez/audio_mazahua.m4a','/catalogo/0008_diez/audio_espanol.m4a','DEMO 0008'),
(91,9,'Pollo','Ñgani','«Ñgani» es la palabra en lengua mazahua para «pollo». Escucha su pronunciación en mazahua y en español.','/catalogo/0009_pollo/imagen.jpg','/catalogo/0009_pollo/audio_mazahua.m4a','/catalogo/0009_pollo/audio_espanol.m4a','DEMO 0009'),
(92,11,'Perro','Dyoo','«Dyoo» es la palabra en lengua mazahua para «perro». Escucha su pronunciación en mazahua y en español.','/catalogo/0011_perro/imagen.jpg','/catalogo/0011_perro/audio_mazahua.m4a','/catalogo/0011_perro/audio_espanol.m4a','DEMO 0011'),
(93,12,'Mesa','Mexa','«Mexa» es la palabra en lengua mazahua para «mesa». Escucha su pronunciación en mazahua y en español.','/catalogo/0012_mesa/imagen.jpg','/catalogo/0012_mesa/audio_mazahua.m4a','/catalogo/0012_mesa/audio_espanol.m4a','DEMO 0012'),
(94,13,'Me llamo','In chuzgo','«In chuzgo» es la palabra en lengua mazahua para «me llamo». Escucha su pronunciación en mazahua y en español.','/catalogo/0013_mellamo/imagen.jpg','/catalogo/0013_mellamo/audio_mazahua.m4a','/catalogo/0013_mellamo/audio_espanol.m4a','DEMO 0013'),
(95,14,'Hola','Kjimi','«Kjimi» es la palabra en lengua mazahua para «hola». Escucha su pronunciación en mazahua y en español.','/catalogo/0014_hola/imagen.jpg','/catalogo/0014_hola/audio_mazahua.m4a','/catalogo/0014_hola/audio_espanol.m4a','DEMO 0014'),
(96,15,'Buenos días','Jiasmaji','«Jiasmaji» es la palabra en lengua mazahua para «buenos días». Escucha su pronunciación en mazahua y en español.','/catalogo/0015_buenosdias/imagen.jpg','/catalogo/0015_buenosdias/audio_mazahua.m4a','/catalogo/0015_buenosdias/audio_espanol.m4a','DEMO 0015'),
(97,16,'Buenas tardes','Ja bi chjenzha','«Ja bi chjenzha» es la palabra en lengua mazahua para «buenas tardes». Escucha su pronunciación en mazahua y en español.','/catalogo/0016_buenastardes/imagen.jpg','/catalogo/0016_buenastardes/audio_mazahua.m4a','/catalogo/0016_buenastardes/audio_espanol.m4a','DEMO 0016'),
(98,17,'Buenas noches','Tsökuaji','«Tsökuaji» es la palabra en lengua mazahua para «buenas noches». Escucha su pronunciación en mazahua y en español.','/catalogo/0017_buenasnoches/imagen.jpg','/catalogo/0017_buenasnoches/audio_mazahua.m4a','/catalogo/0017_buenasnoches/audio_espanol.m4a','DEMO 0017'),
(99,18,'Hasta luego','Maxa','«Maxa» es la palabra en lengua mazahua para «hasta luego». Escucha su pronunciación en mazahua y en español.','/catalogo/0018_hastaluego/imagen.jpg','/catalogo/0018_hastaluego/audio_mazahua.m4a','/catalogo/0018_hastaluego/audio_espanol.m4a','DEMO 0018'),
(100,19,'¿Cómo estás?','Jango jyasï','«Jango jyasï» es la palabra en lengua mazahua para «¿cómo estás?». Escucha su pronunciación en mazahua y en español.','/catalogo/0019_comoestas/imagen.jpg','/catalogo/0019_comoestas/audio_mazahua.m4a','/catalogo/0019_comoestas/audio_espanol.m4a','DEMO 0019'),
(101,20,'Vaca','B’aga','«B’aga» es la palabra en lengua mazahua para «vaca». Escucha su pronunciación en mazahua y en español.','/catalogo/0020_vaca/imagen.jpg','/catalogo/0020_vaca/audio_mazahua.m4a','/catalogo/0020_vaca/audio_espanol.m4a','DEMO 0020'),
(102,21,'Frijol','Tsjúú','«Tsjúú» es la palabra en lengua mazahua para «frijol». Escucha su pronunciación en mazahua y en español.','/catalogo/0021_frijol/imagen.jpg','/catalogo/0021_frijol/audio_mazahua.m4a','/catalogo/0021_frijol/audio_espanol.m4a','DEMO 0021'),
(103,22,'Maíz','Trjöö','«Trjöö» es la palabra en lengua mazahua para «maíz». Escucha su pronunciación en mazahua y en español.','/catalogo/0022_maiz/imagen.jpg','/catalogo/0022_maiz/audio_mazahua.m4a','/catalogo/0022_maiz/audio_espanol.m4a','DEMO 0022'),
(104,23,'Fuego/lumbre','Sibi','«Sibi» es la palabra en lengua mazahua para «fuego/lumbre». Escucha su pronunciación en mazahua y en español.','/catalogo/0023_fuego/imagen.jpg','/catalogo/0023_fuego/audio_mazahua.m4a','/catalogo/0023_fuego/audio_espanol.m4a','DEMO 0023'),
(105,24,'Cuaderno','Skuama','«Skuama» es la palabra en lengua mazahua para «cuaderno». Escucha su pronunciación en mazahua y en español.','/catalogo/0024_cuaderno/imagen.jpg','/catalogo/0024_cuaderno/audio_mazahua.m4a','/catalogo/0024_cuaderno/audio_espanol.m4a','DEMO 0024'),
(106,25,'Silla','Tjujnú','«Tjujnú» es la palabra en lengua mazahua para «silla». Escucha su pronunciación en mazahua y en español.','/catalogo/0025_silla/imagen.jpg','/catalogo/0025_silla/audio_mazahua.m4a','/catalogo/0025_silla/audio_espanol.m4a','DEMO 0025'),
(107,26,'Casa','Ba’ni','«Ba’ni» es la palabra en lengua mazahua para «casa». Escucha su pronunciación en mazahua y en español.','/catalogo/0026_casa/imagen.jpg','/catalogo/0026_casa/audio_mazahua.m4a','/catalogo/0026_casa/audio_espanol.m4a','DEMO 0026'),
(108,27,'Hombre','B’ezo','«B’ezo» es la palabra en lengua mazahua para «hombre». Escucha su pronunciación en mazahua y en español.','/catalogo/0027_hombre/imagen.jpg','/catalogo/0027_hombre/audio_mazahua.m4a','/catalogo/0027_hombre/audio_espanol.m4a','DEMO 0027'),
(109,28,'Mujer','Ndixu','«Ndixu» es la palabra en lengua mazahua para «mujer». Escucha su pronunciación en mazahua y en español.','/catalogo/0028_mujer/imagen.jpg','/catalogo/0028_mujer/audio_mazahua.m4a','/catalogo/0028_mujer/audio_espanol.m4a','DEMO 0028'),
(110,29,'Niño','Tr’ii','«Tr’ii» es la palabra en lengua mazahua para «niño». Escucha su pronunciación en mazahua y en español.','/catalogo/0029_nino/imagen.jpg','/catalogo/0029_nino/audio_mazahua.m4a','/catalogo/0029_nino/audio_espanol.m4a','DEMO 0029'),
(111,30,'Niña','Xitr’i','«Xitr’i» es la palabra en lengua mazahua para «niña». Escucha su pronunciación en mazahua y en español.','/catalogo/0030_nina/imagen.jpg','/catalogo/0030_nina/audio_mazahua.m4a','/catalogo/0030_nina/audio_espanol.m4a','DEMO 0030'),
(112,31,'Cielo','Ajense','«Ajense» es la palabra en lengua mazahua para «cielo». Escucha su pronunciación en mazahua y en español.','/catalogo/0031_cielo/imagen.jpg','/catalogo/0031_cielo/audio_mazahua.m4a','/catalogo/0031_cielo/audio_espanol.m4a','DEMO 0031'),
(113,32,'Coyote','Miño','«Miño» es la palabra en lengua mazahua para «coyote». Escucha su pronunciación en mazahua y en español.','/catalogo/0032_coyote/imagen.jpg','/catalogo/0032_coyote/audio_mazahua.m4a','/catalogo/0032_coyote/audio_espanol.m4a','DEMO 0032'),
(114,33,'Hierba','Pjiño','«Pjiño» es la palabra en lengua mazahua para «hierba». Escucha su pronunciación en mazahua y en español.','/catalogo/0033_hierba/imagen.jpg','/catalogo/0033_hierba/audio_mazahua.m4a','/catalogo/0033_hierba/audio_espanol.m4a','DEMO 0033'),
(115,34,'Pan','Trjomechi','«Trjomechi» es la palabra en lengua mazahua para «pan». Escucha su pronunciación en mazahua y en español.','/catalogo/0034_pan/imagen.jpg','/catalogo/0034_pan/audio_mazahua.m4a','/catalogo/0034_pan/audio_espanol.m4a','DEMO 0034'),
(116,35,'Chile','Ii','«Ii» es la palabra en lengua mazahua para «chile». Escucha su pronunciación en mazahua y en español.','/catalogo/0035_chile/imagen.jpg','/catalogo/0035_chile/audio_mazahua.m4a','/catalogo/0035_chile/audio_espanol.m4a','DEMO 0035'),
(117,36,'Zapato','Dyatzi','«Dyatzi» es la palabra en lengua mazahua para «zapato». Escucha su pronunciación en mazahua y en español.','/catalogo/0036_zapato/imagen.jpg','/catalogo/0036_zapato/audio_mazahua.m4a','/catalogo/0036_zapato/audio_espanol.m4a','DEMO 0036'),
(118,37,'Maestro','Xopute','«Xopute» es la palabra en lengua mazahua para «maestro». Escucha su pronunciación en mazahua y en español.','/catalogo/0037_maestro/imagen.jpg','/catalogo/0037_maestro/audio_mazahua.m4a','/catalogo/0037_maestro/audio_espanol.m4a','DEMO 0037'),
(119,38,'Escuela','Ngunxorú','«Ngunxorú» es la palabra en lengua mazahua para «escuela». Escucha su pronunciación en mazahua y en español.','/catalogo/0038_escuela/imagen.jpg','/catalogo/0038_escuela/audio_mazahua.m4a','/catalogo/0038_escuela/audio_espanol.m4a','DEMO 0038'),
(120,39,'Huevo','Muru','«Muru» es la palabra en lengua mazahua para «huevo». Escucha su pronunciación en mazahua y en español.','/catalogo/0039_huevo/imagen.jpg','/catalogo/0039_huevo/audio_mazahua.m4a','/catalogo/0039_huevo/audio_espanol.m4a','DEMO 0039'),
(121,40,'Carne','Nzee','«Nzee» es la palabra en lengua mazahua para «carne». Escucha su pronunciación en mazahua y en español.','/catalogo/0040_carne/imagen.jpg','/catalogo/0040_carne/audio_mazahua.m4a','/catalogo/0040_carne/audio_espanol.m4a','DEMO 0040'),
(122,41,'Amigo','Inyo','«Inyo» es la palabra en lengua mazahua para «amigo». Escucha su pronunciación en mazahua y en español.','/catalogo/0041_amigo/imagen.jpg','/catalogo/0041_amigo/audio_mazahua.m4a','/catalogo/0041_amigo/audio_espanol.m4a','DEMO 0041'),
(123,42,'Hijo','Ch’ii','«Ch’ii» es la palabra en lengua mazahua para «hijo». Escucha su pronunciación en mazahua y en español.','/catalogo/0042_hijo/imagen.jpg','/catalogo/0042_hijo/audio_mazahua.m4a','/catalogo/0042_hijo/audio_espanol.m4a','DEMO 0042'),
(124,43,'Hija','Chijue','«Chijue» es la palabra en lengua mazahua para «hija». Escucha su pronunciación en mazahua y en español.','/catalogo/0043_hija/imagen.jpg','/catalogo/0043_hija/audio_mazahua.m4a','/catalogo/0043_hija/audio_espanol.m4a','DEMO 0043'),
(125,44,'Bañarse','Jii','«Jii» es la palabra en lengua mazahua para «bañarse». Escucha su pronunciación en mazahua y en español.','/catalogo/0044_banarse/imagen.jpg','/catalogo/0044_banarse/audio_mazahua.m4a','/catalogo/0044_banarse/audio_espanol.m4a','DEMO 0044'),
(126,45,'Lavarse las manos','Xiñe','«Xiñe» es la palabra en lengua mazahua para «lavarse las manos». Escucha su pronunciación en mazahua y en español.','/catalogo/0045_lavarselasmanos/imagen.jpg','/catalogo/0045_lavarselasmanos/audio_mazahua.m4a','/catalogo/0045_lavarselasmanos/audio_espanol.m4a','DEMO 0045'),
(127,46,'Hongos','Kjojo','«Kjojo» es la palabra en lengua mazahua para «hongos». Escucha su pronunciación en mazahua y en español.','/catalogo/0046_hongos/imagen.jpg','/catalogo/0046_hongos/audio_mazahua.m4a','/catalogo/0046_hongos/audio_espanol.m4a','DEMO 0046'),
(128,47,'Leña','Zaa','«Zaa» es la palabra en lengua mazahua para «leña». Escucha su pronunciación en mazahua y en español.','/catalogo/0047_lena/imagen.jpg','/catalogo/0047_lena/audio_mazahua.m4a','/catalogo/0047_lena/audio_espanol.m4a','DEMO 0047'),
(129,48,'Azul','Kangua','«Kangua» es la palabra en lengua mazahua para «azul». Escucha su pronunciación en mazahua y en español.','/catalogo/0048_azul/imagen.jpg','/catalogo/0048_azul/audio_mazahua.m4a','/catalogo/0048_azul/audio_espanol.m4a','DEMO 0048'),
(130,49,'Verde','Mbezhe','«Mbezhe» es la palabra en lengua mazahua para «verde». Escucha su pronunciación en mazahua y en español.','/catalogo/0049_verde/imagen.jpg','/catalogo/0049_verde/audio_mazahua.m4a','/catalogo/0049_verde/audio_espanol.m4a','DEMO 0049'),
(131,50,'Amarillo','K’axt’u','«K’axt’u» es la palabra en lengua mazahua para «amarillo». Escucha su pronunciación en mazahua y en español.','/catalogo/0050_amarillo/imagen.jpg','/catalogo/0050_amarillo/audio_mazahua.m4a','/catalogo/0050_amarillo/audio_espanol.m4a','DEMO 0050'),
(132,51,'Rojo','Mbaja','«Mbaja» es la palabra en lengua mazahua para «rojo». Escucha su pronunciación en mazahua y en español.','/catalogo/0051_rojo/imagen.jpg','/catalogo/0051_rojo/audio_mazahua.m4a','/catalogo/0051_rojo/audio_espanol.m4a','DEMO 0051'),
(133,52,'Naranja','Naraxa','«Naraxa» es la palabra en lengua mazahua para «naranja». Escucha su pronunciación en mazahua y en español.','/catalogo/0052_naranja/imagen.jpg','/catalogo/0052_naranja/audio_mazahua.m4a','/catalogo/0052_naranja/audio_espanol.m4a','DEMO 0052'),
(134,53,'Morado','K’anga','«K’anga» es la palabra en lengua mazahua para «morado». Escucha su pronunciación en mazahua y en español.','/catalogo/0053_morado/imagen.jpg','/catalogo/0053_morado/audio_mazahua.m4a','/catalogo/0053_morado/audio_espanol.m4a','DEMO 0053'),
(135,54,'Rosa','Ixki','«Ixki» es la palabra en lengua mazahua para «rosa». Escucha su pronunciación en mazahua y en español.','/catalogo/0054_rosa/imagen.jpg','/catalogo/0054_rosa/audio_mazahua.m4a','/catalogo/0054_rosa/audio_espanol.m4a','DEMO 0054');
/*!40000 ALTER TABLE `tarjetas` ENABLE KEYS */;
UNLOCK TABLES;
DROP TABLE IF EXISTS `usuarios`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `usuarios` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `nombre` varchar(100) NOT NULL,
  `correo` varchar(254) NOT NULL,
  `password_hash` varchar(255) NOT NULL,
  `fecha_registro` datetime NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `correo` (`correo`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

LOCK TABLES `usuarios` WRITE;
/*!40000 ALTER TABLE `usuarios` DISABLE KEYS */;
/*!40000 ALTER TABLE `usuarios` ENABLE KEYS */;
UNLOCK TABLES;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

