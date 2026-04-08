frappe.ui.form.on("Dynamic Form", {
    refresh(frm) {
        renderPreview(frm);
        addActions(frm);
    },
    fields_meta_add(frm) {
        renderPreview(frm);
    },
    fields_meta_remove(frm) {
        renderPreview(frm);
    },
});

frappe.ui.form.on("Dynamic Form Field", {
    label(frm) {
        renderPreview(frm);
    },
    fieldtype(frm) {
        renderPreview(frm);
    },
    reqd(frm) {
        renderPreview(frm);
    },
    options(frm) {
        renderPreview(frm);
    },
});

function addActions(frm) {
    if (frm.is_new()) {
        return;
    }

    frm.clear_custom_buttons();

    frm.add_custom_button(__("Open Submissions"), () => {
        frappe.set_route("List", "Dynamic Form Submission", { dynamic_form: frm.doc.name });
    });

    if (frm.doc.is_published) {
        frm.add_custom_button(__("New Submission"), () => {
            openSubmissionDialog(frm);
        });
    }
}

function renderPreview(frm) {
    const wrapper = frm.get_field("preview_html").$wrapper;
    wrapper.empty();

    const fields = (frm.doc.fields_meta || []).filter(Boolean);
    if (!fields.length) {
        wrapper.html(`
            <div class="dynamic-form-preview dynamic-form-preview--empty">
                Add fields to see the live preview.
            </div>
        `);
        return;
    }

    const introHtml = frm.doc.introduction
        ? `<div class="dynamic-form-preview__intro">${frappe.utils.escape_html(frm.doc.introduction)}</div>`
        : "";
    const cardsHtml = fields.map((field) => previewCard(field)).join("");

    wrapper.html(`
        <div class="dynamic-form-preview">
            <style>
                .dynamic-form-preview { background: linear-gradient(135deg, #f5fbf8, #eef7ff); border: 1px solid #d8e6eb; border-radius: 18px; padding: 20px; }
                .dynamic-form-preview--empty { color: #52626d; background: #f8fafc; border: 1px dashed #c7d3dd; border-radius: 14px; padding: 20px; }
                .dynamic-form-preview__title { font-size: 20px; font-weight: 700; color: #173042; margin-bottom: 8px; }
                .dynamic-form-preview__intro { color: #4d6371; margin-bottom: 16px; }
                .dynamic-form-preview__grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 12px; }
                .dynamic-form-preview__field { background: rgba(255, 255, 255, 0.92); border: 1px solid #dce7ee; border-radius: 14px; padding: 14px; min-height: 88px; }
                .dynamic-form-preview__field--full { grid-column: 1 / -1; }
                .dynamic-form-preview__field--layout { grid-column: 1 / -1; border-style: dashed; background: rgba(23, 48, 66, 0.04); }
                .dynamic-form-preview__label { font-weight: 600; color: #173042; margin-bottom: 4px; }
                .dynamic-form-preview__meta { font-size: 12px; color: #5f7482; margin-bottom: 8px; text-transform: uppercase; letter-spacing: 0.04em; }
                .dynamic-form-preview__hint { color: #708794; font-size: 13px; }
                @media (max-width: 768px) { .dynamic-form-preview__grid { grid-template-columns: 1fr; } }
            </style>
            <div class="dynamic-form-preview__title">${frappe.utils.escape_html(frm.doc.form_name || "Untitled Form")}</div>
            ${introHtml}
            <div class="dynamic-form-preview__grid">${cardsHtml}</div>
        </div>
    `);
}

function previewCard(field) {
    const fieldtype = field.fieldtype || "Data";
    const label = field.label || field.fieldname || fieldtype;
    const widthClass = field.width === "Half" ? "" : "dynamic-form-preview__field--full";
    const layoutClass = ["Section Break", "Column Break"].includes(fieldtype)
        ? "dynamic-form-preview__field--layout dynamic-form-preview__field--full"
        : widthClass;
    const description = field.description || field.placeholder || field.options || "";
    const requiredText = cint(field.reqd) ? "Required" : "Optional";

    return `
        <div class="dynamic-form-preview__field ${layoutClass}">
            <div class="dynamic-form-preview__label">${frappe.utils.escape_html(label)}</div>
            <div class="dynamic-form-preview__meta">${frappe.utils.escape_html(fieldtype)} • ${requiredText}</div>
            <div class="dynamic-form-preview__hint">${frappe.utils.escape_html(description || "No helper text configured.")}</div>
        </div>
    `;
}

function openSubmissionDialog(frm) {
    const rows = (frm.doc.fields_meta || []).filter((field) => !["Section Break", "Column Break"].includes(field.fieldtype));
    if (!rows.length) {
        frappe.msgprint(__("This form does not have any input fields yet."));
        return;
    }

    const dialog = new frappe.ui.Dialog({
        title: `${frm.doc.form_name || frm.doc.name} Submission`,
        size: "large",
        fields: rows.map((field) => ({
            fieldname: field.fieldname,
            label: field.label,
            fieldtype: normalizeDialogFieldtype(field.fieldtype),
            reqd: cint(field.reqd),
            options: field.fieldtype === "Link" ? field.link_doctype : field.options,
            description: field.description,
            default: field.default_value,
        })),
        primary_action_label: __("Submit"),
        primary_action(values) {
            frappe.call({
                method: "pharma_vn.api.dynamic_forms.submit_form",
                args: {
                    form_name: frm.doc.name,
                    payload: values,
                },
                freeze: true,
                freeze_message: __("Saving submission..."),
            }).then((response) => {
                const payload = response.message || {};
                frappe.show_alert({ message: payload.message || __("Submission saved"), indicator: "green" });
                dialog.hide();
            });
        },
    });

    dialog.show();
}

function normalizeDialogFieldtype(fieldtype) {
    if (fieldtype === "Long Text") {
        return "Small Text";
    }
    return fieldtype;
}

function cint(value) {
    return window.frappe ? frappe.utils.cint(value) : parseInt(value || 0, 10);
}
