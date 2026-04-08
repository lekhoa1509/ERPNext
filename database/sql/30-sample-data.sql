SET NAMES utf8mb4;

INSERT INTO bootstrap_supplier (
    supplier_code, supplier_name, supplier_type, tax_id, gmp_certificate_no, gmp_expiry, approved_status, country
) VALUES
('SUP-RM-DOM-001', 'Sai Gon API Trading', 'Trader', '0309988776', 'GMP-VN-API-2026-01', '2027-12-31', 'Approved', 'Vietnam'),
('SUP-PM-DOM-001', 'Bao Bi An Phat', 'Manufacturer', '0311122233', NULL, NULL, 'Approved', 'Vietnam'),
('SUP-IMP-001', 'Global Pharma Ingredients Pte', 'Importer', 'SG998877', 'GMP-SG-2026-88', '2028-03-31', 'Approved', 'Singapore');

INSERT INTO bootstrap_customer (
    customer_code, customer_name, customer_channel, tax_id, license_no, license_expiry, payment_terms_days, credit_limit, territory
) VALUES
('CUS-PHAR-HCM-001', 'Nha Thuoc Minh Chau Quan 3', 'Pharmacy', '0319988776', 'GPP-HCM-2026-1001', '2027-06-30', 30, 200000000.00, 'HCM'),
('CUS-HOSP-HCM-001', 'Phong Kham Da Khoa An Khang', 'Clinic', '0318877665', 'BYT-HCM-2026-2201', '2027-12-31', 45, 500000000.00, 'HCM'),
('CUS-DIST-HN-001', 'Cong ty Phan Phoi Duoc Ha Noi', 'Distributor', '0101122233', 'GDP-HN-2026-7788', '2028-01-31', 60, 1500000000.00, 'HN');

INSERT INTO bootstrap_item (
    item_code, item_name, item_group_code, item_type, stock_uom, vat_output_tax_code, vat_input_tax_code,
    is_batch_managed, is_expiry_managed, cold_chain_required, min_remaining_shelf_life_days, valuation_rate, default_warehouse_code
) VALUES
('PARA500-H10X10', 'Paracetamol 500mg Hop 10x10', 'OTC', 'Finished Good', 'Box', 'VAT-OUT-5', 'VAT-IN-5', 1, 1, 0, 180, 18200.00, 'WH-BD-FG-REL'),
('AMOX500-H10X10', 'Amoxicillin 500mg Hop 10x10', 'ETC', 'Finished Good', 'Box', 'VAT-OUT-5', 'VAT-IN-5', 1, 1, 0, 180, 26300.00, 'WH-HCM-FG-REL'),
('API-PARACETAMOL', 'Paracetamol API', 'RM', 'Raw Material', 'Kg', 'VAT-OUT-5', 'VAT-IN-5', 1, 1, 0, 365, 160000.00, 'WH-BD-RM-REL'),
('BOX-OTC-001', 'Printed OTC Folding Box', 'PM', 'Packaging Material', 'Nos', 'VAT-OUT-10', 'VAT-IN-10', 0, 0, 0, 0, 950.00, 'WH-BD-RM-REL'),
('VITC-1000-30V', 'Vitamin C 1000mg Hop 30 vien', 'SUPP', 'Finished Good', 'Box', 'VAT-OUT-10', 'VAT-IN-10', 1, 1, 0, 180, 42500.00, 'WH-HN-FG-REL'),
('LOG-SVC-ELIG-8', 'Logistics Service Eligible 8 Percent', 'PHARMA', 'Service', 'Service', 'VAT-OUT-8', 'VAT-IN-8', 0, 0, 0, 0, 0.00, NULL);

INSERT INTO bootstrap_batch (
    batch_no, item_code, warehouse_code, batch_status, manufacturing_date, expiry_date, qty_on_hand, temperature_excursion_flag, coa_no
) VALUES
('BATCH-PARA-2603-001', 'PARA500-H10X10', 'WH-BD-FG-REL', 'Released', '2026-03-10', '2028-03-31', 1200.000, 0, 'COA-PARA-2603-001'),
('BATCH-AMOX-2602-001', 'AMOX500-H10X10', 'WH-HCM-FG-REL', 'Released', '2026-02-15', '2028-02-28', 680.000, 0, 'COA-AMOX-2602-001'),
('BATCH-API-PARA-2601-001', 'API-PARACETAMOL', 'WH-BD-RM-REL', 'Released', '2026-01-12', '2029-01-31', 500.000, 0, 'COA-API-PARA-2601-001'),
('BATCH-VITC-2603-001', 'VITC-1000-30V', 'WH-HN-FG-REL', 'Released', '2026-03-05', '2027-12-31', 300.000, 0, 'COA-VITC-2603-001'),
('BATCH-PARA-COLD-2604-001', 'PARA500-H10X10', 'WH-COLD-2-8', 'Hold', '2026-04-01', '2028-03-31', 50.000, 1, 'COA-PARA-COLD-2604-001');

INSERT INTO bootstrap_purchase_order (
    po_no, company_code, supplier_code, order_date, status, currency, tax_code, total_before_tax, total_tax, grand_total
) VALUES
('PO-RM-2026-0001', 'VAP', 'SUP-RM-DOM-001', '2026-04-02', 'To Receive and Bill', 'VND', 'VAT-IN-5', 32000000.00, 1600000.00, 33600000.00),
('PO-PM-2026-0002', 'VAP', 'SUP-PM-DOM-001', '2026-04-03', 'Draft', 'VND', 'VAT-IN-10', 9500000.00, 950000.00, 10450000.00);

INSERT INTO bootstrap_purchase_order_item (
    po_no, item_code, warehouse_code, qty, rate, line_amount, vat_rate, supplier_batch_no
) VALUES
('PO-RM-2026-0001', 'API-PARACETAMOL', 'WH-BD-RM-QUA', 200.000, 160000.00, 32000000.00, 5.00, 'SUPB-API-APR-2026'),
('PO-PM-2026-0002', 'BOX-OTC-001', 'WH-BD-RM-QUA', 10000.000, 950.00, 9500000.00, 10.00, NULL);

INSERT INTO bootstrap_sales_order (
    so_no, company_code, customer_code, order_date, status, currency, tax_code, total_before_tax, total_tax, grand_total
) VALUES
('SO-B2B-2026-0001', 'VAP', 'CUS-PHAR-HCM-001', '2026-04-05', 'To Deliver and Bill', 'VND', 'VAT-OUT-5', 3500000.00, 175000.00, 3675000.00),
('SO-B2B-2026-0002', 'VAP', 'CUS-DIST-HN-001', '2026-04-06', 'Draft', 'VND', 'VAT-OUT-5', 6312000.00, 315600.00, 6627600.00);

INSERT INTO bootstrap_sales_order_item (
    so_no, item_code, batch_no, warehouse_code, qty, rate, line_amount, vat_rate
) VALUES
('SO-B2B-2026-0001', 'PARA500-H10X10', 'BATCH-PARA-2603-001', 'WH-BD-FG-REL', 100.000, 35000.00, 3500000.00, 5.00),
('SO-B2B-2026-0002', 'AMOX500-H10X10', 'BATCH-AMOX-2602-001', 'WH-HCM-FG-REL', 240.000, 26300.00, 6312000.00, 5.00);
