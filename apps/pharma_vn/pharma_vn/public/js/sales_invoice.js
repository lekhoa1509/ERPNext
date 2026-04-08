frappe.ui.form.on("Sales Invoice", {
    refresh(frm) {
        window.requestAnimationFrame(() => {
            window.pharma_vn?.document_flow?.refresh(frm);
        });
    },
});
