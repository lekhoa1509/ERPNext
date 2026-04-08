SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

DROP TABLE IF EXISTS bootstrap_purchase_order_item;
DROP TABLE IF EXISTS bootstrap_purchase_order;
DROP TABLE IF EXISTS bootstrap_sales_order_item;
DROP TABLE IF EXISTS bootstrap_sales_order;
DROP TABLE IF EXISTS bootstrap_batch;
DROP TABLE IF EXISTS bootstrap_item;
DROP TABLE IF EXISTS bootstrap_customer;
DROP TABLE IF EXISTS bootstrap_supplier;
DROP TABLE IF EXISTS bootstrap_warehouse;
DROP TABLE IF EXISTS bootstrap_item_group;
DROP TABLE IF EXISTS bootstrap_tax_template;
DROP TABLE IF EXISTS bootstrap_account;
DROP TABLE IF EXISTS bootstrap_company;

SET FOREIGN_KEY_CHECKS = 1;

CREATE TABLE bootstrap_company (
    company_code VARCHAR(20) PRIMARY KEY,
    company_name VARCHAR(255) NOT NULL,
    tax_id VARCHAR(30) NOT NULL,
    registration_no VARCHAR(50),
    base_currency VARCHAR(10) NOT NULL DEFAULT 'VND',
    country VARCHAR(100) NOT NULL DEFAULT 'Vietnam',
    accounting_regime VARCHAR(100) NOT NULL,
    vat_method VARCHAR(50) NOT NULL DEFAULT 'Khau tru',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE bootstrap_account (
    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
    company_code VARCHAR(20) NOT NULL,
    account_number VARCHAR(20) NOT NULL,
    account_name VARCHAR(255) NOT NULL,
    parent_account_number VARCHAR(20) DEFAULT NULL,
    root_type VARCHAR(30) NOT NULL,
    report_type VARCHAR(30) NOT NULL,
    account_type VARCHAR(50) DEFAULT NULL,
    is_group TINYINT(1) NOT NULL DEFAULT 0,
    is_tax_account TINYINT(1) NOT NULL DEFAULT 0,
    is_active TINYINT(1) NOT NULL DEFAULT 1,
    legal_basis VARCHAR(255) DEFAULT NULL,
    notes TEXT,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY uq_account_company_number (company_code, account_number),
    CONSTRAINT fk_account_company FOREIGN KEY (company_code)
        REFERENCES bootstrap_company(company_code)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE bootstrap_tax_template (
    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
    company_code VARCHAR(20) NOT NULL,
    tax_code VARCHAR(40) NOT NULL,
    tax_name VARCHAR(255) NOT NULL,
    tax_scope VARCHAR(20) NOT NULL,
    rate DECIMAL(5,2) NOT NULL,
    account_number VARCHAR(20) NOT NULL,
    legal_basis VARCHAR(255) NOT NULL,
    effective_from DATE NOT NULL,
    effective_to DATE DEFAULT NULL,
    applies_to VARCHAR(100) NOT NULL,
    is_active TINYINT(1) NOT NULL DEFAULT 1,
    notes TEXT,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY uq_tax_company_code (company_code, tax_code),
    CONSTRAINT fk_tax_company FOREIGN KEY (company_code)
        REFERENCES bootstrap_company(company_code)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE bootstrap_item_group (
    item_group_code VARCHAR(30) PRIMARY KEY,
    item_group_name VARCHAR(255) NOT NULL,
    parent_item_group_code VARCHAR(30) DEFAULT NULL,
    is_stock_item TINYINT(1) NOT NULL DEFAULT 1,
    description TEXT,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_item_group_parent FOREIGN KEY (parent_item_group_code)
        REFERENCES bootstrap_item_group(item_group_code)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE bootstrap_warehouse (
    warehouse_code VARCHAR(30) PRIMARY KEY,
    warehouse_name VARCHAR(255) NOT NULL,
    branch_code VARCHAR(20) NOT NULL,
    warehouse_type VARCHAR(50) NOT NULL,
    parent_warehouse_code VARCHAR(30) DEFAULT NULL,
    cold_chain_enabled TINYINT(1) NOT NULL DEFAULT 0,
    is_sellable TINYINT(1) NOT NULL DEFAULT 0,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_warehouse_parent FOREIGN KEY (parent_warehouse_code)
        REFERENCES bootstrap_warehouse(warehouse_code)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE bootstrap_supplier (
    supplier_code VARCHAR(30) PRIMARY KEY,
    supplier_name VARCHAR(255) NOT NULL,
    supplier_type VARCHAR(50) NOT NULL,
    tax_id VARCHAR(30),
    gmp_certificate_no VARCHAR(100),
    gmp_expiry DATE,
    approved_status VARCHAR(30) NOT NULL,
    country VARCHAR(100) NOT NULL DEFAULT 'Vietnam',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE bootstrap_customer (
    customer_code VARCHAR(30) PRIMARY KEY,
    customer_name VARCHAR(255) NOT NULL,
    customer_channel VARCHAR(50) NOT NULL,
    tax_id VARCHAR(30),
    license_no VARCHAR(100),
    license_expiry DATE,
    payment_terms_days INT NOT NULL DEFAULT 30,
    credit_limit DECIMAL(18,2) NOT NULL DEFAULT 0,
    territory VARCHAR(100) DEFAULT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE bootstrap_item (
    item_code VARCHAR(40) PRIMARY KEY,
    item_name VARCHAR(255) NOT NULL,
    item_group_code VARCHAR(30) NOT NULL,
    item_type VARCHAR(30) NOT NULL,
    stock_uom VARCHAR(20) NOT NULL DEFAULT 'Nos',
    vat_output_tax_code VARCHAR(40) NOT NULL,
    vat_input_tax_code VARCHAR(40) DEFAULT NULL,
    is_batch_managed TINYINT(1) NOT NULL DEFAULT 1,
    is_expiry_managed TINYINT(1) NOT NULL DEFAULT 1,
    cold_chain_required TINYINT(1) NOT NULL DEFAULT 0,
    min_remaining_shelf_life_days INT NOT NULL DEFAULT 180,
    valuation_rate DECIMAL(18,2) NOT NULL DEFAULT 0,
    default_warehouse_code VARCHAR(30) DEFAULT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_item_group FOREIGN KEY (item_group_code)
        REFERENCES bootstrap_item_group(item_group_code),
    CONSTRAINT fk_item_default_warehouse FOREIGN KEY (default_warehouse_code)
        REFERENCES bootstrap_warehouse(warehouse_code)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE bootstrap_batch (
    batch_no VARCHAR(50) PRIMARY KEY,
    item_code VARCHAR(40) NOT NULL,
    warehouse_code VARCHAR(30) NOT NULL,
    batch_status VARCHAR(20) NOT NULL,
    manufacturing_date DATE DEFAULT NULL,
    expiry_date DATE DEFAULT NULL,
    qty_on_hand DECIMAL(18,3) NOT NULL DEFAULT 0,
    temperature_excursion_flag TINYINT(1) NOT NULL DEFAULT 0,
    coa_no VARCHAR(50) DEFAULT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_batch_item FOREIGN KEY (item_code)
        REFERENCES bootstrap_item(item_code),
    CONSTRAINT fk_batch_warehouse FOREIGN KEY (warehouse_code)
        REFERENCES bootstrap_warehouse(warehouse_code)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE bootstrap_sales_order (
    so_no VARCHAR(30) PRIMARY KEY,
    company_code VARCHAR(20) NOT NULL,
    customer_code VARCHAR(30) NOT NULL,
    order_date DATE NOT NULL,
    status VARCHAR(30) NOT NULL,
    currency VARCHAR(10) NOT NULL DEFAULT 'VND',
    tax_code VARCHAR(40) NOT NULL,
    total_before_tax DECIMAL(18,2) NOT NULL,
    total_tax DECIMAL(18,2) NOT NULL,
    grand_total DECIMAL(18,2) NOT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_so_company FOREIGN KEY (company_code)
        REFERENCES bootstrap_company(company_code),
    CONSTRAINT fk_so_customer FOREIGN KEY (customer_code)
        REFERENCES bootstrap_customer(customer_code)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE bootstrap_sales_order_item (
    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
    so_no VARCHAR(30) NOT NULL,
    item_code VARCHAR(40) NOT NULL,
    batch_no VARCHAR(50) DEFAULT NULL,
    warehouse_code VARCHAR(30) NOT NULL,
    qty DECIMAL(18,3) NOT NULL,
    rate DECIMAL(18,2) NOT NULL,
    line_amount DECIMAL(18,2) NOT NULL,
    vat_rate DECIMAL(5,2) NOT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_soi_so FOREIGN KEY (so_no)
        REFERENCES bootstrap_sales_order(so_no),
    CONSTRAINT fk_soi_item FOREIGN KEY (item_code)
        REFERENCES bootstrap_item(item_code),
    CONSTRAINT fk_soi_batch FOREIGN KEY (batch_no)
        REFERENCES bootstrap_batch(batch_no),
    CONSTRAINT fk_soi_warehouse FOREIGN KEY (warehouse_code)
        REFERENCES bootstrap_warehouse(warehouse_code)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE bootstrap_purchase_order (
    po_no VARCHAR(30) PRIMARY KEY,
    company_code VARCHAR(20) NOT NULL,
    supplier_code VARCHAR(30) NOT NULL,
    order_date DATE NOT NULL,
    status VARCHAR(30) NOT NULL,
    currency VARCHAR(10) NOT NULL DEFAULT 'VND',
    tax_code VARCHAR(40) NOT NULL,
    total_before_tax DECIMAL(18,2) NOT NULL,
    total_tax DECIMAL(18,2) NOT NULL,
    grand_total DECIMAL(18,2) NOT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_po_company FOREIGN KEY (company_code)
        REFERENCES bootstrap_company(company_code),
    CONSTRAINT fk_po_supplier FOREIGN KEY (supplier_code)
        REFERENCES bootstrap_supplier(supplier_code)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE bootstrap_purchase_order_item (
    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
    po_no VARCHAR(30) NOT NULL,
    item_code VARCHAR(40) NOT NULL,
    warehouse_code VARCHAR(30) NOT NULL,
    qty DECIMAL(18,3) NOT NULL,
    rate DECIMAL(18,2) NOT NULL,
    line_amount DECIMAL(18,2) NOT NULL,
    vat_rate DECIMAL(5,2) NOT NULL,
    supplier_batch_no VARCHAR(50) DEFAULT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_poi_po FOREIGN KEY (po_no)
        REFERENCES bootstrap_purchase_order(po_no),
    CONSTRAINT fk_poi_item FOREIGN KEY (item_code)
        REFERENCES bootstrap_item(item_code),
    CONSTRAINT fk_poi_warehouse FOREIGN KEY (warehouse_code)
        REFERENCES bootstrap_warehouse(warehouse_code)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
