frappe.ui.form.on("Purchase Receipt", {
    setup(frm) {
        frm.set_query("wh_layout", "items", (_, cdt, cdn) => {
            const row = locals[cdt][cdn];
            const filters = { is_active: 1 };
            if (row.warehouse) {
                filters.warehouse = row.warehouse;
            }
            return { filters };
        });

        frm.set_query("wh_cell", "items", (_, cdt, cdn) => {
            const row = locals[cdt][cdn];
            const filters = {
                status: ["!=", "Blocked"],
            };
            if (row.wh_layout) {
                filters.layout = row.wh_layout;
            }
            if (row.warehouse) {
                filters.warehouse = row.warehouse;
            }
            return { filters };
        });
    },

    refresh(frm) {
        window.requestAnimationFrame(() => {
            window.pharma_vn?.document_flow?.refresh(frm);
        });
        refreshStorageFieldIndicators(frm);
    },

    async validate(frm) {
        const pendingRows = await getPendingStorageRows(frm);
        applyStorageFieldIndicators(frm, pendingRows);
        if (!pendingRows.length) {
            return;
        }

        frappe.validated = false;
        frappe.throw(__("Thiếu vị trí nhập kho. Vui lòng chọn đủ WH Layout và WH Cell cho các dòng hàng dùng Warehouse Layout 2D."));
    },
});

frappe.ui.form.on("Purchase Receipt Item", {
    warehouse(frm, cdt, cdn) {
        frappe.model.set_value(cdt, cdn, "wh_layout", "");
        frappe.model.set_value(cdt, cdn, "wh_cell", "");
        refreshStorageFieldIndicators(frm);
    },

    wh_layout(frm, cdt, cdn) {
        const row = locals[cdt][cdn];
        refreshStorageFieldIndicators(frm);
        if (!row.wh_layout || !row.wh_cell) {
            return;
        }

        frappe.db.get_value("WH Cell", row.wh_cell, "layout").then((response) => {
            const data = response.message || {};
            if (data.layout && data.layout !== row.wh_layout) {
                frappe.model.set_value(cdt, cdn, "wh_cell", "");
            }
        });
    },

    wh_cell(frm, cdt, cdn) {
        const row = locals[cdt][cdn];
        refreshStorageFieldIndicators(frm);
        if (!row.wh_cell) {
            return;
        }

        frappe.db
            .get_value("WH Cell", row.wh_cell, ["layout", "warehouse", "cell_code"])
            .then((response) => {
                const data = response.message || {};
                if (data.layout && data.layout !== row.wh_layout) {
                    frappe.model.set_value(cdt, cdn, "wh_layout", data.layout);
                }
                if (data.warehouse && row.warehouse && data.warehouse !== row.warehouse) {
                    frappe.throw(
                        __("The selected storage cell belongs to warehouse {0}, not {1}", [
                            data.warehouse,
                            row.warehouse,
                        ])
                    );
                }
            });
    },
});

async function getPendingStorageRows(frm) {
    const candidateRows = (frm.doc.items || []).filter((row) => row.item_code && row.warehouse && !row.wh_cell);
    if (!candidateRows.length) {
        return [];
    }

    const warehouses = [...new Set(candidateRows.map((row) => row.warehouse).filter(Boolean))];
    const response = await frappe.call({
        method: "pharma_vn.api.warehouse_layout.get_active_layouts",
        args: { warehouses },
    });
    const layoutsByWarehouse = response.message?.data?.layouts_by_warehouse || {};

    return candidateRows
        .map((row) => {
            const layout = layoutsByWarehouse[row.warehouse];
            if (!layout) {
                return null;
            }
            return {
                row,
                rowLabel: __("Row #{0}", [row.idx]),
                layoutName: layout.name,
                layoutLabel: layout.layout_name || layout.name,
            };
        })
        .filter(Boolean);
}

function applyStorageFieldIndicators(frm, pendingRows) {
    const pendingNames = new Set((pendingRows || []).map((entry) => entry.row.name));
    const hasPendingRows = pendingNames.size > 0;
    const grid = frm.fields_dict.items?.grid;
    if (!grid) {
        return;
    }

    grid.update_docfield_property("wh_layout", "reqd", hasPendingRows ? 1 : 0);
    grid.update_docfield_property("wh_cell", "reqd", hasPendingRows ? 1 : 0);
    grid.grid_rows.forEach((gridRow) => {
        const shouldRequire = pendingNames.has(gridRow.doc.name);
        if (typeof gridRow.toggle_reqd === "function") {
            gridRow.toggle_reqd("wh_layout", shouldRequire);
            gridRow.toggle_reqd("wh_cell", shouldRequire);
        }
    });
    grid.refresh();
}

async function refreshStorageFieldIndicators(frm) {
    const pendingRows = await getPendingStorageRows(frm);
    applyStorageFieldIndicators(frm, pendingRows);
}
