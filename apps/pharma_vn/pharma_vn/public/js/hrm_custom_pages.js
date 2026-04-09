frappe.provide("pharma_vn.hrm");

(function () {
	const entityOptions = [
		{ label: "Báo cáo", route: "hrm-reports" },
		{ label: "Nhân sự", route: "hrm-employee-profile" },
		{ label: "Hợp đồng", route: "hrm-contracts" },
		{ label: "Chấm công", route: "hrm-attendance" },
		{ label: "Nghỉ phép", route: "hrm-leave" },
		{ label: "Tính lương", route: "hrm-payroll" },
		{ label: "Đánh giá", route: "hrm-performance" },
		{ label: "KPI", route: "hrm-kpi" },
		{ label: "Book phòng họp", route: "hrm-meeting-room-booking" },
		{ label: "Lưu hồ sơ", route: "hrm-document-archive" },
		{ label: "Nghỉ việc", route: "hrm-offboarding" },
	];

	const pageConfigs = {
		"hrm-dashboard": {
			title: "HRM Dashboard",
			description: "Tổng quan nhanh toàn bộ nghiệp vụ nhân sự trên custom page.",
			is_dashboard: true,
		},
		"hrm-reports": {
			title: "Báo cáo",
			description: "Trung tâm report HRM với dropdown chọn từng nghiệp vụ và mẫu báo cáo chuyên nghiệp.",
			is_reports: true,
		},
		"hrm-employee-profile": {
			title: "Hồ sơ nhân sự",
			description: "Lưu hồ sơ nhân sự, thông tin liên hệ, công việc và hồ sơ cơ bản.",
			listTitle: "Danh sách nhân sự",
			formTitle: "Phiếu hồ sơ nhân sự",
			titleField: "full_name",
			fields: [
				field("employee_code", "Mã nhân sự"),
				field("full_name", "Họ và tên", "Data", { required: true }),
				field("status", "Trạng thái", "Select", { options: ["Draft", "Active", "On Leave", "Resigned"] }),
				field("company", "Công ty"),
				field("department", "Phòng ban"),
				field("designation", "Chức danh"),
				field("join_date", "Ngày vào làm", "Date"),
				field("date_of_birth", "Ngày sinh", "Date"),
				field("gender", "Giới tính", "Select", { options: ["Nam", "Nữ", "Khác"] }),
				field("phone", "Điện thoại"),
				field("email", "Email", "Data", { inputType: "email" }),
				field("id_number", "Số CCCD"),
				field("address", "Địa chỉ", "Text"),
				field("bank_account", "Tài khoản ngân hàng"),
				field("emergency_contact", "Liên hệ khẩn cấp"),
				field("notes", "Ghi chú", "Text"),
			],
			columns: [
				column("full_name", "Nhân sự"),
				column("employee_code", "Mã"),
				column("designation", "Chức danh"),
				column("department", "Phòng ban"),
				column("status", "Trạng thái"),
			],
		},
		"hrm-contracts": {
			title: "Hợp đồng",
			description: "Theo dõi hợp đồng lao động, thời hạn và điều khoản chính.",
			listTitle: "Danh sách hợp đồng",
			formTitle: "Phiếu hợp đồng",
			titleField: "contract_title",
			fields: [
				field("contract_title", "Tên hợp đồng", "Data", { required: true }),
				field("employee_name", "Nhân sự", "Data", { required: true }),
				field("employee_code", "Mã nhân sự"),
				field("status", "Trạng thái", "Select", { options: ["Draft", "Pending", "Active", "Expired", "Closed"] }),
				field("company", "Công ty"),
				field("contract_type", "Loại hợp đồng"),
				field("contract_number", "Số hợp đồng"),
				field("contract_start", "Ngày hiệu lực", "Date"),
				field("contract_end", "Ngày hết hạn", "Date"),
				field("salary_amount", "Lương thỏa thuận", "Currency"),
				field("probation_period", "Thử việc"),
				field("signer", "Người ký"),
				field("notes", "Điều khoản/Ghi chú", "Text"),
			],
			columns: [
				column("contract_title", "Hợp đồng"),
				column("employee_name", "Nhân sự"),
				column("contract_type", "Loại"),
				column("contract_start", "Hiệu lực"),
				column("status", "Trạng thái"),
			],
		},
		"hrm-attendance": {
			title: "Chấm công",
			description: "Ghi nhận ngày công, ca làm và số giờ làm việc.",
			listTitle: "Danh sách chấm công",
			formTitle: "Phiếu chấm công",
			titleField: "attendance_title",
			tools: "attendance",
			fields: [
				field("attendance_title", "Tiêu đề", "Data", { required: true }),
				field("employee_name", "Nhân sự", "Data", { required: true }),
				field("employee_code", "Mã nhân sự"),
				field("status", "Trạng thái", "Select", { options: ["Draft", "Submitted", "Approved"] }),
				field("company", "Công ty"),
				field("attendance_date", "Ngày công", "Date"),
				field("shift_name", "Ca làm"),
				field("check_in", "Giờ vào", "Time"),
				field("check_out", "Giờ ra", "Time"),
				field("working_hours", "Số giờ làm", "Float"),
				field("overtime_hours", "Tăng ca", "Float"),
				field("source", "Nguồn dữ liệu"),
				field("device_ip", "IP thiết bị"),
				field("notes", "Ghi chú", "Text"),
			],
			columns: [
				column("attendance_title", "Phiếu"),
				column("employee_name", "Nhân sự"),
				column("attendance_date", "Ngày công"),
				column("working_hours", "Giờ làm"),
				column("status", "Trạng thái"),
			],
		},
		"hrm-leave": {
			title: "Nghỉ phép",
			description: "Quản lý đơn nghỉ phép, thời gian nghỉ và trạng thái phê duyệt.",
			listTitle: "Danh sách nghỉ phép",
			formTitle: "Phiếu nghỉ phép",
			titleField: "leave_title",
			fields: [
				field("leave_title", "Tiêu đề", "Data", { required: true }),
				field("employee_name", "Nhân sự", "Data", { required: true }),
				field("employee_code", "Mã nhân sự"),
				field("status", "Trạng thái", "Select", { options: ["Draft", "Pending", "Approved", "Rejected"] }),
				field("company", "Công ty"),
				field("leave_type", "Loại nghỉ"),
				field("start_date", "Từ ngày", "Date"),
				field("end_date", "Đến ngày", "Date"),
				field("total_days", "Số ngày", "Float"),
				field("approver", "Người duyệt"),
				field("handover_to", "Bàn giao cho"),
				field("reason", "Lý do", "Text"),
			],
			columns: [
				column("leave_title", "Đơn nghỉ"),
				column("employee_name", "Nhân sự"),
				column("leave_type", "Loại nghỉ"),
				column("start_date", "Từ ngày"),
				column("status", "Trạng thái"),
			],
		},
		"hrm-payroll": {
			title: "Tính lương",
			description: "Lập bảng lương theo kỳ, thu nhập, khấu trừ và thực lĩnh.",
			listTitle: "Danh sách bảng lương",
			formTitle: "Phiếu tính lương",
			titleField: "payroll_title",
			tools: "payroll",
			fields: [
				field("payroll_title", "Tên bảng lương", "Data", { required: true }),
				field("employee_name", "Nhân sự", "Data", { required: true }),
				field("employee_code", "Mã nhân sự"),
				field("status", "Trạng thái", "Select", { options: ["Draft", "Calculated", "Approved", "Paid"] }),
				field("company", "Công ty"),
				field("pay_period", "Kỳ lương"),
				field("posting_date", "Ngày tính lương", "Date"),
				field("base_salary", "Lương cơ bản", "Currency"),
				field("allowance_amount", "Phụ cấp", "Currency"),
				field("deduction_amount", "Khấu trừ", "Currency"),
				field("net_salary", "Thực lĩnh", "Currency"),
				field("payment_method", "Phương thức trả lương"),
				field("notes", "Ghi chú", "Text"),
			],
			columns: [
				column("payroll_title", "Bảng lương"),
				column("employee_name", "Nhân sự"),
				column("pay_period", "Kỳ lương"),
				column("net_salary", "Thực lĩnh"),
				column("status", "Trạng thái"),
			],
		},
		"hrm-performance": {
			title: "Đánh giá",
			description: "Lưu phiếu đánh giá năng lực, kết quả và định hướng phát triển.",
			listTitle: "Danh sách đánh giá",
			formTitle: "Phiếu đánh giá",
			titleField: "review_title",
			fields: [
				field("review_title", "Tên phiếu", "Data", { required: true }),
				field("employee_name", "Nhân sự", "Data", { required: true }),
				field("employee_code", "Mã nhân sự"),
				field("status", "Trạng thái", "Select", { options: ["Draft", "In Review", "Completed"] }),
				field("company", "Công ty"),
				field("review_period", "Kỳ đánh giá"),
				field("reviewer", "Người đánh giá"),
				field("score", "Điểm số", "Float"),
				field("strengths", "Điểm mạnh", "Text"),
				field("improvement_plan", "Kế hoạch phát triển", "Text"),
				field("promotion_recommendation", "Đề xuất", "Text"),
			],
			columns: [
				column("review_title", "Phiếu"),
				column("employee_name", "Nhân sự"),
				column("review_period", "Kỳ"),
				column("score", "Điểm"),
				column("status", "Trạng thái"),
			],
		},
		"hrm-kpi": {
			title: "KPI",
			description: "Theo dõi mục tiêu KPI, trọng số, kết quả và mức hoàn thành.",
			listTitle: "Danh sách KPI",
			formTitle: "Phiếu KPI",
			titleField: "kpi_title",
			fields: [
				field("kpi_title", "Tên KPI", "Data", { required: true }),
				field("employee_name", "Nhân sự", "Data", { required: true }),
				field("employee_code", "Mã nhân sự"),
				field("status", "Trạng thái", "Select", { options: ["Draft", "Tracking", "Completed"] }),
				field("company", "Công ty"),
				field("kpi_period", "Kỳ KPI"),
				field("objective", "Mục tiêu", "Text"),
				field("weight", "Trọng số", "Float"),
				field("target_value", "Chỉ tiêu"),
				field("actual_value", "Kết quả"),
				field("achievement_rate", "Tỷ lệ hoàn thành", "Float"),
				field("notes", "Ghi chú", "Text"),
			],
			columns: [
				column("kpi_title", "KPI"),
				column("employee_name", "Nhân sự"),
				column("kpi_period", "Kỳ"),
				column("achievement_rate", "Hoàn thành %"),
				column("status", "Trạng thái"),
			],
		},
		"hrm-meeting-room-booking": {
			title: "Book phòng họp",
			description: "Đặt phòng họp, quản lý lịch sử dụng và người phụ trách.",
			listTitle: "Danh sách đặt phòng",
			formTitle: "Phiếu đặt phòng",
			titleField: "booking_title",
			fields: [
				field("booking_title", "Tên booking", "Data", { required: true }),
				field("employee_name", "Người đặt", "Data", { required: true }),
				field("employee_code", "Mã nhân sự"),
				field("status", "Trạng thái", "Select", { options: ["Draft", "Booked", "Completed", "Cancelled"] }),
				field("company", "Công ty"),
				field("meeting_room", "Phòng họp"),
				field("booking_date", "Ngày họp", "Date"),
				field("from_time", "Từ giờ", "Time"),
				field("to_time", "Đến giờ", "Time"),
				field("attendee_count", "Số người", "Int"),
				field("agenda", "Nội dung", "Text"),
				field("equipment_needed", "Thiết bị", "Text"),
			],
			columns: [
				column("booking_title", "Booking"),
				column("meeting_room", "Phòng"),
				column("booking_date", "Ngày"),
				column("employee_name", "Người đặt"),
				column("status", "Trạng thái"),
			],
		},
		"hrm-document-archive": {
			title: "Lưu hồ sơ",
			description: "Lưu và tra cứu hồ sơ liên quan đến nhân sự, hợp đồng và chứng từ.",
			listTitle: "Kho hồ sơ",
			formTitle: "Phiếu lưu hồ sơ",
			titleField: "document_title",
			fields: [
				field("document_title", "Tên hồ sơ", "Data", { required: true }),
				field("employee_name", "Nhân sự liên quan"),
				field("employee_code", "Mã nhân sự"),
				field("status", "Trạng thái", "Select", { options: ["Draft", "Stored", "Archived"] }),
				field("company", "Công ty"),
				field("document_type", "Loại hồ sơ"),
				field("posting_date", "Ngày lưu", "Date"),
				field("retention_until", "Lưu đến", "Date"),
				field("storage_location", "Vị trí lưu"),
				field("file_url", "File đính kèm", "Attach"),
				field("notes", "Mô tả", "Text"),
			],
			columns: [
				column("document_title", "Hồ sơ"),
				column("document_type", "Loại"),
				column("employee_name", "Nhân sự"),
				column("storage_location", "Vị trí"),
				column("status", "Trạng thái"),
			],
		},
		"hrm-offboarding": {
			title: "Nghỉ việc",
			description: "Theo dõi quy trình nghỉ việc, bàn giao và quyết toán.",
			listTitle: "Danh sách nghỉ việc",
			formTitle: "Phiếu nghỉ việc",
			titleField: "offboarding_title",
			fields: [
				field("offboarding_title", "Tên hồ sơ", "Data", { required: true }),
				field("employee_name", "Nhân sự", "Data", { required: true }),
				field("employee_code", "Mã nhân sự"),
				field("status", "Trạng thái", "Select", { options: ["Draft", "Pending", "In Clearance", "Completed"] }),
				field("company", "Công ty"),
				field("department", "Phòng ban"),
				field("resignation_date", "Ngày nộp đơn", "Date"),
				field("last_working_date", "Ngày làm cuối", "Date"),
				field("handover_to", "Bàn giao cho"),
				field("exit_interview", "Phỏng vấn nghỉ việc", "Text"),
				field("final_settlement", "Quyết toán", "Currency"),
				field("notes", "Ghi chú", "Text"),
			],
			columns: [
				column("offboarding_title", "Hồ sơ"),
				column("employee_name", "Nhân sự"),
				column("department", "Phòng ban"),
				column("last_working_date", "Ngày cuối"),
				column("status", "Trạng thái"),
			],
		},
	};

	function field(name, label, type = "Data", options = {}) {
		return Object.assign({ name, label, type }, options);
	}

	function column(name, label) {
		return { name, label };
	}

	function escapeHtml(value) {
		return frappe.utils.escape_html(value == null ? "" : String(value));
	}

	function formatNumberText(value, precision) {
		const numericValue = Number(value);
		if (!Number.isFinite(numericValue)) {
			return String(value ?? "");
		}

		const hasFraction = precision != null ? precision > 0 : !Number.isInteger(numericValue);
		return new Intl.NumberFormat("vi-VN", {
			minimumFractionDigits: hasFraction ? precision ?? 2 : 0,
			maximumFractionDigits: hasFraction ? precision ?? 2 : 0,
		}).format(numericValue);
	}

	function formatCurrencyText(value) {
		const numericValue = Number(value);
		if (!Number.isFinite(numericValue)) {
			return String(value ?? "");
		}

		const currency = frappe.boot?.sysdefaults?.currency || "VND";
		const formattedAmount = new Intl.NumberFormat("vi-VN", {
			minimumFractionDigits: 0,
			maximumFractionDigits: 0,
		}).format(numericValue);
		return `${currency} ${formattedAmount}`;
	}

	function formatMonthText(value) {
		if (!value) {
			return "";
		}

		const rawValue = String(value);
		const yearMonthMatch = rawValue.match(/^(\d{4})-(\d{2})(?:-\d{2})?$/);
		if (yearMonthMatch) {
			return `${yearMonthMatch[2]}/${yearMonthMatch[1]}`;
		}

		return rawValue;
	}

	function formatValue(fieldDef, value) {
		if (value == null || value === "") {
			return "";
		}
		if (fieldDef.name === "pay_period") {
			return formatMonthText(value);
		}
		if (fieldDef.type === "Currency") {
			return formatCurrencyText(value);
		}
		if (fieldDef.type === "Float") {
			return formatNumberText(value, 2);
		}
		if (fieldDef.type === "Int") {
			return formatNumberText(value, 0);
		}
		return value;
	}

	function formatReportValue(type, value) {
		if (value == null || value === "") {
			return "";
		}
		if (type === "Currency") {
			return formatCurrencyText(value);
		}
		if (type === "Float") {
			return formatNumberText(value, 1);
		}
		if (type === "Percent") {
			return `${formatNumberText(value, 1)}%`;
		}
		if (type === "Int") {
			return formatNumberText(value, 0);
		}
		if (type === "Date") {
			try {
				return frappe.datetime.str_to_user(value);
			} catch (e) {
				return value;
			}
		}
		return value;
	}

	function getColumnClass(fieldDef) {
		if (["Currency", "Float", "Int"].includes(fieldDef.type)) {
			return " class=\"ph-hrm-cell--numeric\"";
		}
		return "";
	}

	function getReportColumnClass(fieldDef) {
		if (["Currency", "Float", "Int", "Percent"].includes(fieldDef.type)) {
			return " class=\"ph-hrm-cell--numeric\"";
		}
		return "";
	}

	function getDefaultReportFilters() {
		return {
			month: frappe.datetime.month_start(),
			department: "",
			company: "",
			employee_keyword: "",
		};
	}

	function getConfig(pageName) {
		return pageConfigs[pageName];
	}

	function getFields(config) {
		return config.fields || [];
	}

	function getDefaultDoc(config) {
		const doc = {};
		getFields(config).forEach((fieldDef) => {
			doc[fieldDef.name] = fieldDef.default || "";
		});
		return doc;
	}

	function renderInput(fieldDef, value) {
		const safeValue = escapeHtml(value || "");
		const requiredAttr = fieldDef.required ? "required" : "";
		if (fieldDef.type === "Text") {
			return `<textarea class="form-control" data-fieldname="${fieldDef.name}" rows="3" ${requiredAttr}>${safeValue}</textarea>`;
		}
		if (fieldDef.type === "Select") {
			const options = (fieldDef.options || []).map((option) => {
				const selected = option === value ? "selected" : "";
				return `<option value="${escapeHtml(option)}" ${selected}>${escapeHtml(option)}</option>`;
			});
			return `<select class="form-control" data-fieldname="${fieldDef.name}" ${requiredAttr}><option value=""></option>${options.join("")}</select>`;
		}
		if (fieldDef.type === "Attach") {
			return `
				<div class="hrm-attach-field">
					<input class="form-control" type="text" data-fieldname="${fieldDef.name}" value="${safeValue}" placeholder="File URL" />
					<button class="btn btn-default btn-sm" type="button" data-attach-field="${fieldDef.name}">Upload</button>
				</div>
			`;
		}
		const inputTypeMap = {
			Date: "date",
			Time: "time",
			Float: "number",
			Int: "number",
			Currency: "number",
		};
		const inputType = fieldDef.inputType || inputTypeMap[fieldDef.type] || "text";
		const step = ["Float", "Currency"].includes(fieldDef.type) ? 'step="0.01"' : "";
		return `<input class="form-control" type="${inputType}" data-fieldname="${fieldDef.name}" value="${safeValue}" ${step} ${requiredAttr} />`;
	}

	function renderDashboard(wrapper, page, state, config) {
		const stats = state.stats || [];
		const recentRecords = state.recentRecords || [];
		const reports = state.reports || [];
		wrapper.find(".layout-main-section").html(`
			<div class="ph-hrm-dashboard">
				<div class="ph-hrm-hero">
					<div>
						<div class="ph-hrm-kicker">Custom HRM Module</div>
						<h1>${escapeHtml(config.title)}</h1>
						<p>${escapeHtml(config.description)}</p>
					</div>
					<div class="ph-hrm-hero-actions">
						<button class="btn btn-primary" data-route="hrm-employee-profile">Mở hồ sơ nhân sự</button>
						<button class="btn btn-default" data-route="hrm-payroll">Mở tính lương</button>
					</div>
				</div>
				<div class="ph-hrm-grid ph-hrm-stat-grid">
					${stats
						.map(
							(item) => `
							<div class="ph-hrm-card ph-hrm-stat-card">
								<div class="ph-hrm-label">${escapeHtml(item.label)}</div>
								<div class="ph-hrm-value">${escapeHtml(item.total)}</div>
								<div class="ph-hrm-meta">${frappe.format(item.total_amount || 0, { fieldtype: "Currency" })}</div>
								<button class="btn btn-link" data-route="${item.page_key}">Mở trang</button>
							</div>
						`
						)
						.join("")}
				</div>
				<div class="ph-hrm-grid ph-hrm-link-grid">
					${entityOptions
						.map(
							(item) => `
							<div class="ph-hrm-card ph-hrm-link-card" data-route="${item.route}">
								<div class="ph-hrm-label">${escapeHtml(item.label)}</div>
								<div class="ph-hrm-meta">Custom page + list + form</div>
							</div>
						`
						)
						.join("")}
				</div>
				<div class="ph-hrm-card">
					<div class="ph-hrm-section-title">Hoạt động gần đây</div>
					<div class="ph-hrm-recent-list">
						${recentRecords.length
							? recentRecords
									.map(
										(item) => `
										<div class="ph-hrm-recent-item" data-route="${item.page_key}">
											<div>
												<div class="ph-hrm-label">${escapeHtml(item.title || item.label)}</div>
												<div class="ph-hrm-meta">${escapeHtml(item.employee_name || item.label || "")}</div>
											</div>
											<div class="ph-hrm-pill">${escapeHtml(item.status || "Saved")}</div>
										</div>
									`
									)
									.join("")
							: '<div class="text-muted">Chưa có dữ liệu HRM.</div>'}
					</div>
				</div>
				<div class="ph-hrm-card">
					<div class="ph-hrm-section-title">Báo cáo HRM</div>
					<div class="ph-hrm-report-grid">
						${reports.length
							? reports
									.map(
										(item) => `
											<div class="ph-hrm-report-card" data-route="${item.page_key}">
												<div class="ph-hrm-label">${escapeHtml(item.title)}</div>
												<div class="ph-hrm-report-meta">Hồ sơ: ${escapeHtml(item.total_records)}</div>
												<div class="ph-hrm-report-meta">Nhân sự: ${escapeHtml(item.total_employees)}</div>
												<div class="ph-hrm-report-meta">Tổng tiền: ${escapeHtml(formatCurrencyText(item.total_amount || 0))}</div>
												<div class="ph-hrm-report-statuses">
													${(item.statuses || [])
														.slice(0, 3)
														.map(
															(statusRow) => `
																<span class="ph-hrm-report-pill">${escapeHtml(statusRow.status)}: ${escapeHtml(statusRow.total)}</span>
															`
														)
														.join("")}
												</div>
											</div>
										`
									)
									.join("")
							: '<div class="text-muted">Chưa có dữ liệu báo cáo.</div>'}
					</div>
				</div>
			</div>
		`);

		wrapper.find("[data-route]").on("click", function () {
			const route = $(this).attr("data-route");
			frappe.set_route(route);
		});
	}

	function renderEntityPage(wrapper, page, state, config) {
		const hasActiveForm = Boolean(state.showForm);
		wrapper.find(".layout-main-section").html(`
			<div class="ph-hrm-entity-page">
				<div class="ph-hrm-page-head">
					<div>
						<div class="ph-hrm-kicker">HRM Custom Page</div>
						<h1>${escapeHtml(config.title)}</h1>
						<p>${escapeHtml(config.description)}</p>
					</div>
				</div>
				${renderTools(state, config)}
				<div class="ph-hrm-grid ph-hrm-main-grid">
					<div class="ph-hrm-card ${hasActiveForm ? "is-split" : "is-full"}">
						<div class="ph-hrm-section-title">${escapeHtml(config.listTitle)}</div>
						<div class="ph-hrm-list" data-region="list"></div>
					</div>
					<div class="ph-hrm-card ph-hrm-form-card ${hasActiveForm ? "" : "is-hidden"}">
						<div class="ph-hrm-section-title">${escapeHtml(config.formTitle)}</div>
						<form class="ph-hrm-form" data-region="form">
							<div class="ph-hrm-form-grid">
								${getFields(config)
									.map(
										(fieldDef) => `
										<div class="ph-hrm-field ${fieldDef.type === "Text" ? "is-full" : ""}">
											<label>${escapeHtml(fieldDef.label)}</label>
											${renderInput(fieldDef, state.formDoc[fieldDef.name])}
										</div>
									`
									)
									.join("")}
							</div>
						</form>
						<div class="ph-hrm-form-footer">
							<div class="text-muted" data-region="status"></div>
							<div class="ph-hrm-inline-actions">
								<button class="btn btn-default" type="button" data-action="close">Đóng</button>
								<button class="btn btn-default" type="button" data-action="delete" ${state.formDoc.name ? "" : "disabled"}>Xóa</button>
								<button class="btn btn-primary" type="button" data-action="save">Lưu</button>
							</div>
						</div>
					</div>
				</div>
			</div>
		`);

		renderList(wrapper, state, config);
		bindForm(wrapper, page, state, config);
	}

	function renderReportsPage(wrapper, page, state, config) {
		const catalog = state.reportCatalog || [];
		const selectedKey = state.selectedReportKey || catalog[0]?.page_key || "";
		const selected = catalog.find((item) => item.page_key === selectedKey) || catalog[0] || {};
		const summary = selected.summary || {};
		const sampleReports = selected.sample_reports || [];
		const selectedTemplateId = state.selectedTemplateId || sampleReports[0]?.id || "";
		const activeTemplate = sampleReports.find((item) => item.id === selectedTemplateId) || sampleReports[0] || {};
		const reportFilters = state.reportFilters || getDefaultReportFilters();

		wrapper.find(".layout-main-section").html(`
			<div class="ph-hrm-entity-page">
				<div class="ph-hrm-page-head">
					<div>
						<div class="ph-hrm-kicker">HRM Report Center</div>
						<h1>${escapeHtml(config.title)}</h1>
						<p>${escapeHtml(config.description)}</p>
					</div>
				</div>
				<div class="ph-hrm-card">
					<div class="ph-hrm-section-title">Chọn mục báo cáo</div>
					<div class="ph-hrm-report-toolbar">
						<select class="form-control" data-report-select>
							${catalog
								.map(
									(item) => `
										<option value="${escapeHtml(item.page_key)}" ${item.page_key === selectedKey ? "selected" : ""}>
											${escapeHtml(item.title)}
										</option>
									`
								)
								.join("")}
						</select>
					</div>
				</div>
				<div class="ph-hrm-report-layout">
					<div class="ph-hrm-card">
						<div class="ph-hrm-section-title">${escapeHtml(selected.title || "Báo cáo")}</div>
						<div class="ph-hrm-preview-grid">
							<div class="ph-hrm-preview-card">
								<div class="ph-hrm-meta">Tổng hồ sơ</div>
								<div class="ph-hrm-label">${escapeHtml(summary.total_records || 0)}</div>
							</div>
							<div class="ph-hrm-preview-card">
								<div class="ph-hrm-meta">Tổng nhân sự</div>
								<div class="ph-hrm-label">${escapeHtml(summary.total_employees || 0)}</div>
							</div>
							<div class="ph-hrm-preview-card">
								<div class="ph-hrm-meta">Tổng tiền</div>
								<div class="ph-hrm-label">${escapeHtml(formatCurrencyText(summary.total_amount || 0))}</div>
							</div>
							<div class="ph-hrm-preview-card">
								<div class="ph-hrm-meta">Cập nhật gần nhất</div>
								<div class="ph-hrm-label">${escapeHtml(summary.latest_update || "Chưa có")}</div>
							</div>
						</div>
					</div>
					<div class="ph-hrm-card">
						<div class="ph-hrm-section-title">Trạng thái chính</div>
						<div class="ph-hrm-report-statuses">
							${(summary.statuses || []).length
								? summary.statuses
										.map(
											(item) => `
												<span class="ph-hrm-report-pill">${escapeHtml(item.status)}: ${escapeHtml(item.total)}</span>
											`
										)
										.join("")
								: '<div class="text-muted">Chưa có dữ liệu trạng thái.</div>'}
						</div>
					</div>
					<div class="ph-hrm-card">
						<div class="ph-hrm-section-title">Mẫu report đề xuất</div>
						<div class="ph-hrm-report-template-list">
							${sampleReports.length
								? sampleReports
										.map(
											(item, index) => `
												<div class="ph-hrm-report-template-item ${item.id === selectedTemplateId ? "is-active" : ""}">
													<div class="ph-hrm-report-template-head">
														<div class="ph-hrm-label">${escapeHtml(item.title || `Report ${index + 1}`)}</div>
														<div class="ph-hrm-report-template-order">Mẫu ${index + 1}</div>
													</div>
													<div class="ph-hrm-meta">${escapeHtml(item.description || item)}</div>
													${Array.isArray(item.metrics) && item.metrics.length
														? `
															<div class="ph-hrm-report-template-group">
																<div class="ph-hrm-report-template-caption">Chỉ số nên xem</div>
																<div class="ph-hrm-report-chip-row">
																	${item.metrics
																		.map((metric) => `<span class="ph-hrm-report-chip is-metric">${escapeHtml(metric)}</span>`)
																		.join("")}
																</div>
															</div>
														`
														: ""}
													${Array.isArray(item.filters) && item.filters.length
														? `
															<div class="ph-hrm-report-template-group">
																<div class="ph-hrm-report-template-caption">Bộ lọc gợi ý</div>
																<div class="ph-hrm-report-chip-row">
																	${item.filters
																		.map((filter) => `<span class="ph-hrm-report-chip is-filter">${escapeHtml(filter)}</span>`)
																		.join("")}
																</div>
															</div>
														`
														: ""}
													<div class="ph-hrm-inline-actions">
														<button class="btn btn-default btn-sm" type="button" data-run-template="${escapeHtml(item.id)}">
															Chạy report
														</button>
													</div>
												</div>
											`
										)
										.join("")
								: '<div class="text-muted">Chưa có mẫu report.</div>'}
						</div>
					</div>
				</div>
			</div>
		`);

		wrapper.find("[data-report-select]").on("change", function () {
			state.selectedReportKey = $(this).val();
			const moduleCatalog = catalog.find((item) => item.page_key === state.selectedReportKey) || {};
			state.selectedTemplateId = moduleCatalog.sample_reports?.[0]?.id || "";
			state.reportData = null;
			renderReportsPage(wrapper, page, state, config);
			loadActiveReport(page);
		});

		wrapper.find("[data-run-template]").on("click", function () {
			state.selectedTemplateId = $(this).attr("data-run-template");
			state.reportData = null;
			renderReportsPage(wrapper, page, state, config);
			openReportViewerDialog(page);
		});
	}

	function renderReportResult(reportData, activeTemplate, isLoading) {
		if (isLoading) {
			return '<div class="text-warning">Đang tải dữ liệu report...</div>';
		}
		if (!activeTemplate?.id) {
			return '<div class="text-muted">Chọn một mẫu report để xem dữ liệu thật.</div>';
		}
		if (!reportData) {
			return '<div class="text-muted">Bấm "Xem dữ liệu thật" để tải bảng dữ liệu cho mẫu report này.</div>';
		}
		const summary = reportData.summary || [];
		const columns = reportData.columns || [];
		const rows = reportData.rows || [];
		return `
			<div class="ph-hrm-meta" style="margin-bottom:12px;">${escapeHtml(reportData.description || activeTemplate.description || "")}</div>
			<div class="ph-hrm-preview-grid">
				${summary.length
					? summary
							.map(
								(item) => `
									<div class="ph-hrm-preview-card">
										<div class="ph-hrm-meta">${escapeHtml(item.label)}</div>
										<div class="ph-hrm-label">${escapeHtml(formatReportValue(item.type, item.value))}</div>
									</div>
								`
							)
							.join("")
					: '<div class="text-muted">Chưa có chỉ số tổng hợp.</div>'}
			</div>
			<div class="ph-hrm-report-table-wrap">
				${rows.length
					? `
						<table class="table table-bordered ph-hrm-table">
							<thead>
								<tr>${columns.map((col) => `<th>${escapeHtml(col.label)}</th>`).join("")}</tr>
							</thead>
							<tbody>
								${rows
									.map(
										(row) => `
											<tr>
												${columns
													.map((col) => `<td${getReportColumnClass(col)}>${escapeHtml(formatReportValue(col.type, row[col.fieldname]))}</td>`)
													.join("")}
											</tr>
										`
									)
									.join("")}
							</tbody>
						</table>
					`
					: `<div class="text-muted">${escapeHtml(reportData.empty_message || "Không có dữ liệu phù hợp.")}</div>`}
			</div>
		`;
	}

	function getActiveReportSelection(state) {
		const catalog = state.reportCatalog || [];
		const selectedModule = catalog.find((item) => item.page_key === state.selectedReportKey) || catalog[0];
		const selectedTemplate =
			(selectedModule?.sample_reports || []).find((item) => item.id === state.selectedTemplateId) ||
			selectedModule?.sample_reports?.[0];
		return { selectedModule, selectedTemplate };
	}

	function openReportViewerDialog(page) {
		const state = page.wrapper.__hrmState || {};
		const { selectedModule, selectedTemplate } = getActiveReportSelection(state);
		if (!selectedModule || !selectedTemplate?.id) {
			frappe.msgprint("Chọn một mẫu report trước khi xem dữ liệu.");
			return;
		}

		const dialog = new frappe.ui.Dialog({
			title: selectedTemplate.title || "Xem báo cáo",
			size: "extra-large",
			fields: [
				{
					fieldname: "viewer_html",
					fieldtype: "HTML",
					options: '<div data-report-viewer-dialog></div>',
				},
			],
		});
		dialog.show();
		dialog.$wrapper.find(".modal-footer").hide();
		renderReportViewerDialog(page, dialog);
		runReportInDialog(page, dialog, false);
	}

	function renderReportViewerDialog(page, dialog) {
		const state = page.wrapper.__hrmState || {};
		const { selectedModule, selectedTemplate } = getActiveReportSelection(state);
		const reportFilters = state.reportFilters || getDefaultReportFilters();
		const reportData = state.reportData || null;
		const viewer = dialog.$wrapper.find("[data-report-viewer-dialog]");
		viewer.html(`
			<div class="ph-hrm-report-dialog-shell">
				<div class="ph-hrm-report-dialog-sidebar">
					<div class="ph-hrm-section-title">Bộ lọc báo cáo</div>
					<div class="ph-hrm-meta">${escapeHtml(selectedModule?.title || "")}</div>
					<div class="ph-hrm-meta" style="margin-top:4px;">${escapeHtml(selectedTemplate?.title || "")}</div>
					<div class="ph-hrm-report-dialog-filter-list">
						<div class="ph-hrm-field">
							<label>Tháng báo cáo</label>
							<input class="form-control" type="date" data-dialog-report-filter="month" value="${escapeHtml(reportFilters.month || "")}" />
						</div>
						<div class="ph-hrm-field">
							<label>Phòng ban</label>
							<input class="form-control" type="text" data-dialog-report-filter="department" value="${escapeHtml(reportFilters.department || "")}" placeholder="Ví dụ: Sales" />
						</div>
						<div class="ph-hrm-field">
							<label>Công ty</label>
							<input class="form-control" type="text" data-dialog-report-filter="company" value="${escapeHtml(reportFilters.company || "")}" placeholder="Ví dụ: Viet An Pharma JSC" />
						</div>
						<div class="ph-hrm-field">
							<label>Từ khóa nhân sự</label>
							<input class="form-control" type="text" data-dialog-report-filter="employee_keyword" value="${escapeHtml(reportFilters.employee_keyword || "")}" placeholder="Mã hoặc tên nhân sự" />
						</div>
					</div>
					<div class="ph-hrm-inline-actions">
						<button class="btn btn-primary" type="button" data-action="dialog-run-report">Xem dữ liệu</button>
						<button class="btn btn-default" type="button" data-action="dialog-export-report" data-export-format="xlsx">Excel</button>
						<button class="btn btn-default" type="button" data-action="dialog-export-report" data-export-format="pdf">PDF</button>
					</div>
				</div>
				<div class="ph-hrm-report-dialog-content">
					<div class="ph-hrm-section-title">Dữ liệu báo cáo</div>
					${renderReportResult(reportData, selectedTemplate, state.isReportLoading)}
				</div>
			</div>
		`);

		viewer.find("[data-dialog-report-filter]").on("change input", function () {
			const fieldname = $(this).attr("data-dialog-report-filter");
			state.reportFilters = state.reportFilters || getDefaultReportFilters();
			state.reportFilters[fieldname] = $(this).val();
		});

		viewer.find('[data-action="dialog-run-report"]').on("click", async () => {
			await runReportInDialog(page, dialog, true);
		});

		viewer.find('[data-action="dialog-export-report"]').on("click", function () {
			exportActiveReport(page, $(this).attr("data-export-format"));
		});
	}

	async function runReportInDialog(page, dialog, forceReload) {
		await loadActiveReport(page, forceReload);
		renderReportViewerDialog(page, dialog);
	}

	function renderTools(state, config) {
		if (config.tools === "attendance") {
			const device = state.deviceConfig || getDefaultDeviceConfig();
			return `
				<div class="ph-hrm-card ph-hrm-tools-card">
					<div class="ph-hrm-tools-grid">
						<div class="ph-hrm-tool-block">
							<div class="ph-hrm-section-title">Import Excel / CSV</div>
							<div class="ph-hrm-meta">Hỗ trợ CSV, XLSX. Dòng đầu tiên là header: employee_code, employee_name, attendance_date, check_in, check_out...</div>
							<div class="ph-hrm-inline-actions">
								<button class="btn btn-default" type="button" data-action="attendance-template">Download template</button>
								<button class="btn btn-primary" type="button" data-action="attendance-import">Import file</button>
							</div>
						</div>
						<div class="ph-hrm-tool-block">
							<div class="ph-hrm-section-title">Kết nối máy chấm công qua IP LAN</div>
							<div class="ph-hrm-lan-grid">
								<div class="ph-hrm-field">
									<label>Protocol</label>
									<select class="form-control" data-device-field="protocol">
										<option value="http" ${device.protocol === "http" ? "selected" : ""}>http</option>
										<option value="https" ${device.protocol === "https" ? "selected" : ""}>https</option>
									</select>
								</div>
								<div class="ph-hrm-field">
									<label>IP Address</label>
									<input class="form-control" data-device-field="ip_address" value="${escapeHtml(device.ip_address || "")}" />
								</div>
								<div class="ph-hrm-field">
									<label>Port</label>
									<input class="form-control" data-device-field="port" value="${escapeHtml(device.port || "80")}" />
								</div>
								<div class="ph-hrm-field">
									<label>Endpoint</label>
									<input class="form-control" data-device-field="endpoint" value="${escapeHtml(device.endpoint || "/api/attendance")}" />
								</div>
								<div class="ph-hrm-field">
									<label>Auth Token</label>
									<input class="form-control" data-device-field="auth_token" value="${escapeHtml(device.auth_token || "")}" />
								</div>
								<div class="ph-hrm-field">
									<label>Timeout (s)</label>
									<input class="form-control" data-device-field="timeout" value="${escapeHtml(device.timeout || "8")}" />
								</div>
							</div>
							<div class="ph-hrm-inline-actions">
								<button class="btn btn-primary" type="button" data-action="attendance-sync-device">Đồng bộ từ IP LAN</button>
							</div>
						</div>
					</div>
				</div>
			`;
		}
		if (config.tools === "payroll") {
			return `
				<div class="ph-hrm-card ph-hrm-tools-card">
					<div class="ph-hrm-tools-grid">
						<div class="ph-hrm-tool-block">
							<div class="ph-hrm-section-title">Tính lương tự động</div>
							<div class="ph-hrm-meta">Lấy dữ liệu trực tiếp từ Attendance, Employee Contract và tạo Salary Slip chuẩn ERPNext theo tháng.</div>
							<div class="ph-hrm-inline-actions">
								<button class="btn btn-primary" type="button" data-action="payroll-generate">Tính lương tự động</button>
								<button class="btn btn-default" type="button" data-action="payroll-refresh">Làm mới danh sách</button>
								<button class="btn btn-default" type="button" data-action="payroll-formula">Công thức tính lương</button>
							</div>
						</div>
					</div>
				</div>
			`;
		}
		return "";
	}

	function renderList(wrapper, state, config) {
		const listContainer = wrapper.find('[data-region="list"]');
		if (!state.records.length) {
			listContainer.html('<div class="text-muted">Chưa có dữ liệu.</div>');
			return;
		}

		listContainer.html(`
			<table class="table table-bordered ph-hrm-table">
				<thead>
					<tr>
						${config.columns.map((col) => `<th>${escapeHtml(col.label)}</th>`).join("")}
						<th style="width: 160px;">Hành động</th>
					</tr>
				</thead>
				<tbody>
					${state.records
						.map(
							(record) => `
							<tr data-record-name="${record.name}">
								${config.columns
									.map((col) => {
										const fieldDef = getFields(config).find((item) => item.name === col.name) || { type: "Data" };
										return `<td${getColumnClass(fieldDef)}>${escapeHtml(formatValue(fieldDef, record[col.name]) || "")}</td>`;
									})
									.join("")}
								<td>
									<button class="btn btn-xs btn-default" data-action="edit" data-record-name="${record.name}">Mở</button>
									<button class="btn btn-xs btn-danger" data-action="delete-row" data-record-name="${record.name}">Xóa</button>
								</td>
							</tr>
						`
						)
						.join("")}
				</tbody>
			</table>
		`);
	}

	function bindForm(wrapper, page, state, config) {
		if (config.tools === "attendance") {
			bindAttendanceTools(wrapper, page, state);
		}
		if (config.tools === "payroll") {
			bindPayrollTools(wrapper, page, state);
		}

		wrapper.find('[data-action="close"]').on("click", () => {
			hideForm(page, state, config);
		});

		wrapper.find('[data-action="save"]').on("click", async () => {
			const doc = collectForm(wrapper, config, state.formDoc);
			if (!validateForm(doc, config)) {
				return;
			}
			await saveRecord(page, state, config, doc);
		});

		wrapper.find('[data-action="delete"]').on("click", async () => {
			if (!state.formDoc.name) {
				return;
			}
			await deleteListRecord(page, state, config, state.formDoc.name);
		});

		wrapper.find('[data-action="edit"]').on("click", function () {
			const recordName = $(this).attr("data-record-name");
			const matched = state.records.find((item) => item.name === recordName);
			if (matched) {
				state.formDoc = Object.assign(getDefaultDoc(config), matched);
				state.showForm = true;
				rerender(page.wrapper, page, state.pageName);
			}
		});

		wrapper.find('[data-action="delete-row"]').on("click", async function (event) {
			event.stopPropagation();
			const recordName = $(this).attr("data-record-name");
			await deleteListRecord(page, state, config, recordName);
		});

		wrapper.find("[data-attach-field]").on("click", function () {
			const fieldname = $(this).attr("data-attach-field");
			new frappe.ui.FileUploader({
				on_success(fileDoc) {
					const input = wrapper.find(`[data-fieldname="${fieldname}"]`);
					input.val(fileDoc.file_url).trigger("change");
				},
			});
		});
	}

	function bindAttendanceTools(wrapper, page, state) {
		wrapper.find("[data-device-field]").on("change input", function () {
			const fieldname = $(this).attr("data-device-field");
			state.deviceConfig = state.deviceConfig || getDefaultDeviceConfig();
			state.deviceConfig[fieldname] = $(this).val();
			saveDeviceConfig(state.deviceConfig);
		});

		wrapper.find('[data-action="attendance-template"]').on("click", () => {
			const url = `/api/method/pharma_vn.api.hrm.download_attendance_template`;
			window.open(url, "_blank");
		});

		wrapper.find('[data-action="attendance-import"]').on("click", () => {
			new frappe.ui.FileUploader({
				allow_multiple: false,
				restrictions: { allowed_file_types: [".csv", ".xlsx", ".xls"] },
				on_success: async (fileDoc) => {
					await importAttendanceFile(page, fileDoc.file_url);
				},
			});
		});

		wrapper.find('[data-action="attendance-sync-device"]').on("click", async () => {
			await syncAttendanceDevice(page, state.deviceConfig || getDefaultDeviceConfig());
		});
	}

	function bindPayrollTools(wrapper, page, state) {
		wrapper.find('[data-action="payroll-generate"]').on("click", () => {
			openPayrollDialog(page);
		});

		wrapper.find('[data-action="payroll-refresh"]').on("click", async () => {
			await refreshEntityData(page, state.pageName);
		});

		wrapper.find('[data-action="payroll-formula"]').on("click", async () => {
			await openPayrollFormulaDialog();
		});
	}

	function openPayrollDialog(page) {
		const dialog = new frappe.ui.Dialog({
			title: "Tính lương tự động",
			fields: [
				{
					fieldname: "all_employees",
					label: "Tính lương toàn bộ nhân viên",
					fieldtype: "Check",
					default: 1,
				},
				{
					fieldname: "employee",
					label: "Nhân sự",
					fieldtype: "Link",
					options: "Employee",
				},
				{
					fieldname: "month",
					label: "Tháng lương",
					fieldtype: "Date",
					reqd: 1,
					default: frappe.datetime.month_start(),
				},
				{
					fieldname: "auto_submit",
					label: "Tự submit Salary Slip",
					fieldtype: "Check",
					default: 0,
				},
				{
					fieldname: "preview_html",
					fieldtype: "HTML",
					options: `
						<div class="ph-hrm-payroll-preview is-empty" data-payroll-preview>
							<div class="ph-hrm-section-title">Preview tính lương</div>
							<div class="ph-hrm-meta">Chọn nhân sự và tháng lương để xem nhanh cách hệ thống tính ra lương.</div>
						</div>
					`,
				},
			],
			primary_action_label: "Tính lương",
			primary_action: async (values) => {
				await generatePayrollFromDialog(page, dialog, values);
			},
		});
		dialog.show();
		togglePayrollEmployeeField(dialog, 1);
		dialog.get_field("all_employees").$input.on("change", () => {
			togglePayrollEmployeeField(dialog, dialog.get_value("all_employees"));
		});
		dialog.get_field("employee").$input.on("change", () => updatePayrollPreview(dialog));
		dialog.get_field("month").$input.on("change", () => updatePayrollPreview(dialog));
	}

	async function generatePayrollFromDialog(page, dialog, values) {
		frappe.dom.freeze("Đang tính lương tự động...");
		try {
			let response;
			if (!values.all_employees && values.employee) {
				response = await frappe.call({
					method: "pharma_vn.api.payroll.generate_salary_slip",
					args: {
						employee: values.employee,
						month: values.month,
						auto_submit: values.auto_submit,
					},
				});
				await syncPayrollRecord(response.message, values.month);
				frappe.show_alert({
					message: `Đã tạo Salary Slip ${response.message.salary_slip}`,
					indicator: "green",
				});
			} else {
				response = await frappe.call({
					method: "pharma_vn.api.payroll.generate_salary_slips",
					args: {
						month: values.month,
						auto_submit: values.auto_submit,
					},
				});
				const generated = response.message.generated || [];
				const synced = response.message.records_synced || [];
				frappe.show_alert({
					message: `Đã tạo ${generated.length} Salary Slip${synced.length ? ` và đồng bộ ${synced.length} bảng lương` : ""}`,
					indicator: "green",
				});
			}

			dialog.hide();
			await refreshEntityData(page, "hrm-payroll");
		} catch (error) {
			frappe.msgprint({
				title: "Không thể tính lương",
				indicator: "red",
				message:
					error?.message ||
					"Site hiện chưa có đầy đủ DocType Payroll chuẩn như Salary Slip. Hãy cài HR/Payroll rồi migrate lại.",
			});
		} finally {
			frappe.dom.unfreeze();
		}
	}

	function togglePayrollEmployeeField(dialog, isAllEmployees) {
		const employeeField = dialog.get_field("employee");
		if (!employeeField) {
			return;
		}
		employeeField.df.read_only = Boolean(isAllEmployees);
		employeeField.refresh();
		if (isAllEmployees) {
			dialog.set_value("employee", "");
			employeeField.$wrapper.find("input").prop("disabled", true).attr("placeholder", "Sẽ tính cho tất cả nhân viên");
			renderPayrollPreviewState(
				dialog,
				"Preview chỉ áp dụng khi tính riêng từng nhân sự. Hãy bỏ tick 'Tính lương toàn bộ nhân viên' để xem chi tiết."
			);
		} else {
			employeeField.$wrapper.find("input").prop("disabled", false).attr("placeholder", "");
			updatePayrollPreview(dialog);
		}
	}

	async function updatePayrollPreview(dialog) {
		if (dialog.get_value("all_employees")) {
			return;
		}
		const employee = dialog.get_value("employee");
		const month = dialog.get_value("month");
		if (!employee || !month) {
			renderPayrollPreviewState(dialog, "Chọn nhân sự và tháng lương để xem preview.");
			return;
		}

		renderPayrollPreviewState(dialog, "Đang tải preview...", true);
		try {
			const response = await frappe.call({
				method: "pharma_vn.api.payroll.preview_salary",
				args: {
					employee,
					from_date: frappe.datetime.month_start(month),
					to_date: frappe.datetime.month_end(month),
				},
			});
			renderPayrollPreview(dialog, response.message || {});
		} catch (error) {
			renderPayrollPreviewState(dialog, error?.message || "Không lấy được preview tính lương.");
		}
	}

	function renderPayrollPreview(dialog, breakdown) {
		const wrapper = dialog.$wrapper.find("[data-payroll-preview]");
		const rows = [
			{ label: "Công thực tế", value: formatNumberText(breakdown.payable_working_days || 0, 0) },
			{ label: "Công chuẩn tháng", value: formatNumberText(breakdown.standard_working_days || 0, 0) },
			{ label: "Lương hợp đồng", value: formatCurrencyText(breakdown.contract_base_salary || 0) },
			{ label: "Lương cơ bản sau công thức", value: formatCurrencyText(breakdown.base_salary || 0) },
		];
		wrapper.removeClass("is-empty").html(`
			<div class="ph-hrm-section-title">Preview tính lương</div>
			<div class="ph-hrm-preview-grid">
				${rows
					.map(
						(item) => `
							<div class="ph-hrm-preview-card">
								<div class="ph-hrm-meta">${escapeHtml(item.label)}</div>
								<div class="ph-hrm-label">${escapeHtml(item.value)}</div>
							</div>
						`
					)
					.join("")}
			</div>
		`);
	}

	function renderPayrollPreviewState(dialog, message, isLoading = false) {
		const wrapper = dialog.$wrapper.find("[data-payroll-preview]");
		wrapper.toggleClass("is-empty", true).html(`
			<div class="ph-hrm-section-title">Preview tính lương</div>
			<div class="ph-hrm-meta ${isLoading ? "text-warning" : ""}">${escapeHtml(message)}</div>
		`);
	}

	async function openPayrollFormulaDialog() {
		const response = await frappe.call({
			method: "pharma_vn.api.payroll.get_formula_settings",
		});
		const payload = response.message || {};
		const formulas = payload.formulas || [];
		const allowedFunctions = payload.allowed_functions || [];
		let activeFieldname = formulas[0]?.fieldname || null;
		const dialog = new frappe.ui.Dialog({
			title: "Công thức tính lương",
			size: "large",
			fields: [
				{
					fieldname: "formula_help",
					fieldtype: "HTML",
					options: `
						<div class="ph-hrm-formula-help">
							<div><strong>Cách dùng:</strong> Chọn biến ở các bảng bên dưới để chèn vào công thức. Công thức sẽ ảnh hưởng trực tiếp tới lần tính lương tiếp theo.</div>
							<div class="text-muted">Biến được hiển thị bằng tiếng Việt trong ngoặc vuông, ví dụ: <code>[Lương cơ bản]</code>.</div>
						</div>
					`,
				},
				...formulas.flatMap((item) => [
					{
						fieldname: `${item.fieldname}_label`,
						fieldtype: "HTML",
						options: `
							<div class="ph-hrm-formula-block-head">
								<div class="ph-hrm-label">${escapeHtml(item.label)}</div>
								<div class="ph-hrm-meta">Bấm vào biến để chèn vào ô công thức đang chọn.</div>
								<div class="ph-hrm-formula-groups">
									${(item.variable_groups || [])
										.map(
											(group) => `
												<div class="ph-hrm-formula-group">
													<div class="ph-hrm-formula-group-title">${escapeHtml(group.group)}</div>
													<div class="ph-hrm-formula-chip-list">
														${(group.items || [])
															.map(
																(variable) => `
																	<button
																		class="btn btn-default btn-xs ph-hrm-formula-chip"
																		type="button"
																		data-insert-token="${escapeHtml(variable.token)}"
																		data-target-field="${item.fieldname}"
																	>${escapeHtml(variable.label)}</button>
																`
															)
															.join("")}
													</div>
												</div>
											`
										)
										.join("")}
								</div>
								<div class="ph-hrm-formula-group">
									<div class="ph-hrm-formula-group-title">Hàm mẫu</div>
									<div class="ph-hrm-formula-chip-list">
										${allowedFunctions
											.map(
												(fn) => `
													<button
														class="btn btn-default btn-xs ph-hrm-formula-chip"
														type="button"
														data-insert-token="${escapeHtml(fn.token)}"
														data-target-field="${item.fieldname}"
													>${escapeHtml(fn.label)}</button>
												`
											)
											.join("")}
									</div>
								</div>
							</div>
						`,
					},
					{
						fieldname: item.fieldname,
						label: item.label,
						fieldtype: "Small Text",
						reqd: 1,
						default: item.formula || "",
						description: `Ví dụ: ${escapeHtml(item.formula || "")}`,
					},
				]),
			],
			primary_action_label: "Lưu công thức",
			primary_action: async (values) => {
				const rows = formulas.map((item) => ({
					fieldname: item.fieldname,
					formula: values[item.fieldname],
				}));
				await frappe.call({
					method: "pharma_vn.api.payroll.save_formula_settings",
					args: {
						formulas: JSON.stringify(rows),
					},
				});
				frappe.show_alert({
					message: "Đã cập nhật công thức tính lương",
					indicator: "green",
				});
				dialog.hide();
			},
		});
		dialog.show();

		formulas.forEach((item) => {
			const field = dialog.get_field(item.fieldname);
			field.$input.on("focus click", () => {
				activeFieldname = item.fieldname;
			});
		});

		dialog.$wrapper.find("[data-insert-token]").on("click", function () {
			const token = $(this).attr("data-insert-token");
			const targetField = activeFieldname || $(this).attr("data-target-field");
			if (!token || !targetField) {
				return;
			}

			const field = dialog.get_field(targetField);
			const input = field?.$input?.get?.(0);
			if (!input) {
				return;
			}

			insertTokenAtCursor(input, token);
			field.set_value(input.value);
			input.focus();
		});
	}

	function insertTokenAtCursor(input, token) {
		const start = input.selectionStart ?? input.value.length;
		const end = input.selectionEnd ?? input.value.length;
		const currentValue = input.value || "";
		const spacerBefore = start > 0 && !/\s|\(|\+|\-|\*|\/$/.test(currentValue.slice(start - 1, start)) ? " " : "";
		const spacerAfter = end < currentValue.length && !/[\s\)\+\-\*\/]/.test(currentValue.slice(end, end + 1)) ? " " : "";
		input.value = `${currentValue.slice(0, start)}${spacerBefore}${token}${spacerAfter}${currentValue.slice(end)}`;
		const nextCursor = start + spacerBefore.length + token.length;
		input.setSelectionRange(nextCursor, nextCursor);
	}

	async function deleteListRecord(page, state, config, recordName) {
		if (!recordName) {
			return;
		}
		const confirmed = window.confirm("Xóa hồ sơ này?");
		if (!confirmed) {
			return;
		}

		if (config.tools === "payroll") {
			await frappe.call({
				method: "pharma_vn.api.payroll.delete_payroll_record",
				args: { record_name: recordName },
			});
		} else {
			await frappe.call({
				method: "pharma_vn.api.hrm.delete_record",
				args: { page_key: state.pageName, record_name: recordName },
			});
		}

		frappe.show_alert({ message: "Đã xóa hồ sơ", indicator: "green" });
		await refreshEntityData(page, state.pageName);
	}

	async function syncPayrollRecord(generateResponse, month) {
		const breakdown = generateResponse?.breakdown || {};
		if (!generateResponse?.salary_slip || !breakdown.employee) {
			return;
		}

		const monthLabel = frappe.datetime.str_to_user(month).slice(3, 10) || month;
		await frappe.call({
			method: "pharma_vn.api.hrm.save_record",
			args: {
				page_key: "hrm-payroll",
				doc: {
					name: generateResponse.salary_slip,
					payroll_title: `${breakdown.employee_name || breakdown.employee} - ${monthLabel}`,
					employee_name: breakdown.employee_name || breakdown.employee,
					employee_code: breakdown.employee,
					status: generateResponse.docstatus === 1 ? "Paid" : "Calculated",
					company: breakdown.company,
					pay_period: month,
					posting_date: breakdown.to_date,
					base_salary: breakdown.base_salary,
					allowance_amount: breakdown.allowance_total,
					deduction_amount: breakdown.total_deduction,
					net_salary: breakdown.net_salary,
					notes: `Salary Slip: ${generateResponse.salary_slip}`,
				},
			},
		});
	}

	function collectForm(wrapper, config, currentDoc) {
		const doc = Object.assign({}, currentDoc);
		getFields(config).forEach((fieldDef) => {
			doc[fieldDef.name] = wrapper.find(`[data-fieldname="${fieldDef.name}"]`).val();
		});
		return doc;
	}

	function validateForm(doc, config) {
		const required = getFields(config).filter((fieldDef) => fieldDef.required);
		for (const fieldDef of required) {
			if (!doc[fieldDef.name]) {
				frappe.msgprint(`${fieldDef.label} là bắt buộc`);
				return false;
			}
		}
		return true;
	}

	async function saveRecord(page, state, config, doc) {
		const statusEl = $(page.wrapper).find('[data-region="status"]');
		statusEl.text("Đang lưu...");
		await frappe.call({
			method: "pharma_vn.api.hrm.save_record",
			args: { page_key: state.pageName, doc },
		});
		frappe.show_alert({ message: "Đã lưu hồ sơ", indicator: "green" });
		await refreshEntityData(page, state.pageName);
	}

	async function loadActiveReport(page, forceReload = false) {
		const state = page.wrapper.__hrmState || {};
		const { selectedModule, selectedTemplate } = getActiveReportSelection(state);
		if (!selectedModule || !selectedTemplate?.id) {
			return;
		}
		if (!forceReload && state.reportData && state.reportData.report_id === selectedTemplate.id && state.reportData.page_key === selectedModule.page_key) {
			return;
		}
		state.isReportLoading = true;
		rerender(page.wrapper, page, "hrm-reports");
		try {
			const response = await frappe.call({
				method: "pharma_vn.api.hrm.get_report_data",
				args: {
					page_key: selectedModule.page_key,
					report_id: selectedTemplate.id,
					filters: state.reportFilters || getDefaultReportFilters(),
				},
			});
			state.reportData = response.message || null;
		} finally {
			state.isReportLoading = false;
			rerender(page.wrapper, page, "hrm-reports");
		}
	}

	function exportActiveReport(page, exportFormat) {
		const state = page.wrapper.__hrmState || {};
		const { selectedModule, selectedTemplate } = getActiveReportSelection(state);
		if (!selectedModule || !selectedTemplate?.id) {
			frappe.msgprint("Chọn một mẫu report trước khi export.");
			return;
		}
		const query = new URLSearchParams({
			page_key: selectedModule.page_key,
			report_id: selectedTemplate.id,
			export_format: exportFormat || "xlsx",
			filters: JSON.stringify(state.reportFilters || getDefaultReportFilters()),
		});
		window.open(`/api/method/pharma_vn.api.hrm.export_report?${query.toString()}`, "_blank");
	}

	async function refreshEntityData(page, pageName) {
		const data = await frappe.call({
			method: "pharma_vn.api.hrm.get_page_data",
			args: { page_key: pageName },
		});
		if (pageName === "hrm-reports") {
			const previousState = page.wrapper.__hrmState || {};
			const catalog = data.message.catalog || [];
			const selectedReportKey = previousState.selectedReportKey || catalog?.[0]?.page_key || "";
			const selectedModule = catalog.find((item) => item.page_key === selectedReportKey) || catalog?.[0] || {};
			const selectedTemplateId =
				(selectedModule.sample_reports || []).some((item) => item.id === previousState.selectedTemplateId)
					? previousState.selectedTemplateId
					: selectedModule.sample_reports?.[0]?.id || "";
			page.wrapper.__hrmState = {
				pageName,
				reportCatalog: catalog,
				selectedReportKey,
				selectedTemplateId,
				reportFilters: previousState.reportFilters || getDefaultReportFilters(),
				reportData: previousState.reportData || null,
				isReportLoading: false,
			};
			rerender(page.wrapper, page, pageName);
			await loadActiveReport(page);
			return;
		}
		page.wrapper.__hrmState = {
			pageName,
			records: data.message.records || [],
			formDoc: getDefaultDoc(getConfig(pageName)),
			showForm: false,
			deviceConfig: page.wrapper.__hrmState?.deviceConfig || getDefaultDeviceConfig(),
		};
		rerender(page.wrapper, page, pageName);
	}

	function showNewForm(page, state, config) {
		state.formDoc = getDefaultDoc(config);
		state.showForm = true;
		rerender(page.wrapper, page, state.pageName);
	}

	function hideForm(page, state, config) {
		state.formDoc = getDefaultDoc(config);
		state.showForm = false;
		rerender(page.wrapper, page, state.pageName);
	}

	function getDefaultDeviceConfig() {
		const saved = window.localStorage.getItem("pharma_vn_hrm_attendance_device");
		if (saved) {
			try {
				return JSON.parse(saved);
			} catch (e) {
				// ignore invalid local state
			}
		}
		return {
			protocol: "http",
			ip_address: "",
			port: "80",
			endpoint: "/api/attendance",
			auth_token: "",
			timeout: "8",
		};
	}

	function saveDeviceConfig(config) {
		window.localStorage.setItem("pharma_vn_hrm_attendance_device", JSON.stringify(config || {}));
	}

	async function importAttendanceFile(page, fileUrl) {
		frappe.dom.freeze("Đang import chấm công...");
		try {
			const response = await frappe.call({
				method: "pharma_vn.api.hrm.import_attendance_file",
				args: { file_url: fileUrl },
			});
			frappe.show_alert({
				message: `Đã import ${response.message.inserted_count} dòng chấm công`,
				indicator: "green",
			});
			await refreshEntityData(page, "hrm-attendance");
		} finally {
			frappe.dom.unfreeze();
		}
	}

	async function syncAttendanceDevice(page, deviceConfig) {
		frappe.dom.freeze("Đang đồng bộ máy chấm công...");
		try {
			const response = await frappe.call({
				method: "pharma_vn.api.hrm.sync_attendance_device",
				args: { device_config: deviceConfig },
			});
			frappe.show_alert({
				message: `Đã đồng bộ ${response.message.inserted_count} bản ghi từ IP LAN`,
				indicator: "green",
			});
			await refreshEntityData(page, "hrm-attendance");
		} finally {
			frappe.dom.unfreeze();
		}
	}

	async function loadDashboard(page, pageName) {
		const data = await frappe.call({
			method: "pharma_vn.api.hrm.get_page_data",
			args: { page_key: pageName },
		});
		page.wrapper.__hrmState = {
			pageName,
			stats: data.message.stats || [],
			recentRecords: data.message.recent_records || [],
			reports: data.message.reports || [],
		};
		rerender(page.wrapper, page, pageName);
	}

	function rerender(wrapper, page, pageName) {
		const state = wrapper.__hrmState || {};
		const config = getConfig(pageName);
		page.set_title(config.title);
		if (page.clear_primary_action) {
			page.clear_primary_action();
		}
		if (page.clear_secondary_action) {
			page.clear_secondary_action();
		}
		if (config.is_dashboard) {
			renderDashboard($(wrapper), page, state, config);
			page.set_primary_action("Làm mới", () => loadDashboard(page, pageName));
			return;
		}
		if (config.is_reports) {
			renderReportsPage($(wrapper), page, state, config);
			page.set_primary_action("Làm mới", () => refreshEntityData(page, pageName));
			return;
		}
		renderEntityPage($(wrapper), page, state, config);
		page.set_primary_action(state.showForm ? "Lưu hồ sơ" : "Tạo mới", () => {
			if (state.showForm) {
				$(wrapper).find('[data-action="save"]').first().trigger("click");
				return;
			}
			showNewForm(page, state, config);
		});
		if (pageName === "hrm-payroll" && !state.showForm) {
			page.set_secondary_action("Tính lương tự động", () => {
				openPayrollDialog(page);
			});
			return;
		}
		if (state.showForm) {
			page.set_secondary_action("Đóng", () => {
				hideForm(page, state, config);
			});
		}
	}

	pharma_vn.hrm.initPage = async function (wrapper, pageName) {
		const page = frappe.ui.make_app_page({
			parent: wrapper,
			title: getConfig(pageName).title,
			single_column: true,
		});
		wrapper.__hrmPage = page;
		wrapper.__hrmState = wrapper.__hrmState || { pageName };
		if (getConfig(pageName).is_dashboard) {
			await loadDashboard(page, pageName);
			return;
		}
		if (getConfig(pageName).is_reports) {
			await refreshEntityData(page, pageName);
			return;
		}
		await refreshEntityData(page, pageName);
	};
})();
