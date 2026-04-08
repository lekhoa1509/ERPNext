const EXTENSION_WIZARDS = {
    Customer: {
        extension_name: "Customer Enrichment Pack",
        description: "Adds account profiling, approval notes, and onboarding details to Customer.",
        rows: [
            { label: "Customer Enrichment", fieldtype: "Section Break", reference_fieldname: "customer_enrichment", insert_after: "territory" },
            { label: "Approval Note", fieldtype: "Small Text", reference_fieldname: "approval_note", insert_after: "territory", description: "Internal approval note for customer onboarding." },
            { label: "Sales Channel", fieldtype: "Select", reference_fieldname: "sales_channel_ext", insert_after: "ext_customer_enrichment__", options: "Retail\nWholesale\nMarketplace\nKey Account", in_list_view: 1 },
            { label: "Onboarding Owner", fieldtype: "Link", reference_fieldname: "onboarding_owner", insert_after: "ext_customer_enrichment_approval_note", link_doctype: "User" },
        ],
    },
    "Sales Order": {
        extension_name: "Sales Order Commercial Pack",
        description: "Adds commercial notes, contract tracking, and approval checkpoints to Sales Order.",
        rows: [
            { label: "Commercial Controls", fieldtype: "Section Break", reference_fieldname: "commercial_controls", insert_after: "delivery_date" },
            { label: "Contract Reference", fieldtype: "Data", reference_fieldname: "contract_reference_ext", insert_after: "delivery_date", in_list_view: 1 },
            { label: "Approval Note", fieldtype: "Small Text", reference_fieldname: "approval_note_ext", insert_after: "ext_sales_order_commerci_contract_reference" },
            { label: "Commercial Reviewer", fieldtype: "Link", reference_fieldname: "commercial_reviewer", insert_after: "ext_sales_order_commerci_approval_note_ext", link_doctype: "User" },
        ],
    },
};

frappe.ui.form.on("Form Extension Manager", {
    refresh(frm) {
        addActions(frm);
        refreshTargetSchema(frm);
    },
    target_doctype(frm) {
        refreshTargetSchema(frm);
    },
});

frappe.ui.form.on("Form Extension Field", {
    label(frm) {
        frm.trigger("target_doctype");
    },
    fieldtype(frm) {
        frm.trigger("target_doctype");
    },
    insert_after(frm) {
        frm.trigger("target_doctype");
    },
});

function addActions(frm) {
    frm.clear_custom_buttons();
    addWizardButtons(frm);
    frm.add_custom_button(__("Refresh Base Schema"), () => refreshTargetSchema(frm));

    if (frm.is_new()) {
        return;
    }

    frm.add_custom_button(__("Apply Extension"), () => {
        frm.call("apply_extension").then((response) => {
            const payload = response.message || {};
            const announcement = payload.announcement || {};
            frappe.msgprint({
                title: __("Extension Applied"),
                indicator: "green",
                message: `
                    <div>
                        <p>${frappe.utils.escape_html(announcement.subject || __("Extension applied successfully."))}</p>
                        <p>${frappe.utils.escape_html(announcement.message || __("Please sign out and sign back in before using the new fields."))}</p>
                        <p>${frappe.utils.escape_html(__("{0} user notification(s) were created.", [announcement.users_notified || 0]))}</p>
                    </div>
                `,
                primary_action: {
                    label: __("Reload Form"),
                    action() {
                        frm.reload_doc();
                    },
                },
            });
        });
    });

    if (frm.doc.status === "Applied") {
        frm.add_custom_button(__("Disable Extension"), () => {
            frm.call("disable_extension").then(() => {
                frappe.show_alert({ message: __("Extension disabled"), indicator: "orange" });
                frm.reload_doc();
            });
        });
    }

    if (["Applied", "Disabled"].includes(frm.doc.status)) {
        frm.add_custom_button(__("Uninstall Extension"), () => {
            frappe.confirm(
                __("This removes the managed custom fields created by this extension. Existing data in those fields may be lost. Continue?"),
                () => {
                    frm.call("uninstall_extension").then(() => {
                        frappe.show_alert({ message: __("Extension uninstalled"), indicator: "red" });
                        frm.reload_doc();
                    });
                }
            );
        });
    }
}

function addWizardButtons(frm) {
    frm.add_custom_button(__("Customer Wizard"), () => openWizard(frm, "Customer"));
    frm.add_custom_button(__("Sales Order Wizard"), () => openWizard(frm, "Sales Order"));
}

function refreshTargetSchema(frm) {
    const grid = frm.fields_dict.extension_fields?.grid;
    if (!grid) {
        return;
    }

    if (!frm.doc.target_doctype) {
        grid.update_docfield_property("insert_after", "options", "");
        renderBaseSchemaPreview(frm, null);
        return;
    }

    frappe.call({
        method: "pharma_vn.api.form_extensions.get_target_fields",
        args: {
            target_doctype: frm.doc.target_doctype,
        },
    }).then((response) => {
        const rows = (response.message || {}).data || [];
        const schema = (response.message || {}).schema || null;
        const anchors = rows.map((row) => row.value).join("\n");
        grid.update_docfield_property("insert_after", "options", anchors);
        grid.update_docfield_property("insert_after", "description", __("Choose where the extension field should be inserted."));
        renderBaseSchemaPreview(frm, schema);
    });
}

function renderBaseSchemaPreview(frm, schema) {
    const wrapper = frm.get_field("base_schema_preview_html").$wrapper;
    wrapper.empty();

    if (!schema || !Array.isArray(schema.fields) || !schema.fields.length) {
        wrapper.html(`
            <div class="form-extension-preview form-extension-preview--empty">
                Select a target DocType to preview the base form structure.
            </div>
        `);
        return;
    }

    const cardsHtml = schema.fields.map((field) => previewFieldCard(field)).join("");
    wrapper.html(`
        <div class="form-extension-preview">
            <style>
                .form-extension-preview { background: linear-gradient(145deg, #f6fbff, #f7f8f3); border: 1px solid #dbe4e8; border-radius: 18px; padding: 20px; }
                .form-extension-preview--empty { color: #5f6f78; background: #f8fafc; border: 1px dashed #ccd7de; border-radius: 14px; padding: 18px; }
                .form-extension-preview__title { font-size: 20px; font-weight: 700; color: #163040; margin-bottom: 6px; }
                .form-extension-preview__meta { color: #5c6e78; margin-bottom: 16px; }
                .form-extension-preview__grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 12px; }
                .form-extension-preview__card { background: rgba(255,255,255,0.92); border: 1px solid #dce6ec; border-radius: 14px; padding: 14px; min-height: 84px; }
                .form-extension-preview__card--full { grid-column: 1 / -1; }
                .form-extension-preview__label { color: #173042; font-weight: 600; margin-bottom: 4px; }
                .form-extension-preview__type { color: #728592; font-size: 12px; text-transform: uppercase; letter-spacing: 0.04em; }
                .form-extension-preview__fieldname { color: #47606d; font-size: 12px; margin-top: 8px; }
                @media (max-width: 768px) { .form-extension-preview__grid { grid-template-columns: 1fr; } }
            </style>
            <div class="form-extension-preview__title">${frappe.utils.escape_html(schema.target_doctype || frm.doc.target_doctype || "")}</div>
            <div class="form-extension-preview__meta">${schema.field_count || 0} base field(s) available for extension.</div>
            <div class="form-extension-preview__grid">${cardsHtml}</div>
        </div>
    `);
}

function previewFieldCard(field) {
    const fieldtype = field.fieldtype || "Data";
    const isFullWidth = ["Section Break", "Column Break", "Small Text", "Text", "Table"].includes(fieldtype);
    return `
        <div class="form-extension-preview__card ${isFullWidth ? "form-extension-preview__card--full" : ""}">
            <div class="form-extension-preview__label">${frappe.utils.escape_html(field.label || field.fieldname || fieldtype)}</div>
            <div class="form-extension-preview__type">${frappe.utils.escape_html(fieldtype)}</div>
            <div class="form-extension-preview__fieldname">${frappe.utils.escape_html(field.fieldname || "-")}</div>
        </div>
    `;
}

function openWizard(frm, targetDoctype) {
    const preset = EXTENSION_WIZARDS[targetDoctype];
    if (!preset) {
        return;
    }

    const dialog = new frappe.ui.Dialog({
        title: __("{0} Extension Wizard", [targetDoctype]),
        fields: [
            {
                fieldname: "mode",
                fieldtype: "Select",
                label: "Apply Mode",
                options: "Replace Draft\nAppend To Draft",
                default: "Replace Draft",
                reqd: 1,
            },
            {
                fieldname: "extension_name",
                fieldtype: "Data",
                label: "Extension Name",
                default: preset.extension_name,
                reqd: 1,
            },
            {
                fieldname: "description",
                fieldtype: "Small Text",
                label: "Description",
                default: preset.description,
            },
        ],
        primary_action_label: __("Create Draft"),
        primary_action(values) {
            applyWizardPreset(frm, targetDoctype, preset, values);
            dialog.hide();
        },
    });

    dialog.show();
}

function applyWizardPreset(frm, targetDoctype, preset, values) {
    const replaceDraft = values.mode === "Replace Draft";
    frm.set_value("target_doctype", targetDoctype);
    frm.set_value("extension_name", values.extension_name);
    frm.set_value("description", values.description);

    if (replaceDraft) {
        frm.clear_table("extension_fields");
    }

    const rows = preset.rows.map((row, index) => normalizeWizardRow(frm, values.extension_name, row, index, preset.rows));
    rows.forEach((row) => frm.add_child("extension_fields", row));
    frm.refresh_field("extension_fields");
    frm.dirty();
    refreshTargetSchema(frm);
    frappe.show_alert({ message: __("{0} draft prepared", [targetDoctype]), indicator: "green" });
}

function normalizeWizardRow(frm, extensionName, row, index, allRows) {
    const current = { ...row };
    const priorManaged = [];

    allRows.slice(0, index).forEach((candidate) => {
        priorManaged.push(buildManagedFieldname(extensionName, candidate.reference_fieldname || candidate.label || `field_${index}`));
    });

    if (current.insert_after && current.insert_after.startsWith("ext_") && priorManaged.length) {
        current.insert_after = priorManaged[priorManaged.length - 1];
    }

    if (!current.insert_after) {
        current.insert_after = frm.doc.target_doctype ? "" : "name";
    }

    return {
        label: current.label,
        fieldtype: current.fieldtype,
        reference_fieldname: current.reference_fieldname || "",
        insert_after: current.insert_after,
        reqd: current.reqd || 0,
        allow_on_submit: current.allow_on_submit || 0,
        in_list_view: current.in_list_view || 0,
        hidden: current.hidden || 0,
        options: current.options || "",
        link_doctype: current.link_doctype || "",
        table_doctype: current.table_doctype || "",
        default_value: current.default_value || "",
        description: current.description || "",
    };
}

function buildManagedFieldname(extensionName, label) {
    const extensionSlug = slugify(extensionName).slice(0, 20);
    const labelSlug = slugify(label).slice(0, 24);
    return `ext_${extensionSlug}_${labelSlug}`.replace(/^_+|_+$/g, "").slice(0, 61);
}

function slugify(value) {
    return String(value || "")
        .trim()
        .toLowerCase()
        .replace(/\s+/g, "_")
        .replace(/[^a-z0-9_]+/g, "_")
        .replace(/_+/g, "_")
        .replace(/^_+|_+$/g, "");
}
