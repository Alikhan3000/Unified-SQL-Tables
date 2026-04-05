-- MySQL dump 10.13  Distrib 8.0.40, for Win64 (x86_64)
--
-- Host: 127.0.0.1    Database: unified
-- ------------------------------------------------------
-- Server version	8.0.40

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!50503 SET NAMES utf8 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Table structure for table `remote_device_reading`
--

DROP TABLE IF EXISTS `remote_device_reading`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `remote_device_reading` (
  `device_reading_id` bigint unsigned NOT NULL AUTO_INCREMENT COMMENT 'Surrogate key for each individual device reading.',
  `patient_id` bigint unsigned NOT NULL COMMENT 'Foreign key to patient_demographics.patient_id; links readings to a patient.',
  `device_id` varchar(100) NOT NULL COMMENT 'Logical identifier for the device in your platform.',
  `device_type` varchar(100) NOT NULL COMMENT 'General category (Smartwatch, Glucometer, BP cuff, Pulse oximeter, etc.).',
  `manufacturer` varchar(100) DEFAULT NULL COMMENT 'Device manufacturer (Apple, Fitbit, Omron, etc.).',
  `model` varchar(100) DEFAULT NULL COMMENT 'Device model name/number (e.g., Apple Watch Series 9).',
  `measurement_type` varchar(100) NOT NULL COMMENT 'What was measured (heart_rate, steps, systolic_bp, spo2, glucose, etc.).',
  `measurement_value` decimal(18,4) NOT NULL COMMENT 'Numeric value of the measurement (precision can be tuned).',
  `measurement_unit` varchar(50) DEFAULT NULL COMMENT 'Unit of measure (bpm, mmHg, mg/dL, kg, %, steps, etc.).',
  `measurement_time` datetime NOT NULL COMMENT 'Timestamp (preferably UTC) when the device recorded the measurement.',
  `ingestion_time` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT 'When your platform received the reading.',
  `data_quality_flag` varchar(50) DEFAULT NULL COMMENT 'Simple QA flag: OK, ESTIMATED, OUT_OF_RANGE, ARTIFACT, etc.',
  `source_system` varchar(100) DEFAULT NULL COMMENT 'Origin system (Apple HealthKit, Google Fit, Vendor API X, etc.).',
  `context_encounter_id` varchar(64) DEFAULT NULL COMMENT 'Optional ID for the encounter/telehealth session associated with this reading.',
  `raw_payload` json DEFAULT NULL COMMENT 'Optional raw JSON payload from the vendor/device for traceability.',
  `created_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT 'When this row was created in the DB.',
  `updated_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT 'Last time this record was updated.',
  PRIMARY KEY (`device_reading_id`),
  KEY `fk_device_patient` (`patient_id`),
  CONSTRAINT `fk_device_patient` FOREIGN KEY (`patient_id`) REFERENCES `patient_demographics` (`patient_id`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `remote_device_reading`
--

LOCK TABLES `remote_device_reading` WRITE;
/*!40000 ALTER TABLE `remote_device_reading` DISABLE KEYS */;
/*!40000 ALTER TABLE `remote_device_reading` ENABLE KEYS */;
UNLOCK TABLES;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2026-01-24 13:38:42
