frappe.ui.form.on("Salary Slip", {
	refresh(frm) {
		if (frm.is_new() || frm.doc.docstatus > 0 || !frm.doc.employee) {
			return;
		}

		frm.add_custom_button(__("Auto Calculate"), async () => {
			if (!frm.doc.start_date || !frm.doc.end_date) {
				frappe.msgprint(__("Vui lòng chọn Start Date và End Date trước khi tính lương."));
				return;
			}

			const response = await frappe.call({
				method: "pharma_vn.api.payroll.preview_salary",
				args: {
					employee: frm.doc.employee,
					from_date: frm.doc.start_date,
					to_date: frm.doc.end_date,
				},
			});

			const breakdown = response.message || {};
			frm.set_value("employee_contract", breakdown.employee_contract || null);
			frm.set_value("pharma_total_working_days", breakdown.total_working_days || 0);
			frm.set_value("pharma_total_working_hours", breakdown.total_working_hours || 0);
			frm.set_value("pharma_overtime_hours", breakdown.overtime_hours || 0);
			frm.set_value("pharma_base_salary", breakdown.base_salary || 0);
			frm.set_value("pharma_overtime_salary", breakdown.overtime_salary || 0);
			frm.set_value("pharma_allowance_total", breakdown.allowance_total || 0);
			frm.set_value("pharma_deduction_total", breakdown.total_deduction || 0);
			frm.set_value("pharma_taxable_income", breakdown.taxable_income || 0);
			frm.set_value("pharma_payroll_breakdown_json", JSON.stringify(breakdown, null, 2));

			frappe.msgprint(__("Đã tính lương tự động. Hãy lưu Salary Slip để ghi nhận earnings/deductions."));
		});
	},
});
