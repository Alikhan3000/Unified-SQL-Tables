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
-- Table structure for table `claims_encounter`
--

DROP TABLE IF EXISTS `claims_encounter`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `claims_encounter` (
  `claim_id` bigint unsigned NOT NULL AUTO_INCREMENT COMMENT 'Unique identifier for each claim record.',
  `patient_id` bigint unsigned NOT NULL COMMENT 'FK to patient_demographics.patient_id.',
  `claim_number` varchar(100) NOT NULL COMMENT 'Payer claim number.',
  `payer` varchar(200) DEFAULT NULL COMMENT 'Insurance payer name.',
  `claim_status` varchar(50) DEFAULT NULL COMMENT 'Submitted, Paid, Denied, Pending, etc.',
  `service_start_date` date NOT NULL COMMENT 'Start of service period.',
  `service_end_date` date DEFAULT NULL COMMENT 'End of service period.',
  `billed_amount` decimal(18,2) DEFAULT NULL COMMENT 'Total amount billed.',
  `paid_amount` decimal(18,2) DEFAULT NULL COMMENT 'Amount paid by payer.',
  `diagnosis_codes` json DEFAULT NULL COMMENT 'List of ICD-10 codes associated with the claim.',
  `procedure_codes` json DEFAULT NULL COMMENT 'List of CPT/HCPCS codes associated with the claim.',
  `created_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`claim_id`),
  KEY `fk_claims_patient` (`patient_id`),
  CONSTRAINT `fk_claims_patient` FOREIGN KEY (`patient_id`) REFERENCES `patient_demographics` (`patient_id`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `claims_encounter`
--

LOCK TABLES `claims_encounter` WRITE;
/*!40000 ALTER TABLE `claims_encounter` DISABLE KEYS */;
/*!40000 ALTER TABLE `claims_encounter` ENABLE KEYS */;
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
