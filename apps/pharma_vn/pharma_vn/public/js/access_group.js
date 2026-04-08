frappe.ui.form.on("Access Group", {
    refresh(frm) {
        if (frm.is_new()) {
            frm.add_custom_button(__("Load Accountant Base"), () => {
                loadAccountantBase(frm);
            });
        }
    },
});

function loadAccountantBase(frm) {
    frm.set_value("group_name", "Accountant Base");
    frm.set_value("description", "Base access set for accounting staff.");
    frm.clear_table("permissions_matrix");

    [
        "ACC_DASHBOARD",
        "ACC_PAYMENT_ENTRY",
        "ACC_JOURNAL_ENTRY",
        "ACC_AR_AP",
    ].forEach((code) => {
        frm.add_child("permissions_matrix", {
            function_access: code,
            access_mode: "Allow",
        });
    });

    frm.refresh_field("permissions_matrix");
    frm.dirty();
}
