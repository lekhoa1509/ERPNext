window.pharma_vn = window.pharma_vn || {};

(() => {
    const SECTION_CLASS = "pharma-document-flow-section";
    const SECTION_LABEL = "Document Flow";
    const FLOW_METHOD = "pharma_vn.api.document_flow.get_document_flow";
    const SUPPORTED_DOCTYPES = new Set([
        "Quotation",
        "Sales Order",
        "Delivery Note",
        "Sales Invoice",
        "Material Request",
        "Purchase Order",
        "Purchase Receipt",
        "Purchase Invoice",
        "Payment Entry",
        "Stock Entry",
    ]);
    const STEP_STATE_LABELS = {
        complete: "Done",
        current: "Current",
        upcoming: "Upcoming",
        blocked: "Blocked",
    };

    function escapeHtml(value) {
        return $("<div>").text(value == null ? "" : String(value)).html();
    }

    function formatDate(value) {
        if (!value) {
            return "";
        }

        const dateOnly = String(value).slice(0, 10);
        if (frappe?.datetime?.str_to_user) {
            return frappe.datetime.str_to_user(dateOnly);
        }

        return dateOnly;
    }

    function renderOverview(overview) {
        const items = [
            { label: "Flow", value: overview?.company_flow || "N/A" },
            { label: "Party", value: overview?.party || "N/A" },
            { label: "Step Status", value: overview?.delivery_status || overview?.receipt_status || overview?.status || "N/A" },
            { label: "Billing", value: overview?.invoice_status || overview?.billing_status || "N/A" },
        ];

        return `
            <div class="pharma-document-flow__overview">
                ${items
                    .map(
                        (item) => `
                            <div class="pharma-document-flow__overview-item">
                                <span class="pharma-document-flow__overview-label">${escapeHtml(item.label)}</span>
                                <strong class="pharma-document-flow__overview-value">${escapeHtml(item.value)}</strong>
                            </div>
                        `
                    )
                    .join("")}
            </div>
        `;
    }

    function renderCurrentState(data) {
        const currentStep = data.current_step || {};
        const nextStep = data.next_step || {};
        const isBlocked = data.flow_status === "blocked";
        const isComplete = data.flow_status === "complete";

        return `
            <div class="pharma-document-flow__hero">
                <div class="pharma-document-flow__hero-card pharma-document-flow__hero-card--current ${isBlocked ? "is-blocked" : ""}">
                    <div class="pharma-document-flow__eyebrow">Bước hiện tại</div>
                    <div class="pharma-document-flow__hero-title">${escapeHtml(currentStep.title || "Chưa xác định")}</div>
                    <div class="pharma-document-flow__hero-text">${escapeHtml(currentStep.summary || data.flow_message || "")}</div>
                </div>
                <div class="pharma-document-flow__hero-card pharma-document-flow__hero-card--next ${isComplete ? "is-complete" : ""}">
                    <div class="pharma-document-flow__eyebrow">Bước tiếp theo</div>
                    <div class="pharma-document-flow__hero-title">${escapeHtml(nextStep.title || (isComplete ? "Flow Completed" : "Chưa có"))}</div>
                    <div class="pharma-document-flow__hero-text">${escapeHtml(nextStep.detail || data.flow_message || "Không còn bước follow-up nào đang chờ.")}</div>
                </div>
            </div>
        `;
    }

    function renderDocuments(documents) {
        if (!documents || !documents.length) {
            return `<div class="pharma-document-flow__doc-empty">Chưa có chứng từ follow-on ở bước này.</div>`;
        }

        return `
            <div class="pharma-document-flow__doc-list">
                ${documents
                    .map((document) => {
                        const metaParts = [document.status, formatDate(document.date), document.meta]
                            .filter(Boolean)
                            .map((part) => escapeHtml(part));

                        return `
                            <button
                                type="button"
                                class="pharma-document-flow__doc-pill ${document.is_anchor ? "is-anchor" : ""}"
                                data-doctype="${escapeHtml(document.doctype)}"
                                data-name="${escapeHtml(document.name)}"
                            >
                                <span class="pharma-document-flow__doc-doctype">${escapeHtml(document.doctype)}</span>
                                <span class="pharma-document-flow__doc-name">${escapeHtml(document.name)}</span>
                                <span class="pharma-document-flow__doc-meta">${metaParts.join(" · ")}</span>
                            </button>
                        `;
                    })
                    .join("")}
            </div>
        `;
    }

    function renderSteps(steps) {
        return `
            <div class="pharma-document-flow__lane">
                ${steps
                    .map(
                        (step, index) => `
                            <section class="pharma-document-flow__step pharma-document-flow__step--${escapeHtml(step.status)}">
                                <div class="pharma-document-flow__step-index">0${index + 1}</div>
                                <div class="pharma-document-flow__step-header">
                                    <h4 class="pharma-document-flow__step-title">${escapeHtml(step.title)}</h4>
                                    <span class="pharma-document-flow__step-state">${escapeHtml(STEP_STATE_LABELS[step.status] || step.status)}</span>
                                </div>
                                <p class="pharma-document-flow__step-summary">${escapeHtml(step.summary || step.description || "")}</p>
                                ${renderDocuments(step.documents)}
                            </section>
                        `
                    )
                    .join("")}
            </div>
        `;
    }

    function buildMarkup(data) {
        return `
            <div class="pharma-document-flow">
                ${renderCurrentState(data)}
                ${renderOverview(data.overview)}
                ${renderSteps(data.steps || [])}
            </div>
        `;
    }

    function ensureSection(frm) {
        frm.dashboard.parent.find(`.${SECTION_CLASS}`).remove();
        return frm.dashboard.add_section("", SECTION_LABEL, SECTION_CLASS);
    }

    function showPlaceholder(frm, message) {
        const sectionBody = ensureSection(frm);
        sectionBody.html(`<div class="pharma-document-flow__empty">${escapeHtml(message)}</div>`);
    }

    function bindEvents(sectionBody) {
        sectionBody.find(".pharma-document-flow__doc-pill").on("click", function () {
            const doctype = $(this).attr("data-doctype");
            const name = $(this).attr("data-name");
            if (!doctype || !name) {
                return;
            }

            frappe.set_route("Form", doctype, name);
        });
    }

    function render(frm, data) {
        const sectionBody = ensureSection(frm);
        sectionBody.html(buildMarkup(data));
        bindEvents(sectionBody);
    }

    function refresh(frm) {
        if (!SUPPORTED_DOCTYPES.has(frm.doctype)) {
            return;
        }

        if (frm.is_new()) {
            showPlaceholder(frm, "Lưu chứng từ trước để xem document flow.");
            return;
        }

        const requestToken = `${frm.doctype}:${frm.doc.name}:${Date.now()}`;
        frm.__pharma_document_flow_request = requestToken;
        showPlaceholder(frm, "Đang tải document flow...");

        frappe.call({
            method: FLOW_METHOD,
            args: {
                doctype: frm.doctype,
                name: frm.doc.name,
            },
            callback: (response) => {
                if (frm.__pharma_document_flow_request !== requestToken) {
                    return;
                }

                const data = response.message;
                if (!data?.ok) {
                    showPlaceholder(frm, data?.message || "Không dựng được document flow cho chứng từ này.");
                    return;
                }

                render(frm, data);
            },
            error: () => {
                if (frm.__pharma_document_flow_request !== requestToken) {
                    return;
                }

                showPlaceholder(frm, "Không tải được document flow. Kiểm tra lại backend rồi refresh form.");
            },
        });
    }

    window.pharma_vn.document_flow = {
        refresh,
    };
})();
