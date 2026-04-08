SET NAMES utf8mb4;

INSERT INTO bootstrap_company (
    company_code, company_name, tax_id, registration_no, base_currency, country, accounting_regime, vat_method
) VALUES (
    'VAP',
    'Viet An Pharma JSC',
    '0312345678',
    'DN-2026-ERP-PHARMA',
    'VND',
    'Vietnam',
    'Thong tu 99/2025/TT-BTC',
    'Khau tru'
);

INSERT INTO bootstrap_account (
    company_code, account_number, account_name, parent_account_number, root_type, report_type, account_type, is_group, is_tax_account, legal_basis
) VALUES
('VAP', '111', 'Tien mat', NULL, 'Asset', 'Balance Sheet', 'Cash', 1, 0, 'TT99/2025/TT-BTC'),
('VAP', '1111', 'Tien mat VND', '111', 'Asset', 'Balance Sheet', 'Cash', 0, 0, 'TT99/2025/TT-BTC'),
('VAP', '112', 'Tien gui ngan hang', NULL, 'Asset', 'Balance Sheet', 'Bank', 1, 0, 'TT99/2025/TT-BTC'),
('VAP', '1121', 'Tien gui ngan hang VND', '112', 'Asset', 'Balance Sheet', 'Bank', 0, 0, 'TT99/2025/TT-BTC'),
('VAP', '131', 'Phai thu cua khach hang', NULL, 'Asset', 'Balance Sheet', 'Receivable', 0, 0, 'TT99/2025/TT-BTC'),
('VAP', '133', 'Thue GTGT duoc khau tru', NULL, 'Asset', 'Balance Sheet', 'Tax', 1, 1, 'TT99/2025/TT-BTC (implementation mapping)'),
('VAP', '1331', 'Thue GTGT duoc khau tru cua hang hoa dich vu', '133', 'Asset', 'Balance Sheet', 'Tax', 0, 1, 'TT99/2025/TT-BTC (implementation mapping)'),
('VAP', '1332', 'Thue GTGT duoc khau tru cua tai san co dinh', '133', 'Asset', 'Balance Sheet', 'Tax', 0, 1, 'TT99/2025/TT-BTC (implementation mapping)'),
('VAP', '141', 'Tam ung', NULL, 'Asset', 'Balance Sheet', 'Current Asset', 0, 0, 'TT99/2025/TT-BTC'),
('VAP', '152', 'Nguyen lieu vat lieu', NULL, 'Asset', 'Balance Sheet', 'Stock', 0, 0, 'TT99/2025/TT-BTC'),
('VAP', '153', 'Cong cu dung cu', NULL, 'Asset', 'Balance Sheet', 'Current Asset', 0, 0, 'TT99/2025/TT-BTC'),
('VAP', '154', 'Chi phi san xuat kinh doanh do dang', NULL, 'Asset', 'Balance Sheet', 'Stock', 0, 0, 'TT99/2025/TT-BTC'),
('VAP', '155', 'Thanh pham', NULL, 'Asset', 'Balance Sheet', 'Stock', 0, 0, 'TT99/2025/TT-BTC'),
('VAP', '156', 'Hang hoa', NULL, 'Asset', 'Balance Sheet', 'Stock', 0, 0, 'TT99/2025/TT-BTC'),
('VAP', '211', 'Tai san co dinh huu hinh', NULL, 'Asset', 'Balance Sheet', 'Fixed Asset', 1, 0, 'TT99/2025/TT-BTC'),
('VAP', '2113', 'May moc thiet bi', '211', 'Asset', 'Balance Sheet', 'Fixed Asset', 0, 0, 'TT99/2025/TT-BTC'),
('VAP', '214', 'Hao mon tai san co dinh', NULL, 'Asset', 'Balance Sheet', 'Accumulated Depreciation', 1, 0, 'TT99/2025/TT-BTC'),
('VAP', '2141', 'Hao mon tai san co dinh huu hinh', '214', 'Asset', 'Balance Sheet', 'Accumulated Depreciation', 0, 0, 'TT99/2025/TT-BTC'),
('VAP', '242', 'Chi phi tra truoc', NULL, 'Asset', 'Balance Sheet', 'Current Asset', 0, 0, 'TT99/2025/TT-BTC'),
('VAP', '331', 'Phai tra nguoi ban', NULL, 'Liability', 'Balance Sheet', 'Payable', 0, 0, 'TT99/2025/TT-BTC'),
('VAP', '333', 'Thue va cac khoan phai nop nha nuoc', NULL, 'Liability', 'Balance Sheet', 'Tax', 1, 1, 'TT99/2025/TT-BTC'),
('VAP', '33311', 'Thue GTGT dau ra phai nop', '333', 'Liability', 'Balance Sheet', 'Tax', 0, 1, 'TT99/2025/TT-BTC; official MOF Q&A in 2026 still references TK 33311'),
('VAP', '33312', 'Thue GTGT hang nhap khau', '333', 'Liability', 'Balance Sheet', 'Tax', 0, 1, 'TT99/2025/TT-BTC (implementation mapping)'),
('VAP', '3334', 'Thue thu nhap doanh nghiep', '333', 'Liability', 'Balance Sheet', 'Tax', 0, 1, 'TT99/2025/TT-BTC'),
('VAP', '3335', 'Thue thu nhap ca nhan', '333', 'Liability', 'Balance Sheet', 'Tax', 0, 1, 'TT99/2025/TT-BTC'),
('VAP', '334', 'Phai tra nguoi lao dong', NULL, 'Liability', 'Balance Sheet', 'Payable', 0, 0, 'TT99/2025/TT-BTC'),
('VAP', '338', 'Phai tra phai nop khac', NULL, 'Liability', 'Balance Sheet', 'Current Liability', 1, 0, 'TT99/2025/TT-BTC'),
('VAP', '3383', 'Bao hiem xa hoi', '338', 'Liability', 'Balance Sheet', 'Current Liability', 0, 0, 'TT99/2025/TT-BTC'),
('VAP', '3384', 'Bao hiem y te', '338', 'Liability', 'Balance Sheet', 'Current Liability', 0, 0, 'TT99/2025/TT-BTC'),
('VAP', '3386', 'Bao hiem that nghiep', '338', 'Liability', 'Balance Sheet', 'Current Liability', 0, 0, 'TT99/2025/TT-BTC'),
('VAP', '411', 'Von dau tu cua chu so huu', NULL, 'Equity', 'Balance Sheet', 'Equity', 1, 0, 'TT99/2025/TT-BTC'),
('VAP', '4111', 'Von gop cua chu so huu', '411', 'Equity', 'Balance Sheet', 'Equity', 0, 0, 'TT99/2025/TT-BTC'),
('VAP', '421', 'Loi nhuan sau thue chua phan phoi', NULL, 'Equity', 'Balance Sheet', 'Equity', 1, 0, 'TT99/2025/TT-BTC'),
('VAP', '4212', 'Loi nhuan sau thue chua phan phoi nam nay', '421', 'Equity', 'Balance Sheet', 'Equity', 0, 0, 'TT99/2025/TT-BTC'),
('VAP', '511', 'Doanh thu ban hang va cung cap dich vu', NULL, 'Income', 'Profit and Loss', 'Income Account', 1, 0, 'TT99/2025/TT-BTC'),
('VAP', '5111', 'Doanh thu ban hang hoa', '511', 'Income', 'Profit and Loss', 'Income Account', 0, 0, 'TT99/2025/TT-BTC'),
('VAP', '5112', 'Doanh thu ban thanh pham', '511', 'Income', 'Profit and Loss', 'Income Account', 0, 0, 'TT99/2025/TT-BTC'),
('VAP', '515', 'Doanh thu hoat dong tai chinh', NULL, 'Income', 'Profit and Loss', 'Income Account', 0, 0, 'TT99/2025/TT-BTC'),
('VAP', '521', 'Cac khoan giam tru doanh thu', NULL, 'Income', 'Profit and Loss', 'Income Account', 1, 0, 'TT99/2025/TT-BTC'),
('VAP', '5211', 'Chiet khau thuong mai', '521', 'Income', 'Profit and Loss', 'Income Account', 0, 0, 'TT99/2025/TT-BTC'),
('VAP', '632', 'Gia von hang ban', NULL, 'Expense', 'Profit and Loss', 'Cost of Goods Sold', 0, 0, 'TT99/2025/TT-BTC'),
('VAP', '635', 'Chi phi tai chinh', NULL, 'Expense', 'Profit and Loss', 'Expense Account', 0, 0, 'TT99/2025/TT-BTC'),
('VAP', '641', 'Chi phi ban hang', NULL, 'Expense', 'Profit and Loss', 'Expense Account', 0, 0, 'TT99/2025/TT-BTC'),
('VAP', '642', 'Chi phi quan ly doanh nghiep', NULL, 'Expense', 'Profit and Loss', 'Expense Account', 0, 0, 'TT99/2025/TT-BTC'),
('VAP', '711', 'Thu nhap khac', NULL, 'Income', 'Profit and Loss', 'Income Account', 0, 0, 'TT99/2025/TT-BTC'),
('VAP', '811', 'Chi phi khac', NULL, 'Expense', 'Profit and Loss', 'Expense Account', 0, 0, 'TT99/2025/TT-BTC'),
('VAP', '8211', 'Chi phi thue TNDN hien hanh', NULL, 'Expense', 'Profit and Loss', 'Tax', 0, 1, 'TT99/2025/TT-BTC'),
('VAP', '911', 'Xac dinh ket qua kinh doanh', NULL, 'Equity', 'Profit and Loss', 'Temporary', 0, 0, 'TT99/2025/TT-BTC');

INSERT INTO bootstrap_tax_template (
    company_code, tax_code, tax_name, tax_scope, rate, account_number, legal_basis, effective_from, effective_to, applies_to, notes
) VALUES
('VAP', 'VAT-OUT-5', 'VAT output 5 percent', 'Output', 5.00, '33311', 'Luat 48/2024/QH15; reviewed against Luat 149/2025/QH15 context', '2025-07-01', NULL, 'Medicines, preventive drugs, pharmaceutical raw materials, medical devices where applicable', 'Dung cho thuoc chua benh, thuoc phong benh, duoc chat nguyen lieu san xuat thuoc. Can doi chieu voi tax advisor khi go-live.'),
('VAP', 'VAT-IN-5', 'VAT input 5 percent', 'Input', 5.00, '1331', 'Luat 48/2024/QH15; reviewed against Luat 149/2025/QH15 context', '2025-07-01', NULL, 'Deductible input VAT for qualifying 5 percent goods', 'Mapping trien khai cho ERPNext.'),
('VAP', 'VAT-OUT-8', 'VAT output 8 percent', 'Output', 8.00, '33311', 'Nghi quyet 204/2025/QH15; Nghi dinh 174/2025/ND-CP', '2025-07-01', '2026-12-31', 'Eligible goods and services normally subject to 10 percent VAT', 'Chi ap dung cho nhom du dieu kien giam 2 percent. Can xac minh theo item category thuc te.'),
('VAP', 'VAT-IN-8', 'VAT input 8 percent', 'Input', 8.00, '1331', 'Nghi quyet 204/2025/QH15; Nghi dinh 174/2025/ND-CP', '2025-07-01', '2026-12-31', 'Deductible input VAT for qualifying reduced-rate goods and services', 'Template de dung trong giai doan giam thue.'),
('VAP', 'VAT-OUT-10', 'VAT output 10 percent', 'Output', 10.00, '33311', 'Luat 48/2024/QH15; reviewed against Luat 149/2025/QH15 context', '2025-07-01', NULL, 'General rate for goods and services not in 0/5 percent and not under temporary reduction', 'Dung cho nhom hang hoa dich vu ap dung muc thong thuong 10 percent.'),
('VAP', 'VAT-IN-10', 'VAT input 10 percent', 'Input', 10.00, '1331', 'Luat 48/2024/QH15; reviewed against Luat 149/2025/QH15 context', '2025-07-01', NULL, 'Deductible input VAT for 10 percent goods and services', 'Mapping trien khai cho ERPNext.'),
('VAP', 'VAT-OUT-0', 'VAT output 0 percent', 'Output', 0.00, '33311', 'Luat 48/2024/QH15; reviewed against Luat 149/2025/QH15 context', '2025-07-01', NULL, 'Export sales and zero-rated supplies where conditions are met', 'Chi dung khi dap ung day du dieu kien ho so zero-rate.');

INSERT INTO bootstrap_item_group (
    item_group_code, item_group_name, parent_item_group_code, is_stock_item, description
) VALUES
('PHARMA', 'Pharma Root', NULL, 1, 'Top level item group for pharma business'),
('FG', 'Finished Goods', 'PHARMA', 1, 'Finished goods for sale'),
('RM', 'Raw Materials', 'PHARMA', 1, 'API and excipients'),
('PM', 'Packaging Materials', 'PHARMA', 1, 'Cartons, foils, labels'),
('OTC', 'OTC Medicines', 'FG', 1, 'Over-the-counter finished medicines'),
('ETC', 'ETC Medicines', 'FG', 1, 'Prescription medicines'),
('SUPP', 'Supplements', 'FG', 1, 'Food supplements and wellness products');

INSERT INTO bootstrap_warehouse (
    warehouse_code, warehouse_name, branch_code, warehouse_type, parent_warehouse_code, cold_chain_enabled, is_sellable
) VALUES
('WH-BD', 'Binh Duong Main Site', 'BD', 'Site', NULL, 0, 0),
('WH-BD-RM-QUA', 'Binh Duong Raw Material Quarantine', 'BD', 'Raw Material', 'WH-BD', 0, 0),
('WH-BD-RM-REL', 'Binh Duong Raw Material Released', 'BD', 'Raw Material', 'WH-BD', 0, 0),
('WH-BD-FG-QUA', 'Binh Duong Finished Goods Quarantine', 'BD', 'Finished Goods', 'WH-BD', 0, 0),
('WH-BD-FG-REL', 'Binh Duong Finished Goods Released', 'BD', 'Finished Goods', 'WH-BD', 0, 1),
('WH-HCM', 'HCM Distribution Site', 'HCM', 'Site', NULL, 0, 0),
('WH-HCM-FG-REL', 'HCM Finished Goods Released', 'HCM', 'Finished Goods', 'WH-HCM', 0, 1),
('WH-HN', 'Ha Noi Distribution Site', 'HN', 'Site', NULL, 0, 0),
('WH-HN-FG-REL', 'Ha Noi Finished Goods Released', 'HN', 'Finished Goods', 'WH-HN', 0, 1),
('WH-COLD-2-8', 'Cold Storage 2 to 8C', 'BD', 'Cold Storage', 'WH-BD', 1, 1),
('WH-RETURNS', 'Customer Returns Warehouse', 'BD', 'Returns', 'WH-BD', 0, 0),
('WH-REJECTED', 'Rejected Warehouse', 'BD', 'Rejected', 'WH-BD', 0, 0);
