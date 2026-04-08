frappe.ui.form.on("User Access Profile", {
    refresh(frm) {
        frm.clear_custom_buttons();
        if (frm.doc.user) {
            frm.add_custom_button(__("Refresh Effective Access"), () => frm.reload_doc());
            frm.add_custom_button(__("Add Accountant Base"), () => {
                frm.add_child("group_assignments", {
                    access_group: "Accountant Base",
                    priority: 100,
                    is_active: 1,
                });
                frm.refresh_field("group_assignments");
                frm.dirty();
            });
        }
    },
});
