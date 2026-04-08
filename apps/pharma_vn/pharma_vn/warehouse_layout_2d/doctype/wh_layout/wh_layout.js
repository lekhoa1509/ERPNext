frappe.ui.form.on("WH Layout", {
    refresh(frm) {
        renderLayoutPreview(frm);
    },
});

function renderLayoutPreview(frm) {
    const wrapper = frm.get_field("layout_preview_html").$wrapper;
    wrapper.empty();

    if (frm.is_new()) {
        wrapper.html(
            `<div class="warehouse-layout-placeholder">
                Save this layout to auto-generate cells and open the 2D preview.
            </div>`
        );
        return;
    }

    if (!frm.doc.total_rows || !frm.doc.total_columns) {
        wrapper.html(
            `<div class="warehouse-layout-placeholder">
                Set total rows and columns to render the 2D layout.
            </div>`
        );
        return;
    }

    frappe.call({
        method: "pharma_vn.api.warehouse_layout.get_layout",
        args: {
            layout_name: frm.doc.name,
        },
    }).then((response) => {
        const payload = response.message || {};
        const data = payload.data || {};
        drawGrid(wrapper, data.layout || {}, data.cells || []);
    });
}

function drawGrid(wrapper, layout, cells) {
    const columns = Math.max(layout.total_columns || 1, 1);
    const totalQty = cells.reduce((sum, cell) => sum + (cell.total_qty || 0), 0);
    const occupiedCells = cells.filter((cell) => cell.total_qty > 0).length;

    const gridHtml = cells.map((cell) => {
        const occupancyLabel = cell.total_qty > 0
            ? `${formatQty(cell.total_qty)} qty / ${cell.item_count} item`
            : "Empty";

        return `
            <button
                type="button"
                class="warehouse-layout-cell warehouse-layout-cell--${(cell.status || "available").toLowerCase()}"
                data-cell-name="${frappe.utils.escape_html(cell.name)}"
            >
                <span class="warehouse-layout-cell__code">${frappe.utils.escape_html(cell.cell_code || "")}</span>
                <span class="warehouse-layout-cell__meta">${frappe.utils.escape_html(occupancyLabel)}</span>
            </button>
        `;
    }).join("");

    wrapper.html(`
        <div class="warehouse-layout-board">
            <div class="warehouse-layout-board__summary">
                <div><strong>${frappe.utils.escape_html(layout.layout_name || layout.name || "")}</strong></div>
                <div>${occupiedCells} occupied cell(s)</div>
                <div>Total tracked qty: ${formatQty(totalQty)}</div>
            </div>
            <div class="warehouse-layout-grid" style="grid-template-columns: repeat(${columns}, minmax(110px, 1fr));">
                ${gridHtml}
            </div>
        </div>
    `);

    wrapper.find(".warehouse-layout-cell").on("click", function clickCell() {
        const cell = cells.find((row) => row.name === this.dataset.cellName);
        if (!cell) {
            return;
        }

        const stockRows = (cell.stock_rows || []).length
            ? `
                <table class="table table-bordered table-sm warehouse-layout-stock-table">
                    <thead>
                        <tr>
                            <th>Item</th>
                            <th>Batch</th>
                            <th>Qty</th>
                            <th>UOM</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${(cell.stock_rows || []).map((stockRow) => `
                            <tr>
                                <td>${frappe.utils.escape_html(stockRow.item_code || "")}</td>
                                <td>${frappe.utils.escape_html(stockRow.batch_no || "-")}</td>
                                <td>${formatQty(stockRow.qty || 0)}</td>
                                <td>${frappe.utils.escape_html(stockRow.uom || "-")}</td>
                            </tr>
                        `).join("")}
                    </tbody>
                </table>
            `
            : `<div class="warehouse-layout-placeholder">This cell is currently empty.</div>`;

        frappe.msgprint({
            title: `${cell.cell_code || cell.name}`,
            message: `
                <div class="warehouse-layout-cell-dialog">
                    <div><strong>Status:</strong> ${frappe.utils.escape_html(cell.status || "Available")}</div>
                    <div><strong>Total Qty:</strong> ${formatQty(cell.total_qty || 0)}</div>
                    <div><strong>Tracked Items:</strong> ${cell.item_count || 0}</div>
                    ${stockRows}
                </div>
            `,
        });
    });
}

function formatQty(value) {
    const numericValue = Number(value || 0);
    return frappe.format(numericValue, { fieldtype: "Float", precision: 2 });
}
