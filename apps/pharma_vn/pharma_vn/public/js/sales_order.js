const SALES_ORDER_RISK_CHECK_METHOD = "pharma_vn.api.risk.check";
const SALES_ORDER_RISK_SNAPSHOT_METHOD = "pharma_vn.api.risk.get_customer_risk";
const SALES_ORDER_RISK_SLOT_CLASS = "pharma-sales-order-risk-slot";

frappe.ui.form.on("Sales Order", {
    refresh(frm) {
        window.requestAnimationFrame(() => {
            window.pharma_vn?.document_flow?.refresh(frm);
            void refreshSalesOrderRisk(frm);
        });
    },

    customer(frm) {
        hideSalesOrderRiskDialog(frm);
        void refreshSalesOrderRisk(frm);
    },
});

async function refreshSalesOrderRisk(frm) {
    const customer = (frm.doc.customer || "").trim();
    if (!customer) {
        hideSalesOrderRiskDialog(frm);
        renderSalesOrderRisk(frm, {
            status: "empty",
            customer: "",
            customer_name: "",
            tax_code: "",
            message: __("Select a customer to view risk information."),
        });
        return;
    }

    const requestToken = `${customer}:${Date.now()}`;
    frm.__sales_order_risk_request = requestToken;

    renderSalesOrderRisk(frm, {
        status: "loading",
        customer,
        customer_name: frm.doc.customer_name || customer,
        tax_code: "",
        message: __("Loading the latest saved risk profile..."),
    });

    try {
        const response = await frappe.call({
            method: SALES_ORDER_RISK_SNAPSHOT_METHOD,
            args: { customer },
        });

        if (frm.__sales_order_risk_request !== requestToken || customer !== (frm.doc.customer || "").trim()) {
            return;
        }

        renderSalesOrderRisk(frm, buildSalesOrderRiskPayload(frm, response.message || {}));
    } catch (error) {
        if (frm.__sales_order_risk_request !== requestToken) {
            return;
        }

        renderSalesOrderRisk(frm, {
            status: "error",
            customer,
            customer_name: frm.doc.customer_name || customer,
            tax_code: "",
            message: extractRiskErrorMessage(error, __("Unable to load the latest customer risk profile.")),
        });
    }
}

async function runSalesOrderRiskCheck(frm, forceRefresh = false) {
    const customer = (frm.doc.customer || "").trim();
    if (!customer) {
        frappe.msgprint(__("Please select a Customer before checking risk."));
        return;
    }

    const requestToken = `${customer}:${Date.now()}`;
    frm.__sales_order_risk_request = requestToken;

    renderSalesOrderRisk(frm, {
        status: "loading",
        customer,
        customer_name: frm.doc.customer_name || customer,
        tax_code: "",
        checking: true,
        message: forceRefresh
            ? __("Refreshing the risk engine with the latest external data...")
            : __("Checking customer risk..."),
    });

    try {
        const response = await frappe.call({
            method: SALES_ORDER_RISK_CHECK_METHOD,
            args: {
                customer,
                force_refresh: forceRefresh ? 1 : 0,
            },
            freeze: true,
            freeze_message: forceRefresh
                ? __("Refreshing customer risk assessment...")
                : __("Running customer risk assessment..."),
        });

        if (frm.__sales_order_risk_request !== requestToken || customer !== (frm.doc.customer || "").trim()) {
            return;
        }

        const payload = buildSalesOrderRiskPayload(frm, response.message || {});
        renderSalesOrderRisk(frm, payload);
        frappe.show_alert({
            message: forceRefresh
                ? __("Customer risk profile refreshed")
                : __("Customer risk profile loaded"),
            indicator: "green",
        });
        showSalesOrderRiskDialog(frm, payload);
    } catch (error) {
        if (frm.__sales_order_risk_request !== requestToken) {
            return;
        }

        renderSalesOrderRisk(frm, {
            status: "error",
            customer,
            customer_name: frm.doc.customer_name || customer,
            tax_code: "",
            message: extractRiskErrorMessage(
                error,
                __("The risk engine request failed. Review backend connectivity and try again."),
            ),
        });
    }
}

function buildSalesOrderRiskPayload(frm, payload) {
    return {
        ...payload,
        customer: payload.customer || frm.doc.customer,
        customer_name: payload.customer_name || frm.doc.customer_name || frm.doc.customer,
        tax_code: payload.tax_code || "",
        checking: false,
    };
}

function renderSalesOrderRisk(frm, payload) {
    const slot = ensureSalesOrderRiskSlot(frm);
    if (!slot || !slot.length) {
        return;
    }

    frm.__sales_order_risk_payload = payload;

    const level = normalizeRiskLevel(payload.risk_level, payload.risk_score);
    const hasReadyPayload = (
        payload.status === "ready"
        || typeof payload.risk_score === "number"
        || Boolean(level)
        || Boolean(payload.business_profile)
        || Boolean(payload.warnings && payload.warnings.length)
    );
    const isBusy = payload.status === "loading" || Boolean(payload.checking);
    const score = formatRiskScore(payload.risk_score);
    const reasons = sanitizeList(payload.reasons);
    const primaryReason = reasons[0] || getRiskLevelDescription(level);
    const badgeLevel = (level || "PENDING").toLowerCase();

    let bodyHtml = `
        <div class="pharma-sales-order-risk__status">
            <p>${escapeRiskHtml(payload.message || __("Select a customer to view risk information."))}</p>
        </div>
    `;

    if (payload.customer && hasReadyPayload) {
        bodyHtml = `
            <div class="pharma-sales-order-risk__compact pharma-sales-order-risk__compact--${badgeLevel}">
                <div class="pharma-sales-order-risk__compact-topline">
                    <span class="pharma-sales-order-risk__label">${escapeRiskHtml(__("Customer Risk"))}</span>
                    <div class="pharma-sales-order-risk__score-row">
                        <strong class="pharma-sales-order-risk__score">${escapeRiskHtml(score)}</strong>
                        <span class="customer-risk-widget__badge customer-risk-widget__badge--${escapeRiskHtml(badgeLevel)}">
                            ${escapeRiskHtml(level || "PENDING")}
                        </span>
                    </div>
                </div>
                <p class="pharma-sales-order-risk__compact-copy">${escapeRiskHtml(primaryReason)}</p>
                <div class="pharma-sales-order-risk__compact-meta">
                    <span>${escapeRiskHtml(payload.tax_code || __("Missing tax code"))}</span>
                    <span>${escapeRiskHtml(formatRiskDateTime(payload.last_check_date))}</span>
                </div>
            </div>
        `;
    } else if (payload.customer) {
        bodyHtml = `
            <div class="pharma-sales-order-risk__status${payload.status === "error" ? " pharma-sales-order-risk__status--error" : ""}">
                <p>${escapeRiskHtml(payload.message || __("No customer risk assessment has been run yet."))}</p>
            </div>
        `;
    }

    slot.html(`
        <div class="pharma-sales-order-risk">
            <div class="pharma-sales-order-risk__actions">
                <button
                    type="button"
                    class="btn btn-sm btn-primary"
                    data-risk-action="check"
                    ${payload.customer && !isBusy ? "" : "disabled"}
                >
                    ${escapeRiskHtml(payload.checking ? __("Checking...") : __("Check Risk"))}
                </button>
                ${payload.customer && hasReadyPayload ? `
                    <button
                        type="button"
                        class="btn btn-sm btn-default"
                        data-risk-action="view"
                    >
                        ${escapeRiskHtml(__("View Details"))}
                    </button>
                ` : ""}
            </div>
            <div class="pharma-sales-order-risk__body">
                ${bodyHtml}
            </div>
        </div>
    `);

    slot.find("[data-risk-action='check']").on("click", () => {
        void runSalesOrderRiskCheck(frm, false);
    });

    slot.find("[data-risk-action='view']").on("click", () => {
        showSalesOrderRiskDialog(frm, frm.__sales_order_risk_payload || payload);
    });
}

function showSalesOrderRiskDialog(frm, payload) {
    if (!payload || !payload.customer) {
        return;
    }

    hideSalesOrderRiskDialog(frm);

    const dialog = new frappe.ui.Dialog({
        title: `${__("Customer Risk")} · ${payload.customer_name || payload.customer}`,
        fields: [
            {
                fieldtype: "HTML",
                fieldname: "risk_content",
            },
        ],
        size: "large",
    });

    frm.__sales_order_risk_dialog = dialog;
    dialog.fields_dict.risk_content.$wrapper.html(renderSalesOrderRiskDialog(payload));
    dialog.show();

    const $wrapper = dialog.fields_dict.risk_content.$wrapper;

    $wrapper.on("click", "[data-risk-dialog-action='refresh']", () => {
        dialog.hide();
        frm.__sales_order_risk_dialog = null;
        void runSalesOrderRiskCheck(frm, true);
    });

    $wrapper.on("click", "[data-risk-dialog-action='history']", () => {
        frappe.set_route("List", "Customer Risk Profile", { customer: payload.customer });
    });

    dialog.onhide = () => {
        if (frm.__sales_order_risk_dialog === dialog) {
            frm.__sales_order_risk_dialog = null;
        }
    };
}

function hideSalesOrderRiskDialog(frm) {
    if (!frm.__sales_order_risk_dialog) {
        return;
    }

    frm.__sales_order_risk_dialog.hide();
    frm.__sales_order_risk_dialog = null;
}

function renderSalesOrderRiskDialog(payload) {
    const level = normalizeRiskLevel(payload.risk_level, payload.risk_score);
    const reasons = sanitizeList(payload.reasons);
    const warnings = sanitizeList(payload.warnings);
    const hasReadyPayload = (
        payload.status === "ready"
        || typeof payload.risk_score === "number"
        || Boolean(level)
        || Boolean(payload.business_profile)
        || Boolean(payload.warnings && payload.warnings.length)
    );

    return `
        <div class="pharma-sales-order-risk__dialog">
            <section class="customer-risk-widget customer-risk-widget--${escapeRiskHtml(payload.status || "ready")}">
                <header class="customer-risk-widget__header">
                    <div>
                        <p class="customer-risk-widget__eyebrow">${escapeRiskHtml(__("Customer Risk Assessment"))}</p>
                        <h2 class="customer-risk-widget__title">
                            ${escapeRiskHtml(payload.customer_name || payload.customer || __("Customer"))}
                        </h2>
                        <p class="customer-risk-widget__subtitle">
                            ${escapeRiskHtml(__("Tax Code"))}: <strong>${escapeRiskHtml(payload.tax_code || __("Missing tax code"))}</strong>
                        </p>
                    </div>
                    <div class="customer-risk-widget__action-row">
                        <button
                            type="button"
                            class="customer-risk-widget__button customer-risk-widget__button--ghost"
                            data-risk-dialog-action="refresh"
                        >
                            ${escapeRiskHtml(__("Refresh Engine"))}
                        </button>
                        <button
                            type="button"
                            class="customer-risk-widget__button customer-risk-widget__button--ghost"
                            data-risk-dialog-action="history"
                        >
                            ${escapeRiskHtml(__("Open History"))}
                        </button>
                    </div>
                </header>
                ${hasReadyPayload ? `
                    <div class="customer-risk-widget__layout">
                        ${renderDialogScoreCard(payload, level)}
                        ${renderReasonsPanel(reasons, warnings)}
                        ${renderBusinessProfilePanel(payload.business_profile)}
                        ${renderHistoryPanel(payload.history)}
                    </div>
                ` : `
                    <div class="customer-risk-widget__empty-state">
                        <h3>${escapeRiskHtml(payload.status === "error" ? __("Unable to load risk profile") : __("No risk profile yet"))}</h3>
                        <p>${escapeRiskHtml(payload.message || __("No customer risk assessment has been run yet."))}</p>
                    </div>
                `}
            </section>
        </div>
    `;
}

function renderDialogScoreCard(payload, level) {
    return `
        <section class="customer-risk-widget__score-card customer-risk-widget__score-card--${escapeRiskHtml((level || "pending").toLowerCase())}">
            <div class="customer-risk-widget__score-topline">
                <span class="customer-risk-widget__eyebrow">${escapeRiskHtml(__("Risk Score"))}</span>
                <span class="customer-risk-widget__badge customer-risk-widget__badge--${escapeRiskHtml((level || "PENDING").toLowerCase())}">
                    ${escapeRiskHtml(level || "PENDING")}
                </span>
            </div>
            <div class="customer-risk-widget__score-value">${escapeRiskHtml(formatRiskScore(payload.risk_score))}</div>
            <p class="customer-risk-widget__score-copy">${escapeRiskHtml(getRiskLevelDescription(level))}</p>
            <div class="customer-risk-widget__meta-grid">
                <div class="customer-risk-widget__meta-item">
                    <span class="customer-risk-widget__meta-label">${escapeRiskHtml(__("Last check"))}</span>
                    <strong>${escapeRiskHtml(formatRiskDateTime(payload.last_check_date))}</strong>
                </div>
                <div class="customer-risk-widget__meta-item">
                    <span class="customer-risk-widget__meta-label">${escapeRiskHtml(__("Data mode"))}</span>
                    <strong>${escapeRiskHtml(payload.from_cache ? __("Cached profile") : __("Fresh engine run"))}</strong>
                </div>
            </div>
        </section>
    `;
}

function renderReasonsPanel(reasons, warnings) {
    return `
        <section class="customer-risk-widget__panel">
            <div class="customer-risk-widget__panel-header">
                <h3>${escapeRiskHtml(__("Risk Details"))}</h3>
                <span>${escapeRiskHtml(__("Full reasons from the latest assessment"))}</span>
            </div>
            <div class="customer-risk-widget__reason-list">
                ${reasons.length
        ? reasons.map((reason) => `
                            <div class="customer-risk-widget__reason">
                                <span class="customer-risk-widget__reason-dot"></span>
                                <span>${escapeRiskHtml(reason)}</span>
                            </div>
                        `).join("")
        : `
                        <div class="customer-risk-widget__reason customer-risk-widget__reason--empty">
                            <span class="customer-risk-widget__reason-dot"></span>
                            <span>${escapeRiskHtml(__("No detailed reasons were returned for this customer yet."))}</span>
                        </div>
                    `}
            </div>
            ${warnings.length ? `
                <div class="customer-risk-widget__warning-box">
                    ${warnings.map((warning) => `<p>${escapeRiskHtml(warning)}</p>`).join("")}
                </div>
            ` : ""}
        </section>
    `;
}

function renderBusinessProfilePanel(businessProfile) {
    const profile = businessProfile && typeof businessProfile === "object" ? businessProfile : null;
    const rows = [
        renderBusinessProfileRow(__("Company"), profile?.company_name),
        renderBusinessProfileRow(__("Short Name"), profile?.short_name),
        renderBusinessProfileRow(__("Tax Code"), profile?.tax_code),
        renderBusinessProfileRow(__("Status"), profile?.status),
        renderBusinessProfileRow(__("Org Type"), profile?.organization_type),
        renderBusinessProfileRow(__("Established"), profile?.established_date),
        renderBusinessProfileRow(__("Business Lines"), Array.isArray(profile?.business_lines) ? profile.business_lines.join(", ") : ""),
        renderBusinessProfileRow(__("Tax Dept."), profile?.tax_department),
        renderBusinessProfileRow(__("Address"), profile?.address),
        renderBusinessProfileRow(__("Representative"), profile?.representative),
        renderBusinessProfileRow(__("Updated At"), profile?.updated_at),
    ].filter(Boolean);

    return `
        <section class="customer-risk-widget__panel">
            <div class="customer-risk-widget__panel-header">
                <h3>${escapeRiskHtml(__("Business Profile"))}</h3>
                <span>${escapeRiskHtml(profile?.source || __("External data source"))}</span>
            </div>
            ${rows.length
        ? `<dl class="customer-risk-widget__company-grid">${rows.join("")}</dl>`
        : `<p class="customer-risk-widget__history-empty">${escapeRiskHtml(__("No business profile details are available yet."))}</p>`}
        </section>
    `;
}

function renderBusinessProfileRow(label, value) {
    const text = String(value || "").trim();
    if (!text) {
        return "";
    }

    return `
        <dt>${escapeRiskHtml(label)}</dt>
        <dd>${escapeRiskHtml(text)}</dd>
    `;
}

function renderHistoryPanel(history) {
    const items = Array.isArray(history) ? history : [];

    return `
        <section class="customer-risk-widget__panel pharma-sales-order-risk__panel--full">
            <div class="customer-risk-widget__panel-header">
                <h3>${escapeRiskHtml(__("Check History"))}</h3>
                <span>${escapeRiskHtml(__("Most recent saved assessments"))}</span>
            </div>
            <div class="customer-risk-widget__history">
                ${items.length
        ? items.map((item) => renderHistoryItem(item)).join("")
        : `<p class="customer-risk-widget__history-empty">${escapeRiskHtml(__("No saved history yet."))}</p>`}
            </div>
        </section>
    `;
}

function renderHistoryItem(item) {
    const level = normalizeRiskLevel(item?.risk_level, item?.risk_score);
    const badgeLevel = (level || "PENDING").toLowerCase();
    const reasons = sanitizeList(item?.reasons);

    return `
        <article class="customer-risk-widget__history-item">
            <div class="customer-risk-widget__history-topline">
                <strong>${escapeRiskHtml(formatRiskDateTime(item?.last_check_date))}</strong>
                <span class="customer-risk-widget__badge customer-risk-widget__badge--${escapeRiskHtml(badgeLevel)}">
                    ${escapeRiskHtml(level || "PENDING")}
                </span>
            </div>
            <div class="customer-risk-widget__history-score">
                ${escapeRiskHtml(__("Score"))} ${escapeRiskHtml(formatRiskScore(item?.risk_score))}
            </div>
            <p class="customer-risk-widget__history-copy">
                ${escapeRiskHtml(reasons[0] || __("No detailed reason provided."))}
            </p>
        </article>
    `;
}

function ensureSalesOrderRiskSlot(frm) {
    const customerField = frm.get_field("customer");
    if (!customerField || !customerField.wrapper) {
        return null;
    }

    const $customerControl = $(customerField.wrapper).hasClass("frappe-control")
        ? $(customerField.wrapper)
        : $(customerField.wrapper).closest(".frappe-control");

    if (!$customerControl.length) {
        return null;
    }

    let $slot = $customerControl.siblings(`.${SALES_ORDER_RISK_SLOT_CLASS}`).first();
    if (!$slot.length) {
        $slot = $(`<div class="${SALES_ORDER_RISK_SLOT_CLASS}"></div>`);
        $customerControl.after($slot);
    }

    $customerControl.siblings(`.${SALES_ORDER_RISK_SLOT_CLASS}`).not($slot).remove();
    return $slot;
}

function normalizeRiskLevel(level, score) {
    const normalized = String(level || "").trim().toUpperCase();
    if (["SAFE", "WARNING", "HIGH"].includes(normalized)) {
        return normalized;
    }

    if (typeof score === "number" && !Number.isNaN(score)) {
        if (score >= 70) {
            return "HIGH";
        }
        if (score >= 40) {
            return "WARNING";
        }
        return "SAFE";
    }

    return "";
}

function formatRiskDateTime(value) {
    if (!value) {
        return __("Not checked yet");
    }

    const parsed = new Date(value);
    if (Number.isNaN(parsed.getTime())) {
        return value;
    }

    return new Intl.DateTimeFormat("en-GB", {
        day: "2-digit",
        month: "short",
        year: "numeric",
        hour: "2-digit",
        minute: "2-digit",
    }).format(parsed);
}

function formatRiskScore(score) {
    if (typeof score !== "number" || Number.isNaN(score)) {
        return "--";
    }

    return String(Math.round(score));
}

function getRiskLevelDescription(level) {
    if (level === "HIGH") {
        return __("Escalate to finance and legal review before approving this order.");
    }

    if (level === "WARNING") {
        return __("Proceed with caution and review the latest evidence carefully.");
    }

    if (level === "") {
        return __("Tax data is available, but the risk engine has not returned a score yet.");
    }

    return __("Customer profile looks healthy based on the latest assessment.");
}

function sanitizeList(values) {
    if (!Array.isArray(values)) {
        return [];
    }

    return values
        .map((value) => String(value || "").trim())
        .filter(Boolean);
}

function extractRiskErrorMessage(error, fallbackMessage) {
    const serverMessages = error?._server_messages;
    if (serverMessages) {
        try {
            const parsed = JSON.parse(serverMessages);
            const firstMessage = Array.isArray(parsed) ? parsed[0] : parsed;
            if (typeof firstMessage === "string") {
                try {
                    const innerMessage = JSON.parse(firstMessage);
                    if (innerMessage?.message) {
                        return innerMessage.message;
                    }
                } catch (innerParsingError) {
                    return firstMessage;
                }

                return firstMessage;
            }
        } catch (parsingError) {
            // Ignore parsing errors and fall through to the next fallback.
        }
    }

    if (typeof error?.message === "string" && error.message.trim()) {
        return error.message.trim();
    }

    return fallbackMessage;
}

function escapeRiskHtml(value) {
    return $("<div>").text(value == null ? "" : String(value)).html();
}
