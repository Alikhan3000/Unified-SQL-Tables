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
-- Table structure for table `ehr_encounter`
--

DROP TABLE IF EXISTS `ehr_encounter`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `ehr_encounter` (
  `encounter_id` bigint unsigned NOT NULL AUTO_INCREMENT COMMENT 'Unique identifier for each clinical encounter.',
  `patient_id` bigint unsigned NOT NULL COMMENT 'FK to patient_demographics.patient_id.',
  `encounter_type` varchar(100) NOT NULL COMMENT 'Inpatient, Outpatient, ED, Telehealth, Urgent Care, etc.',
  `encounter_start` datetime NOT NULL COMMENT 'Start time of the encounter.',
  `encounter_end` datetime DEFAULT NULL COMMENT 'End time of the encounter; NULL if ongoing.',
  `provider_id` varchar(64) DEFAULT NULL COMMENT 'Optional provider identifier from EHR.',
  `facility` varchar(200) DEFAULT NULL COMMENT 'Hospital or clinic where encounter occurred.',
  `chief_complaint` varchar(255) DEFAULT NULL COMMENT 'Primary reason for visit.',
  `notes` text COMMENT 'Optional clinical notes (avoid PHI in analytics).',
  `created_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`encounter_id`),
  KEY `fk_ehr_patient` (`patient_id`),
  CONSTRAINT `fk_ehr_patient` FOREIGN KEY (`patient_id`) REFERENCES `patient_demographics` (`patient_id`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `ehr_encounter`
--

LOCK TABLES `ehr_encounter` WRITE;
/*!40000 ALTER TABLE `ehr_encounter` DISABLE KEYS */;
/*!40000 ALTER TABLE `ehr_encounter` ENABLE KEYS */;
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
