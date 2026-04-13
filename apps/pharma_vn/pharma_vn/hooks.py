app_name = "pharma_vn"
app_title = "Pharma Vietnam"
app_publisher = "OpenAI Codex"
app_description = "ERPNext customizations for pharmaceutical operations in Vietnam"
app_email = "support@example.com"
app_license = "MIT"
required_apps = ["erpnext"]
ASSET_VERSION = "20260413.1115"

after_install = "pharma_vn.install.after_install"
after_migrate = "pharma_vn.install.after_migrate"
override_doctype_class = {
    "Customer": "pharma_vn.overrides.customer.PharmaVNCustomer",
}
app_include_css = [
    f"/assets/pharma_vn/css/pharma_byd.css?v={ASSET_VERSION}",
    f"/assets/pharma_vn/css/erp_home.css?v={ASSET_VERSION}",
    f"/assets/pharma_vn/css/hrm_custom_pages.css?v={ASSET_VERSION}",
    f"/assets/pharma_vn/css/customer_risk_widget.css?v={ASSET_VERSION}",
]
app_include_js = [
    f"/assets/pharma_vn/js/document_flow.js?v={ASSET_VERSION}",
    f"/assets/pharma_vn/js/erp_home.js?v={ASSET_VERSION}",
    f"/assets/pharma_vn/js/ai_assistant.js?v={ASSET_VERSION}",
    f"/assets/pharma_vn/js/transaction_vat.js?v={ASSET_VERSION}",
    f"/assets/pharma_vn/js/customer_quick_entry.js?v={ASSET_VERSION}",
    f"/assets/pharma_vn/js/hrm_custom_pages.js?v={ASSET_VERSION}",
]
doctype_js = {
    "Quotation": "public/js/document_flow_form.js",
    "Customer": "public/js/customer.js",
    "Sales Order": "public/js/sales_order.js",
    "Delivery Note": "public/js/delivery_note.js",
    "Sales Invoice": "public/js/sales_invoice.js",
    "Material Request": "public/js/document_flow_form.js",
    "Purchase Order": "public/js/document_flow_form.js",
    "Purchase Receipt": "public/js/purchase_inbound.js",
    "Purchase Invoice": "public/js/purchase_inbound.js",
    "Payment Entry": "public/js/document_flow_form.js",
    "Stock Entry": "public/js/document_flow_form.js",
    "Dynamic Form": "public/js/dynamic_form.js",
    "Form Extension Manager": "public/js/form_extension_manager.js",
    "User Access Profile": "public/js/user_access_profile.js",
    "Access Group": "public/js/access_group.js",
    "Salary Slip": "public/js/salary_slip.js",
}

doc_events = {
    "Sales Order": {
        "validate": "pharma_vn.automation.sales_order.validate_sales_order",
        "before_submit": "pharma_vn.risk_assessment.service.block_high_risk_sales_order",
        "on_submit": "pharma_vn.automation.next_documents.create_follow_up_for_sales_order",
    },
    "Quotation": {
        "validate": "pharma_vn.automation.transaction_taxes.sync_transaction_taxes",
    },
    "Delivery Note": {
        "validate": "pharma_vn.automation.delivery_note.validate_delivery_note",
        "before_submit": "pharma_vn.automation.delivery_note.validate_storage_locations_for_submit",
        "on_submit": "pharma_vn.automation.delivery_note.handle_delivery_note_on_submit",
        "on_cancel": "pharma_vn.automation.delivery_note.handle_delivery_note_on_cancel",
    },
    "Sales Invoice": {
        "validate": "pharma_vn.automation.sales_invoice.validate_sales_invoice",
        "on_submit": "pharma_vn.automation.sales_invoice.prepare_e_invoice_payload",
    },
    "Purchase Order": {
        "validate": "pharma_vn.automation.transaction_taxes.sync_transaction_taxes",
        "on_submit": "pharma_vn.automation.next_documents.create_follow_up_for_purchase_order",
    },
    "Purchase Receipt": {
        "validate": "pharma_vn.automation.purchase_receipt.validate_purchase_receipt",
        "on_submit": "pharma_vn.automation.purchase_receipt.handle_purchase_receipt_on_submit",
        "on_cancel": "pharma_vn.automation.purchase_receipt.handle_purchase_receipt_on_cancel",
    },
    "Purchase Invoice": {
        "validate": "pharma_vn.automation.transaction_taxes.sync_transaction_taxes",
    },
    "Salary Slip": {
        "before_save": "pharma_vn.hrm.payroll.before_save_salary_slip",
    },
}

scheduler_events = {
    "hourly": [
        "pharma_vn.automation.scheduler.process_temperature_excursions",
        "pharma_vn.automation.scheduler.process_invoice_failures",
        "pharma_vn.automation.scheduler.process_stock_mismatches",
    ],
    "daily": ["pharma_vn.automation.scheduler.process_near_expiry_batches"],
    "monthly": ["pharma_vn.hrm.payroll.run_monthly_payroll_scheduler"],
}
