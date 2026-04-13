frappe.ui.form.on("Customer", {
    refresh(frm) {
        hideLegacyRiskUI(frm);
    },
});

function hideLegacyRiskUI(frm) {
    frm.remove_custom_button(__("Check Risk"));
    frm.remove_custom_button(__("Open Risk History"));

    ["customer_risk_assessment_section", "customer_risk_dashboard_html"].forEach((fieldname) => {
        const field = frm.get_field(fieldname);
        if (!field) {
            return;
        }

        frm.set_df_property(fieldname, "hidden", 1);
        frm.refresh_field(fieldname);

        if (field.wrapper) {
            $(field.wrapper).closest(".form-section, .frappe-control").hide();
        }
    });
}
