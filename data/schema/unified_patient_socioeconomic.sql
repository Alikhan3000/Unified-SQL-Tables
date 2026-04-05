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
-- Table structure for table `patient_socioeconomic`
--

DROP TABLE IF EXISTS `patient_socioeconomic`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `patient_socioeconomic` (
  `soc_id` bigint unsigned NOT NULL AUTO_INCREMENT COMMENT 'Surrogate key for this socioeconomic record; allows multiple time-stamped rows per patient.',
  `patient_id` bigint unsigned NOT NULL COMMENT 'Foreign key to patient_demographics.patient_id.',
  `effective_start_date` date NOT NULL COMMENT 'Date when this set of socioeconomic attributes became valid.',
  `effective_end_date` date DEFAULT NULL COMMENT 'Optional end date; NULL means the record is current.',
  `employment_status` varchar(50) DEFAULT NULL COMMENT 'Employment status (full-time, part-time, unemployed, student, retired, etc.).',
  `income_bracket` varchar(50) DEFAULT NULL COMMENT 'Income band for privacy (e.g., <25k, 25k-50k, etc.).',
  `education_level` varchar(100) DEFAULT NULL COMMENT 'Highest level of education completed.',
  `housing_status` varchar(100) DEFAULT NULL COMMENT 'Housing situation (stable, renting, homeless, shelter, at risk, unknown).',
  `household_size` int DEFAULT NULL COMMENT 'Number of people living in the same household.',
  `marital_status` varchar(50) DEFAULT NULL COMMENT 'Single, Married, Divorced, Widowed, Domestic partnership, etc.',
  `insurance_type` varchar(100) DEFAULT NULL COMMENT 'Primary payer category (Commercial, Medicare, Medicaid, Self-pay, etc.).',
  `food_insecurity_flag` tinyint(1) DEFAULT NULL COMMENT 'TRUE if patient is documented as food insecure.',
  `transportation_barrier_flag` tinyint(1) DEFAULT NULL COMMENT 'TRUE if patient reports transport barriers to accessing care.',
  `notes` text COMMENT 'Optional short summary of SDOH screening results or context (avoid PHI).',
  `created_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT 'When this socioeconomic record was first created.',
  `updated_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT 'Last time this record was updated.',
  PRIMARY KEY (`soc_id`),
  KEY `fk_socio_patient` (`patient_id`),
  CONSTRAINT `fk_socio_patient` FOREIGN KEY (`patient_id`) REFERENCES `patient_demographics` (`patient_id`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `patient_socioeconomic`
--

LOCK TABLES `patient_socioeconomic` WRITE;
/*!40000 ALTER TABLE `patient_socioeconomic` DISABLE KEYS */;
/*!40000 ALTER TABLE `patient_socioeconomic` ENABLE KEYS */;
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
