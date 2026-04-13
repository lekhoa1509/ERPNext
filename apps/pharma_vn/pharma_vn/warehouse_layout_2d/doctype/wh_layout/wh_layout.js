frappe.ui.form.on("WH Layout", {
    refresh(frm) {
        renderLayoutPreview(frm);
        addPlcSimulatorButton(frm);
    },
});

function addPlcSimulatorButton(frm) {
    if (frm.is_new()) {
        return;
    }

    frm.add_custom_button(__("Connect Local Simulator"), () => connectPlcSimulator(frm, { use_local_simulator_profile: 1 }), __("WCS"));
    frm.add_custom_button(__("Connect PLC Simulator"), () => connectPlcSimulator(frm), __("WCS"));
}

function connectPlcSimulator(frm, options = {}) {
    if (frm.is_dirty()) {
        frappe.msgprint(__("Save this layout before connecting the PLC simulator so the latest 2D dimensions are sent to WCS."));
        return;
    }

    frappe.call({
        method: "pharma_vn.api.warehouse_layout.connect_plc_simulator",
        args: {
            layout_name: frm.doc.name,
            payload: options,
        },
        freeze: true,
        freeze_message: __("Connecting PLC simulator..."),
    }).then((response) => {
        const payload = response.message || {};
        const data = payload.data || {};
        const snapshot = data.snapshot || {};
        const notices = Array.isArray(data.notices) ? data.notices : [];
        const actions = Array.isArray(data.actions) ? data.actions : [];
        const deviceStatuses = data.device_statuses || {};
        const deviceRows = Object.entries(deviceStatuses).map(([deviceId, status]) => `
            <tr>
                <td>${frappe.utils.escape_html(deviceId)}</td>
                <td>${frappe.utils.escape_html(status)}</td>
            </tr>
        `).join("");

        const noticeHtml = notices.length
            ? `<div class="alert alert-warning">${notices.map((notice) => frappe.utils.escape_html(notice)).join("<br>")}</div>`
            : "";
        const actionHtml = actions.length
            ? `<div><strong>${__("Actions")}:</strong> ${actions.map((action) => frappe.utils.escape_html(action)).join(", ")}</div>`
            : "";
        const deviceTable = deviceRows
            ? `
                <table class="table table-bordered table-sm warehouse-layout-stock-table">
                    <thead>
                        <tr>
                            <th>${__("Device")}</th>
                            <th>${__("Status")}</th>
                        </tr>
                    </thead>
                    <tbody>${deviceRows}</tbody>
                </table>
            `
            : `<div class="warehouse-layout-placeholder">${__("No devices returned from WCS bridge.")}</div>`;

        frm.dashboard.set_headline_alert(
            __("PLC simulator ready: {0} device(s)", [snapshot.deviceCount || 0]),
            "green"
        );

        frappe.msgprint({
            title: __("PLC Simulator"),
            message: `
                <div class="warehouse-layout-cell-dialog">
                    <div><strong>${__("Bridge URL")}:</strong> ${frappe.utils.escape_html(data.bridge_url || "")}</div>
                    <div><strong>${__("Configuration")}:</strong> ${frappe.utils.escape_html(data.used_configuration_path || __("Inline JSON"))}</div>
                    <div><strong>${__("Initialized")}:</strong> ${snapshot.isInitialized ? __("Yes") : __("No")}</div>
                    <div><strong>${__("Device Count")}:</strong> ${snapshot.deviceCount || 0}</div>
                    <div><strong>${__("Event Count")}:</strong> ${snapshot.eventCount || 0}</div>
                    ${actionHtml}
                    ${noticeHtml}
                    ${deviceTable}
                </div>
            `,
        });
    });
}

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

    if (!frm.doc.total_floors || !frm.doc.total_rails || !frm.doc.total_blocks || !frm.doc.total_depths) {
        wrapper.html(
            `<div class="warehouse-layout-placeholder">
                Set floors, rails, blocks, and depths to render the WCS layout.
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
        drawGrid(wrapper, data.layout || {}, data.positions || []);
    });
}

function drawGrid(wrapper, layout, positions) {
    const floors = Array.from(
        { length: Math.max(layout.total_floors || 1, 1) },
        (_, index) => index + 1
    );
    const totalQty = positions.reduce((sum, position) => sum + (position.total_qty || 0), 0);
    const occupiedPositions = positions.filter((position) => position.total_qty > 0).length;
    const positionMap = new Map();

    positions.forEach((position) => {
        const floor = Number(position.floor || 0);
        if (!positionMap.has(floor)) {
            positionMap.set(floor, new Map());
        }
        positionMap.get(floor).set(`${position.rail}:${position.block}`, position);
    });

    let selectedFloor = floors[0];

    function renderFloor() {
        const floorPositions = positionMap.get(selectedFloor) || new Map();
        const gridCells = [];

        for (let rail = 1; rail <= Math.max(layout.total_rails || 1, 1); rail += 1) {
            for (let block = 1; block <= Math.max(layout.total_blocks || 1, 1); block += 1) {
                const position = floorPositions.get(`${rail}:${block}`);
                if (!position) {
                    gridCells.push(`
                        <button type="button" class="warehouse-layout-cell" disabled>
                            <span class="warehouse-layout-cell__code">F${selectedFloor}R${rail}B${block}</span>
                            <span class="warehouse-layout-cell__meta">No depth cell configured</span>
                        </button>
                    `);
                    continue;
                }

                const occupancyLabel = position.total_qty > 0
                    ? `${formatQty(position.total_qty)} qty / ${position.occupied_depths || 0} depth`
                    : `${position.depth_cells.length || 0} depth / Empty`;
                const depthChips = (position.depth_cells || []).map((cell) => `
                    <span class="warehouse-layout-depth-chip ${cell.total_qty > 0 ? "is-occupied" : ""}">
                        D${cell.depth}
                    </span>
                `).join("");

                gridCells.push(`
                    <button
                        type="button"
                        class="warehouse-layout-cell warehouse-layout-cell--${(position.status || "available").toLowerCase()}"
                        data-floor="${selectedFloor}"
                        data-rail="${rail}"
                        data-block="${block}"
                    >
                        <span class="warehouse-layout-cell__code">${frappe.utils.escape_html(position.position_code || "")}</span>
                        <span class="warehouse-layout-cell__meta">${frappe.utils.escape_html(occupancyLabel)}</span>
                        <div class="warehouse-layout-cell__stack">${depthChips}</div>
                    </button>
                `);
            }
        }

        const floorTabs = floors.map((floor) => `
            <button
                type="button"
                class="warehouse-layout-floor-tab ${floor === selectedFloor ? "is-active" : ""}"
                data-floor="${floor}"
            >
                Floor ${floor}
            </button>
        `).join("");

        wrapper.html(`
            <div class="warehouse-layout-board">
                <div class="warehouse-layout-board__summary">
                    <div><strong>${frappe.utils.escape_html(layout.layout_name || layout.name || "")}</strong></div>
                    <div>${occupiedPositions} occupied position(s)</div>
                    <div>Total tracked qty: ${formatQty(totalQty)}</div>
                    <div>${layout.total_rails || 0} rail(s) x ${layout.total_blocks || 0} block(s) x ${layout.total_depths || 0} depth(s)</div>
                </div>
                <div class="warehouse-layout-floor-tabs">${floorTabs}</div>
                <div class="warehouse-layout-axis-note">
                    Viewing Floor ${selectedFloor}. Grid columns = Block, grid rows = Rail.
                </div>
                <div class="warehouse-layout-grid" style="grid-template-columns: repeat(${Math.max(layout.total_blocks || 1, 1)}, minmax(130px, 1fr));">
                    ${gridCells.join("")}
                </div>
            </div>
        `);

        wrapper.find(".warehouse-layout-floor-tab").on("click", function switchFloor() {
            selectedFloor = Number(this.dataset.floor || floors[0]);
            renderFloor();
        });

        wrapper.find(".warehouse-layout-cell").not("[disabled]").on("click", function clickPosition() {
            const floor = Number(this.dataset.floor || 0);
            const rail = Number(this.dataset.rail || 0);
            const block = Number(this.dataset.block || 0);
            const position = (positionMap.get(floor) || new Map()).get(`${rail}:${block}`);
            if (!position) {
                return;
            }

            showPositionDetails(position);
        });
    }

    renderFloor();
}

function showPositionDetails(position) {
    const depthRows = (position.depth_cells || []).map((cell) => `
        <tr>
            <td>D${cell.depth}</td>
            <td>${frappe.utils.escape_html(cell.status || "Available")}</td>
            <td>${formatQty(cell.total_qty || 0)}</td>
            <td>${cell.item_count || 0}</td>
            <td>${frappe.utils.escape_html(cell.notes || "-")}</td>
        </tr>
    `).join("");

    const stockRows = [];
    (position.depth_cells || []).forEach((cell) => {
        (cell.stock_rows || []).forEach((stockRow) => {
            stockRows.push(`
                <tr>
                    <td>D${cell.depth}</td>
                    <td>${frappe.utils.escape_html(stockRow.item_code || "")}</td>
                    <td>${frappe.utils.escape_html(stockRow.batch_no || "-")}</td>
                    <td>${formatQty(stockRow.qty || 0)}</td>
                    <td>${frappe.utils.escape_html(stockRow.uom || "-")}</td>
                </tr>
            `);
        });
    });

    const stockTable = stockRows.length
        ? `
            <table class="table table-bordered table-sm warehouse-layout-stock-table">
                <thead>
                    <tr>
                        <th>Depth</th>
                        <th>Item</th>
                        <th>Batch</th>
                        <th>Qty</th>
                        <th>UOM</th>
                    </tr>
                </thead>
                <tbody>${stockRows.join("")}</tbody>
            </table>
        `
        : `<div class="warehouse-layout-placeholder">This position is currently empty across all depths.</div>`;

    frappe.msgprint({
        title: `${position.position_code || position.position_label || ""}`,
        message: `
            <div class="warehouse-layout-cell-dialog">
                <div><strong>Status:</strong> ${frappe.utils.escape_html(position.status || "Available")}</div>
                <div><strong>Total Qty:</strong> ${formatQty(position.total_qty || 0)}</div>
                <div><strong>Tracked Items:</strong> ${position.item_count || 0}</div>
                <table class="table table-bordered table-sm warehouse-layout-stock-table">
                    <thead>
                        <tr>
                            <th>Depth</th>
                            <th>Status</th>
                            <th>Total Qty</th>
                            <th>Items</th>
                            <th>Notes</th>
                        </tr>
                    </thead>
                    <tbody>${depthRows}</tbody>
                </table>
                ${stockTable}
            </div>
        `,
    });
}

function formatQty(value) {
    const numericValue = Number(value || 0);
    return frappe.format(numericValue, { fieldtype: "Float", precision: 2 });
}
