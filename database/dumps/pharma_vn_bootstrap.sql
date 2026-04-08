/*M!999999\- enable the sandbox mode */ 
-- MariaDB dump 10.19  Distrib 10.6.25-MariaDB, for osx10.21 (arm64)
--
-- Host: localhost    Database: pharma_vn_bootstrap
-- ------------------------------------------------------
-- Server version	10.6.25-MariaDB

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

--
-- Current Database: `pharma_vn_bootstrap`
--

CREATE DATABASE /*!32312 IF NOT EXISTS*/ `pharma_vn_bootstrap` /*!40100 DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci */;

USE `pharma_vn_bootstrap`;

--
-- Table structure for table `bootstrap_account`
--

DROP TABLE IF EXISTS `bootstrap_account`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `bootstrap_account` (
  `id` bigint(20) unsigned NOT NULL AUTO_INCREMENT,
  `company_code` varchar(20) NOT NULL,
  `account_number` varchar(20) NOT NULL,
  `account_name` varchar(255) NOT NULL,
  `parent_account_number` varchar(20) DEFAULT NULL,
  `root_type` varchar(30) NOT NULL,
  `report_type` varchar(30) NOT NULL,
  `account_type` varchar(50) DEFAULT NULL,
  `is_group` tinyint(1) NOT NULL DEFAULT 0,
  `is_tax_account` tinyint(1) NOT NULL DEFAULT 0,
  `is_active` tinyint(1) NOT NULL DEFAULT 1,
  `legal_basis` varchar(255) DEFAULT NULL,
  `notes` text DEFAULT NULL,
  `created_at` datetime NOT NULL DEFAULT current_timestamp(),
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_account_company_number` (`company_code`,`account_number`),
  CONSTRAINT `fk_account_company` FOREIGN KEY (`company_code`) REFERENCES `bootstrap_company` (`company_code`)
) ENGINE=InnoDB AUTO_INCREMENT=49 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `bootstrap_account`
--

LOCK TABLES `bootstrap_account` WRITE;
/*!40000 ALTER TABLE `bootstrap_account` DISABLE KEYS */;
INSERT INTO `bootstrap_account` VALUES (1,'VAP','111','Tien mat',NULL,'Asset','Balance Sheet','Cash',1,0,1,'TT99/2025/TT-BTC',NULL,'2026-04-06 08:55:56'),(2,'VAP','1111','Tien mat VND','111','Asset','Balance Sheet','Cash',0,0,1,'TT99/2025/TT-BTC',NULL,'2026-04-06 08:55:56'),(3,'VAP','112','Tien gui ngan hang',NULL,'Asset','Balance Sheet','Bank',1,0,1,'TT99/2025/TT-BTC',NULL,'2026-04-06 08:55:56'),(4,'VAP','1121','Tien gui ngan hang VND','112','Asset','Balance Sheet','Bank',0,0,1,'TT99/2025/TT-BTC',NULL,'2026-04-06 08:55:56'),(5,'VAP','131','Phai thu cua khach hang',NULL,'Asset','Balance Sheet','Receivable',0,0,1,'TT99/2025/TT-BTC',NULL,'2026-04-06 08:55:56'),(6,'VAP','133','Thue GTGT duoc khau tru',NULL,'Asset','Balance Sheet','Tax',1,1,1,'TT99/2025/TT-BTC (implementation mapping)',NULL,'2026-04-06 08:55:56'),(7,'VAP','1331','Thue GTGT duoc khau tru cua hang hoa dich vu','133','Asset','Balance Sheet','Tax',0,1,1,'TT99/2025/TT-BTC (implementation mapping)',NULL,'2026-04-06 08:55:56'),(8,'VAP','1332','Thue GTGT duoc khau tru cua tai san co dinh','133','Asset','Balance Sheet','Tax',0,1,1,'TT99/2025/TT-BTC (implementation mapping)',NULL,'2026-04-06 08:55:56'),(9,'VAP','141','Tam ung',NULL,'Asset','Balance Sheet','Current Asset',0,0,1,'TT99/2025/TT-BTC',NULL,'2026-04-06 08:55:56'),(10,'VAP','152','Nguyen lieu vat lieu',NULL,'Asset','Balance Sheet','Stock',0,0,1,'TT99/2025/TT-BTC',NULL,'2026-04-06 08:55:56'),(11,'VAP','153','Cong cu dung cu',NULL,'Asset','Balance Sheet','Current Asset',0,0,1,'TT99/2025/TT-BTC',NULL,'2026-04-06 08:55:56'),(12,'VAP','154','Chi phi san xuat kinh doanh do dang',NULL,'Asset','Balance Sheet','Stock',0,0,1,'TT99/2025/TT-BTC',NULL,'2026-04-06 08:55:56'),(13,'VAP','155','Thanh pham',NULL,'Asset','Balance Sheet','Stock',0,0,1,'TT99/2025/TT-BTC',NULL,'2026-04-06 08:55:56'),(14,'VAP','156','Hang hoa',NULL,'Asset','Balance Sheet','Stock',0,0,1,'TT99/2025/TT-BTC',NULL,'2026-04-06 08:55:56'),(15,'VAP','211','Tai san co dinh huu hinh',NULL,'Asset','Balance Sheet','Fixed Asset',1,0,1,'TT99/2025/TT-BTC',NULL,'2026-04-06 08:55:56'),(16,'VAP','2113','May moc thiet bi','211','Asset','Balance Sheet','Fixed Asset',0,0,1,'TT99/2025/TT-BTC',NULL,'2026-04-06 08:55:56'),(17,'VAP','214','Hao mon tai san co dinh',NULL,'Asset','Balance Sheet','Accumulated Depreciation',1,0,1,'TT99/2025/TT-BTC',NULL,'2026-04-06 08:55:56'),(18,'VAP','2141','Hao mon tai san co dinh huu hinh','214','Asset','Balance Sheet','Accumulated Depreciation',0,0,1,'TT99/2025/TT-BTC',NULL,'2026-04-06 08:55:56'),(19,'VAP','242','Chi phi tra truoc',NULL,'Asset','Balance Sheet','Current Asset',0,0,1,'TT99/2025/TT-BTC',NULL,'2026-04-06 08:55:56'),(20,'VAP','331','Phai tra nguoi ban',NULL,'Liability','Balance Sheet','Payable',0,0,1,'TT99/2025/TT-BTC',NULL,'2026-04-06 08:55:56'),(21,'VAP','333','Thue va cac khoan phai nop nha nuoc',NULL,'Liability','Balance Sheet','Tax',1,1,1,'TT99/2025/TT-BTC',NULL,'2026-04-06 08:55:56'),(22,'VAP','33311','Thue GTGT dau ra phai nop','333','Liability','Balance Sheet','Tax',0,1,1,'TT99/2025/TT-BTC; official MOF Q&A in 2026 still references TK 33311',NULL,'2026-04-06 08:55:56'),(23,'VAP','33312','Thue GTGT hang nhap khau','333','Liability','Balance Sheet','Tax',0,1,1,'TT99/2025/TT-BTC (implementation mapping)',NULL,'2026-04-06 08:55:56'),(24,'VAP','3334','Thue thu nhap doanh nghiep','333','Liability','Balance Sheet','Tax',0,1,1,'TT99/2025/TT-BTC',NULL,'2026-04-06 08:55:56'),(25,'VAP','3335','Thue thu nhap ca nhan','333','Liability','Balance Sheet','Tax',0,1,1,'TT99/2025/TT-BTC',NULL,'2026-04-06 08:55:56'),(26,'VAP','334','Phai tra nguoi lao dong',NULL,'Liability','Balance Sheet','Payable',0,0,1,'TT99/2025/TT-BTC',NULL,'2026-04-06 08:55:56'),(27,'VAP','338','Phai tra phai nop khac',NULL,'Liability','Balance Sheet','Current Liability',1,0,1,'TT99/2025/TT-BTC',NULL,'2026-04-06 08:55:56'),(28,'VAP','3383','Bao hiem xa hoi','338','Liability','Balance Sheet','Current Liability',0,0,1,'TT99/2025/TT-BTC',NULL,'2026-04-06 08:55:56'),(29,'VAP','3384','Bao hiem y te','338','Liability','Balance Sheet','Current Liability',0,0,1,'TT99/2025/TT-BTC',NULL,'2026-04-06 08:55:56'),(30,'VAP','3386','Bao hiem that nghiep','338','Liability','Balance Sheet','Current Liability',0,0,1,'TT99/2025/TT-BTC',NULL,'2026-04-06 08:55:56'),(31,'VAP','411','Von dau tu cua chu so huu',NULL,'Equity','Balance Sheet','Equity',1,0,1,'TT99/2025/TT-BTC',NULL,'2026-04-06 08:55:56'),(32,'VAP','4111','Von gop cua chu so huu','411','Equity','Balance Sheet','Equity',0,0,1,'TT99/2025/TT-BTC',NULL,'2026-04-06 08:55:56'),(33,'VAP','421','Loi nhuan sau thue chua phan phoi',NULL,'Equity','Balance Sheet','Equity',1,0,1,'TT99/2025/TT-BTC',NULL,'2026-04-06 08:55:56'),(34,'VAP','4212','Loi nhuan sau thue chua phan phoi nam nay','421','Equity','Balance Sheet','Equity',0,0,1,'TT99/2025/TT-BTC',NULL,'2026-04-06 08:55:56'),(35,'VAP','511','Doanh thu ban hang va cung cap dich vu',NULL,'Income','Profit and Loss','Income Account',1,0,1,'TT99/2025/TT-BTC',NULL,'2026-04-06 08:55:56'),(36,'VAP','5111','Doanh thu ban hang hoa','511','Income','Profit and Loss','Income Account',0,0,1,'TT99/2025/TT-BTC',NULL,'2026-04-06 08:55:56'),(37,'VAP','5112','Doanh thu ban thanh pham','511','Income','Profit and Loss','Income Account',0,0,1,'TT99/2025/TT-BTC',NULL,'2026-04-06 08:55:56'),(38,'VAP','515','Doanh thu hoat dong tai chinh',NULL,'Income','Profit and Loss','Income Account',0,0,1,'TT99/2025/TT-BTC',NULL,'2026-04-06 08:55:56'),(39,'VAP','521','Cac khoan giam tru doanh thu',NULL,'Income','Profit and Loss','Income Account',1,0,1,'TT99/2025/TT-BTC',NULL,'2026-04-06 08:55:56'),(40,'VAP','5211','Chiet khau thuong mai','521','Income','Profit and Loss','Income Account',0,0,1,'TT99/2025/TT-BTC',NULL,'2026-04-06 08:55:56'),(41,'VAP','632','Gia von hang ban',NULL,'Expense','Profit and Loss','Cost of Goods Sold',0,0,1,'TT99/2025/TT-BTC',NULL,'2026-04-06 08:55:56'),(42,'VAP','635','Chi phi tai chinh',NULL,'Expense','Profit and Loss','Expense Account',0,0,1,'TT99/2025/TT-BTC',NULL,'2026-04-06 08:55:56'),(43,'VAP','641','Chi phi ban hang',NULL,'Expense','Profit and Loss','Expense Account',0,0,1,'TT99/2025/TT-BTC',NULL,'2026-04-06 08:55:56'),(44,'VAP','642','Chi phi quan ly doanh nghiep',NULL,'Expense','Profit and Loss','Expense Account',0,0,1,'TT99/2025/TT-BTC',NULL,'2026-04-06 08:55:56'),(45,'VAP','711','Thu nhap khac',NULL,'Income','Profit and Loss','Income Account',0,0,1,'TT99/2025/TT-BTC',NULL,'2026-04-06 08:55:56'),(46,'VAP','811','Chi phi khac',NULL,'Expense','Profit and Loss','Expense Account',0,0,1,'TT99/2025/TT-BTC',NULL,'2026-04-06 08:55:56'),(47,'VAP','8211','Chi phi thue TNDN hien hanh',NULL,'Expense','Profit and Loss','Tax',0,1,1,'TT99/2025/TT-BTC',NULL,'2026-04-06 08:55:56'),(48,'VAP','911','Xac dinh ket qua kinh doanh',NULL,'Equity','Profit and Loss','Temporary',0,0,1,'TT99/2025/TT-BTC',NULL,'2026-04-06 08:55:56');
/*!40000 ALTER TABLE `bootstrap_account` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `bootstrap_batch`
--

DROP TABLE IF EXISTS `bootstrap_batch`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `bootstrap_batch` (
  `batch_no` varchar(50) NOT NULL,
  `item_code` varchar(40) NOT NULL,
  `warehouse_code` varchar(30) NOT NULL,
  `batch_status` varchar(20) NOT NULL,
  `manufacturing_date` date DEFAULT NULL,
  `expiry_date` date DEFAULT NULL,
  `qty_on_hand` decimal(18,3) NOT NULL DEFAULT 0.000,
  `temperature_excursion_flag` tinyint(1) NOT NULL DEFAULT 0,
  `coa_no` varchar(50) DEFAULT NULL,
  `created_at` datetime NOT NULL DEFAULT current_timestamp(),
  PRIMARY KEY (`batch_no`),
  KEY `fk_batch_item` (`item_code`),
  KEY `fk_batch_warehouse` (`warehouse_code`),
  CONSTRAINT `fk_batch_item` FOREIGN KEY (`item_code`) REFERENCES `bootstrap_item` (`item_code`),
  CONSTRAINT `fk_batch_warehouse` FOREIGN KEY (`warehouse_code`) REFERENCES `bootstrap_warehouse` (`warehouse_code`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `bootstrap_batch`
--

LOCK TABLES `bootstrap_batch` WRITE;
/*!40000 ALTER TABLE `bootstrap_batch` DISABLE KEYS */;
INSERT INTO `bootstrap_batch` VALUES ('BATCH-AMOX-2602-001','AMOX500-H10X10','WH-HCM-FG-REL','Released','2026-02-15','2028-02-28',680.000,0,'COA-AMOX-2602-001','2026-04-06 08:55:56'),('BATCH-API-PARA-2601-001','API-PARACETAMOL','WH-BD-RM-REL','Released','2026-01-12','2029-01-31',500.000,0,'COA-API-PARA-2601-001','2026-04-06 08:55:56'),('BATCH-PARA-2603-001','PARA500-H10X10','WH-BD-FG-REL','Released','2026-03-10','2028-03-31',1200.000,0,'COA-PARA-2603-001','2026-04-06 08:55:56'),('BATCH-PARA-COLD-2604-001','PARA500-H10X10','WH-COLD-2-8','Hold','2026-04-01','2028-03-31',50.000,1,'COA-PARA-COLD-2604-001','2026-04-06 08:55:56'),('BATCH-VITC-2603-001','VITC-1000-30V','WH-HN-FG-REL','Released','2026-03-05','2027-12-31',300.000,0,'COA-VITC-2603-001','2026-04-06 08:55:56');
/*!40000 ALTER TABLE `bootstrap_batch` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `bootstrap_company`
--

DROP TABLE IF EXISTS `bootstrap_company`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `bootstrap_company` (
  `company_code` varchar(20) NOT NULL,
  `company_name` varchar(255) NOT NULL,
  `tax_id` varchar(30) NOT NULL,
  `registration_no` varchar(50) DEFAULT NULL,
  `base_currency` varchar(10) NOT NULL DEFAULT 'VND',
  `country` varchar(100) NOT NULL DEFAULT 'Vietnam',
  `accounting_regime` varchar(100) NOT NULL,
  `vat_method` varchar(50) NOT NULL DEFAULT 'Khau tru',
  `created_at` datetime NOT NULL DEFAULT current_timestamp(),
  PRIMARY KEY (`company_code`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `bootstrap_company`
--

LOCK TABLES `bootstrap_company` WRITE;
/*!40000 ALTER TABLE `bootstrap_company` DISABLE KEYS */;
INSERT INTO `bootstrap_company` VALUES ('VAP','Viet An Pharma JSC','0312345678','DN-2026-ERP-PHARMA','VND','Vietnam','Thong tu 99/2025/TT-BTC','Khau tru','2026-04-06 08:55:56');
/*!40000 ALTER TABLE `bootstrap_company` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `bootstrap_customer`
--

DROP TABLE IF EXISTS `bootstrap_customer`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `bootstrap_customer` (
  `customer_code` varchar(30) NOT NULL,
  `customer_name` varchar(255) NOT NULL,
  `customer_channel` varchar(50) NOT NULL,
  `tax_id` varchar(30) DEFAULT NULL,
  `license_no` varchar(100) DEFAULT NULL,
  `license_expiry` date DEFAULT NULL,
  `payment_terms_days` int(11) NOT NULL DEFAULT 30,
  `credit_limit` decimal(18,2) NOT NULL DEFAULT 0.00,
  `territory` varchar(100) DEFAULT NULL,
  `created_at` datetime NOT NULL DEFAULT current_timestamp(),
  PRIMARY KEY (`customer_code`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `bootstrap_customer`
--

LOCK TABLES `bootstrap_customer` WRITE;
/*!40000 ALTER TABLE `bootstrap_customer` DISABLE KEYS */;
INSERT INTO `bootstrap_customer` VALUES ('CUS-DIST-HN-001','Cong ty Phan Phoi Duoc Ha Noi','Distributor','0101122233','GDP-HN-2026-7788','2028-01-31',60,1500000000.00,'HN','2026-04-06 08:55:56'),('CUS-HOSP-HCM-001','Phong Kham Da Khoa An Khang','Clinic','0318877665','BYT-HCM-2026-2201','2027-12-31',45,500000000.00,'HCM','2026-04-06 08:55:56'),('CUS-PHAR-HCM-001','Nha Thuoc Minh Chau Quan 3','Pharmacy','0319988776','GPP-HCM-2026-1001','2027-06-30',30,200000000.00,'HCM','2026-04-06 08:55:56');
/*!40000 ALTER TABLE `bootstrap_customer` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `bootstrap_item`
--

DROP TABLE IF EXISTS `bootstrap_item`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `bootstrap_item` (
  `item_code` varchar(40) NOT NULL,
  `item_name` varchar(255) NOT NULL,
  `item_group_code` varchar(30) NOT NULL,
  `item_type` varchar(30) NOT NULL,
  `stock_uom` varchar(20) NOT NULL DEFAULT 'Nos',
  `vat_output_tax_code` varchar(40) NOT NULL,
  `vat_input_tax_code` varchar(40) DEFAULT NULL,
  `is_batch_managed` tinyint(1) NOT NULL DEFAULT 1,
  `is_expiry_managed` tinyint(1) NOT NULL DEFAULT 1,
  `cold_chain_required` tinyint(1) NOT NULL DEFAULT 0,
  `min_remaining_shelf_life_days` int(11) NOT NULL DEFAULT 180,
  `valuation_rate` decimal(18,2) NOT NULL DEFAULT 0.00,
  `default_warehouse_code` varchar(30) DEFAULT NULL,
  `created_at` datetime NOT NULL DEFAULT current_timestamp(),
  PRIMARY KEY (`item_code`),
  KEY `fk_item_group` (`item_group_code`),
  KEY `fk_item_default_warehouse` (`default_warehouse_code`),
  CONSTRAINT `fk_item_default_warehouse` FOREIGN KEY (`default_warehouse_code`) REFERENCES `bootstrap_warehouse` (`warehouse_code`),
  CONSTRAINT `fk_item_group` FOREIGN KEY (`item_group_code`) REFERENCES `bootstrap_item_group` (`item_group_code`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `bootstrap_item`
--

LOCK TABLES `bootstrap_item` WRITE;
/*!40000 ALTER TABLE `bootstrap_item` DISABLE KEYS */;
INSERT INTO `bootstrap_item` VALUES ('AMOX500-H10X10','Amoxicillin 500mg Hop 10x10','ETC','Finished Good','Box','VAT-OUT-5','VAT-IN-5',1,1,0,180,26300.00,'WH-HCM-FG-REL','2026-04-06 08:55:56'),('API-PARACETAMOL','Paracetamol API','RM','Raw Material','Kg','VAT-OUT-5','VAT-IN-5',1,1,0,365,160000.00,'WH-BD-RM-REL','2026-04-06 08:55:56'),('BOX-OTC-001','Printed OTC Folding Box','PM','Packaging Material','Nos','VAT-OUT-10','VAT-IN-10',0,0,0,0,950.00,'WH-BD-RM-REL','2026-04-06 08:55:56'),('LOG-SVC-ELIG-8','Logistics Service Eligible 8 Percent','PHARMA','Service','Service','VAT-OUT-8','VAT-IN-8',0,0,0,0,0.00,NULL,'2026-04-06 08:55:56'),('PARA500-H10X10','Paracetamol 500mg Hop 10x10','OTC','Finished Good','Box','VAT-OUT-5','VAT-IN-5',1,1,0,180,18200.00,'WH-BD-FG-REL','2026-04-06 08:55:56'),('VITC-1000-30V','Vitamin C 1000mg Hop 30 vien','SUPP','Finished Good','Box','VAT-OUT-10','VAT-IN-10',1,1,0,180,42500.00,'WH-HN-FG-REL','2026-04-06 08:55:56');
/*!40000 ALTER TABLE `bootstrap_item` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `bootstrap_item_group`
--

DROP TABLE IF EXISTS `bootstrap_item_group`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `bootstrap_item_group` (
  `item_group_code` varchar(30) NOT NULL,
  `item_group_name` varchar(255) NOT NULL,
  `parent_item_group_code` varchar(30) DEFAULT NULL,
  `is_stock_item` tinyint(1) NOT NULL DEFAULT 1,
  `description` text DEFAULT NULL,
  `created_at` datetime NOT NULL DEFAULT current_timestamp(),
  PRIMARY KEY (`item_group_code`),
  KEY `fk_item_group_parent` (`parent_item_group_code`),
  CONSTRAINT `fk_item_group_parent` FOREIGN KEY (`parent_item_group_code`) REFERENCES `bootstrap_item_group` (`item_group_code`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `bootstrap_item_group`
--

LOCK TABLES `bootstrap_item_group` WRITE;
/*!40000 ALTER TABLE `bootstrap_item_group` DISABLE KEYS */;
INSERT INTO `bootstrap_item_group` VALUES ('ETC','ETC Medicines','FG',1,'Prescription medicines','2026-04-06 08:55:56'),('FG','Finished Goods','PHARMA',1,'Finished goods for sale','2026-04-06 08:55:56'),('OTC','OTC Medicines','FG',1,'Over-the-counter finished medicines','2026-04-06 08:55:56'),('PHARMA','Pharma Root',NULL,1,'Top level item group for pharma business','2026-04-06 08:55:56'),('PM','Packaging Materials','PHARMA',1,'Cartons, foils, labels','2026-04-06 08:55:56'),('RM','Raw Materials','PHARMA',1,'API and excipients','2026-04-06 08:55:56'),('SUPP','Supplements','FG',1,'Food supplements and wellness products','2026-04-06 08:55:56');
/*!40000 ALTER TABLE `bootstrap_item_group` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `bootstrap_purchase_order`
--

DROP TABLE IF EXISTS `bootstrap_purchase_order`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `bootstrap_purchase_order` (
  `po_no` varchar(30) NOT NULL,
  `company_code` varchar(20) NOT NULL,
  `supplier_code` varchar(30) NOT NULL,
  `order_date` date NOT NULL,
  `status` varchar(30) NOT NULL,
  `currency` varchar(10) NOT NULL DEFAULT 'VND',
  `tax_code` varchar(40) NOT NULL,
  `total_before_tax` decimal(18,2) NOT NULL,
  `total_tax` decimal(18,2) NOT NULL,
  `grand_total` decimal(18,2) NOT NULL,
  `created_at` datetime NOT NULL DEFAULT current_timestamp(),
  PRIMARY KEY (`po_no`),
  KEY `fk_po_company` (`company_code`),
  KEY `fk_po_supplier` (`supplier_code`),
  CONSTRAINT `fk_po_company` FOREIGN KEY (`company_code`) REFERENCES `bootstrap_company` (`company_code`),
  CONSTRAINT `fk_po_supplier` FOREIGN KEY (`supplier_code`) REFERENCES `bootstrap_supplier` (`supplier_code`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `bootstrap_purchase_order`
--

LOCK TABLES `bootstrap_purchase_order` WRITE;
/*!40000 ALTER TABLE `bootstrap_purchase_order` DISABLE KEYS */;
INSERT INTO `bootstrap_purchase_order` VALUES ('PO-PM-2026-0002','VAP','SUP-PM-DOM-001','2026-04-03','Draft','VND','VAT-IN-10',9500000.00,950000.00,10450000.00,'2026-04-06 08:55:56'),('PO-RM-2026-0001','VAP','SUP-RM-DOM-001','2026-04-02','To Receive and Bill','VND','VAT-IN-5',32000000.00,1600000.00,33600000.00,'2026-04-06 08:55:56');
/*!40000 ALTER TABLE `bootstrap_purchase_order` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `bootstrap_purchase_order_item`
--

DROP TABLE IF EXISTS `bootstrap_purchase_order_item`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `bootstrap_purchase_order_item` (
  `id` bigint(20) unsigned NOT NULL AUTO_INCREMENT,
  `po_no` varchar(30) NOT NULL,
  `item_code` varchar(40) NOT NULL,
  `warehouse_code` varchar(30) NOT NULL,
  `qty` decimal(18,3) NOT NULL,
  `rate` decimal(18,2) NOT NULL,
  `line_amount` decimal(18,2) NOT NULL,
  `vat_rate` decimal(5,2) NOT NULL,
  `supplier_batch_no` varchar(50) DEFAULT NULL,
  `created_at` datetime NOT NULL DEFAULT current_timestamp(),
  PRIMARY KEY (`id`),
  KEY `fk_poi_po` (`po_no`),
  KEY `fk_poi_item` (`item_code`),
  KEY `fk_poi_warehouse` (`warehouse_code`),
  CONSTRAINT `fk_poi_item` FOREIGN KEY (`item_code`) REFERENCES `bootstrap_item` (`item_code`),
  CONSTRAINT `fk_poi_po` FOREIGN KEY (`po_no`) REFERENCES `bootstrap_purchase_order` (`po_no`),
  CONSTRAINT `fk_poi_warehouse` FOREIGN KEY (`warehouse_code`) REFERENCES `bootstrap_warehouse` (`warehouse_code`)
) ENGINE=InnoDB AUTO_INCREMENT=3 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `bootstrap_purchase_order_item`
--

LOCK TABLES `bootstrap_purchase_order_item` WRITE;
/*!40000 ALTER TABLE `bootstrap_purchase_order_item` DISABLE KEYS */;
INSERT INTO `bootstrap_purchase_order_item` VALUES (1,'PO-RM-2026-0001','API-PARACETAMOL','WH-BD-RM-QUA',200.000,160000.00,32000000.00,5.00,'SUPB-API-APR-2026','2026-04-06 08:55:56'),(2,'PO-PM-2026-0002','BOX-OTC-001','WH-BD-RM-QUA',10000.000,950.00,9500000.00,10.00,NULL,'2026-04-06 08:55:56');
/*!40000 ALTER TABLE `bootstrap_purchase_order_item` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `bootstrap_sales_order`
--

DROP TABLE IF EXISTS `bootstrap_sales_order`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `bootstrap_sales_order` (
  `so_no` varchar(30) NOT NULL,
  `company_code` varchar(20) NOT NULL,
  `customer_code` varchar(30) NOT NULL,
  `order_date` date NOT NULL,
  `status` varchar(30) NOT NULL,
  `currency` varchar(10) NOT NULL DEFAULT 'VND',
  `tax_code` varchar(40) NOT NULL,
  `total_before_tax` decimal(18,2) NOT NULL,
  `total_tax` decimal(18,2) NOT NULL,
  `grand_total` decimal(18,2) NOT NULL,
  `created_at` datetime NOT NULL DEFAULT current_timestamp(),
  PRIMARY KEY (`so_no`),
  KEY `fk_so_company` (`company_code`),
  KEY `fk_so_customer` (`customer_code`),
  CONSTRAINT `fk_so_company` FOREIGN KEY (`company_code`) REFERENCES `bootstrap_company` (`company_code`),
  CONSTRAINT `fk_so_customer` FOREIGN KEY (`customer_code`) REFERENCES `bootstrap_customer` (`customer_code`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `bootstrap_sales_order`
--

LOCK TABLES `bootstrap_sales_order` WRITE;
/*!40000 ALTER TABLE `bootstrap_sales_order` DISABLE KEYS */;
INSERT INTO `bootstrap_sales_order` VALUES ('SO-B2B-2026-0001','VAP','CUS-PHAR-HCM-001','2026-04-05','To Deliver and Bill','VND','VAT-OUT-5',3500000.00,175000.00,3675000.00,'2026-04-06 08:55:56'),('SO-B2B-2026-0002','VAP','CUS-DIST-HN-001','2026-04-06','Draft','VND','VAT-OUT-5',6312000.00,315600.00,6627600.00,'2026-04-06 08:55:56');
/*!40000 ALTER TABLE `bootstrap_sales_order` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `bootstrap_sales_order_item`
--

DROP TABLE IF EXISTS `bootstrap_sales_order_item`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `bootstrap_sales_order_item` (
  `id` bigint(20) unsigned NOT NULL AUTO_INCREMENT,
  `so_no` varchar(30) NOT NULL,
  `item_code` varchar(40) NOT NULL,
  `batch_no` varchar(50) DEFAULT NULL,
  `warehouse_code` varchar(30) NOT NULL,
  `qty` decimal(18,3) NOT NULL,
  `rate` decimal(18,2) NOT NULL,
  `line_amount` decimal(18,2) NOT NULL,
  `vat_rate` decimal(5,2) NOT NULL,
  `created_at` datetime NOT NULL DEFAULT current_timestamp(),
  PRIMARY KEY (`id`),
  KEY `fk_soi_so` (`so_no`),
  KEY `fk_soi_item` (`item_code`),
  KEY `fk_soi_batch` (`batch_no`),
  KEY `fk_soi_warehouse` (`warehouse_code`),
  CONSTRAINT `fk_soi_batch` FOREIGN KEY (`batch_no`) REFERENCES `bootstrap_batch` (`batch_no`),
  CONSTRAINT `fk_soi_item` FOREIGN KEY (`item_code`) REFERENCES `bootstrap_item` (`item_code`),
  CONSTRAINT `fk_soi_so` FOREIGN KEY (`so_no`) REFERENCES `bootstrap_sales_order` (`so_no`),
  CONSTRAINT `fk_soi_warehouse` FOREIGN KEY (`warehouse_code`) REFERENCES `bootstrap_warehouse` (`warehouse_code`)
) ENGINE=InnoDB AUTO_INCREMENT=3 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `bootstrap_sales_order_item`
--

LOCK TABLES `bootstrap_sales_order_item` WRITE;
/*!40000 ALTER TABLE `bootstrap_sales_order_item` DISABLE KEYS */;
INSERT INTO `bootstrap_sales_order_item` VALUES (1,'SO-B2B-2026-0001','PARA500-H10X10','BATCH-PARA-2603-001','WH-BD-FG-REL',100.000,35000.00,3500000.00,5.00,'2026-04-06 08:55:56'),(2,'SO-B2B-2026-0002','AMOX500-H10X10','BATCH-AMOX-2602-001','WH-HCM-FG-REL',240.000,26300.00,6312000.00,5.00,'2026-04-06 08:55:56');
/*!40000 ALTER TABLE `bootstrap_sales_order_item` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `bootstrap_supplier`
--

DROP TABLE IF EXISTS `bootstrap_supplier`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `bootstrap_supplier` (
  `supplier_code` varchar(30) NOT NULL,
  `supplier_name` varchar(255) NOT NULL,
  `supplier_type` varchar(50) NOT NULL,
  `tax_id` varchar(30) DEFAULT NULL,
  `gmp_certificate_no` varchar(100) DEFAULT NULL,
  `gmp_expiry` date DEFAULT NULL,
  `approved_status` varchar(30) NOT NULL,
  `country` varchar(100) NOT NULL DEFAULT 'Vietnam',
  `created_at` datetime NOT NULL DEFAULT current_timestamp(),
  PRIMARY KEY (`supplier_code`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `bootstrap_supplier`
--

LOCK TABLES `bootstrap_supplier` WRITE;
/*!40000 ALTER TABLE `bootstrap_supplier` DISABLE KEYS */;
INSERT INTO `bootstrap_supplier` VALUES ('SUP-IMP-001','Global Pharma Ingredients Pte','Importer','SG998877','GMP-SG-2026-88','2028-03-31','Approved','Singapore','2026-04-06 08:55:56'),('SUP-PM-DOM-001','Bao Bi An Phat','Manufacturer','0311122233',NULL,NULL,'Approved','Vietnam','2026-04-06 08:55:56'),('SUP-RM-DOM-001','Sai Gon API Trading','Trader','0309988776','GMP-VN-API-2026-01','2027-12-31','Approved','Vietnam','2026-04-06 08:55:56');
/*!40000 ALTER TABLE `bootstrap_supplier` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `bootstrap_tax_template`
--

DROP TABLE IF EXISTS `bootstrap_tax_template`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `bootstrap_tax_template` (
  `id` bigint(20) unsigned NOT NULL AUTO_INCREMENT,
  `company_code` varchar(20) NOT NULL,
  `tax_code` varchar(40) NOT NULL,
  `tax_name` varchar(255) NOT NULL,
  `tax_scope` varchar(20) NOT NULL,
  `rate` decimal(5,2) NOT NULL,
  `account_number` varchar(20) NOT NULL,
  `legal_basis` varchar(255) NOT NULL,
  `effective_from` date NOT NULL,
  `effective_to` date DEFAULT NULL,
  `applies_to` varchar(100) NOT NULL,
  `is_active` tinyint(1) NOT NULL DEFAULT 1,
  `notes` text DEFAULT NULL,
  `created_at` datetime NOT NULL DEFAULT current_timestamp(),
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_tax_company_code` (`company_code`,`tax_code`),
  CONSTRAINT `fk_tax_company` FOREIGN KEY (`company_code`) REFERENCES `bootstrap_company` (`company_code`)
) ENGINE=InnoDB AUTO_INCREMENT=8 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `bootstrap_tax_template`
--

LOCK TABLES `bootstrap_tax_template` WRITE;
/*!40000 ALTER TABLE `bootstrap_tax_template` DISABLE KEYS */;
INSERT INTO `bootstrap_tax_template` VALUES (1,'VAP','VAT-OUT-5','VAT output 5 percent','Output',5.00,'33311','Luat 48/2024/QH15; reviewed against Luat 149/2025/QH15 context','2025-07-01',NULL,'Medicines, preventive drugs, pharmaceutical raw materials, medical devices where applicable',1,'Dung cho thuoc chua benh, thuoc phong benh, duoc chat nguyen lieu san xuat thuoc. Can doi chieu voi tax advisor khi go-live.','2026-04-06 08:55:56'),(2,'VAP','VAT-IN-5','VAT input 5 percent','Input',5.00,'1331','Luat 48/2024/QH15; reviewed against Luat 149/2025/QH15 context','2025-07-01',NULL,'Deductible input VAT for qualifying 5 percent goods',1,'Mapping trien khai cho ERPNext.','2026-04-06 08:55:56'),(3,'VAP','VAT-OUT-8','VAT output 8 percent','Output',8.00,'33311','Nghi quyet 204/2025/QH15; Nghi dinh 174/2025/ND-CP','2025-07-01','2026-12-31','Eligible goods and services normally subject to 10 percent VAT',1,'Chi ap dung cho nhom du dieu kien giam 2 percent. Can xac minh theo item category thuc te.','2026-04-06 08:55:56'),(4,'VAP','VAT-IN-8','VAT input 8 percent','Input',8.00,'1331','Nghi quyet 204/2025/QH15; Nghi dinh 174/2025/ND-CP','2025-07-01','2026-12-31','Deductible input VAT for qualifying reduced-rate goods and services',1,'Template de dung trong giai doan giam thue.','2026-04-06 08:55:56'),(5,'VAP','VAT-OUT-10','VAT output 10 percent','Output',10.00,'33311','Luat 48/2024/QH15; reviewed against Luat 149/2025/QH15 context','2025-07-01',NULL,'General rate for goods and services not in 0/5 percent and not under temporary reduction',1,'Dung cho nhom hang hoa dich vu ap dung muc thong thuong 10 percent.','2026-04-06 08:55:56'),(6,'VAP','VAT-IN-10','VAT input 10 percent','Input',10.00,'1331','Luat 48/2024/QH15; reviewed against Luat 149/2025/QH15 context','2025-07-01',NULL,'Deductible input VAT for 10 percent goods and services',1,'Mapping trien khai cho ERPNext.','2026-04-06 08:55:56'),(7,'VAP','VAT-OUT-0','VAT output 0 percent','Output',0.00,'33311','Luat 48/2024/QH15; reviewed against Luat 149/2025/QH15 context','2025-07-01',NULL,'Export sales and zero-rated supplies where conditions are met',1,'Chi dung khi dap ung day du dieu kien ho so zero-rate.','2026-04-06 08:55:56');
/*!40000 ALTER TABLE `bootstrap_tax_template` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `bootstrap_warehouse`
--

DROP TABLE IF EXISTS `bootstrap_warehouse`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `bootstrap_warehouse` (
  `warehouse_code` varchar(30) NOT NULL,
  `warehouse_name` varchar(255) NOT NULL,
  `branch_code` varchar(20) NOT NULL,
  `warehouse_type` varchar(50) NOT NULL,
  `parent_warehouse_code` varchar(30) DEFAULT NULL,
  `cold_chain_enabled` tinyint(1) NOT NULL DEFAULT 0,
  `is_sellable` tinyint(1) NOT NULL DEFAULT 0,
  `created_at` datetime NOT NULL DEFAULT current_timestamp(),
  PRIMARY KEY (`warehouse_code`),
  KEY `fk_warehouse_parent` (`parent_warehouse_code`),
  CONSTRAINT `fk_warehouse_parent` FOREIGN KEY (`parent_warehouse_code`) REFERENCES `bootstrap_warehouse` (`warehouse_code`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `bootstrap_warehouse`
--

LOCK TABLES `bootstrap_warehouse` WRITE;
/*!40000 ALTER TABLE `bootstrap_warehouse` DISABLE KEYS */;
INSERT INTO `bootstrap_warehouse` VALUES ('WH-BD','Binh Duong Main Site','BD','Site',NULL,0,0,'2026-04-06 08:55:56'),('WH-BD-FG-QUA','Binh Duong Finished Goods Quarantine','BD','Finished Goods','WH-BD',0,0,'2026-04-06 08:55:56'),('WH-BD-FG-REL','Binh Duong Finished Goods Released','BD','Finished Goods','WH-BD',0,1,'2026-04-06 08:55:56'),('WH-BD-RM-QUA','Binh Duong Raw Material Quarantine','BD','Raw Material','WH-BD',0,0,'2026-04-06 08:55:56'),('WH-BD-RM-REL','Binh Duong Raw Material Released','BD','Raw Material','WH-BD',0,0,'2026-04-06 08:55:56'),('WH-COLD-2-8','Cold Storage 2 to 8C','BD','Cold Storage','WH-BD',1,1,'2026-04-06 08:55:56'),('WH-HCM','HCM Distribution Site','HCM','Site',NULL,0,0,'2026-04-06 08:55:56'),('WH-HCM-FG-REL','HCM Finished Goods Released','HCM','Finished Goods','WH-HCM',0,1,'2026-04-06 08:55:56'),('WH-HN','Ha Noi Distribution Site','HN','Site',NULL,0,0,'2026-04-06 08:55:56'),('WH-HN-FG-REL','Ha Noi Finished Goods Released','HN','Finished Goods','WH-HN',0,1,'2026-04-06 08:55:56'),('WH-REJECTED','Rejected Warehouse','BD','Rejected','WH-BD',0,0,'2026-04-06 08:55:56'),('WH-RETURNS','Customer Returns Warehouse','BD','Returns','WH-BD',0,0,'2026-04-06 08:55:56');
/*!40000 ALTER TABLE `bootstrap_warehouse` ENABLE KEYS */;
UNLOCK TABLES;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2026-04-06  8:55:56
