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
-- Table structure for table `patient_demographics`
--

DROP TABLE IF EXISTS `patient_demographics`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `patient_demographics` (
  `patient_id` bigint unsigned NOT NULL AUTO_INCREMENT COMMENT 'Surrogate key that uniquely identifies a patient in your platform; used as the main foreign key in other tables.',
  `external_patient_id` varchar(64) DEFAULT NULL COMMENT 'Optional source-system identifier (e.g., MRN) for trace-back to the originating EHR or registration system.',
  `first_name` varchar(100) DEFAULT NULL COMMENT 'Patient first name (can be excluded or tokenized in de-identified views).',
  `last_name` varchar(100) DEFAULT NULL COMMENT 'Patient last name (can be excluded or tokenized in de-identified views).',
  `date_of_birth` date NOT NULL COMMENT 'Full date of birth; can be truncated to year for privacy in analytics views.',
  `sex_at_birth` varchar(50) NOT NULL COMMENT 'Sex assigned at birth (Male, Female, Intersex, Unknown, etc.).',
  `gender_identity` varchar(50) DEFAULT NULL COMMENT 'Current gender identity, kept separate from sex_at_birth.',
  `race` varchar(50) DEFAULT NULL COMMENT 'High-level race category; could later be normalized to coded vocabularies.',
  `ethnicity` varchar(50) DEFAULT NULL COMMENT 'Ethnicity such as Hispanic/Latino, Not Hispanic/Latino, Unknown, etc.',
  `preferred_language` varchar(50) DEFAULT NULL COMMENT 'Primary language for communication, used for care coordination.',
  `country` varchar(100) DEFAULT NULL COMMENT 'Country of residence.',
  `state_province` varchar(100) DEFAULT NULL COMMENT 'State or province; useful for regional analytics and area-level indices.',
  `city` varchar(100) DEFAULT NULL COMMENT 'City of residence.',
  `postal_code` varchar(20) DEFAULT NULL COMMENT 'Zip/postal code, often used to link to neighborhood-level indicators.',
  `created_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT 'Timestamp when the record was first created in the unified platform.',
  `updated_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT 'Last time this demographic record was updated.',
  PRIMARY KEY (`patient_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `patient_demographics`
--

LOCK TABLES `patient_demographics` WRITE;
/*!40000 ALTER TABLE `patient_demographics` DISABLE KEYS */;
/*!40000 ALTER TABLE `patient_demographics` ENABLE KEYS */;
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
