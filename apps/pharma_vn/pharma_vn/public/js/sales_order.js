frappe.ui.form.on("Sales Order", {
    refresh(frm) {
        window.requestAnimationFrame(() => {
            window.pharma_vn?.document_flow?.refresh(frm);
        });
    },
});
