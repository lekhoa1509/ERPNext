window.pharma_vn = window.pharma_vn || {};

(() => {
    const CREATE_METHOD = "pharma_vn.api.risk.quick_create_customer";
    const WRAPPER_CLASS = "pharma-customer-tax-quick-entry";
    const STATUS_CLASS = "pharma-customer-tax-quick-entry__status";
    let installed = false;

    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", installQuickEntryEnhancer);
    } else {
        installQuickEntryEnhancer();
    }

    function installQuickEntryEnhancer() {
        if (installed || typeof $ === "undefined") {
            return;
        }

        installed = true;
        $(document).on("shown.bs.modal", ".modal", () => {
            window.setTimeout(enhanceCustomerQuickEntry, 0);
        });
        window.setTimeout(enhanceCustomerQuickEntry, 0);
    }

    function enhanceCustomerQuickEntry() {
        const dialog = window.cur_dialog;
        if (!isCustomerQuickEntry(dialog)) {
            return;
        }

        const customerTypeField = dialog.fields_dict.customer_type;
        if (!customerTypeField || !customerTypeField.$wrapper || !customerTypeField.$wrapper.length) {
            return;
        }

        if (dialog.$wrapper.find(`.${WRAPPER_CLASS}`).length) {
            return;
        }

        const wrapper = $(`
            <div class="${WRAPPER_CLASS}" style="margin: 10px 0 16px;">
                <label class="control-label" style="display:block; margin-bottom: 6px;">${__("Tax ID / MST")}</label>
                <div style="display:flex; gap:8px; align-items:center;">
                    <input type="text" class="form-control input-with-feedback" placeholder="${__("Enter tax ID to generate customer")}" />
                    <button type="button" class="btn btn-secondary btn-sm">${__("Gen & Save")}</button>
                </div>
                <div class="${STATUS_CLASS}" style="margin-top: 6px; font-size: 12px; color: var(--text-muted);">
                    ${__("Enter tax ID, then the system will fetch company info and create the customer automatically.")}
                </div>
            </div>
        `);

        customerTypeField.$wrapper.after(wrapper);

        const input = wrapper.find("input");
        const button = wrapper.find("button");
        const status = wrapper.find(`.${STATUS_CLASS}`);

        button.on("click", () => handleQuickCreate(dialog, input, button, status));
        input.on("keydown", (event) => {
            if (event.key !== "Enter") {
                return;
            }
            event.preventDefault();
            handleQuickCreate(dialog, input, button, status);
        });
    }

    function isCustomerQuickEntry(dialog) {
        if (!dialog || !dialog.fields_dict) {
            return false;
        }

        if (!dialog.fields_dict.customer_name || !dialog.fields_dict.customer_type) {
            return false;
        }

        const title = cstr(dialog.title || dialog.$wrapper?.find(".modal-title").text()).trim().toLowerCase();
        return !title || title.includes("customer");
    }

    async function handleQuickCreate(dialog, input, button, status) {
        const taxCode = sanitizeTaxCode(input.val());
        if (!taxCode) {
            setStatus(status, __("Please enter Tax ID / MST."), "#d94841");
            input.trigger("focus");
            return;
        }
        if (button.prop("disabled")) {
            return;
        }

        const originalLabel = button.text();
        button.prop("disabled", true).text(__("Generating..."));
        setStatus(status, __("Fetching business info and creating customer..."));

        try {
            const response = await frappe.call({
                method: CREATE_METHOD,
                args: {
                    tax_code: taxCode,
                    customer_type: getDialogValue(dialog, "customer_type") || "Company",
                },
                freeze: true,
                freeze_message: __("Creating customer from Tax ID..."),
            });
            const payload = response.message || {};

            if (payload.customer_name) {
                setDialogValue(dialog, "customer_name", payload.customer_name);
            }

            if (payload.tax_code) {
                input.val(payload.tax_code);
                setDialogValue(dialog, "tax_id", payload.tax_code);
                setDialogValue(dialog, "tax_code", payload.tax_code);
            }

            if (payload.status === "existing") {
                frappe.show_alert({
                    message: __("Customer already exists for Tax ID {0}", [payload.tax_code || taxCode]),
                    indicator: "orange",
                });
                closeDialog(dialog);
                routeToCustomer(payload.customer, true);
                return;
            }

            frappe.show_alert({
                message: __("Customer {0} created", [payload.customer_name || payload.customer]),
                indicator: "green",
            });
            closeDialog(dialog);
            routeToCustomer(payload.customer, false);
        } catch (error) {
            const message = extractErrorMessage(error) || __("Could not create customer from Tax ID.");
            setStatus(status, message, "#d94841");
            frappe.msgprint(message);
        } finally {
            button.prop("disabled", false).text(originalLabel);
        }
    }

    function sanitizeTaxCode(value) {
        return cstr(value).trim().replace(/\s+/g, "").toUpperCase();
    }

    function getDialogValue(dialog, fieldname) {
        if (!dialog || !fieldname) {
            return "";
        }
        if (typeof dialog.get_value === "function") {
            return dialog.get_value(fieldname);
        }
        const field = dialog.fields_dict?.[fieldname];
        if (field && typeof field.get_value === "function") {
            return field.get_value();
        }
        return "";
    }

    function setDialogValue(dialog, fieldname, value) {
        if (!dialog || !fieldname || !dialog.fields_dict?.[fieldname]) {
            return;
        }
        if (typeof dialog.set_value === "function") {
            dialog.set_value(fieldname, value);
            return;
        }
        const field = dialog.fields_dict[fieldname];
        if (field && typeof field.set_value === "function") {
            field.set_value(value);
        }
    }

    function setStatus(status, message, color) {
        if (!status || !status.length) {
            return;
        }
        status.text(message || "");
        status.css("color", color || "var(--text-muted)");
    }

    function closeDialog(dialog) {
        if (!dialog) {
            return;
        }
        if (typeof dialog.hide === "function") {
            dialog.hide();
            return;
        }
        if (dialog.$wrapper && typeof dialog.$wrapper.modal === "function") {
            dialog.$wrapper.modal("hide");
        }
    }

    function routeToCustomer(customer, forceRoute) {
        if (!customer) {
            return;
        }

        const route = typeof frappe.get_route === "function" ? frappe.get_route() : [];
        if (!forceRoute && route[0] === "List" && route[1] === "Customer" && window.cur_list && typeof cur_list.refresh === "function") {
            cur_list.refresh();
            return;
        }

        frappe.set_route("Form", "Customer", customer);
    }

    function extractErrorMessage(error) {
        if (!error) {
            return "";
        }

        if (error._server_messages) {
            try {
                const serverMessages = JSON.parse(error._server_messages);
                if (Array.isArray(serverMessages) && serverMessages.length) {
                    return cstr(serverMessages[0]).replace(/<[^>]+>/g, "").trim();
                }
            } catch (parsingError) {
                return cstr(error._server_messages).trim();
            }
        }

        return cstr(error.message || error.exc || error).trim();
    }

    function cstr(value) {
        return value == null ? "" : String(value);
    }
})();
