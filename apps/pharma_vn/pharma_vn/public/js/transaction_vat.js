(() => {
    const SALES_DOCTYPES = new Set(["Quotation", "Sales Order", "Delivery Note", "Sales Invoice"]);
    const ROW_DOCTYPES = [
        "Quotation Item",
        "Sales Order Item",
        "Delivery Note Item",
        "Sales Invoice Item",
        "Purchase Order Item",
        "Purchase Receipt Item",
        "Purchase Invoice Item",
    ];

    function getItemVatField(parentDoctype) {
        return SALES_DOCTYPES.has(parentDoctype)
            ? "pharma_default_sales_vat_rate"
            : "pharma_default_purchase_vat_rate";
    }

    function refreshTaxes(frm) {
        if (typeof frm.cscript?.calculate_taxes_and_totals === "function") {
            frm.cscript.calculate_taxes_and_totals();
        }
        frm.refresh_field("taxes");
        frm.refresh_field("items");
    }

    function applyVatChoice(frm, cdt, cdn) {
        const row = locals[cdt][cdn];
        if (!row || !frm.doc.company || !row.pharma_vat_rate) {
            return Promise.resolve();
        }

        return frappe.call({
            method: "pharma_vn.api.taxes.get_item_vat_choice",
            args: {
                company: frm.doc.company,
                parent_doctype: frm.doc.doctype,
                vat_rate: row.pharma_vat_rate,
            },
        }).then((response) => {
            const choice = response.message || {};
            return frappe.model
                .set_value(cdt, cdn, "item_tax_template", choice.item_tax_template || "")
                .then(() => frappe.model.set_value(cdt, cdn, "item_tax_rate", choice.item_tax_rate || "{}"))
                .then(() => {
                    if (!frm.doc.taxes_and_charges) {
                        return;
                    }
                    return frm.set_value("taxes_and_charges", "");
                })
                .then(() => refreshTaxes(frm));
        });
    }

    function syncVatFromItem(frm, cdt, cdn) {
        const row = locals[cdt][cdn];
        if (!row?.item_code) {
            return;
        }

        frappe.db
            .get_value("Item", row.item_code, getItemVatField(frm.doc.doctype))
            .then((response) => {
                const fieldname = getItemVatField(frm.doc.doctype);
                const vatRate = response.message?.[fieldname] || "10";
                return frappe.model.set_value(cdt, cdn, "pharma_vat_rate", vatRate);
            })
            .then(() => applyVatChoice(frm, cdt, cdn));
    }

    ROW_DOCTYPES.forEach((doctype) => {
        frappe.ui.form.on(doctype, {
            item_code(frm, cdt, cdn) {
                syncVatFromItem(frm, cdt, cdn);
            },
            pharma_vat_rate(frm, cdt, cdn) {
                applyVatChoice(frm, cdt, cdn);
            },
        });
    });
})();
