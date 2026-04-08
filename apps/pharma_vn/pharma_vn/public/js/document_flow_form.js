function refreshPharmaDocumentFlow(frm) {
    window.requestAnimationFrame(() => {
        window.pharma_vn?.document_flow?.refresh(frm);
    });
}

[
    "Quotation",
    "Purchase Order",
    "Purchase Invoice",
    "Payment Entry",
    "Material Request",
    "Stock Entry",
].forEach((doctype) => {
    frappe.ui.form.on(doctype, {
        refresh(frm) {
            refreshPharmaDocumentFlow(frm);
        },
    });
});
