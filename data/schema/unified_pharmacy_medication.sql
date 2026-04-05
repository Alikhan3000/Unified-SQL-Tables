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
-- Table structure for table `pharmacy_medication`
--

DROP TABLE IF EXISTS `pharmacy_medication`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `pharmacy_medication` (
  `medication_id` bigint unsigned NOT NULL AUTO_INCREMENT COMMENT 'Unique identifier for each medication record.',
  `patient_id` bigint unsigned NOT NULL COMMENT 'FK to patient_demographics.patient_id.',
  `medication_name` varchar(200) NOT NULL COMMENT 'Drug name (generic or brand).',
  `ndc_code` varchar(20) DEFAULT NULL COMMENT 'National Drug Code if available.',
  `dosage` varchar(100) DEFAULT NULL COMMENT 'Dosage instructions (e.g., 10 mg).',
  `route` varchar(50) DEFAULT NULL COMMENT 'Oral, IV, IM, Subcutaneous, etc.',
  `frequency` varchar(50) DEFAULT NULL COMMENT 'How often the medication is taken.',
  `quantity` int DEFAULT NULL COMMENT 'Quantity dispensed.',
  `days_supply` int DEFAULT NULL COMMENT 'Number of days the medication should last.',
  `prescribing_provider` varchar(100) DEFAULT NULL COMMENT 'Provider who prescribed the medication.',
  `fill_date` date DEFAULT NULL COMMENT 'Date the prescription was filled.',
  `created_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`medication_id`),
  KEY `fk_med_patient` (`patient_id`),
  CONSTRAINT `fk_med_patient` FOREIGN KEY (`patient_id`) REFERENCES `patient_demographics` (`patient_id`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `pharmacy_medication`
--

LOCK TABLES `pharmacy_medication` WRITE;
/*!40000 ALTER TABLE `pharmacy_medication` DISABLE KEYS */;
/*!40000 ALTER TABLE `pharmacy_medication` ENABLE KEYS */;
UNLOCK TABLES;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2026-01-24 13:41:42
